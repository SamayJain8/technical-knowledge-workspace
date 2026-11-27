# Architecture decision log
| ID | Decision | Rationale / alternative | Status |
|---|---|---|---|
| ADR01 | Technical/database corpus | Replaces historical mental-health dataset; aligns simulator | Established |
| ADR02 | Oracle relational + vector store | No separate vector DB | Established |
| ADR03 | Hugging Face MiniLM local CPU, 384 floats | Small baseline, reproducible; no training | Established |
| ADR04 | Tokenizer-aware chunks initially 180–220 tokens incl. safe special-token budget, overlap ~30 | MiniLM default max sequence 256 wordpieces; measure actual tokenizer/model limit, never truncate silently; replaces 300–500 words and 300–400 tokens | Adopted adjustment; tune |
| ADR05 | Cloud Oracle first, local fallback | 16 GB laptop; verify account, vector support, TLS/wallet and limits | Adopted adjustment |
| ADR06 | External LLM API first; one provider adapter | Avoid local inference overhead; Ollama optional | Adopted adjustment |
| ADR07 | One FastAPI worker initially, modular monolith | Avoid duplicate CPU model and pool; scale measured | Adopted adjustment |
| ADR08 | Separate /search and /answer | Retrieval independently testable | Established |
| ADR09 | Exact cosine search first | Baseline before approximate index/hybrid/rerank | Established |
| ADR10 | V2 LangGraph, bounded single-agent workflow | Deterministic tools before autonomy; no V1 orchestration framework | Established |
| ADR11 | SQL fixed read-only templates | Least privilege and evidence integrity | Established |
| ADR12 | No fine-tuning initially; MCP optional | Only after measured gap or integration need | Established |
| ADR13 | Release v0.1 then v1.0 then v2.0 | Apply early; same repo | Proposed version labels |
| ADR14 | Feedback/history privacy | Opt-in or session-local; no raw sensitive logs | Proposed guardrail |
| ADR15 | React or plain HTML UI after API | Prefer simplest working demo | Choice delegated |
| ADR17 | Gemini behind a provider protocol with extractive answers | 2026-11-26, R07–R08. Locally validating full source sentences makes grounding deterministic for the reviewed seed corpus. Free-form synthesis would require a separate support check. One live call verified the structured contract. | Implemented |
| ADR18 | Use a response deadline and retain worker admission until work finishes | 2026-11-26, R09–R10. Reuses synchronous integrations while freeing the event loop. Active work may finish after 504. Local generation admission returns 429 with Retry-After. Upstream 429 degrades with evidence. | Implemented for one worker |
| ADR19 | Extend existing tables and share the model across ingestion and queries | 2026-11-26, R03–R07, R19–R21. Migration 002 adds document fields and nullable page numbers. One in-memory upload slot keeps parsing and ingestion bounded. Durable jobs require a separate persistence design. | Implemented |
| ADR20 | Opt-in public evidence and exact page citations | 2026-11-26, R08, R15, R23. Uploaded evidence starts private for Gemini. Approval and revocation serialize with external requests. Synthesis validates source quotations and requires separate relevance review. | Implemented |
| ADR21 | Oracle CLOB lexical matching and RRF | 2026-11-26, R14. CTX_DDL was not visible in the inspected account. Use bounded substring candidates and keep cosine and rank-fusion scores separate. Keep exact semantic search as baseline. | Implemented for small library |
| ADR22 | Bound context separately from retrieval and annotate partial synthesis | 2026-11-27. Keep exact quotes and explicit consent. Use query-term coverage and page/document diversity to select excerpts from a larger internal candidate set. | Implemented, evaluated on authored fixtures |
| ADR23 | Yield model admission between bounded ingestion turns | 2026-11-27. Retain one model and atomic DML. Measure the latency/availability trade-off before using a higher upload profile. | Implemented, bounded local measurement |
| ADR16 | M1 ingests immutable snapshots and serves one search at a time | 2026-11-26, R03–R07 and R10. Stable IDs let a repeat skip writes, and one transaction prevents partial corpus writes. Mutable replacement and per-version selection remain R21 work. A one-slot pool and admission gate bound work on the laptop. Measure before increasing them. See EVALUATION_RESULTS.md. | Implemented for local M1 |

Verify current vendor documentation and versions before execution. Model comparison candidates (BGE-small-en, E5-small, BGE-M3, cross-encoders) are experiments, not dependencies. Change model only with new embedding version, compatible schema/index, re-ingestion and evaluation. Source priority in README. New decisions must record date, alternatives, trade-offs, evidence and affected requirements. No claims of optimality without measurements.
