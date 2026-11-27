# Feature registry — planned, not verified
P0 = today's target; P1 = remaining V1; P2 = V2; F = future/conditional. All statuses UNVERIFIED until Codex records evidence. The target is a working subset rather than a guarantee. Features whose prior version varied are retained here as proposed priority assignments.

| ID | Priority | Requirement | Acceptance evidence |
|---|---|---|---|
| R01 | P0 | Verify local Python/Git/VS Code, Oracle Cloud account and API credentials | recorded versions and successful connectivity, no secrets |
| R02 | P0 | Hugging Face MiniLM 384-D normalized local vectors, pinned revision | real encode and dimension/model compatibility tests |
| R03 | P0 | Curated technical corpus, licenses, source URLs, cleaning, token chunking, dedup | manifest, counts, sample valid and invalid rows |
| R04 | P0 | Oracle schema, batch inserts, transactional ingestion CLI | real insert/search, repeat ingestion idempotency |
| R05 | P0 | Exact cosine top-K and similarity score | real Oracle integration and known-source test |
| R06 | P0 | Configurable similarity threshold, insufficient evidence | weak/no result test; tune not universal |
| R07 | P0 | FastAPI retrieval /search and /answer, Pydantic validation | API tests; documented contract |
| R08 | P0 | External LLM adapter, grounded answer, verified citation IDs | real API smoke; unsupported citation rejected |
| R09 | P0 | .env config, logs/request IDs, liveness/readiness | validation, readiness dependency failure test |
| R10 | P0 | Connection pooling, bounded CPU inference, timeout, fallback and rate limit | overload, DB failure, LLM timeout tests |
| R11 | P0 | Small retrieval benchmark and unit/integration tests | expected-source labels, actual results and run commands |
| R12 | P0/P1 | Docker, README, reproducible setup, Git release | run image smoke or explicitly record blocker |
| R13 | P1 | Metadata filters topic/source/date/language | filter isolation and invalid filter tests |
| R14 | P1 | Hybrid keyword + vector search, compare fusion strategies | same benchmark vs dense baseline; distinct scores |
| R15 | P1 | UI: citations/scores/expandable chunks | demonstrate with real API and failure states |
| R16 | P1 | Search history, suggested questions | privacy-safe session/history and relevance tests |
| R17 | P1 | Streaming answer | cancellation, error, final citation validation |
| R18 | P1 | Helpful/not helpful feedback | validated request reference, aggregate feedback rate |
| R19 | P1 | Admin upload, separate background job | auth, size/type validation, no search blocking |
| R20 | P1 | Batch ingestion status pending/running/completed/failed; failed row retry ledger | durable status, retry idempotency, failure recovery |
| R21 | P1 | Dataset/model version tracking, re-embedding command | prevent mixed revisions, versioned migration, rollback plan |
| R22 | P1 | Quality/performance: Recall@K, MRR, citation fidelity, latency, errors, feedback | reproducible evaluation; no fabricated metrics |
| R23 | P1 | Prompt versioning, structured LLM outputs, provenance, regression tests | recorded versions, malformed-output handling |
| R24 | P1 | Vector index/reranking comparison | benchmark latency/recall; keep exact baseline |
| R25 | P2 | Import simulator metrics and workload schema | actual attributed measurements or explicitly synthetic demo data |
| R26 | P2 | Read-only parameterized SQL tool registry | allowlist, least privilege, row/time cap tests |
| R27 | P2 | LangGraph route docs/metrics/both, typed state | route and transition tests |
| R28 | P2 | Adaptive retrieval/query rewrite/evidence checks | bounded retry and insufficient evidence cases |
| R29 | P2 | Grounded diagnostic report with observations vs hypotheses | expected evidence and citation evaluation |
| R30 | P2 | Trace, tool accuracy, trajectory/task evaluation, budgets | observed calls and failures; tool selection and termination tests |
| R31 | P2/F | Checkpointing, human approval where needed, MCP | justified use, safe replay/permission tests |
| R32 | F | Redis, distributed rate limit, queues, independent workers, load balancer | measurable trigger and load/recovery tests |
| R33 | F | Multiple agents, alternative models, fine-tuning/LoRA | explicit decision and controlled comparison; not required |
| R34 | F | Cloud app hosting, CI/CD, monitoring/tracing, alerting | reproducible deploy, cost approval and verified telemetry |
| R35 | Conditional | Historical mental-health safety | only if that domain returns: disclaimer, crisis route to emergency help, no PII query storage; domain-specific safety review |

## Definition of done
For each ID record commit/path, command, real vs mock, observed pass/fail, limitations, date. P0 release gate requires real Oracle vector retrieval and real grounded generation with citations, documented run instructions and essential tests. A retrieval-only milestone may be published honestly if LLM blocked; it is not full RAG. Docker or optional features may be deferred explicitly; resume text must match actual evidence. Keep all P1/P2/F entries rather than deleting them.
