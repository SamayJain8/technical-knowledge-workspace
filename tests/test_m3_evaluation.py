"""Held-apart seed questions with one expected source per answerable case."""

import json
import os
from statistics import median
from time import perf_counter

import pytest
from fastapi.testclient import TestClient

from app.main import app

CASES = [
    ("What can prevent a failed funds transfer from leaving only one account updated?", "tutorial-transactions.html"),
    ("What happens when I roll back my pending operations?", "tutorial-transactions.html"),
    ("Does EXPLAIN ANALYZE execute a statement that modifies data?", "using-explain.html"),
    ("How can I spot discrepancies between estimated cardinality and measured row counts?", "using-explain.html"),
    ("Why does PostgreSQL keep previous versions after a DELETE?", "routine-vacuuming.html"),
    ("Which database cleanup rewrites a table and takes an exclusive lock?", "routine-vacuuming.html"),
    ("Can the planner sometimes use skip scan on later columns?", "indexes-multicolumn.html"),
    ("What kind of composite index can use a range after an equality condition?", "indexes-multicolumn.html"),
    ("What is the boiling point of ethanol?", None),
    ("Who led France at the Battle of Austerlitz?", None),
    ("How do I repair a flat bicycle tire?", None),
    ("Why do migrating birds fly in formation?", None),
]


@pytest.mark.oracle
def test_m3_labeled_retrieval_and_runtime():
    if os.getenv("RUN_ORACLE_TESTS") != "1":
        pytest.skip("Set RUN_ORACLE_TESTS=1")
    ranks, negatives, elapsed = [], [], []
    with TestClient(app, base_url="http://localhost") as client:
        assert client.get("/health/ready").json() == {"status": "ready"}
        # One warm-up. The measurements below are sequential ASGI requests.
        assert client.post("/api/v1/search", json={"query": "PostgreSQL transactions"}).status_code == 200
        for query, source in CASES:
            start = perf_counter()
            response = client.post("/api/v1/search", json={"query": query, "top_k": 3, "document_type": "seed"})
            elapsed.append(round((perf_counter() - start) * 1000, 2))
            assert response.status_code == 200
            assert response.headers["x-request-id"] == response.json()["request_id"]
            rows = response.json()["results"]
            rank = next((i for i, row in enumerate(rows, 1) if source and row["source_url"].endswith(source)), 0)
            if source:
                ranks.append(rank)
            else:
                negatives.append(not rows)
            print(json.dumps({"query": query, "expected": source, "rank": rank,
                              "status": response.json()["status"], "latency_ms": elapsed[-1]}))
    print(json.dumps({"requests": len(elapsed), "recall_at_3": sum(bool(rank) for rank in ranks) / len(ranks),
                      "mrr_at_3": sum(1/rank for rank in ranks if rank) / len(ranks),
                      "negative_passes": sum(negatives), "median_ms": median(elapsed),
                      "min_ms": min(elapsed), "max_ms": max(elapsed)}))
    assert sum(bool(rank) for rank in ranks) >= 7
    assert sum(negatives) >= 3


@pytest.mark.gemini
def test_live_m3_vacuum_answer():
    if os.getenv("RUN_GEMINI_TESTS") != "1":
        pytest.skip("Set RUN_GEMINI_TESTS=1 only after approving one countTokens and one generation call")
    with TestClient(app, base_url="http://localhost") as client:
        response = client.post("/api/v1/answer", json={
            "query": "Which database cleanup rewrites a table and takes an exclusive lock?",
            "public_question": True, "top_k": 3, "document_type": "seed",
        })
    assert response.status_code == 200
    data = response.json()
    print(json.dumps({"status": data["status"], "latency_ms": data["latency_ms"],
                      "citations": data["citations"]}))
    assert data["status"] == "ok" and "VACUUM FULL" in data["answer"]
    assert "exclusive lock" in data["answer"]
    sources = {row["chunk_id"]: row for row in data["sources"]}
    assert data["citations"]
    for citation in data["citations"]:
        row = sources[citation["chunk_id"]]
        assert row["source_url"].endswith("/routine-vacuuming.html")
        assert citation["quote"] in row["text"]
