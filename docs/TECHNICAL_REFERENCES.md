# Technical references

| Status | Technology | Version, use and implementation | Official references |
|---|---|---|---|
| Implemented | Python and Git | Python 3.11.6, Git 2.55.0. Local virtualenv and pinned Windows dependency lock. | [Python 3.11](https://docs.python.org/3.11/) |
| Implemented | Oracle Cloud and python-oracledb | Autonomous AI Database 26ai reported by user, driver server version 23.26.4.1.0. Thin driver 3.4.1, `PoolParams`, `connect`, `create_pool`, `executemany(batch_size=8)`, `array('f')` VECTOR binding. See `app/oracle.py`, `app/search.py`, `sql/001_retrieval.sql`. | [Driver 3.4.1](https://python-oracledb.readthedocs.io/en/v3.4.1/), [Oracle exact similarity](https://docs.oracle.com/en/database/oracle/oracle-database/26/vecse/perform-exact-similarity-search.html) |
| Implemented | Sentence Transformers, HF Hub, PyTorch | 6.3.0, 2.5.0, 2.13.0 respectively. Transformers 5.24.1, NumPy 2.3.5. MiniLM revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, Apache-2.0. CPU safetensors, 384-D, 256 tokens including two special tokens. `app/embeddings.py` and `app/corpus.py`. | [Pinned model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/tree/1110a243fdf4706b3f48f1d95db1a4f5529b4d41), [Sentence-BERT paper](https://aclanthology.org/D19-1410/), [v6.3.0 release](https://github.com/huggingface/sentence-transformers/releases/tag/v6.3.0) |
| Implemented | FastAPI, Starlette, Pydantic and Uvicorn | 0.165.0, 1.10.0, 2.12.5, 0.38.0. Lifespan, thread-dispatched search, strict body schema, one local worker. `app/main.py`. | [FastAPI releases](https://fastapi.tiangolo.com/release-notes/), [Starlette releases](https://starlette.dev/release-notes/) |
| Implemented | pytest and HTTPX | 9.0.3 and 0.28.1. Unit, CPU model and real database checks. ASGI tests use TestClient with an HTTPX deprecation warning. | [pytest releases](https://docs.pytest.org/en/stable/changelog.html), [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/) |
| Implemented | PostgreSQL 18 documentation | Source material for four original summaries. Attribution and upstream license are in `corpus/`. | [License](https://www.postgresql.org/about/licence/) |
| Implemented | Gemini Developer API | google-genai 1.68.0. `gemini-3.5-flash-lite` verified on authenticated listing and with structured generation. 3.1 listed as an alternative. `app/gemini.py` and `app/answer.py`. | [SDK v1.68.0](https://github.com/googleapis/python-genai/tree/v1.68.0), [model and capabilities](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite) |
| Planned | LangGraph, named read-only SQL tools | M4–M6 add constrained investigation and evaluation. | [Roadmap](IMPLEMENTATION_PLAN.md) |
| Optional | MCP, alternative models, fine-tuning | Consider against measured needs. | [Architecture decisions](ARCHITECTURE_DECISIONS.md) |

See Learning references for the existing courses and videos.

M3 uses Python 3.11 asyncio timeout semantics, FastAPI/Starlette thread-pool
dispatch, Oracle 3.4.1 pool callbacks, and static browser assets. No new
application dependency was needed. Docker Desktop uses a Linux Python 3.11
image and CPU PyTorch. See [asyncio tasks](https://docs.python.org/3.11/library/asyncio-task.html),
[Oracle PoolParams](https://python-oracledb.readthedocs.io/en/v3.4.1/api_manual/pool_params.html),
and the [Dockerfile reference](https://docs.docker.com/reference/dockerfile/).

M3.1 pins `pypdf==7.1.1` (BSD-3-Clause, Python >=3.10). PyPI lists it as
the latest stable release on 26 November 2026. OSV returned no matching
advisories for the exact 7.1.0 and 7.1.1 versions queried. A database lookup
is a point-in-time check. The parser sets independent pypdf work limits and
runs in a timed, credential-stripped child process. See the
[7.1.1 release](https://github.com/py-pdf/pypdf/releases/tag/7.1.1),
[PyPI metadata](https://pypi.org/project/pypdf/7.1.1/) and
[pypdf security limits](https://pypdf.readthedocs.io/en/7.1.0/user/security.html).
## Pre-frontend ML dependency review · 2026-11-27

| Current pin | Applicable advisory surfaces | Candidate |
|---|---|---|
| PyTorch 2.9.1 | Untrusted checkpoint loading, LSTM cell and JIT script memory corruption. The app uses a pinned safetensors MiniLM model and CPU encoder inference. Uploads never supply checkpoints, JIT input or model selection. | 2.13.0. The JIT advisory lists this fix. PyPI lists a Windows CPython 3.11 x64 wheel. A matching dedicated CPU-index wheel was not confirmed. |
| Transformers 4.57.3 | Model initialization and custom generation, Trainer, and chat-template export paths. The app uses a fixed encoder, with no training, model export or Transformer generation. | 5.24.1. Requires Python 3.11+, huggingface-hub >=1.31,<3 and tokenizers >=0.23.1,<0.24. Refresh the transitive lock together. |
| Sentence Transformers 5.1.2 | A locally controlled model directory could bypass the remote-code opt-out. The fixed revision and trusted cache reduce exposure. Keep the cache isolated from uploaded files and untrusted writers. | 6.3.0. The advisory lists 5.6.0 as the first patch. 6.3.0 requires Transformers >=5,<6 and PyTorch >=2.2. |

Exact-version OSV queries returned no matches on the three candidates on
2026-11-27. The official Windows PyPI wheel reported no CUDA build and
the isolated Python 3.11.6 environment passed pip check, a 52-package
OSV scan, the CPU MiniLM comparison and read-only Oracle retrieval.
After the full Windows regression, the preview pins were updated and the
original workspace environment was preserved for rollback. The official
CPU index also lists Linux wheels. Final Linux runtime verification is
pending. See [verification evidence](../EVALUATION_RESULTS.md).

[PyTorch JIT advisory](https://github.com/advisories/GHSA-rrmf-rvhw-rf47)
[Transformers releases](https://github.com/huggingface/transformers/releases)
[Sentence Transformers advisory](https://github.com/advisories/GHSA-jhr6-gm9c-rqjv)
