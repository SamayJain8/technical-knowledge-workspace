# Known limitations

- The user verified both original PDFs in the running browser instance.
  The automated read-only SQL trace found no matching SQLite title in its
  configured library. The omitted page-size range in the historical multipart
  response remains unattributed to a specific stage.
- Synthesis can explicitly report partial support, but a model can still omit
  a question part without reporting it. Validation checks exact quote text,
  chunk identity and the presence of a numeral for an explicit byte quantity
  in the claim. The byte check can reject equivalent number words, and a
  matching numeral can appear in a sentence about another quantity. Semantic
  support and preservation of all qualifications still need human evaluation.
- The measured 5 MB / 40-page / 120,000-character / 128-chunk profile is
  now the default. Chunking policy and parser safeguards are unchanged. Large-document
  evidence is limited to the authored 20/40-page probes. Busy HTTP searches
  may still receive 503. The test measured model-admission opportunities and
  parent memory, not production concurrency or PDF child memory.
- The migrated Windows stack returned zero OSV matches on 2026-11-27.
  Linux container and operating-system scans remain pending. Dedicated
  Oracle runtime accounts, final Docker runtime and Prompt 4 release
  review remain open.

- M3.1 is a loopback single-user workspace. Uploads are stored as text and
  vectors in Oracle Cloud. There is no multi-user authorization. Only
  separately approved public excerpts and questions may reach Gemini.
- The job registry retains 64 volatile entries, with one accepted upload
  slot and no waiting backlog. After restart, reread the indexed library and
  retry an absent upload. Shutdown waits for accepted work. Oracle transactions
  keep incomplete documents from appearing. The PDF child has an 8-second
  wall limit and independent decode/work bounds, without an operating-system
  memory sandbox. OCR and encrypted PDFs are unsupported.
- For the small local library, hybrid uses bounded Oracle substring matching
  and reciprocal rank fusion. It is neither Oracle Text nor BM25. The
  evaluation does not establish improvement over the dense baseline.
- Synthesis validates citations and exact quotations. Human judgment is still
  needed to decide whether each paraphrase is fully supported. Validation
  failure degrades to locally retrieved evidence without another provider call.
- The local verification account owns the tables. Separate reader/writer
  access and final Docker runtime verification remain open.

- V1 selects cited sentences from the reviewed seed corpus. Exact excerpt
  validation checks provenance and text but cannot prove that selected sentences
  answer all parts of a question. Two live positives across M2/M3 and the
  recorded abstention controls are a qualitative check. Grounded generative
  synthesis is implemented. A larger answer-quality dataset remains pending.
- Initial evaluation uses four source summaries, eight answerable queries and
  two unrelated negatives. The 0.25 threshold is provisional. Larger
  held-out data, ambiguous questions and workload measurements remain pending.
- External generation requires per-request confirmation of a public test
  question. The confirmation is caller-provided. The provider receives no
  arbitrary Oracle chunk text, but a caller can mislabel their question.
  Local admission allows six attempts per minute per worker, each with at most
  two provider calls. Daily quota is unconfirmed. The 20-second deadline limits
  the client wait. A synchronous operation already running can outlive the
  response and keeps its admission slot until it exits. Gemini's transport
  timeout is ten seconds per phase.
- Oversized token counting disables the tokenizer's warning for this intentional
  validation call. Full counts and explicit rejection remain in place.
- Ingestion keeps immutable snapshots. Edited metadata, content or chunk policy
  creates a new ID. Older snapshots using the same embedding fingerprint can
  still appear in search. Replacement and selection among corpus versions are
  R21 work. Run one ingestion process at a time. If concurrent inserts conflict,
  Oracle rejects the duplicate key, rolls back the attempted transaction and
  the CLI can be rerun.
- The tested local account owns the tables. A separate Oracle READ account is
  supported by configuration but needs live setup and verification. The demo
  is loopback-only. Public deployment would require authentication, shared
  request/usage limits and centralized observability.
- Schema DDL commits and is intended for a new schema. Inspect a partial
  initialization before retrying. No table deletion or automated migration
  rollback is available.
- The dependency lock is for the tested Windows Python 3.11 environment.
  A clean reinstall on another machine and a transitive license audit
  remain pending. The migrated regression emitted a deprecation warning
  for the Sentence Transformers dimension getter.
- Dockerfile and Compose static checks pass. The first build was stopped
  during dependency downloads after a security fix made its source snapshot
  stale. A final Linux image, image audit and startup smoke remain pending.
- The application uses the MIT license. Docker verification, remote
  publication and preview tagging remain open.
