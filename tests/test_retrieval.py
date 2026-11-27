import json
import os
from threading import BoundedSemaphore
from unittest.mock import Mock

import oracledb
import pytest
from fastapi.testclient import TestClient

from app.corpus import DEFAULT_CORPUS, chunk_text, load_documents
from app.embeddings import MiniLM
from app.main import app


def test_corpus_validates_and_deduplicates(tmp_path):
    source = tmp_path / "corpus.jsonl"
    row = vars(load_documents(DEFAULT_CORPUS)[0]).copy()
    source.write_text(json.dumps(row) + "\n" +
                      json.dumps({**row, "source_url": "https://example.org/same"}), encoding="utf-8")
    assert len(load_documents(source)) == 1
    source.write_text(json.dumps({**row, "source_url": "http://example.org/invalid"}), encoding="utf-8")
    with pytest.raises(ValueError, match="line 1"):
        load_documents(source)


@pytest.mark.model
def test_chunks_use_real_tokenizer_and_preserve_tail():
    if os.environ.get("RUN_MODEL_TESTS") != "1":
        pytest.skip("Set RUN_MODEL_TESTS=1")
    model = MiniLM()
    chunks = chunk_text("database " * 420 + "final marker café", model)
    assert len(chunks) >= 3
    assert chunks[-1].endswith("final marker café")
    assert all(len(model.model.tokenizer.encode(chunk)) <= 256 for chunk in chunks)
    assert len(model.encode(chunks)) == len(chunks)


@pytest.mark.parametrize("payload", [
    {"query": " "}, {"query": "x" * 2049}, {"query": "valid", "top_k": "2"},
    {"query": "valid", "top_k": 11}, {"query": "valid", "extra": True},
])
def test_search_rejects_invalid_requests(payload):
    response = TestClient(app, base_url="http://localhost").post("/api/v1/search", json=payload)
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid search request"}


def test_search_busy_and_database_failure(monkeypatch):
    admission = BoundedSemaphore(1)
    pool = Mock()
    pool.acquire.side_effect = oracledb.OperationalError("sensitive example")
    monkeypatch.setattr(app.state, "admission", admission, raising=False)
    monkeypatch.setattr(app.state, "pool", pool, raising=False)
    client = TestClient(app, base_url="http://localhost")
    admission.acquire()
    assert client.post("/api/v1/search", json={"query": "valid"}).json() == {"detail": "Search is busy"}
    admission.release()
    response = client.post("/api/v1/search", json={"query": "valid"})
    assert response.status_code == 503
    assert response.json() == {"detail": "Search database unavailable"}
    assert admission.acquire(blocking=False)
    admission.release()


# One relevant source for each positive query. Labels fixed before first run.
CASES = [
    ("How do I undo a subset of writes while keeping the transaction open?", "tutorial-transactions.html"),
    ("How can I ensure both bank balance changes commit together?", "tutorial-transactions.html"),
    ("How can I compare the optimizer's expected row count to what actually ran?", "using-explain.html"),
    ("What shows the operations chosen by the query planner?", "using-explain.html"),
    ("Which maintenance operation makes storage from dead rows reusable?", "routine-vacuuming.html"),
    ("What automatically schedules cleanup of obsolete tuples?", "routine-vacuuming.html"),
    ("Which key should come first for equality on customer and a range on date?", "indexes-multicolumn.html"),
    ("How does the order of columns in a composite B-tree affect scanning?", "indexes-multicolumn.html"),
    ("What causes a solar eclipse?", None),
    ("How do I bake a chocolate cake?", None),
]


@pytest.mark.oracle
def test_live_api_retrieval_evaluation():
    if os.environ.get("RUN_ORACLE_TESTS") != "1":
        pytest.skip("Set RUN_ORACLE_TESTS=1 after ingesting the reference corpus")
    ranks, negatives = [], []
    with TestClient(app, base_url="http://localhost") as client:
        for query, expected in CASES:
            response = client.post("/api/v1/search", json={"query": query, "top_k": 3, "document_type": "seed"})
            assert response.status_code == 200, response.text
            data = response.json()
            results = data["results"]
            scores = [hit["similarity_score"] for hit in results]
            assert scores == sorted(scores, reverse=True)
            assert len(results) <= 3 and all(hit["text"] and hit["provenance"] for hit in results)
            rank = next((i for i, hit in enumerate(results, 1)
                         if expected and hit["source_url"].endswith("/" + expected)), 0)
            if expected:
                ranks.append(rank)
            else:
                negatives.append(data["status"] == "insufficient_evidence" and not results)
            print(json.dumps({"query": query, "expected": expected, "rank": rank,
                              "sources": [hit["source_url"] for hit in results], "scores": scores}))
        too_long = client.post("/api/v1/search", json={"query": "database " * 180 + "a " * 80})
        assert too_long.status_code == 422
    print(json.dumps({"recall@3": sum(bool(rank) for rank in ranks) / len(ranks),
                      "mrr@3": sum(1 / rank for rank in ranks if rank) / len(ranks),
                      "no_evidence": sum(negatives), "negative_queries": len(negatives)}))
    assert sum(bool(rank) for rank in ranks) >= 7
    assert all(negatives)
