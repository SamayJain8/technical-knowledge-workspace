# Development journal

## 2026-11-27 · Development-preview preparation

The UI keeps the existing API calls and divides the workspace into library,
question/answer and evidence panels. The screenshot uses a separate local
fixture so the public image contains no uploaded material. The patched CPU
stack passed the full Windows regression before promotion. Rollback keeps
the original environment and copies of its three dependency files under
the ignored cache directory. See [verification evidence](EVALUATION_RESULTS.md).

## 2026-11-27 · Pre-frontend closure

The earlier capacity measurements became the upload defaults. We kept the
PDF parser bounds, model batch size and single-job admission. A focused
library suite and direct runtime-limit assertion confirmed the configuration.
Oracle accepted a read-only diagnostic session and returned Atlas only for
the two filename probes. Project `.env` loading gives precedence to process
environment values, and Compose supplies a separate runtime file. Without a
live browser server to compare, the historical mismatch remains unresolved.
Administrator SQL and the separate environment upgrade plan are documented.

## 2026-11-27 · Final functional correction pass

Independent Atlas/SQLite testing exposed the gap between retrieval ranking,
sent context, and answer completeness. We kept exact citation validation and
gave the UI a separate reason for each skip or fallback. Token count and
generation remain behind both consent gates. Synthesis v2 asks for every
supported part and lists unanswered parts explicitly. It still needs a
separate semantic evaluation.

The original-PDF browser follow-up confirmed cross-document synthesis and
exposed a gap between quotation integrity and factual support. We added a
deterministic byte-numeral check and a direct-support prompt instruction in
synthesis v3. This retains the existing provider boundary and evidence
fallback. A common value in an unrelated sentence can still pass. The local
Oracle trace identifies where evidence drops out when the original indexed
PDF is visible, without sending its text to an external provider.

Real Oracle rollback fixtures separated query ranking from generation tests.
The ingestion probe justified small between-turn handoff windows while
retaining one shared model and atomic persistence. The trade-off was higher
total ingestion time in exchange for more opportunities for search. Release
advisories and Oracle role separation remain visible in the status and setup
guides. See [actual commands/results](EVALUATION_RESULTS.md).

## 2026-11-26 · M3.1 document workspace

Inspected four documents and four chunks before applying additive library DDL.
Used the same MiniLM tokenizer and embedder for uploaded text, with a separate
bounded child for PDF extraction and one shared model admission gate. Database
transactions make documents searchable only after all chunks commit. Jobs are
ephemeral, while the indexed library is reconciled by rereading Oracle.

The Oracle account could not see Oracle Text's CTX_DDL package. The hybrid
fallback counts bounded substring matches in the same scoped SQL query and
combines candidate rankings with reciprocal rank fusion. Exact cosine remains
selectable. The browser lets the user approve excerpts and the question as
separate actions. Synthesis associates each claim with a checked quote, and
the API supplies document name and page from the stored chunk.

The first parser test revealed that pypdf's page-tree page entry cap counts
attributes as well as pages. We retained both an entry budget and an explicit
page-count check. The new dependency is pinned to 7.1.1 after checking official
release data, the installed APIs and OSV.

## 2026-11-26 · Independent M3 demo acceptance

The user verified health endpoints, the browser interface, Oracle transaction
retrieval, a live Gemini savepoint answer with two supporting excerpts and
links, and abstention on an unrelated question. The local demo is accepted.
[Evaluation results](EVALUATION_RESULTS.md) separates these observations from
automated runs. M3.1 will cover PDF/TXT upload and dynamic ingestion once the
complete prompt arrives.

## 2026-11-26 · M3 local release engineering

The user independently verified M2 using a correct savepoint answer, an
unrelated question, sanitized 422 and matching OpenAPI. Their timings and the
37-test M2 baseline are recorded separately in EVALUATION_RESULTS.md.

FastAPI dispatches the synchronous Oracle, MiniLM and Gemini calls to threads.
The HTTP deadline limits the client wait. Semaphores stay with active workers
so a timeout does not oversubscribe the model or provider. The readiness probe
uses the pooled session to check access to both tables. The browser demo uses
same-origin requests, text rendering and HTTPS citation links.

Using Gemini's model-aware token preflight costs an extra request. We lowered
admission to one eligible attempt every ten seconds, kept zero retries, and
kept local evidence available on upstream failures. V2 can reuse the DAO and
retrieval pipeline while keeping investigation orchestration and named SQL
tools outside the V1 route. Before increasing workers or replacing exact
search, measure load, memory and retrieval quality on representative data.

Interview questions: Why can work outlive a 504? What does an exact quote
check establish about grounding? How does Oracle READ differ from SELECT?
When would exact cosine search become the bottleneck?

## 2026-11-26 · Grounded answers with Gemini

The user reported a free-tier Google AI Studio project. Codex installed
google-genai 1.68.0 and verified model availability with one authenticated
listing. Google documents 3.5 Flash-Lite structured output. The single approved
generation returned two relevant savepoint excerpts that passed local validation.

Both routes use the same MiniLM and Oracle retrieval function. The provider
receives only chunks that match the bundled public corpus and a test question
the caller approves for external use. A provider protocol keeps SDK types
out of retrieval. Instead of accepting free-form claims with attached IDs,
the app checks complete excerpts against exactly what Gemini received and
assembles the response locally. This makes citation checks deterministic and
limits synthesis. Oracle resources are released before generation.

Why separate text verification from answer relevance? Exact source matching
shows where a sentence came from. It cannot show that the sentence fully
answers the question. See the seed evaluation and failure cases in
[evaluation results](EVALUATION_RESULTS.md).

## 2026-11-26 · Independent M1 acceptance

The user reported successful independent checks outside the Codex sandbox and
completion of external code and architecture review. In VS Code, the user
followed a request through application state, admission control, the database
connection and MiniLM. They observed a 384-value vector, a 0.25 similarity
threshold and a successful attributed result. Debugger pauses inflated the
reported latency. See [Evaluation results](EVALUATION_RESULTS.md).

The review caught a mismatch between the runtime 422 error body and its
OpenAPI schema. Contract alignment stays in the pre-release backlog. Codex
also confirmed that the archived historical JUnit report was malformed after
path redaction, repaired the archive, and parsed both archived reports.
A focused local check used the real tokenizer and verified that both oversized
test inputs were rejected without calling the underlying inference method.

## 2026-11-26 · First M1 increment

The workspace began with the Revision 2 handover and no Git repository. The
first session initialized local Git, created a Python 3.11.6 virtual environment,
and pinned MiniLM and its dependencies. Sandbox DNS blocked the package registry
and Hugging Face. Scoped network retries succeeded, and the Windows model cache
worked through file copies without changing system permissions. CPU inference
verified 384 normalized float32 values, a 256-token limit, and two special tokens.
The Oracle smoke and schema were written but database settings were absent.
See the first entry in [Evaluation results](EVALUATION_RESULTS.md).

## 2026-11-26 · Oracle Cloud and corpus retrieval

The user reported provisioning Always Free Autonomous AI Database 26ai, Transaction
Processing in Mumbai, and configuring a project user, quota, wallet, and `_low`
alias. Codex verified Thin-mode TCPS, server version, privileges, a 100 MiB quota,
and vector SQL through the driver. The schema was empty before initialization.
The first real 384-D vector smoke returned the probe's own chunk first with zero
cosine distance and rolled back both probe rows.

The local JSONL corpus uses original summaries of PostgreSQL 18 documentation.
Ingestion validates metadata and preserves source provenance. It slices original
text at tokenizer offsets and rechecks each slice against the actual model limit.
Document and chunk IDs are deterministic hashes. A transaction commits new
documents and chunks together, and repeated ingestion skips known IDs. The first
ingestion inserted four documents and four chunks. The repeat inserted zero.

The HLD keeps the CPU model, Oracle access and HTTP service in one process, with
ingestion as a separate command. At the LLD level, an immutable document dataclass
holds validated data, MiniLM owns the encoder and fingerprint, and Pydantic models
define the HTTP boundary. FastAPI composes these components with a single Oracle
pool connection and one search admission slot. This keeps synchronous inference
and SQL off the event loop and places a clear bound on work. Exact cosine search
gives a baseline for later index experiments. There is no orchestration component
at this stage. See [Verification instructions](docs/M1_VERIFICATION.md) and
[Evaluation results](EVALUATION_RESULTS.md).

The first real API suite failed with `DPY-4005` because Thin can fill the
initial pool after startup. The lifespan now acquires and pings a connection
using a bounded wait before the service accepts requests. The rerun passed all
30 tests, including the live retrieval evaluation and rollback checks.

Interview questions: Why include the embedding fingerprint in retrieval? Which
changes create a new document ID, and why does a transaction matter after partial
batch failure? How would you detect missed results before switching to an
approximate index? How would you replace immutable snapshots safely?
