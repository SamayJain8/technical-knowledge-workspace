# Low-level design
The following source-derived contracts are retained; amendments below override older chunk-size and local setup suggestions.
## 3. End-to-end V1 design

### 3.1 Offline ingestion (independent job)

```text
Curated public technical docs (JSONL/CSV/Markdown/text)
  → loader + source metadata
  → validation / normalize whitespace / reject empty or duplicate docs
  → token-aware chunking (initial experiment ~300–400 tokens, with overlap)
  → local MiniLM embedding in bounded batches (384 floats/chunk)
  → python-oracledb executemany + transaction / failure logging
  → Oracle documents + document_chunks tables
  → verify stored counts, dimensions, source references, sample retrieval
```

Track document IDs, chunk positions, source URL/title/topic/language, ingestion status, content hashes, and embedding revision. Design repeated ingestion to avoid duplicate records. A command-line ingestion job is enough initially; admin upload and background queue processing are enhancements.

### 3.2 Online answering

```text
User / simple web UI
  → POST /api/v1/search or /api/v1/answer
  → FastAPI validation, rate limit, request ID
  → embedding_service: same MiniLM model as ingestion
  → vector_search_service: Oracle cosine-distance top-K (start K=5)
  → relevance threshold / optional metadata filters
  → if inadequate evidence: honest insufficient-evidence response
  → else llm_service: cited, context-grounded prompt with selected chunks
  → answer + source IDs/URLs + similarity scores + latency + request ID
```

First milestone: `/search` returns chunks without any LLM. Next milestone: `/answer` calls LLM. Source links must be real; retrieved content is untrusted data, not instructions to the assistant.

### 3.3 V1 modules

- `app/main.py`: app creation, lifespan and routes.
- `app/config.py`: validated settings from environment; no hardcoded secrets.
- `app/api/search_routes.py`, `health_routes.py`: endpoints and Pydantic schemas.
- `app/services/embedding_service.py`: model loaded once per process; consistent normalization, dimensions, bounded CPU work.
- `app/services/vector_search_service.py`: SQL retrieval, parameter binding, threshold/filters, result mapping.
- `app/services/search_service.py`: orchestration between validation, embed, retrieval, LLM.
- `app/services/llm_service.py`: provider adapter, grounding, timeouts, retries, fallbacks.
- `app/database/oracle_connection.py`: pooled DB connections, initialized per process.
- `ingestion/`: loader, cleaner, chunker, CLI ingestion and failed-row log.
- `sql/`: versioned DDL and indexes.
- `evaluation/`: labeled queries and retrieval benchmark scripts.
- `tests/`: unit, integration, later load tests.
- `frontend/`: simple UI after backend works.
- `.env.example`, `requirements.txt` or locked dependency manifest, `Dockerfile`, `docker-compose.yml`, `README.md`.

Create these **incrementally**, not all as empty scaffolding on day one.


## 4. Core relational/vector data model

**`documents`**: `document_id` PK, `title`, `source_url`, `source_type`, `topic`, `language`, `content_hash`, `ingested_at`, optional licensing/provenance/version metadata.

**`document_chunks`**: `chunk_id` PK, `document_id` FK, `chunk_number`, `chunk_text` CLOB, `embedding VECTOR(384, FLOAT32)`, `embedding_model`, `embedding_version` (+ optional chunk hash/token count). Associate retrieval results with a document/source.

**`ingestion_jobs`** (can follow after initial CLI): `job_id`, `dataset_name`, `status` (`pending`, `running`, `completed`, `failed`), `total_rows`, `processed_rows`, `failed_rows`, start/end timestamps. Keep retry records for invalid rows.

**V2 workload tables** will include workload-run IDs, run configurations, query/request metrics, throughput, p50/p95 latency, failures, concurrent connections, pool utilization, and time windows. Final schema should follow actual simulator data. Avoid hallucinating a preexisting simulator API or table layout.

Example **conceptual** Oracle query (check syntax/driver behavior against installed Oracle release before using):

```sql
SELECT chunk_id, document_id, chunk_text,
       VECTOR_DISTANCE(embedding, :query_vector, COSINE) AS distance
FROM document_chunks
ORDER BY distance
FETCH FIRST 5 ROWS ONLY;
```

Lower cosine distance means a closer vector match. If displaying a score, define precisely how the distance is transformed. Tune any threshold empirically; don't assume `0.60` is universally appropriate. Exact search first; evaluate HNSW/IVF indexing later based on corpus size, recall, latency, and memory.


## 7. APIs (target contracts; refine during development)

| Method / path | Version | Description |
|---|---|---|
| GET `/health/live` | V1 | Process liveness |
| GET `/health/ready` | V1 | DB/model readiness |
| POST `/api/v1/search` | V1 | Query → top-K chunks, scores, source references |
| POST `/api/v1/answer` | V1 | Grounded LLM response with sources |
| POST `/api/v1/feedback` | V1 optional | User helpful/unhelpful rating |
| POST `/api/v1/evaluate` | V1 optional admin-only | Trigger benchmark (or use offline CLI) |
| POST `/api/v1/investigate` | V2 | Orchestrate RAG and read-only SQL evidence |
| GET `/api/v1/ingestion/{job_id}` | V1 later | Check ingestion job status |

Example *illustrative* `/search` result:

```json
{
  "request_id": "example-request-id",
  "query": "What causes database connection exhaustion?",
  "results": [{
    "chunk_id": 42,
    "document_id": 8,
    "title": "Database Connection Pooling Guide",
    "source_url": "https://example.com/placeholder",
    "similarity_score": 0.87,
    "text": "Illustrative retrieved excerpt..."
  }],
  "latency_ms": 125
}
```

*Every number, title and URL above is illustrative; not a measured result or ingested document.*


## Amendments and implementation details
- Token-aware chunks initially 180–220 tokens, ~30 overlap, enforce actual model limit incl. special tokens. Test long input and Unicode; stable chunk IDs/hash and version.
- Config keys (proposed): ORACLE_USER, ORACLE_PASSWORD, ORACLE_DSN, optional ORACLE_WALLET_DIR and wallet password, EMBEDDING_MODEL, EMBEDDING_REVISION, TOP_K_DEFAULT=5, TOP_K_MAX=10, SIMILARITY_THRESHOLD, DB_POOL_MIN=1, DB_POOL_MAX=3, EMBEDDING_WORKERS=1, LLM_PROVIDER, LLM_MODEL, LLM_BASE_URL, LLM_API_KEY, REQUEST_TIMEOUT_S, LLM_TIMEOUT_S, MAX_CONTEXT_TOKENS, RATE_LIMIT. Validate and redact. Actual cloud limits govern. No secrets in .env.example.
- One model/pool per process via lifespan; close on shutdown. Offload CPU and any blocking DB calls to bounded executor; avoid holding DB connection during LLM calls. Bound queue/wait time; return 429/503 on saturation as appropriate.
- Add document source date and metadata filters, ingestion version and stable uniqueness constraint. Use migrations; exact query with model/revision filter and parameterized metadata predicates. Limit top-K via validated binding or safe constant construction verified for Oracle release. Convert CLOB while connection open. Use float32 driver format validated by live smoke test.
- Response schemas: source ID/title/URL/text excerpt/score; answer status (ok/insufficient_evidence/degraded), request ID, latency; validate cited IDs against retrieved evidence. No fabricated URLs. Similarity is not a probability. For hybrid results keep cosine and fusion scores distinct.
- API validation errors use documented status (FastAPI 422 default acceptable; 400 if explicit contract). Dependency failure 503, rate limit 429, malformed output controlled fallback. Liveness excludes remote dependencies; readiness tests bounded DB/model availability.
- UI: query input, result/answer panel, source list with score and expandable excerpt, loading/error/empty states. Later history, suggestions, streaming and feedback. Never expose keys in UI.
