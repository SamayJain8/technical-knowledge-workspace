# Scaling roadmap
| Stage | Topology | Trigger and verification |
|---|---|---|
| Local V1 | one FastAPI process, local MiniLM, Oracle Cloud, external LLM, ingestion CLI | functional and integration tests |
| Deployable V1 | Docker app, managed DB and API provider, CI tests | repeatable setup, smoke checks, monitored errors |
| More traffic | stateless replicas behind load balancer, shared rate limit | sustained CPU/latency saturation under measured concurrency; cap total Oracle connections and provider quota |
| Heavy ingestion | durable queue, separate workers, retries, idempotency, job status | ingestion contention or unreliable long jobs; replay and failure tests |
| Retrieval scale | evaluate HNSW/IVF, Oracle Text/hybrid, reranking | corpus growth and measured exact search latency; same recall benchmark |
| Repeated requests | optional Redis cache | measured repeat rate and latency improvement; key includes corpus/model/prompt/filter version, auth scope and TTL; invalidate on corpus updates |
| Long investigations | persistent graph checkpoints, bounded jobs, cancellation | recovery/resume requirements; test restart and budget exhaustion |
| Larger model demand | shared embedding worker service or managed inference | model replicas consume excessive RAM/CPU; benchmark transfer overhead |
| Mature operations | tracing, alerts, circuit breakers, deployment rollout, backup/restore | observed reliability needs and agreed SLOs |
No Kubernetes/Kafka/microservices required initially. Compare complexity, cost, latency, consistency, operational burden, security and evaluation at each stage. Do not claim scalability beyond measured results.
