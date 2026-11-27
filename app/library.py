"""Bounded local ingestion and Oracle-backed document metadata."""
import asyncio
import json
import logging
import os
import re
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import replace
from pathlib import PurePath
from threading import Lock
from time import perf_counter, sleep
from typing import Annotated
from uuid import uuid4

import oracledb
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool

from app.config import OracleSettings
from app.corpus import chunk_text, digest
from app.oracle import connect
from app.request_limits import within_deadline

router = APIRouter(prefix="/api/v1", tags=["documents"])
logger = logging.getLogger(__name__)
DocumentID = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


def bounded_setting(name: str, default: int, maximum: int) -> int:
    value = int(os.getenv(name, str(default)))
    if not 1 <= value <= maximum:
        raise ValueError(f"{name} must be between 1 and {maximum}")
    return value


def filename_kind(name: str) -> str:
    suffix = PurePath(name).suffix.lower().lstrip(".")
    if (not name or len(name.encode("utf-8")) > 240 or any(c in name for c in "/\\:")
            or any(not c.isprintable() for c in name) or name in {".", ".."}):
        raise ValueError("Invalid filename")
    if suffix not in {"pdf", "txt", "md"}:
        raise ValueError("Choose a PDF, TXT or Markdown file")
    return suffix


def extract(data: bytes, kind: str, max_pages: int, max_chars: int, max_bytes: int):
    if kind == "pdf":
        if not data.startswith(b"%PDF-"):
            raise ValueError("Invalid PDF header")
        try:
            # Do not pass server credentials to the parsing child.
            env = {key: os.environ[key] for key in ("SystemRoot", "WINDIR", "PATH") if key in os.environ}
            result = subprocess.run(
                [sys.executable, "-I", os.path.join(os.path.dirname(__file__), "pdf_extract.py"),
                 str(max_pages), str(max_chars), str(max_bytes)],
                input=data, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env,
                timeout=8, check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except subprocess.TimeoutExpired:
            raise ValueError("PDF parsing time limit exceeded") from None
        if result.returncode:
            raise ValueError({2: "Encrypted PDF is unsupported", 3: f"PDF page limit exceeded ({max_pages} pages)",
                              4: f"Extracted text limit exceeded ({max_chars:,} characters). Try a shorter excerpt.",
                              5: "PDF has no text. OCR is unsupported."
                              }.get(result.returncode, "Malformed or unsupported PDF"))
        record = json.loads(result.stdout)
        return record["page_count"], record["pages"]
    try:
        text = data.decode("utf-8-sig").strip()
    except UnicodeError:
        raise ValueError("Text documents must use UTF-8") from None
    if not text or text.startswith("%PDF-") or any(not c.isprintable() and c not in "\t\r\n" for c in text):
        raise ValueError("Empty or binary text document")
    if len(text) > max_chars:
        raise ValueError(f"Extracted text limit exceeded ({max_chars:,} characters). Try a shorter excerpt.")
    return None, [(None, text)]


class Library:
    def __init__(self, owner: OracleSettings, schema: str, model, admission):
        user, password = os.getenv("ORACLE_WRITE_USER"), os.getenv("ORACLE_WRITE_PASSWORD")
        if bool(user) != bool(password):
            raise ValueError("Configure both ORACLE_WRITE_USER and ORACLE_WRITE_PASSWORD")
        self.settings = replace(owner, user=user, password=password) if user and password else owner
        self.schema, self.model, self.admission = schema, model, admission
        self.max_bytes = bounded_setting("UPLOAD_MAX_BYTES", 5_000_000, 5_000_000)
        self.max_pages = bounded_setting("UPLOAD_MAX_PAGES", 40, 100)
        self.max_chars = bounded_setting("UPLOAD_MAX_CHARS", 120_000, 160_000)
        self.max_chunks = bounded_setting("UPLOAD_MAX_CHUNKS", 128, 128)
        self.jobs: dict[str, dict] = {}
        self.task: asyncio.Task | None = None
        self.busy = False
        self.privacy = Lock()
        self.revision = 0

    @contextmanager
    def writer(self):
        with connect(self.settings) as connection:
            if self.schema:
                with connection.cursor() as cursor:
                    cursor.execute(f"ALTER SESSION SET CURRENT_SCHEMA = {self.schema}")
            yield connection

    @contextmanager
    def model_turn(self):
        # Leave a bounded admission window for fail-fast searches between turns.
        sleep(0.025)
        if not self.admission.acquire(timeout=3):
            raise ValueError("Embedding service is busy. Try again.")
        try:
            yield
        finally:
            self.admission.release()

    def ingest(self, data: bytes, title: str, kind: str):
        page_count, pages = extract(data, kind, self.max_pages, self.max_chars, self.max_bytes)
        # Ignore whitespace-only differences. Preserve page boundaries in the hash.
        content_hash = digest(json.dumps([(page, " ".join(text.split())) for page, text in pages]))
        with self.writer() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT document_id FROM documents WHERE content_hash = :hash", hash=content_hash)
            if row := cursor.fetchone():
                return row[0], True
        rows = []
        for page, text in pages:
            with self.model_turn():
                parts = chunk_text(text, self.model)
            if len(rows) + len(parts) > self.max_chunks:
                raise ValueError(f"Document exceeds the {self.max_chunks}-chunk limit. Try a shorter excerpt.")
            for start in range(0, len(parts), 8):
                batch = parts[start:start + 8]
                with self.model_turn():
                    for chunk, vector in zip(batch, self.model.encode(batch), strict=True):
                        position = len(rows)
                        rows.append((digest(f"{content_hash}:{position}"), content_hash, position,
                                     chunk, vector, self.model.fingerprint, page))
        with self.writer() as connection, connection.cursor() as cursor, connection.cursor() as chunks:
            cursor.execute("SELECT COUNT(*) FROM documents WHERE content_hash IS NOT NULL")
            if cursor.fetchone()[0] >= 24:
                raise ValueError("Library capacity reached")
            cursor.execute(
                """INSERT INTO documents (document_id, title, provenance, document_type,
                           content_hash, page_count, byte_count)
                   VALUES (:id, :title, :provenance, :kind, :hash, :pages, :bytes)""",
                id=content_hash, title=title, provenance="Local upload; publication status unverified",
                kind=kind, hash=content_hash, pages=page_count, bytes=len(data),
            )
            chunks.setinputsizes(None, None, None, oracledb.DB_TYPE_CLOB, None, None, oracledb.DB_TYPE_NUMBER)
            chunks.executemany(
                """INSERT INTO document_chunks (chunk_id, document_id, chunk_number, chunk_text,
                          embedding, embedding_version, page_number) VALUES (:1,:2,:3,:4,:5,:6,:7)""",
                rows, batch_size=8,
            )
            connection.commit()
        return content_hash, False

    async def process(self, job_id: str, data: bytes, title: str, kind: str):
        job = self.jobs[job_id]
        job["status"] = "processing"
        started = perf_counter()
        try:
            doc_id, duplicate = await run_in_threadpool(self.ingest, data, title, kind)
            job.update(status="indexed", document_id=doc_id, duplicate=duplicate)
        except ValueError as error:
            job.update(status="failed", detail=str(error))
        except Exception:
            job.update(status="failed", detail="Document ingestion failed")
        finally:
            job["duration_ms"] = round((perf_counter() - started) * 1000, 2)
            logger.info("ingestion job_id=%s status=%s duration_ms=%s", job_id, job["status"], job["duration_ms"])
            self.busy = False

    def modify(self, doc_id: str, approved: bool | None):
        if not self.privacy.acquire(blocking=False):
            raise HTTPException(409, "An answer is processing. Try again.")
        try:
            with self.writer() as connection, connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE documents SET external_ok = :flag WHERE document_id = :id AND content_hash IS NOT NULL",
                    flag=int(approved is True), id=doc_id,
                )
                if not cursor.rowcount:
                    raise HTTPException(404, "Uploaded document not found")
                if approved is None:
                    cursor.execute("DELETE FROM document_chunks WHERE document_id = :id", id=doc_id)
                    cursor.execute("DELETE FROM documents WHERE document_id = :id", id=doc_id)
                connection.commit()
                self.revision += 1
        finally:
            self.privacy.release()


def local_change(request: Request):
    if request.headers.get("x-library-action") != "1":
        raise HTTPException(403, "Library action header required")
    host = request.headers.get("host", "").lower()
    if not re.fullmatch(r"(?:localhost|127\.0\.0\.1)(?::[0-9]{1,5})?", host):
        raise HTTPException(403, "Local host required")
    origin = request.headers.get("origin")
    if origin and origin != f"{request.url.scheme}://{host}":
        raise HTTPException(403, "Cross-origin library action refused")


@router.post("/documents", status_code=202)
async def upload(request: Request):
    local_change(request)
    if request.headers.get("content-type") != "application/octet-stream":
        raise HTTPException(415, "Send raw file bytes")
    name = request.query_params.get("name", "")
    try:
        kind = filename_kind(name)
    except ValueError as error:
        raise HTTPException(422, str(error)) from None
    library: Library = request.app.state.library
    if library.busy:
        raise HTTPException(429, "Ingestion is busy", headers={"Retry-After": "5"})
    library.busy = True
    scheduled = False
    try:
        body = bytearray()
        try:
            async with asyncio.timeout(max(0, request.state.deadline - perf_counter())):
                async for part in request.stream():
                    if len(body) + len(part) > library.max_bytes:
                        raise HTTPException(413, "Upload size limit exceeded")
                    body.extend(part)
        except TimeoutError:
            raise HTTPException(504, "Upload deadline exceeded") from None
        if not body:
            raise HTTPException(422, "Empty file")
        job_id = uuid4().hex
        if len(library.jobs) >= 64:
            library.jobs.pop(next(iter(library.jobs)))
        library.jobs[job_id] = {"job_id": job_id, "status": "queued"}
        library.task = asyncio.create_task(library.process(job_id, bytes(body), name, kind))
        scheduled = True
        return dict(library.jobs[job_id])
    finally:
        if not scheduled:
            library.busy = False


@router.get("/ingestion/{job_id}")
async def job_status(job_id: str, request: Request):
    job = request.app.state.library.jobs.get(job_id)
    if job is None:
        raise HTTPException(404, "Job not found. Check the indexed library.")
    return dict(job)


def list_indexed(request: Request):
    try:
        with request.app.state.pool.acquire() as connection, connection.cursor() as cursor:
            connection.call_timeout = 5000
            cursor.execute("""SELECT d.document_id, d.title, d.document_type, d.page_count,
                              d.byte_count, d.external_ok, COUNT(c.chunk_id), d.ingested_at
                       FROM documents d JOIN document_chunks c ON c.document_id=d.document_id
                       WHERE d.content_hash IS NOT NULL OR d.source_url IS NOT NULL
                       GROUP BY d.document_id, d.title, d.document_type, d.page_count,
                                d.byte_count, d.external_ok, d.ingested_at
                       ORDER BY d.ingested_at DESC, d.document_id FETCH FIRST 100 ROWS ONLY""")
            keys = ("document_id", "title", "document_type", "page_count", "byte_count",
                    "external_ok", "chunk_count", "ingested_at")
            return [dict(zip(keys, row, strict=True), status="indexed") for row in cursor]
    except (oracledb.Error, OSError):
        raise HTTPException(503, "Library unavailable") from None


@router.get("/documents")
async def list_documents(request: Request):
    return await within_deadline(request, list_indexed, request)


class Eligibility(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    approved_public: bool


def change(library: Library, doc_id: str, approved: bool | None):
    try:
        library.modify(doc_id, approved)
    except (oracledb.Error, OSError):
        raise HTTPException(503, "Library update unavailable") from None
    return {"document_id": doc_id, "external_ok": approved}


@router.patch("/documents/{doc_id}/eligibility")
async def eligibility(doc_id: DocumentID, payload: Eligibility, request: Request):
    local_change(request)
    return await within_deadline(request, change, request.app.state.library, doc_id, payload.approved_public)


@router.delete("/documents/{doc_id}")
async def delete(doc_id: DocumentID, request: Request):
    local_change(request)
    if request.headers.get("x-confirm-delete") != doc_id:
        raise HTTPException(400, "Document deletion must be confirmed")
    return await within_deadline(request, change, request.app.state.library, doc_id, None)
