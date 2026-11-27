"""Thin-mode TLS connection and rollback-only M1 vector smoke check."""

import math
from pathlib import Path
from uuid import uuid4

import oracledb

from app.config import ConfigurationError, OracleSettings
from app.embeddings import MiniLM


def connection_params(settings: OracleSettings) -> oracledb.PoolParams:
    params = oracledb.PoolParams(
        user=settings.user, password=settings.password,
        config_dir=settings.wallet_dir, wallet_location=settings.wallet_dir,
        wallet_password=settings.wallet_password,
        tcp_connect_timeout=10, retry_count=0, ssl_server_dn_match=True,
    )
    params.parse_connect_string(settings.dsn)
    protocols = params.protocol if isinstance(params.protocol, list) else [params.protocol]
    if not protocols or any(protocol != "tcps" for protocol in protocols):
        raise ConfigurationError("Oracle connection must use TLS (tcps)")
    # A connect descriptor can override constructor settings during parsing.
    params.set(user=settings.user, password=settings.password,
               tcp_connect_timeout=10, retry_count=0, ssl_server_dn_match=True)
    return params


def connect(settings: OracleSettings) -> oracledb.Connection:
    connection = oracledb.connect(params=connection_params(settings))
    connection.call_timeout = 10000
    return connection


def initialize_schema(connection: oracledb.Connection) -> None:
    """Explicit DDL: Oracle commits DDL. Run once on a dedicated project schema."""
    path = Path(__file__).resolve().parents[1] / "sql" / "001_retrieval.sql"
    with connection.cursor() as cursor:
        for statement in path.read_text(encoding="utf-8").split(";"):
            if statement.strip():
                cursor.execute(statement.strip())


def vector_smoke(connection: oracledb.Connection, model: MiniLM) -> dict:
    """Insert synthetic probes into the real table, exact search, always rollback.

    Probes test vector transport/ranking, not corpus retrieval quality. Call only
    on a fresh dedicated connection: rollback also undoes other pending writes.
    """
    if connection.autocommit:
        raise ValueError("Smoke check requires autocommit disabled")
    texts = [
        "A connection pool reuses database connections and limits concurrent sessions.",
        "A sunflower grows toward the sun in a garden.",
    ]
    vectors = model.encode(texts)
    run_id = uuid4().hex
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO documents (document_id, title, source_url, provenance) "
                "VALUES (:1, :2, :3, :4)",
                [run_id, "Synthetic M1 probe", None, "Project-authored test fixture; not corpus evidence"],
            )
            cursor.executemany(
                "INSERT INTO document_chunks "
                "(chunk_id, document_id, chunk_number, chunk_text, embedding, embedding_version) "
                "VALUES (:1, :2, :3, :4, :5, :6)",
                [(run_id + str(i), run_id, i, text, vector, model.fingerprint)
                 for i, (text, vector) in enumerate(zip(texts, vectors))],
            )
            cursor.execute(
                "SELECT chunk_number, VECTOR_DISTANCE(embedding, :vector, COSINE) AS distance "
                "FROM document_chunks WHERE document_id = :document_id "
                "AND embedding_version = :version ORDER BY distance FETCH EXACT FIRST 2 ROWS ONLY",
                vector=vectors[0], document_id=run_id, version=model.fingerprint,
            )
            rows = cursor.fetchall()
            if (len(rows) != 2 or any(not math.isfinite(row[1]) for row in rows)
                    or rows[0][0] != 0 or abs(rows[0][1]) > 1e-5
                    or rows[1][1] <= rows[0][1]):
                raise ValueError("Oracle vector roundtrip or nearest-neighbor check failed")
            return {"database_version": connection.version, "rows": len(rows),
                    "nearest_chunk": rows[0][0], "self_distance": rows[0][1]}
    finally:
        connection.rollback()
