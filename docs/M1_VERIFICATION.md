# Verify M1 locally

For future external review ZIPs, redact local paths in XML using a plain
placeholder such as `[workspace]`, or XML-escape any angle brackets. Parse
every archived JUnit report after redaction and reopen the ZIP to confirm
its integrity. The previous raw `<workspace>` replacement broke a closing
tag in the historical JUnit report. The Desktop archive has been repaired.

The automated evidence is in [Evaluation results](../EVALUATION_RESULTS.md).
Use these steps for your own verification. Your reported Oracle provisioning
is recorded separately in the [journal](../DEVELOPMENT_JOURNAL.md).

Run from the repository root in PowerShell. Use the existing local wallet and
`.env`. For a fresh machine install `requirements.txt` in a Python 3.11 venv
and run `.venv/Scripts/python -m app.smoke model --download` once.

```powershell
git check-ignore .env wallet/ewallet.pem .venv/Scripts/python.exe .cache/huggingface/model.safetensors
.venv/Scripts/python -m app.smoke oracle
.venv/Scripts/python -m app.ingest
$env:RUN_MODEL_TESTS = '1'
$env:RUN_ORACLE_TESTS = '1'
$env:SIMILARITY_THRESHOLD = '0.25'
.venv/Scripts/python -m pytest -q -s -rs
```

Expect the four paths to be ignored, smoke JSON with 384 dimensions, two probe
rows and self-distance near zero, and ingestion reporting four documents and
four chunks with zero inserts on a repeat. `--init-schema` is for a fresh schema
only after inspecting `USER_OBJECTS`. With both test flags enabled, the M1
baseline is 30 passing tests.

In Oracle Database Actions as the project user, run these read-only checks.

```sql
SELECT SYS_CONTEXT('USERENV', 'NETWORK_PROTOCOL') FROM dual;
SELECT privilege FROM session_privs WHERE privilege IN ('CREATE SESSION', 'CREATE TABLE');
SELECT tablespace_name, bytes, max_bytes FROM user_ts_quotas;
SELECT table_name FROM user_tables WHERE table_name IN ('DOCUMENTS', 'DOCUMENT_CHUNKS');
SELECT COUNT(*) FROM documents WHERE source_url IS NULL;
SELECT source_url, COUNT(*) FROM documents JOIN document_chunks USING (document_id)
GROUP BY source_url ORDER BY source_url;
```

Expect TCPS if using the Python wallet connection, both privileges, a bounded
DATA quota, both tables, zero persisted probes and four source rows on a schema
that contains only the reference corpus. Database Actions may report a different
network protocol because it uses its own connection.

```powershell
.venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 --limit-concurrency 8
```

Open Swagger at `http://127.0.0.1:8000/docs`. Execute `POST /api/v1/search`
with `{"query":"How do I undo part of a transaction?","top_k":3}`. Expect
HTTP 200, `status: ok`, and an attributed transaction result. Try
`{"query":"What causes a solar eclipse?"}` for `insufficient_evidence` with
empty results and `{"query":" "}` for 422.

In VS Code select the interpreter `.venv/Scripts/python.exe`. Use a Python
Debugger module configuration for `uvicorn` with arguments
`app.main:app --host 127.0.0.1 --port 8000 --workers 1 --limit-concurrency 8`
and the repository root as the working directory. Set breakpoints in
`app/main.py` at `search_route` and `app/search.py` at the cursor query.
Submit the Swagger request and inspect the result rows and similarity scores.
For ingestion use module `app.ingest` and break before `connection.commit()`.
Keep connection parameters and environment values out of debug captures.
