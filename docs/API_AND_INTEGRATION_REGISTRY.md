# API and integration registry

| Integration | Contract and credentials | Limits and failure handling | Location and verification |
|---|---|---|---|
| Oracle Cloud | python-oracledb 3.4.1 Thin over TCPS with instance wallet. `connect(settings)` returns a connection. `ORACLE_USER`, `ORACLE_PASSWORD`, `ORACLE_DSN`, `ORACLE_WALLET_DIR`, `ORACLE_WALLET_PASSWORD`. | 10 s TCP connect and query round-trip limits, no connection retries. Bound vector and metadata values. Smoke rolls back. Ingestion commits all new rows together. | `app/config.py`, `app/oracle.py`, `app/ingest.py`. Real smoke and repeat ingestion verified. [Driver docs](https://python-oracledb.readthedocs.io/en/v3.4.1/user_guide/connection_handling.html) |
| MiniLM | Public Hugging Face HTTPS download via Sentence Transformers 5.1.2 and Hub 0.36.2. `MiniLM(allow_download=False).encode(texts)` yields normalized float32 vectors. Anonymous download when requested. | Local cache by default, at most 32 inputs, inference batches of eight, 256 tokens including special tokens, CPU only. Artifact download uses upstream retries. | `app/embeddings.py`. Download and real local inference tested. [Model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) |
| Corpus acquisition | Curated original summaries checked against versioned PostgreSQL pages via HTTPS. `load_documents(path)` reads local JSONL. `ingest(path, model, settings)` returns counts. No runtime fetch or dataset credentials. | 256 KiB, 32 sources, 256 chunks. Invalid files stop before writes. Existing identical snapshots are skipped. | `corpus/`, `app/corpus.py`, `app/ingest.py`. Real load and repeat verified. [Upstream license](https://www.postgresql.org/about/licence/) |
| HTTP retrieval | FastAPI 0.121.3 `POST /api/v1/search` with JSON `{"query":"...","top_k":3}`. Returns request ID, status, latency and attributed chunks with similarity scores. OpenAPI at `/openapi.json`, Swagger at `/docs`. Local loopback demo uses no HTTP authentication. | Query 1–2048 characters and 256 model tokens. Top K 1–10, default 5. `SIMILARITY_THRESHOLD` default 0.25. One search and one pooled connection, with up to 10 s wait for the connection. Empty evidence returns HTTP 200. Validation 422, saturation or database failure 503. | `app/main.py`, `app/search.py`. Live Oracle-backed ASGI evaluation passed. See [test evidence](../EVALUATION_RESULTS.md). [FastAPI documentation](https://fastapi.tiangolo.com/) |

| Grounded answers | `POST /api/v1/answer` adds optional `public_question` to the search body. Returns request ID, status, answer, citations, local sources and latency. | HTTP 200 with `ok`, `insufficient_evidence` or `degraded`. Invalid requests return 422 with string `detail` in both OpenAPI and runtime. Database and search saturation retain 503. | `app/main.py`, `app/answer.py`. Mocked failures and real positive and negative ASGI requests passed. |
| Gemini Developer API | HTTPS v1beta, google-genai 1.68.0. Explicit `GEMINI_API_KEY`, `LLM_PROVIDER=gemini`, `LLM_MODEL`. `count_tokens` then `generate_content` with JSON schema and minimal thinking. | Zero retries, 10 s HTTP phase timeout. Model-token input preflight at 2048 including 128 reserved for framing. Max 768 output tokens. Up to three eligible chunks and one active attempt. At least 10 s between attempts. Token counts, request ID and prompt version logged. | `app/gemini.py`. M2 real generation used 452 total tokens. M3 VACUUM generation used 643 total tokens after one count request. [SDK v1.68.0](https://github.com/googleapis/python-genai/tree/v1.68.0), [token counting](https://ai.google.dev/api/tokens). |

M3 adds `GET /health/live`, `GET /health/ready`, the browser demo at `/`,
and `X-Request-ID` plus JSON status and timing events. Search and answer accept
JSON bodies up to 8192 bytes (413 beyond). The response deadline is 20 s
(504). Search saturation or database failure returns 503. Local generation
saturation or cooldown returns 429 with Retry-After. Gemini 429 is an upstream
failure and returns HTTP 200 with degraded status and Oracle evidence.
The Oracle pool waits up to 3 s and readiness checks table access. An optional
`ORACLE_DATA_SCHEMA` selects the corpus owner for a dedicated READ account.

Answers use up to 16 internal retrieval candidates and a distinct compiled
context budget of six chunks, twelve excerpts and 2,600 excerpt characters.
The provider token preflight still applies. `top_k` controls search output
and the local fallback. A successful answer includes its eligible sources.
`reason` distinguishes missing evidence, missing document or question
approval, provider abstention, partial answers, provider failures,
rate limiting and citation/response validation failure. Local generation
429s include evidence and Retry-After. Upstream 429 and provider transport
timeout degrade to HTTP 200 with evidence. Outer request deadline returns 504.
Synthesis v2 pairs each claim with its verified quote and can return
`unanswered` reasons. Semantic faithfulness still needs separate review.

LangGraph, SQL investigation and any MCP integrations are recorded here when implemented.

M3.1 library endpoints:

| Request | Contract |
|---|---|
| `POST /api/v1/documents?name=...` | Raw `application/octet-stream` bytes. Returns 202 and a job ID, or 429 while the one slot is busy. Defaults are 5,000,000 bytes, 40 PDF pages, 120,000 extracted characters and 128 chunks. |
| `GET /api/v1/ingestion/{job_id}` | Queued, processing, indexed or failed, with duration and document ID on success. Last 64 jobs in memory. Indexed documents persist across restarts. |
| `GET /api/v1/documents` | Up to 100 indexed rows, including title, type, timestamp, chunk count and permission status. |
| `PATCH /api/v1/documents/{id}/eligibility` | Body `{"approved_public":true}` or false to revoke. |
| `DELETE /api/v1/documents/{id}` | Adds `X-Confirm-Delete` equal to the path ID. Seed documents are protected. Upload and authorization updates require `X-Library-Action: 1`, loopback host and same-origin browser requests. The same guard applies to deletion. |

Search and answer accept up to 16 `document_ids`, optional `document_type`
and `strategy` (`semantic` or `hybrid`). Answer additionally accepts
`mode` (`extractive` or `synthesis`). Results and citations carry page numbers
when present. The hybrid fallback counts Oracle CLOB substrings, uses the same
filters in both branches, caps each to 24 candidates, and combines rank by
RRF with k=60. Native Oracle Text was not visible to the account. Fusion scores
are separate from cosine similarity.

Synthesis prompt `synthesis-v3` requires direct supporting quotations. Claim
validation requires the cited excerpt to contain each explicit byte numeral
from the claim. Failure returns the existing `degraded` response with
`reason=validation_rejected` and retains local evidence. The sanitized
internal log code is `byte_value_missing_from_quote`.
