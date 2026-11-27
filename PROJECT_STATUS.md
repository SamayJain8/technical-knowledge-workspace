# Living status — M3.1 document workspace

27 November 2026. The development-preview frontend and README are prepared.
The patched ML stack passed the full Windows application regression and is
now pinned. The previous local environment is available for rollback.
M3.2 is postponed. The independent review passed and the maintainer approved
the MIT license. Dedicated Oracle roles and final Docker runtime verification
remain open. The initial commit, tag and remote publication are maintainer-run.

27 November 2026. The functional follow-up is accepted. Retrieval, chunking,
synthesis and citation-quality enhancements are frozen for V1 except critical
correctness or security fixes. Benchmarked upload defaults are adopted.
Separate Oracle identities await administrator provisioning. The candidate
ML pins passed the isolated Windows encoder and Oracle compatibility check.
The subsequent development-preview regression verified and adopted those pins.

27 November 2026. The final functional correction pass is verified on
controlled fixtures. It is ready for the separate frontend redesign. Public
release at that checkpoint was gated by reader/writer verification, ML dependency remediation,
final Docker verification, Prompt 4 review and sanitized source inspection.
No 100-page support claim. See [evaluation](EVALUATION_RESULTS.md).

The user independently verified cross-document synthesis on the original
PDFs. The SQLite multipart check was partial and exposed one weak citation.
Synthesis v3 guards against that byte-quantity mismatch. The historical
page-size omission remains open because the configured replay library
could not locate the original SQLite row.

26 November 2026. M1 is accepted for the local retrieval demo following
successful automated checks, user-reported independent verification and
external code and architecture review. M2 passed automated integration checks
with one real Gemini generation and independent verification. M3 adds local
safeguards, demo UI and a broader seed evaluation. M3 is accepted for the local
demo after independent user-performed functional verification. Release blockers
remain open: dedicated Oracle READ access, dependency remediation, Docker
runtime verification and independent final release review. M3.1 adds PDF, TXT
and Markdown uploads, page-aware search, and explicit document eligibility.
M4–M6 are planned.
See [evaluation](EVALUATION_RESULTS.md).

- Verified for the local candidate: R01–R08, R09–R11 and the implemented
  subset of R13–R15 and R23 (scoped retrieval, exact/hybrid ranking, visible
  citations and versioned prompts). See the verification scope for each gate.
- Partial: R12 packaging, R19–R21 authorized and durable ingestion/versioning,
  and R22 realistic answer-quality, ranking and load evaluation. Reader/writer
  privilege verification and Linux dependency auditing remain release gates.
- Deferred: R16 history and suggestions, R17 streaming, R18 feedback, and
  R24 index/reranker comparisons. R25–R31 remain V2. R32–R35, including
  caching and multi-instance scaling, remain conditional.

| Requirement | Observed status | Evidence and next action |
|---|---|---|
| R01 | Oracle, Python and Gemini verified | Python 3.11.6, Thin 3.4.1, Oracle 23.26.4.1.0 over wallet TCPS. Gemini free tier and dashboard quotas are user-reported. |
| R02 | Tested | Real pinned CPU MiniLM, normalized 384-D FLOAT32, 256 tokens including two special tokens. |
| R03–R04 | Tested | Four attributed documents, four chunks. Real ingestion added four of each. Repeat added zero. Chunking checked against the real tokenizer. |
| R05–R06 | Tested on seed corpus | Exact Oracle cosine ranking with bound top K and version filter. Threshold 0.25. Eight expected sources ranked first. Two unrelated queries returned empty evidence. |
| R07–R08 | M2 verified | Search preserved. Answer returns verified excerpts and chunk IDs, abstains without evidence and degrades on provider failures. One genuine Gemini generation passed. |
| R09–R10 | Local safeguards tested | Live/ready, request IDs, JSON access events, maximum body size, 20 s response deadline and bounded admission. Dedicated READ account not verified. |
| R11, R22 | Seed evaluation performed | Eight new answerable and four unrelated questions against real Oracle. Recall@3 and MRR@3 both 1.00 on these labels. Two single-query live Gemini checks across M2 and M3. Broader quality and load evidence pending. |
| R12 | Partial | Windows dependency regression, advisory scan and independent preview review passed. MIT license approved. Full Linux image build, audit, startup and tagging remain pending. |
| R13–R15, R19–R21, R23 | Local M3.1 slice | Document scope/type, two retrieval modes, library UI, bounded upload jobs, metadata, stable content IDs and cited extractive/synthesis modes. Admin auth, durable jobs and dataset replacement remain open. |
| Remaining | Preserved by identifier | Extended filtering and corpus-scale hybrid evaluation, R16–R18, durable operations and versioning under R19–R21, and R24 remain V1 work. R25–R31 are V2. R32–R35 are future or conditional. |
| Release | Local demo and independent preview review accepted | Initial commit, tag and push are pending. |

M3.1 Checkpoint A passed with a real Chrome upload and a live Gemini answer
citing page 2 of the newly indexed PDF. Checkpoint B includes semantic/hybrid
comparison, both answer modes and bounded lifecycle controls. Checkpoint C
is partial. Confirmed deletion was exercised against a disposable TXT, and a
malformed PDF failed without creating an indexed row. Review
[actual results](EVALUATION_RESULTS.md) for the mock/live
distinction and release blockers.

V1 follow-up keeps R13–R14 and R24 together so metadata isolation, hybrid
ranking and any index/reranker can be compared to the exact-search baseline.
R16–R18 follow after session privacy, streaming cancellation and feedback
contracts are designed. R19–R21 follow after defining admin authorization,
ingestion state/recovery and dataset replacement. None are claimed in the
local candidate. R22 grows with a larger labeled corpus and load profile.
R25–R31 start only in M4–M6. R32–R35 remain conditional on measured needs
or a scope change.

The independent M1 run passed 30 tests with no failures or skips and without an
explicit threshold override. M2 aligned both OpenAPI 422 schemas with runtime.
Tokenizer and Starlette/AnyIO warning reviews remain open. The Desktop review archive's
JUnit redaction was repaired and both reports now parse. See
[independent evidence](EVALUATION_RESULTS.md) and [limitations](KNOWN_LIMITATIONS.md).

Current resume claim: Built and verified a FastAPI retrieval and grounded-answer
service using local 384-D MiniLM, Oracle Cloud exact cosine search and Gemini
structured output with validated source excerpts.

Gemini 3.5 Flash-Lite is configured locally. Authenticated listing also returned
3.1 Flash-Lite as an alternative. The account's free tier and 15 RPM / 250,000 TPM
are user-reported, and the daily limit is unconfirmed. Release actions await
independent review. See [limitations](KNOWN_LIMITATIONS.md) and
[setup and execution](README.md#run-locally).
