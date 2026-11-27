# Evaluation results

## 2026-11-27 · Development-preview verification

The isolated Windows Python 3.11 environment ran the full application with
PyTorch 2.13.0, Transformers 5.24.1 and Sentence Transformers 6.3.0.
With `RUN_MODEL_TESTS=1`, `RUN_ORACLE_TESTS=1`, `HF_HUB_OFFLINE=1`,
`RUN_LIBRARY_TESTS=0` and `RUN_GEMINI_TESTS=0`, `python -m pytest -q -rs`
reported 67 passed, 0 failed and 2 skipped in 78.42 s. The skips are
persistent uploads and live Gemini. Four warnings concern the renamed
Sentence Transformers dimension getter. Pip check passed. OSV returned
zero matches for the 74-package installed Windows environment, including
pip. The scan does not cover the Linux container or operating system.

Headless Chrome tested fixture-backed readiness and library rendering,
title filtering, scoped search, consent fallback, synthesis citation
rendering and a 390 px layout with no horizontal overflow. The desktop
screenshot uses authored fixtures and is labeled. It contains no user uploads.
The final polish repeated one representative fixture smoke with the revised
composer, citation chips and ranked evidence layout. Filtering, document
scope, search, consent fallback, citation rendering and 390 px layout passed.

## Isolated Windows ML compatibility check

The Python 3.11 environment under `.cache/ml-verify-311` used official PyPI
binary wheels and a hash-locked test list. The PyTorch wheel was 122 MB and
the drive had 207 GB free. The probe ran with `HF_HUB_OFFLINE=1` and reused
the pinned MiniLM cache.

Both stacks produced three finite, normalized 384-dimensional embeddings.
The 256-token limit, special-token count, token IDs and stored-vector
fingerprint matched. The candidate rejected oversized input and differed
by at most 6.71e-8 per vector element. All three read-only Oracle queries
matched the baseline's top-three ordering and scores within 1e-5.
Sentence Transformers 6.3.0 emitted a FutureWarning for the dimension
getter. This checked the encoder and Oracle retrieval boundary. Full
application and Docker compatibility remain separate release checks.
The Windows wheel reported no CUDA build. After updating the isolated
bootstrap pip to 26.3, pip check passed and OSV returned zero matches
across the 52 installed packages. The main environment and production
pins were preserved. No Oracle writes or Gemini calls were made.

## 2026-11-27 · Pre-frontend closure

The current PowerShell diagnostic inherited none of the checked Oracle
configuration keys and used the project `.env`. Oracle confirmed a service
and a current schema equal to the login. The exact case-insensitive title
lookup returned SQLite 0 and Atlas 1. No separate owner/writer settings or
Compose `.env.runtime` were present. No process was listening on the
documented local browser port. Identity of the historical browser session
remains unverified. No document or permission changes were made.

The upload profile from the earlier 20/40-page benchmark is now the default.
`.venv/Scripts/python -m pytest -q -rs tests/test_library.py` returned
9 passed, 1 opt-in live-write skip and the known TestClient warning. No
benchmark or retrieval evaluation was repeated.

The public OSV exact-version queries returned 5 PyTorch, 11 Transformers
and 2 Sentence Transformers records for the installed versions, including
overlapping records. The candidate pins and application exposure analysis
are recorded in the technical registry.

## 2026-11-27 · Final functional correction pass

**Independent browser follow-up (after corrections, before synthesis v3).**
The user verified both original uploads remained indexed in their running app.
The SQLite reference PDF had 10 pages and 40 chunks. The Atlas
policy PDF had 2 pages and 2 chunks. In semantic synthesis the
three-part SQLite question answered the 100-byte header size and correctly
reported the non-zero condition and matching values at offsets 24 and 92.
It explicitly left supported page sizes unanswered. The citation for the
100-byte claim described the header string and page-size field, leaving the
claim unsupported by its quoted sentence. The request took 3420 ms.
Cross-document synthesis returned SQLite's 65,536-byte maximum page size and
Atlas's 45-day backup retention with citations to both original PDFs. The
documents were ranked first and second, with similarities 0.715 and 0.689.
These are user-performed observations. The latency is one request.

**Bounded automated follow-up.** The read-only
`.venv/Scripts/python evaluation/final_retrieval.py --trace-sqlite` connected
to Oracle and found zero PDF rows for the SQLite title after case and
whitespace normalization. This rules out the library endpoint's 100-row
display cap as the explanation for the lookup in this session. The cause
of the difference with the browser instance is unresolved. No documents
were reuploaded or reindexed, and this follow-up made no Gemini calls.
The [SQLite specification](https://www.sqlite.org/fileformat2.html#pages)
gives the page-size range separately from the
[header size](https://www.sqlite.org/fileformat2.html#the_database_header).
The project-authored fixture below proved all three SQLite facts can
survive retrieval and local context selection. For the historical browser
request, the actual candidate list and sent excerpts are unavailable, so
the missing page-size fact cannot be attributed to retrieval, excerpt
selection or generation. Synthesis v3 adds a narrow citation check for
explicit digit-form byte quantities and keeps full semantic support open
for review.

**Focused regression and pre-frontend checks.**
`.venv/Scripts/python -m pytest -q tests/test_answer.py tests/test_release.py`
returned 27 passed, 0 failed, 0 skipped (3.90 s), with the existing
Starlette TestClient deprecation warning. Mocked answers exercised an exact
but unrelated 100-byte citation, a nearby number, direct support and an
implicitly byte-based range with a differently formatted numeral.
`.venv/Scripts/python -m pip check` passed. `git check-ignore` confirmed
the private config, wallet, virtual environment and cache paths.
`docker compose config --no-env-resolution --no-interpolate --quiet` passed.
A Dockerfile lint recheck could not open the local Buildx lock from the
sandbox. A Dockerfile lint passed earlier. Final build and runtime verification
are scheduled after the frontend pass.

**Independent user observations (before corrections).** Chrome verified
Atlas and the ten-page SQLite PDF, duplicate detection, Oracle page
references, approvals, fallback and correct AES abstention. The ten-page
excerpt indexed 40 chunks. The full PDF failed the extracted-text cap.
On offset 24 the first relevant rank was 1 for semantic and 2 for hybrid.
SQLite synthesis omitted the non-zero condition in one response and answered
only one of three parts in another. Atlas–SQLite retrieval found both facts,
but the answer degraded with an undifferentiated validation log. Revoking
consent preserved local matches but showed insufficient evidence. Library
and approval state persisted across restart. Post-restart retrieval was not
independently tested. These results came from the user, separate from this
pass's measurements.

**Automated regression.** With `RUN_MODEL_TESTS=1`, `RUN_ORACLE_TESTS=1`,
`RUN_LIBRARY_TESTS=0` and `RUN_GEMINI_TESTS=0`, running
`.venv/Scripts/python -m pytest -q -rs` returned 63 passed, 0 failed, 2
intentional skips (persistent upload and previous live Gemini test), 32.11 s.
Mocked realistic cases validated multi-page/cross-document context, exact
citation association, explicit partial answers and AES abstention. The SDK
test asserts neither countTokens nor generateContent runs when consent blocks.
Starlette now emits its httpx TestClient deprecation warning.

**Live Oracle and MiniLM.** `.venv/Scripts/python evaluation/final_retrieval.py`
could not find both original titles in the connected library, so the comparison
used `--rollback-fixture`: six project-authored chunks and four answerable
questions with seven labeled facts, plus one unsupported question. Both
strategies scored Hit@5, MRR@5 and fact Recall@5 of 1.00. The offset result
ranked first in each. The SQLite multipart facts ranked [2, 1, 4] for semantic
and [3, 1, 2] for hybrid. Both cross-document facts ranked [2, 1] under each.
Local simulated context selection retained all seven labeled facts for each
strategy. The unsupported query retrieved related evidence, so this stage
does not prove model abstention. All fixture rows were rolled back and
verified absent. No ranking claim about the original user PDFs follows.

**Live Gemini.** Two approved free-tier count/generate pairs used only
project-authored excerpts, separate from the Oracle fixtures. SQLite returned
three correctly cited facts including powers of two and the non-zero condition
(486 generation-reported total tokens, 2306.96 ms). Atlas–SQLite returned
both cited facts (316 total tokens, 2262.83 ms). Both returned zero unanswered
parts and exact quotes. These are two targeted passes, not an answer-quality
rate. The AES path used the independent prior live observation and a new mock.

**Capacity.** Windows CPU, one loaded MiniLM, 5 MB / 40 pages / 120,000
Unicode characters / 128 chunks test profile, batches of eight. The source
is a deterministic authored PDF fixture, not the SQLite original.

| Input | Characters / chunks | Real parse / embedding | Oracle write / total | Parent peak working set |
|---|---:|---:|---:|---:|
| 20 pages, 57,780 bytes | 49,556 / 60 | 646 ms / 5.50 s | 3.25 s / 10.67 s | 467.8 MiB |
| 40 pages, 115,401 bytes | 99,256 / 120 | 739 ms / 10.64 s | 6.40 s / 20.10 s | 470.6 MiB |

`.venv/Scripts/python evaluation/capacity_probe.py --oracle-rollback`
timed actual statement execution and array DML, excluding commit. The
transaction rolled back and both rows were verified absent. Working set
excludes the PDF child. The warm parent peak was about 441 MiB.
The same 40-page profile with mocked Oracle was available on 19/392
admission probes (4.8%) before batch handoff and 109/458 (23.8%) afterward,
with total local times of 11.82 s and 14.37 s. One run per condition. These
were periodic permit probes, not HTTP search latency samples. The longest
measured embedding batch after handoff was about 332 ms in the live probe.
Production defaults, parser bounds and stored embeddings stay unchanged.
The profile is suitable for further local trials. Actual dense or complex
40-page PDFs may exceed chunk or parser limits. 100-page testing is deferred.

An offline sentence-boundary prototype on three authored pages produced nine
chunks, the same count as the current chunker. Three current chunks lacked
terminal punctuation versus zero prototype chunks. The prototype's longest
chunk was 193 model tokens including special tokens. This simple check did
not measure excerpt quality on tables or retrieval, and the prototype had
no overlap. No production chunking or re-indexing change was adopted.

**Security.** pip check passed. A public OSV refresh on all 64 locked PyPI
packages returned no matches for the upgraded FastAPI, Starlette, pytest,
or python-dotenv pins. Three ML pins still matched published advisories
(PyTorch, Transformers, Sentence Transformers). This was a dependency
inventory scan, not a platform or container audit. The private local
configuration does not yet contain separate reader/writer settings. No
grant or account changes were applied. Docker build/runtime is intentionally
scheduled after source stabilization and frontend redesign.

## 2026-11-26 · M3.1 document workspace

**Checkpoint A.** Headless Chrome used the actual upload form to index the
project-authored two-page public PDF `Restore marker browser demo.pdf` in
Oracle. The library reported two chunks and two pages. Selected hybrid
search returned page 2 in 209.79 ms. One approved Gemini token-count request
and one generation produced HTTP 200 `ok` in 2701.99 ms. The explanation
identified what RUNBOOK_LYRA records, and the exact quoted sentence, document
title and page were verified in the UI. The fixture's Gemini approval was
revoked after the smoke. These are individual timings, not a benchmark.

**Checkpoint B.** The live API run indexed project-authored PDF, TXT and
Markdown fixtures in 1710.81, 797.76 and 849.54 ms respectively on the first
run. The first focused run had one parser test failure from a misconfigured
pypdf page-tree entry budget, even though the default-budget live PDF indexed.
After correction, the consolidated run verified duplicate detection, PDF page
metadata, job polling, type and document selection, and approval/revocation.
An unapproved PDF query reached no provider call. The mocked synthesis test
also verified that mixed private evidence is excluded.

| Verification | Actual result |
|---|---|
| `$env:RUN_MODEL_TESTS='1'; $env:RUN_ORACLE_TESTS='1'; $env:RUN_LIBRARY_TESTS='1'; $env:RUN_GEMINI_TESTS='0'; .venv/Scripts/python -m pytest -q -s -rs --junitxml=evaluation/m3-1-tests.xml` | 59 passed, zero failures and one opt-in Gemini skip, 32.68 s. Real Oracle and MiniLM. Provider paths mocked except the separate browser smoke. |
| Hybrid comparison | Three fixed questions scoped to the three uploaded documents. Dense and hybrid ranks were both [1, 1, 1], Recall@3 and MRR@3 both 1.00. One exact checkpoint identifier and two paraphrases. No measured improvement. |
| Seed regression | Prior seed questions scoped to the fixed seed corpus. Twelve M3 cases retained Recall@3 and MRR@3 of 1.00 with four correct abstentions. Observed median lookup 74.88 ms, 62.62–129.73 ms for those sequential ASGI requests. |
| Scoped live lifecycle smoke | A malformed PDF reached the failed job state with no indexed row. An unconfirmed DELETE on a newly indexed disposable TXT returned 400. A confirmed DELETE removed that document from the library and eliminated its scoped search results. |

**Checkpoint C.** Read-only inspection verified the old schema and four
documents and chunks before adding migration 002. The currently configured
owner verified the migration and subsequent retrieval. Dedicated Oracle
reader/writer accounts are still unprovisioned. `pip check`, Python
compilation, JavaScript syntax, Git ignore checks and Compose static
validation passed. The new pypdf 7.1.1 pin had no exact-version OSV match.
Previously flagged dependency advisories, the final Docker image/run and
independent release review remain open. Broader multi-document synthesis,
quantitative answer quality and load/resource benchmarking are unverified.

Raw console and JUnit artifacts are retained locally. The table records the
command and outcome for reproduction.

## 2026-11-26 · Independent M3 functional verification

The user performed these checks separately from Codex's automated evaluation.

| Check | User-observed result |
|---|---|
| Liveness and readiness | `alive` and `ready` |
| Frontend | Loaded successfully |
| Semantic search | Correct PostgreSQL transaction evidence, similarity 0.356, 203 ms |
| Live Gemini answer | Correct SAVEPOINT and ROLLBACK TO SAVEPOINT explanation with two supporting excerpts and source links, 4942 ms |
| Unrelated Napoleon question | Correct insufficient-evidence handling, 86 ms |

The three timings are individual observations. M3 is accepted for the
verified local demo. Release verification remains open.

## 2026-11-26 · M3 candidate verification

Independent M2 checks reported by the user: the relevant savepoint question
returned HTTP 200, `ok`, two valid citations, similarity 0.3559896627673813
and 5516.08 ms. The Napoleon question returned HTTP 200,
`insufficient_evidence`, a null answer, empty citations and sources, and
109.31 ms. Whitespace produced a sanitized 422 matching OpenAPI. These
individual latency readings are separate from M3's automated measurements.
The recorded M2 regression result was 37 passed with zero failures or skips.

| M3 automated check | Actual outcome |
|---|---|
| `$env:RUN_MODEL_TESTS='1'; $env:RUN_ORACLE_TESTS='1'; $env:RUN_GEMINI_TESTS='0'; .venv/Scripts/python -m pytest -q -s -rs --junitxml=evaluation/m3-tests.xml` | **48 passed, 1 opt-in skip**, 28.08 s. Live MiniLM and Oracle. Mocked Gemini timeouts, 429, 503, transport error, invalid quotes, admission, deadline, readiness failure and untrusted evidence. Upstream Starlette/AnyIO deprecation warning remains. |
| `$env:RUN_GEMINI_TESTS='1'; .venv/Scripts/python -m pytest -q -s tests/test_m3_evaluation.py -m gemini -o log_cli=true -o log_cli_level=INFO` | One approved live test passed. Gemini count and generate each returned HTTP 200. 551 input and 92 candidate-output tokens, 643 total as reported for generation. No separate cost statement inspected. |
| `node --check app/ui/demo.js`, `pip check`, `compileall -q app tests`, Git ignore/secret checks | Passed. No dependency versions changed. |
| Headless browser on local Uvicorn, 375 px viewport, Gemini disabled | Initial Edge launch exited before loading the page. Chrome passed real Oracle search, expandable evidence and source link, degraded response, and no-evidence flow. A mocked cited answer verified that markup stayed plain text and a non-HTTPS URL was never linked. |
| `.venv/Scripts/python -m pytest -q tests/test_release.py tests/test_answer.py` after static-route mitigation | **17 passed**, 3.63 s. The two fixed assets returned 200, another asset path returned 404, and mocked API protections still passed. |
| `docker compose config --no-env-resolution --no-interpolate --quiet` and `docker build --check .` | Passed after starting Docker Desktop. Dockerfile check issued no warnings. |
| `docker build --tag v1-agent-m3-local .` | CPU PyTorch installed. The build was stopped during slow Linux dependency downloads, after it became stale relative to the static-route fix. No final image or container startup was verified. |

The 12 new labeled search cases ran sequentially through TestClient on Windows
with local CPU MiniLM, the real Oracle Cloud connection, one warm-up, top K 3,
and the existing seed corpus and 0.25 threshold. All 12 requests returned 200.
All eight positives ranked first, for Recall@3 and MRR@3 of 1.00. All four
unrelated questions abstained. Client-observed range was 72.76–90.28 ms, median
81.46 ms. Small serial sample, without a throughput or production latency
claim. Raw observations and JUnit output are retained locally.

The live M3 answer correctly identified VACUUM FULL, rewrites and the exclusive
lock. Its one returned citation matched the expected vacuum source and exact
text. Reported route latency was 1744.21 ms. Alongside the prior savepoint smoke
this supports qualitative correctness on two topics, without an aggregate
answer quality estimate. The SDK logged its default automatic function
calling setting during live verification. No tools were supplied and there was
one generation request. The final regression checks that AFC is explicitly
disabled. No new live Gemini call was needed after that client-side safeguard.

The OSV batch lookup sent only public PyPI names and versions from
`requirements.txt`. It matched advisories in six of 62 packages:
pytest 8.4.2, python-dotenv 1.2.1, sentence-transformers 5.1.2, Starlette 0.50.0,
PyTorch 2.9.1 and Transformers 4.57.3. The Windows StaticFiles advisory
GHSA-wqp7-x3pw-xc5r applied to the initial UI implementation. Replacing the
mount with two fixed FileResponse routes removes that app path. The app loads
the pinned model revision with safetensors and remote code disabled, and uses
dotenv for reading. These narrow usage choices do not clear all advisories.
Triage the remaining upstream findings, upgrade compatible dependencies and
reverify before public release. The scan did not cover OS/container packages.
[OSV batch API](https://google.github.io/osv.dev/post-v1-querybatch/)

## 2026-11-26 · M2 automated and live verification

Windows, Python 3.11.6, google-genai 1.68.0, pinned MiniLM and the existing
Oracle Cloud corpus. `pip check` passed. The authorized authenticated
`models.list` call returned `generateContent` support for
`gemini-3.5-flash-lite` and `gemini-3.1-flash-lite`. Google documents
structured output for 3.5 Flash-Lite.

| Check | Observed result |
|---|---|
| `$env:RUN_MODEL_TESTS='1'; $env:RUN_ORACLE_TESTS='1'; .venv/Scripts/python -m pytest -q -rs` | **37 passed, 0 failed, 0 skipped** in 20.87 s. Includes real MiniLM and Oracle, plus mocked generation, timeout, malformed output, forged citation and no-evidence paths. Existing AnyIO warning remains. |
| Real ASGI answer smoke via FastAPI TestClient, using the two README requests | Negative returned insufficient evidence without changing the generation admission timestamp. Exactly one approved positive generation returned HTTP 200 and two validated citations from the Transactions source. |
| Gemini usage | 247 input, 205 candidate-output and 452 total tokens as reported by the provider. One free-tier generation with billing unchanged. No separate billing statement was inspected. |

The two exact excerpts explain that SAVEPOINT marks a position and ROLLBACK TO
SAVEPOINT discards changes after that position while keeping the transaction
open. The smoke asserted the expected source, matching chunk IDs and quoted
text. This is one qualitative sample, without a measured answer accuracy rate.
See [manual reproduction](README.md#verify-grounded-answers).

Review checked that the key never enters the payload or app logs, the Oracle
connection is released before generation, and provider errors preserve
retrieved evidence. The seed corpus and caller confirmation bound what can be
sent. General request deadlines, quota tracking and expanded evaluation remain open.

## 2026-11-26 · Independent verification and review

The following results were reported by the user from outside the Codex sandbox.

| Check | Independent observation |
|---|---|
| Git and dependencies | Git excludes .env, wallet, virtual environment and model cache. `pip check` passed. |
| MiniLM and Oracle smoke | 384 dimensions, maximum 256 tokens, matching fingerprint. Two Oracle probe rows, nearest chunk 0, self-distance 0.0. |
| Repeat ingestion and SQL | Four documents, four chunks, zero new inserts. Direct SQL confirmed the persisted counts, zero null-source probes and the native VECTOR column. |
| Live pytest | 30 passed in 20.60 s, zero failures and skips, with no explicit similarity threshold override. Recall@3 and MRR@3 were both 1.00 on the existing seed set. |
| Uvicorn and Swagger | Relevant query returned 200 with correct evidence. Napoleon query returned insufficient_evidence. Blank query and top_k=100 both returned 422. |
| Latency and debugging | Application reported 199.82 ms for the transaction query and 91.65 ms for the unrelated query. These are individual observations. VS Code traced the 384-value vector, threshold 0.25, admission and database access, and returned the expected result with HTTP 200. Debugger pauses invalidate that request as a latency observation. |

Codex follow-up used the pinned local model and the real tokenizer. With the
underlying Sentence Transformers inference call guarded by a test double,
the 302-token and 262-token inputs both raised ValueError and the guarded
method recorded zero calls. The warnings come from counting full tokens with
`truncation=False` before comparing the length to 256. The tokenizer can
warn during counting even though the app rejects the input before inference.

Codex also parsed both original archive entries and reproduced a mismatched
tag in `evaluation/m1-tests.xml`. The live JUnit report parsed successfully.
The repaired archive preserves 74 entries and both JUnit reports parse.
No new live Oracle or HTTP runs were performed for this follow-up.

## 2026-11-26 — M1 Oracle and retrieval acceptance

Codex ran these checks on Windows with Python 3.11.6 and the pinned dependency
lock. The user reported creating the Mumbai Always Free 26ai TP instance and
setting up the wallet and schema account. Codex verified TCPS and Thin mode,
driver-reported server version `23.26.4.1.0`, the intended user, CREATE SESSION,
CREATE TABLE, a 104857600-byte DATA quota and no target objects before DDL.
The read-only SQL checks are listed in [M1 verification](docs/M1_VERIFICATION.md).
Sandbox DNS initially failed with Windows error 11001. The approved connection
retry returned cosine self-distance 0.0 using the database's vector functions.

| Check | Command or protocol | Observed result |
|---|---|---|
| Schema and real MiniLM smoke | `.venv/Scripts/python -m app.smoke oracle --init-schema` | Exit 0. Two probe chunks, nearest was chunk 0, self-distance 0.0, 384 dimensions and 256-token limit. |
| Ingest and repeat | `.venv/Scripts/python -m app.ingest` twice | Exit 0. First inserted four documents and four chunks. Second inserted zero of either. SQL counted zero persisted probes, four documents and four chunks. |
| First full suite | `RUN_MODEL_TESTS=1`, `RUN_ORACLE_TESTS=1` and pytest | 29 passed, one failed. API returned 503. Focused rerun identified `DPY-4005`. Startup acquire and ping fixed the Thin pool readiness race. |
| Default local suite | `.venv/Scripts/python -m pytest -q -rs` | 26 passed, four opt-in tests skipped, zero failures. The sandboxed run stalled in asyncio's Windows loopback socket setup and was interrupted. The same command passed with scoped loopback access. |
| Final full suite | `$env:RUN_MODEL_TESTS='1'; $env:RUN_ORACLE_TESTS='1'; $env:SIMILARITY_THRESHOLD='0.25'; .venv/Scripts/python -m pytest -q -s -rs --junitxml=evaluation/m1-live-tests.xml` | Exit 0. **30 passed, 0 failed, 0 skipped** in 19.57 s. One upstream AnyIO deprecation warning. Includes simulated failure/overload, real MiniLM, Oracle rollback and live Oracle-backed API checks. |
| Served HTTP | `.venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8073 --workers 1 --limit-concurrency 8`, GET OpenAPI/Swagger and POST requests from the verification guide | OpenAPI and Swagger 200. Answerable search 200 with Transactions ranked first. Unrelated search 200 with empty evidence. Blank query 422. |
| Local review | `pip check`, `compileall -q app tests`, Git ignore and tracked-file checks | Passed. No tracked wallet, .env, model cache or virtual environment. |

The fixed corpus is `corpus/database_operations.jsonl`, with the same pinned
model and fingerprint as the earlier entry. Eight answerable and two unrelated
queries were labeled before their first execution. With top K 3 and similarity
threshold 0.25, all eight expected sources ranked first. Recall@3 and MRR@3
were 1.00 on this sample, and both unrelated queries returned no evidence.
Raw per-query results and JUnit output are retained locally. This small seed
test provides no generalization or production performance estimate.

Review checked SQL binds, deterministic ranking, model fingerprint, input limits,
transaction scopes, pool handling, disclosure and attribution. No unresolved
critical or high findings for the loopback demo. All M1 acceptance gates pass.
Full V1 release gates, authorization for remote actions and the M2 provider
smoke remain open. The HTTP and SQL steps above were automated by Codex. No
separate manual verification results have been reported by the user.

## 2026-11-26 — initial M1 component verification

Environment: Windows, Python 3.11.6, fresh project .venv; 15.40 GiB total RAM and
4.24 GiB available at inspection, about 188 GiB free on C:. CPU model inference,
two torch threads. No Oracle server, cloud quota or API billing verified. Local
Git main initialized, no commit or release. Exact resolved dependencies are in
requirements.txt; .venv/Scripts/python -m pip check passed.

Model: sentence-transformers/all-MiniLM-L6-v2, revision
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`; normalized float32, identity-v1 text
preprocessing. Observed dimensions 384, total token limit 256, special tokens 2.
Fingerprint: `346fdccbfeccc19587e4367c6a13a678671c248c1d9bff8c0fe4ca6796df9560`.
Corpus/prompt revision: not applicable; synthetic test sentences only, no LLM.

| Command | Observed result | Evidence type |
|---|---|---|
| `.venv/Scripts/python -m pip install ...` with pins in requirements.in | Passed on approved network retry; initial sandbox DNS failure | Real isolated install |
| `.venv/Scripts/python -m pytest -q` | 19 passed, 2 skipped, 1.43 s, exit 0 | Local validation/driver parsing; one mocked DB failure cleanup check; model/Oracle skipped |
| `.venv/Scripts/python -m app.smoke model --download` | Passed, exit 0, 384 dimensions/256 tokens/2 special tokens | Real public weights + CPU inference; approved network retry after sandbox DNS failure |
| `$env:RUN_MODEL_TESTS='1'; .venv/Scripts/python -m pytest -q -rs` | 20 passed, 1 skipped, 23.68 s, exit 0 (before final finite-distance review guard) | Real cached model + unit checks; Oracle integration skipped |
| `$env:RUN_MODEL_TESTS='1'; .venv/Scripts/python -m pytest -q -rs --junitxml=evaluation/m1-tests.xml` | 20 passed, 1 skipped, 22.19 s, exit 0 after final code review change | Final real cached model + unit run; raw report: evaluation/m1-tests.xml; Oracle skipped |
| `.venv/Scripts/python -m app.smoke oracle; exit $LASTEXITCODE` | Exit 2: missing ORACLE_USER, ORACLE_PASSWORD, ORACLE_DSN | Real configuration failure; no DB connection attempted |
| `.venv/Scripts/python -m compileall -q app tests` | Passed | Syntax compilation |
| `git diff --check`, ignore probes, implementation secret-pattern scan | Passed; 0 matches across 11 implementation files at scan time | Narrow static check, not proof of absence of every possible secret |

Early test attempts during installation failed because pytest/oracledb were not
installed yet; subsequent post-install runs above passed. No failed test assertion
was weakened. Windows cache emitted a symlink limitation warning; normal file
copies worked without administrator changes. No retrieval Recall@K, MRR, latency
benchmark, throughput, citation quality or end-to-end success measured. The 23.68 s
figure is pytest runtime, not API/inference latency. Real Oracle and LLM checks
remain required. Raw smoke fields and test summaries are recorded here; there is
no benchmark dataset or raw benchmark output yet.
