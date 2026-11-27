"""Prepare corpus in memory, then commit its new documents as one transaction."""

import argparse
import json
import sys
from pathlib import Path

import oracledb

from app.config import OracleSettings
from app.corpus import DEFAULT_CORPUS, chunk_text, digest, load_documents
from app.embeddings import MiniLM
from app.oracle import connect


def ingest(path: Path, model: MiniLM, settings: OracleSettings) -> dict[str, int]:
    prepared = []
    count = 0
    for doc in load_documents(path):
        parts = chunk_text(doc.text, model)
        count += len(parts)
        if count > 256:
            raise ValueError("Corpus exceeds 256 chunks")
        provenance = f"{doc.provenance} | Upstream license: {doc.license}"
        doc_id = digest(json.dumps([doc.title, doc.source_url, provenance, digest(doc.text),
                                    model.fingerprint, "offset-200-30-v1"]))
        prepared.append((doc_id, doc, provenance, parts))
    # Read existing IDs first so repeats skip CPU embedding work as well as writes.
    with connect(settings) as connection, connection.cursor() as cursor:
        pending = []
        for doc_id, doc, provenance, parts in prepared:
            cursor.execute("SELECT COUNT(*) FROM document_chunks WHERE document_id = :id",
                           id=doc_id)
            existing = cursor.fetchone()[0]
            if existing == len(parts):
                continue
            if existing:
                raise ValueError("Existing document has an unexpected chunk count")
            pending.append((doc_id, doc, provenance, parts))
    batches = []
    for doc_id, doc, provenance, parts in pending:
        rows = []
        for start in range(0, len(parts), 8):
            batch = parts[start:start + 8]
            for position, (part, vector) in enumerate(zip(batch, model.encode(batch), strict=True), start):
                rows.append((digest(f"{doc_id}:{position}"), doc_id, position, part,
                             vector, model.fingerprint))
        batches.append(((doc_id, doc.title, doc.source_url, provenance), rows))
    if batches:
        with connect(settings) as connection, connection.cursor() as cursor, connection.cursor() as chunks:
            chunks.setinputsizes(None, None, None, oracledb.DB_TYPE_CLOB, None, None)
            for metadata, rows in batches:
                cursor.execute(
                    "INSERT INTO documents (document_id, title, source_url, provenance) "
                    "VALUES (:1, :2, :3, :4)", metadata,
                )
                chunks.executemany(
                    "INSERT INTO document_chunks (chunk_id, document_id, chunk_number, "
                    "chunk_text, embedding, embedding_version) VALUES (:1, :2, :3, :4, :5, :6)",
                    rows, batch_size=8,
                )
            connection.commit()
    return {"documents": len(prepared), "chunks": count, "inserted_documents": len(batches),
            "inserted_chunks": sum(len(rows) for _, rows in batches)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT_CORPUS)
    args = parser.parse_args()
    try:
        settings = OracleSettings.from_env()
        print(json.dumps(ingest(args.path, MiniLM(), settings)))
    except (oracledb.Error, OSError, ValueError) as error:
        label = getattr(error.args[0], "full_code", type(error).__name__) if error.args else type(error).__name__
        print(f"Ingestion failed ({label}). Check corpus, model cache and Oracle configuration.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
