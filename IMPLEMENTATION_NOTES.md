# Implementation notes

## 2026-11-27 · Final functional correction pass

The answer API retains its major statuses and adds `reason`. Successful
synthesis returns claim-linked citations and explicitly unanswered parts.
Internal candidates (up to sixteen), local display limits and provider context
budgets have distinct roles. Exact quotes still match the sent context.
Synthesis v3 also checks each explicit digit-form byte value against the
same quotation, normalizing thousands separators. An omitted value uses
the existing validation fallback. Search results remain visible and the
internal reason code contains no model or source text.
Numeric hybrid matches retain Oracle binds and use boundaries for short
offsets. One 25 ms ingestion handoff window precedes each page-tokenizing turn
and embedding batch. It is an opportunity for search, not a fairness guarantee.

## 2026-11-26 · M3.1

`app/library.py` handles upload/status/library lifecycle and optional Oracle
writer credentials. `app/pdf_extract.py` extracts page text in a timed process.
`sql/002_library.sql` adds upload metadata, content hash and page references.
Retrieval applies bound scope/type predicates before ranking. The renderer
uses text nodes and navigates only to validated HTTPS source URLs.

## 2026-11-26 · M3

- `app/request_limits.py` owns JSON body protection, request IDs, response
  deadlines and JSON access events. The body read consumes the same deadline.
- `app/gemini.py` counts the serialized question, evidence, instructions and
  schema with Gemini, reserves 128 tokens for framing and skips generation
  when the count is invalid, over budget or the deadline has expired.
- `app/answer.py` deduplicates normalized sentence text and validates exact
  quotes against the sent chunk ID. Public allowlisting uses the same
  chunking as ingestion. Ingestion alone grants no external-send permission.
- `app/ui/` renders source evidence as text. The build context is allowlisted.
  Oracle owner and runtime separation is a deployment step.

## 2026-11-26 · M2

`app/answer.py` owns the evidence and citation contract. `app/gemini.py`
translates it to the official SDK. `app/main.py` shares retrieval across the
two routes and releases the Oracle connection before provider work. Generation
admission and cooldown are independent of retrieval. No provider-generated
link or arbitrary answer prose is trusted. See the journal for trade-offs.

## 2026-11-26 — M1 continuation

See [Development journal](DEVELOPMENT_JOURNAL.md) for the design and learning
record, [M1 verification](docs/M1_VERIFICATION.md) for reproducible commands, and
[Evaluation results](EVALUATION_RESULTS.md) for actual runs. The Oracle schema
from the initial increment was applied after a read-only empty-schema check.
The retrieval slice reuses that schema and the pinned model. It adds an
immutable JSONL document contract, deterministic version-aware IDs, exact
top-K SQL with bound limits and a small local API. M2 and M3 remain separate.

## 2026-11-26 — M1 first increment (not a passed milestone)

- R01: inspected documentation-only workspace, initialized local Git main and
  isolated Python 3.11.6 .venv. Installed pinned dependencies from the package
  registry with scoped network approval; froze transitive versions in
  requirements.txt. Global ML packages were inspected but not reused or modified.
- R02: app/embeddings.py pins public Apache-2.0 MiniLM weights to an immutable
  revision, CPU, normalized float32/384-D vectors, at most 32 texts per call,
  encode batch 8 and two CPU threads. Actual tokenizer/model limits checked at
  runtime; oversized text fails before Sentence Transformers can truncate it.
  Revision/preprocessing fingerprint distinguishes incompatible embeddings even
  when dimensions match. Local weights and cache stay ignored.
- R04–R05: sql/001_retrieval.sql creates relational documents/chunks with native
  VECTOR(384,FLOAT32). app/oracle.py binds array('f') vectors, filters probe
  document/version, performs exact cosine search, verifies self-match, and always
  rolls back probe DML. DDL is separate/explicit because Oracle commits DDL.
  This is synthetic transport/ranking validation, not corpus ingestion/evaluation.
- R09 partial: app/config.py reads project .env with environment precedence and
  excludes values from repr/errors. TLS is enforced for every parsed address,
  server DN matching is reasserted after descriptor parsing, connection retries
  disabled, connect/call timeout 10 s each. app/smoke.py emits safe exception type
  or allowlisted Oracle error code rather than full driver text.
- Tests cover input/vector rejection, secret-safe config, plaintext/mixed TLS
  rejection, autocommit rejection and rollback on simulated failure. Real CPU
  tests check shape, normalization, related sentence ordering, Unicode and input
  token bounds. Oracle live test is explicitly opt-in and currently skipped.
- Added README.md with reproducible commands, .env.example, .gitignore, and
  docs/ORACLE_SETUP.md in response to user's request for setup guidance.

Review against docs/CODE_REVIEW_CHECKLIST.md found and fixed: incorrect proposed
driver getter (use documented protocol property), mixed-address TLS bypass,
descriptor overrides of DN/timeout settings, autocommit undermining rollback,
and missing rejection of nonfinite database distances. No remaining critical/high
issue found in local component review; live Oracle correctness remains unverified.
DDL partial application, per-call versus overall timeout, application licensing
and unavailable online lifecycle/pooling are explicitly documented limitations.

Learning notes: cosine distance is lower for closer vectors; similarity would be
1-distance, not a probability. Same model/config must embed both queries and
chunks. Self-match smoke verifies transport, whereas a labeled question/source
benchmark measures retrieval usefulness. Rollback protects probe data, not DDL.
Interview checks: explain why a 384-D vector alone cannot identify its model, why
silent truncation harms retrieval, and why mocked rollback is not live DB proof.

Next increment after Oracle setup: real schema/insert/search/rollback test, then
legally attributed corpus, token chunking, idempotent ingestion and /search.
FastAPI/LLM/UI scaffolding deliberately waits for the retrieval gate.
