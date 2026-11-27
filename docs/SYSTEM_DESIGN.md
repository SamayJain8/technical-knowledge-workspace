## 6. System design and future scalability

**Initial deploy:** one stateless FastAPI service (possibly embedding model in-process), one Oracle database, separate ingestion CLI/job, configurable LLM API, simple UI and Docker Compose. Do not presume production scale.

**Prepare for scaling without premature distribution:**

| Concern | Initial design | Later scale path |
|---|---|---|
| API | Thin FastAPI routes, modular services, request IDs | Stateless replicas behind load balancer / API gateway |
| DB connections | Per-process `python-oracledb` connection pool | Tune sum of pools across replicas; protect DB capacity |
| Embeddings | Local MiniLM loaded once per worker, bounded concurrent inference | Separate shared model service or worker pool |
| Search | Exact top-K with measured quality | Index selection, hybrid, reranking, partitioning if warranted |
| Ingestion | Separate idempotent CLI/job | Durable queue + independently scaled workers and retry ledger |
| Agent state | Request-scoped V1 | Persistent LangGraph checkpoints for V2/multi-replica resume |
| Cache | None initially | Optional Redis only when repeated query patterns justify it; include invalidation/versioning |
| Reliability | Timeouts, retries where safe, fallback | Circuit breakers, error budgets, failover planning |
| Observability | Structured logs, request IDs, latency per stage | Distributed traces, alerting, traffic and saturation metrics |
| Security | Secret handling, input validation, least privilege | Auth, tenant isolation if needed, auditable tool permissions |

**Important implementation detail:** `async def` does not automatically make local embedding computation nonblocking. Handle CPU-bound inference with a bounded executor/semaphore and measure event-loop responsiveness. Connection pools are created per process; e.g. 4 API workers with maximum pool size 10 can consume up to 40 connections. Don't create independent unbounded pools.

The system should preserve service boundaries so later adding a load balancer, persistent checkpoints or shared embedding inference does **not** require rewriting retrieval logic. Future architecture is an option, not a claim that distributed deployment is already built.


## Current development topology
Cloud-first DB; one local API process, local CPU MiniLM, remote LLM. Do not treat earlier local Docker Oracle instructions as default. Begin with pool 1–3 and one inference slot, adjust after measuring; avoid unbounded waiting and enforce aggregate pool limits across instances. Async network I/O, bounded blocking work; DB connections returned before LLM. Backpressure with finite admission/queue and clear overload responses. Config-driven deadlines propagate across stages. Retry only transient safe operations, capped with jitter, no uncontrolled duplicate spend. Ingestion transaction per batch with idempotency key and retry ledger. Stateless queries; user history optional opt-in, persistent state only where justified. Measure p50/p95/p99, throughput, CPU/RAM, pool saturation, LLM errors, cost and quality before sizing. No invented SLOs; set target after baseline. Design for TLS, least privilege, retention and future tenant isolation; no public admin endpoint without auth. See scaling roadmap.

## Revision 2 — resource and failure review
Use explicit bounded admission (semaphore plus finite waiting/deadline; semaphore alone does not cap queued requests). CPU inference off event loop, account for thread safety and cancellation: cancelled await does not necessarily stop running CPU thread; retain permit until work finishes. Async DB driver where supported or bounded executor for sync driver; release DB connections before external LLM calls. Pool upper bound = replicas × workers × max pool size, plus ingestion/other consumers. Measure queue wait, per-stage latency, memory, saturation, errors and connection usage. Start one worker on 16 GB laptop. Backoff/jitter only for safe transient retries, cap overall deadline; avoid retry amplification. Graceful shutdown closes pools/clients and handles in-flight work. Liveness distinct from readiness; do not make health checks expensive. Circuit breakers/bulkheads, cache versioning and durable queues only with real need. See engineering standards and review checklist.
