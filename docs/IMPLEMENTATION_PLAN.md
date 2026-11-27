# Execution plan — deadline 26 November 2026
Do not spend today watching courses or generating endless scaffolding. Use Codex to implement and test vertical slices. Time estimates are not guarantees. Existing repository state unknown.

| Gate | Work | Exit evidence |
|---|---|---|
| 0 | inspect repo, Python, Git, available RAM/disk; check cloud accounts, credentials locally, network and budget | actual environment log; no secret output |
| 1 (M1) | create minimal app environment; provision/connect vector-capable Oracle Cloud with user approval; MiniLM encode; minimal schema insert and exact search | live 384-D vector smoke test, real nearest-neighbor query |
| 2 (M1) | attributed technical corpus, loader, token-aware chunking, idempotent batch ingestion, /search | real corpus counts, source IDs, test query |
| 3 (M2) | provider adapter, /answer, context limits, grounding/citations, no evidence and timeout paths | real LLM call and validated citations, fallback test |
| 4 (M3) | config, pooled connections, bounded executor, rate limits, logs, liveness/readiness, tests/evaluation | recorded test results and measured baseline |
| 5 (M3) | README, Docker when feasible, Git diff/secrets check, user-authorized push/tag, resume evidence | runnable repo, verified status and limitations |
| 6 (remaining V1) | filters, hybrid/rerank, UX, ingestion operations, quality and load tests | R13–R24 evidence |
| 7 (M4) | simulator data mapping, deterministic read-only SQL tools | R25–R26 evidence |
| 8 (M5) | LangGraph routing, state, bounded adaptive investigation/report | R27–R29 evidence |
| 9 (M6) | agent evaluation, tracing, security and measured scaling | R30 onward, optional features only as justified |

## Environment checklist
PowerShell: `python --version`, `py --version`, `git --version`, `docker --version`, `docker compose version`, `wsl --status`, `wsl --list --verbose`; Docker/WSL optional for initial cloud-first development. Verify available RAM/disk, interpreter and dependency compatibility. Create venv; install minimal compatible packages, pin reproducible versions. Cloud Oracle: check current official provisioning docs, availability, vector support, cost, connection string and TLS/wallet; create least-privileged app schema; verify `python-oracledb` connectivity and query/insert. User configures credentials locally. No assumption of free capacity or existing account. External LLM: select one available provider/model, check API quota/billing and run minimal smoke with permission. If blocked, continue tests with labeled mocks; never silently replace required Oracle or claim live success. Local Oracle fallback only after evaluating resource needs and approval; local LLM optional, not default.

## Releases (proposed labels)
v0.1 first working release → v0.2 retrieval enhancements → v1.0 complete V1 → v1.1 investigation tools → v2.0 agent → v2.x measured extensions. Tags are immutable snapshots; main remains usable. Same GitHub link on resume; update claims only as verified. Do not wait for V2 to apply. Original handoff's sprint roadmap preserved in references; these M1–M6 gates consolidate current priorities.

## Revision 2 — checkpoint discipline
At each gate: inspect current repo, implement smallest slice, execute relevant tests, run critical review, fix or mark blockers, update living evidence and explain decisions. Use docs/DEFINITION_OF_DONE.md and prompts/ for task-specific instructions. Do not introduce all recommended tools or UI polish before first verified end-to-end flow. Keep planned features in registry, not fake stubs. Review staged changes and rights before any authorized release. Resume deadline remains priority, not permission to skip verification.
