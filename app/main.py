"""Local technical knowledge retrieval and grounded answers."""

import logging
import os
import re
from contextlib import asynccontextmanager
from pathlib import Path
from threading import BoundedSemaphore
from time import perf_counter
from typing import Literal

import oracledb
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.answer import (
    PROMPT_VERSION, SYNTHESIS_PROMPT_VERSION, AnswerProvider, AnswerResponse, Claim, InvalidSelection, ProviderFailure,
    SourcedCitation, eligible_hits, public_evidence,
    validated_selection,
)
from app.config import OracleSettings
from app.corpus import DEFAULT_CORPUS, chunk_text, load_documents
from app.embeddings import MiniLM
from app.gemini import Gemini
from app.library import DocumentID, Library, router as library_router
from app.oracle import connection_params
from app.request_limits import RequestLimits, within_deadline
from app.search import SearchHit, search

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = OracleSettings.from_env()
    params = connection_params(settings)
    schema = os.getenv("ORACLE_DATA_SCHEMA", "").strip().upper()
    if schema and not re.fullmatch(r"[A-Z][A-Z0-9_]{0,29}", schema):
        raise ValueError("ORACLE_DATA_SCHEMA must be an unquoted Oracle schema name")

    def set_schema(connection, _tag):
        connection.call_timeout = 10000
        with connection.cursor() as cursor:
            cursor.execute(f"ALTER SESSION SET CURRENT_SCHEMA = {schema}")

    threshold = float(os.environ.get("SIMILARITY_THRESHOLD", "0.25"))
    if not -1 <= threshold <= 1:
        raise ValueError("SIMILARITY_THRESHOLD must be between -1 and 1")
    app.state.model = MiniLM()
    app.state.threshold = threshold
    app.state.admission = BoundedSemaphore(1)
    try:
        pool = oracledb.create_pool(params=params, min=1, max=1, increment=1,
                                    getmode=oracledb.POOL_GETMODE_TIMEDWAIT,
                                    wait_timeout=3000, ping_timeout=3000,
                                    session_callback=set_schema if schema else None)
    except (oracledb.Error, OSError):
        raise RuntimeError("Oracle pool startup failed. Run the Oracle smoke check.") from None
    app.state.pool = pool
    provider = None
    try:
        # Thin can fill its initial pool in the background. Verify a usable
        # connection before accepting requests.
        try:
            with pool.acquire() as connection:
                connection.call_timeout = 10000
                connection.ping()
        except (oracledb.Error, OSError):
            raise RuntimeError("Oracle pool verification failed. Run the Oracle smoke check.") from None
        app.state.public_docs = frozenset(
            (doc.title, doc.source_url, part)
            for doc in load_documents(DEFAULT_CORPUS)
            for part in chunk_text(doc.text, app.state.model)
        )
        provider = Gemini.from_env()
        app.state.provider = provider
        app.state.generation_slot = BoundedSemaphore(1)
        app.state.next_generation_at = 0.0
        app.state.library = Library(settings, schema, app.state.model, app.state.admission)
        app.state.ready = True
        yield
    finally:
        app.state.ready = False
        try:
            library = getattr(app.state, "library", None)
            if library is not None and library.task is not None:
                await library.task
            if provider is not None:
                provider.close()
        finally:
            pool.close()


app = FastAPI(title="Technical Knowledge Search", lifespan=lifespan)
app.add_middleware(RequestLimits)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])
app.include_router(library_router)
UI_DIR = Path(__file__).with_name("ui")


@app.get("/", include_in_schema=False)
async def demo():
    return FileResponse(UI_DIR / "index.html", headers={
        "Content-Security-Policy": "default-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
        "X-Content-Type-Options": "nosniff",
    })


@app.get("/assets/demo.js", include_in_schema=False)
async def demo_script():
    return FileResponse(UI_DIR / "demo.js", media_type="text/javascript")


@app.get("/assets/demo.css", include_in_schema=False)
async def demo_styles():
    return FileResponse(UI_DIR / "demo.css", media_type="text/css")


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)
    query: str = Field(min_length=1, max_length=2048)
    top_k: int = Field(default=5, ge=1, le=10)
    document_ids: list[DocumentID] = Field(default_factory=list, max_length=16)
    document_type: Literal["seed", "pdf", "txt", "md"] | None = None
    strategy: Literal["semantic", "hybrid"] = "semantic"


class SearchResponse(BaseModel):
    request_id: str
    status: Literal["ok", "insufficient_evidence"]
    results: list[SearchHit]
    latency_ms: float


class AnswerRequest(SearchRequest):
    mode: Literal["extractive", "synthesis"] = "extractive"
    public_question: bool = Field(
        default=False,
        description="Confirm this test question is public and may be sent to the external provider.",
    )


class ErrorResponse(BaseModel):
    detail: str


LIMIT_RESPONSES = {code: {"model": ErrorResponse} for code in (413, 422, 429, 503, 504)}


@app.get("/health/live")
async def live():
    return {"status": "alive"}


def check_readiness(request: Request):
    state = request.app.state
    if not getattr(state, "ready", False) or not state.admission.acquire(blocking=False):
        raise HTTPException(503, "Service is not ready")
    try:
        with state.pool.acquire() as connection, connection.cursor() as cursor:
            connection.call_timeout = 2000
            cursor.execute("SELECT document_type, page_number FROM documents JOIN document_chunks USING (document_id) WHERE 1 = 0")
    except (oracledb.Error, OSError):
        raise HTTPException(503, "Service is not ready") from None
    finally:
        state.admission.release()
    return {"status": "ready"}


@app.get("/health/ready")
async def ready(request: Request):
    return await within_deadline(request, check_readiness, request)


@app.exception_handler(RequestValidationError)
async def invalid_request(request: Request, error: RequestValidationError):
    return JSONResponse({"detail": "Invalid search request"}, status_code=422)


def retrieve(payload: SearchRequest, request: Request, request_id: str, *, for_answer: bool = False) -> list[SearchHit]:
    state = request.app.state
    if not state.admission.acquire(blocking=False):
        raise HTTPException(503, "Search is busy")
    try:
        if perf_counter() >= request.state.deadline:
            raise HTTPException(504, "Request deadline exceeded")
        with state.pool.acquire() as connection:
            connection.call_timeout = 10000
            results = search(connection, state.model, payload.query, payload.top_k, state.threshold,
                             document_ids=payload.document_ids, document_type=payload.document_type,
                             strategy=payload.strategy, candidate_limit=16 if for_answer else None)
    except ValueError:
        raise HTTPException(422, "Query could not be embedded within model limits") from None
    except (oracledb.Error, OSError) as error:
        code = getattr(error.args[0], "full_code", type(error).__name__) if error.args else type(error).__name__
        logger.warning("Oracle search unavailable request_id=%s code=%s", request_id, code)
        raise HTTPException(503, "Search database unavailable") from None
    finally:
        state.admission.release()
    return results


def search_work(payload: SearchRequest, request: Request) -> SearchResponse:
    request_id = request.state.request_id
    started = perf_counter()
    results = retrieve(payload, request, request_id)
    return SearchResponse(request_id=request_id, status="ok" if results else "insufficient_evidence",
                          results=results, latency_ms=round((perf_counter() - started) * 1000, 2))


@app.post("/api/v1/search", response_model=SearchResponse, responses=LIMIT_RESPONSES)
async def search_route(payload: SearchRequest, request: Request):
    return await within_deadline(request, search_work, payload, request)


def answer_work(payload: AnswerRequest, request: Request) -> AnswerResponse | JSONResponse:
    request_id = request.state.request_id
    started = perf_counter()
    state = request.app.state
    library = getattr(state, "library", None)
    revision = library.revision if library else None
    hits = retrieve(payload, request, request_id, for_answer=True)
    retrieved = perf_counter()
    eligible = eligible_hits(hits, state.public_docs)
    evidence = public_evidence(eligible, state.public_docs, payload.query)
    prepared = perf_counter()
    response = AnswerResponse(request_id=request_id, status="insufficient_evidence",
                              reason="no_matching_evidence", sources=hits[:payload.top_k])
    attempted = False
    provider_ms = None

    def limited(detail):
        response.latency_ms = round((perf_counter() - started) * 1000, 2)
        return JSONResponse(status_code=429, headers={"Retry-After": "10"},
                            content={**response.model_dump(mode="json"), "detail": detail})

    if hits and not eligible:
        response.status, response.reason = "degraded", "no_eligible_documents"
    elif eligible and not evidence:
        response.reason = "no_quotable_evidence"
    if evidence:
        response.status = "degraded"
        provider: AnswerProvider | None = state.provider
        response.reason = "question_consent_required" if not payload.public_question else "provider_not_configured"
        if payload.public_question and provider is not None:
            if not state.generation_slot.acquire(blocking=False):
                response.reason = "provider_rate_limited"
                return limited("Generation is busy")
            privacy_acquired = False
            try:
                if library:
                    privacy_acquired = library.privacy.acquire(blocking=False)
                    if not privacy_acquired or library.revision != revision:
                        raise HTTPException(409, "Document permissions changed. Try again.")
                now = perf_counter()
                if now >= request.state.deadline:
                    raise HTTPException(504, "Request deadline exceeded")
                if now < state.next_generation_at:
                    response.reason = "provider_rate_limited"
                    return limited("Generation cooldown")
                state.next_generation_at = now + 10
                attempted = True
                try:
                    output = provider.generate(payload.query, evidence, deadline=request.state.deadline, mode=payload.mode)
                finally:
                    provider_ms = round((perf_counter() - now) * 1000, 2)
                logger.info("generation request_id=%s prompt_version=%s input_tokens=%s output_tokens=%s total_tokens=%s",
                            request_id, SYNTHESIS_PROMPT_VERSION if payload.mode == "synthesis" else PROMPT_VERSION,
                            output.input_tokens, output.output_tokens, output.total_tokens)
                citations, unanswered = validated_selection(output, evidence, payload.mode)
                sources = {hit.chunk_id: hit for hit in hits if hit.chunk_id in evidence}
                response.status = "ok" if citations else "insufficient_evidence"
                response.reason = ("partial_answer" if unanswered else None) if citations else "provider_abstained"
                response.unanswered = unanswered
                response.citations = [SourcedCitation(
                    chunk_id=item.chunk_id, quote=item.quote, document_id=sources[item.chunk_id].document_id,
                    document_title=sources[item.chunk_id].title, page_number=sources[item.chunk_id].page_number,
                    claim=item.claim if isinstance(item, Claim) else None,
                ) for item in citations]
                response.answer = " ".join(
                    item.claim if isinstance(item, Claim) else item.quote for item in citations
                ) if citations else None
                response.sources = list(sources.values())
            except ProviderFailure as error:
                response.reason = {
                    "http_429": "provider_rate_limited", "timeout": "provider_timeout",
                    "deadline": "provider_timeout", "input_budget": "input_budget",
                }.get(str(error), "provider_failure")
                logger.warning("generation_failed request_id=%s category=%s", request_id, error)
            except InvalidSelection as error:
                response.reason = "validation_rejected"
                logger.warning("generation_failed request_id=%s category=invalid_selection reason=%s", request_id, error)
            finally:
                if privacy_acquired:
                    library.privacy.release()
                state.generation_slot.release()
    response.latency_ms = round((perf_counter() - started) * 1000, 2)
    logger.info(
        "answer_outcome request_id=%s strategy=%s candidates=%d eligible=%d context_chunks=%d "
        "context_documents=%d provider_attempted=%s reason=%s retrieval_ms=%.2f context_ms=%.2f provider_ms=%s",
        request_id, payload.strategy, len(hits), len(eligible), len(evidence),
        len({hit.document_id for hit in eligible if hit.chunk_id in evidence}), attempted,
        response.reason, (retrieved - started) * 1000, (prepared - retrieved) * 1000, provider_ms,
    )
    return response


@app.post("/api/v1/answer", response_model=AnswerResponse,
          responses={**LIMIT_RESPONSES, 429: {"model": AnswerResponse}})
async def answer_route(payload: AnswerRequest, request: Request):
    return await within_deadline(request, answer_work, payload, request)
