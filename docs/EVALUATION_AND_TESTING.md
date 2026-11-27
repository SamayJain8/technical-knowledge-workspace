## 8. Evaluation and engineering acceptance criteria

**Retrieval:** label an initial set of ~30–50 questions with expected source IDs/chunks; expand later. Compute Recall@K, MRR, bad/no-result cases, citation fidelity, and latency. Compare exact vector search to hybrid/reranking only under the same test set and conditions.

**Reliability:** tests for invalid input, empty corpus, unknown question, incompatible embedding dimensions, corrupt ingestion rows, repeated ingestion, Oracle disconnect, LLM timeout, and concurrent requests. Return useful fallback and sources when LLM is unavailable (where available).

**Performance:** report observed p50 and p95 end-to-end latency; throughput and errors under a stated load-test setup. Avoid invented speedups or headline metrics.

**V2:** test planner routing, read-only SQL enforcement, query parameter validation, tool budget exhaustion, retries, persistence behavior if checkpointing is used, evidence-grounded report generation, and citation correctness.

**Security:** credentials outside code; `.env` not committed, strict tool authorizations, source prompt-injection resistance, HTTP/auth controls for admin endpoints, logging that excludes API keys and sensitive user queries.


## Test matrix
| Layer | Tests |
|---|---|
| Unit | cleaner/dedup, token limits/overlap, 384-D validation, config, distance-score transform, Pydantic bounds, citation allowlist, timeout fallback, prompt injection fixture |
| Integration | real Oracle vector bind/insert/search, metadata filters, transaction rollback/retry, pool release, real LLM smoke, API lifecycle/readiness; mark network tests separately |
| End-to-end | known query → real attributed sources → cited answer; out-of-domain/no evidence; degraded response when provider fails; UI displays sources |
| Load | concurrent requests with stated worker/pool settings, warm/cold distinction, p50/p95/p99, throughput/error rate, saturation and memory |
| Security | credentials absent, SQL injection inputs, unauthorized admin, oversized inputs, malicious retrieved instructions, invalid citation IDs, V2 forbidden queries |
| V2 | route accuracy, expected tool inputs/outputs, exact numeric metrics, step budget, timeouts, invalid output, partial evidence, checkpoint replay if used |

## Evaluation protocol
Use a small labeled set initially (expand toward 30–50 questions), expected source/chunk IDs and answerable flag, fixed corpus/version, model and config. Avoid evaluating only handpicked successes. Recall@K = relevant retrieved / all labeled relevant; Precision@K = relevant / K (document denominator policy); MRR = mean reciprocal first relevant rank (0 if absent); NDCG when graded judgments exist. Record citation validity (ID exists) separately from citation support (claim actually supported). Human review faithfulness, correctness, relevance, uncertainty; optional judge model with rubric and spot checks. Measure no-answer correctness, hallucination rate, failure/timeout rate, feedback rate, token usage/cost when known. V2 task success, tool-selection accuracy, tool failure rate, step count, loop termination, evidence coverage, report correctness and cost per task; trajectory means observable calls not hidden reasoning. Compare baseline vs candidate on identical corpus/query set and conditions. Save raw results (redacted), run metadata and scripts. No numerical target or improvement asserted until measured. Mock tests verify code only, not provider/database functionality.

## Revision 2 — evidence gates
Apply DEFINITION_OF_DONE and CODE_REVIEW_CHECKLIST. Record test command, revision, config/corpus/model versions, environment, timestamps, exit code and pass/fail/skip counts; redact secrets. Separate unit mocks, real integration and end-to-end evidence. Assert actual behavior, negative paths and failures; do not weaken tests or fabricate results. Include independent review of evaluator labels and citation support; keep held-out examples when tuning thresholds. Report latency sample size, warm/cold conditions, concurrency and provider limitations; don't claim large-scale results from laptop smoke tests. Run regression comparisons after retrieval/prompt/tool changes; record actual costs where available. Block affected features on missing required live tests.
