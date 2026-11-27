"""Format checks and opt-in live uploaded-document verification."""
import io
import os
from time import monotonic, sleep

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from app.library import extract, filename_kind
from app.main import app

ACTION = {"X-Library-Action": "1"}
PAGE_TWO = "A checkpoint marker named RUNBOOK_VEGA records the last fully verified restore."


def fixture_pdf(page_two=PAGE_TWO):
    writer = PdfWriter()
    for text in ("This public technical exercise documents database restore operations.", page_two):
        page = writer.add_blank_page(width=595, height=842)
        page[NameObject("/Resources")] = DictionaryObject({
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): DictionaryObject({
                NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            })}),
        })
        stream = DecodedStreamObject()
        stream.set_data(f"BT /F1 12 Tf 60 780 Td ({text}) Tj ET".encode("ascii"))
        page[NameObject("/Contents")] = stream
    target = io.BytesIO()
    writer.write(target)
    return target.getvalue()


def test_formats_keep_pdf_page_numbers():
    count, pages = extract(fixture_pdf(), "pdf", 5, 10000, 100000)
    assert count == 2 and pages[1] == [2, PAGE_TWO]
    assert extract(b"# A runbook", "md", 5, 100, 100)[1][0] == (None, "# A runbook")
    assert extract(b"Plain text", "txt", 5, 100, 100)[1][0] == (None, "Plain text")
    with pytest.raises(ValueError, match="page limit|Malformed"):
        extract(fixture_pdf(), "pdf", 1, 10000, 100000)


@pytest.mark.parametrize("name", ["../private.txt", "C:\\secret.txt", "a.exe", "a\n.txt"])
def test_invalid_filenames(name):
    with pytest.raises(ValueError):
        filename_kind(name)


@pytest.mark.parametrize("data, kind", [(b"%PDF-bad", "pdf"), (b"\0binary", "txt"), (b"  ", "md")])
def test_reject_invalid_content(data, kind):
    with pytest.raises(ValueError):
        extract(data, kind, 5, 100, 100)


def test_browser_cross_origin_mutation_is_refused():
    response = TestClient(app, base_url="http://localhost").post("/api/v1/documents?name=x.txt", content=b"example",
                                   headers={**ACTION, "Origin": "https://example.org",
                                            "Content-Type": "application/octet-stream"})
    assert response.status_code == 403
    assert TestClient(app).get("/api/v1/documents").status_code == 400


def submit_and_wait(client, name, raw):
    response = client.post("/api/v1/documents", params={"name": name}, content=raw,
                           headers={**ACTION, "Content-Type": "application/octet-stream"})
    assert response.status_code == 202, response.text
    job_id = response.json()["job_id"]
    deadline = monotonic() + 30
    while monotonic() < deadline:
        result = client.get(f"/api/v1/ingestion/{job_id}").json()
        if result["status"] in {"indexed", "failed"}:
            return result
        sleep(.1)
    pytest.fail("Ingestion status did not finish")


@pytest.mark.oracle
def test_uploaded_lookup_and_privacy():
    if os.getenv("RUN_LIBRARY_TESTS") != "1":
        pytest.skip("Set RUN_LIBRARY_TESTS=1 after authorizing the public fixture writes")
    with TestClient(app, base_url="http://localhost") as client:
        fixtures = [
            ("Restore checkpoint.pdf", fixture_pdf()),
            ("Query troubleshooting.txt", b"A query execution plan lists scans, joins, filters and sort operations."),
            ("Maintenance notes.md", b"# Maintenance\nPostgreSQL VACUUM removes dead row versions for reuse."),
        ]
        ids = []
        for name, raw in fixtures:
            job = submit_and_wait(client, name, raw)
            assert job["status"] == "indexed", job
            print(name, job["status"], job["duration_ms"], "duplicate", job["duplicate"])
            ids.append(job["document_id"])
        assert submit_and_wait(client, "Copy of checkpoint.pdf", fixtures[0][1])["duplicate"]
        docs = {doc["document_id"]: doc for doc in client.get("/api/v1/documents").json()}
        assert docs[ids[0]]["page_count"] == 2
        assert all(not docs[doc_id]["external_ok"] for doc_id in ids)
        body = {"query": "What does the RUNBOOK_VEGA checkpoint record?",
                "document_ids": [ids[0]], "document_type": "pdf", "top_k": 3}
        for strategy in ("semantic", "hybrid"):
            response = client.post("/api/v1/search", json={**body, "strategy": strategy})
            assert response.status_code == 200, response.text
            top = response.json()["results"][0]
            assert top["page_number"] == 2 and top["document_id"] == ids[0]
            print(strategy, "rank 1 page", top["page_number"], "latency_ms", response.json()["latency_ms"])
        cases = [
            (body["query"], ids[0], 2),
            ("Which evidence shows the operations in a query execution plan?", ids[1], None),
            ("How does PostgreSQL reclaim space from dead row versions?", ids[2], None),
        ]
        for strategy in ("semantic", "hybrid"):
            ranks = []
            for query, expected_id, page in cases:
                data = client.post("/api/v1/search", json={
                    "query": query, "document_ids": ids, "strategy": strategy, "top_k": 3,
                }).json()
                rank = next((i for i, hit in enumerate(data["results"], 1)
                             if (hit["document_id"], hit["page_number"]) == (expected_id, page)), 0)
                ranks.append(rank)
            print("comparison", strategy, "ranks", ranks,
                  "recall_at_3", sum(bool(r) for r in ranks) / len(ranks),
                  "mrr_at_3", sum(1 / r for r in ranks if r) / len(ranks))
            assert all(ranks)
        filtered = client.post("/api/v1/search", json={**body, "document_ids": [ids[1]]})
        assert filtered.json()["results"] == []
        response = client.post("/api/v1/answer", json={**body, "public_question": True})
        assert response.json()["reason"] == "no_eligible_documents"
        assert app.state.next_generation_at == 0
        path = f"/api/v1/documents/{ids[0]}/eligibility"
        assert client.patch(path, json={"approved_public": True}, headers=ACTION).status_code == 200
        assert client.patch(path, json={"approved_public": False}, headers=ACTION).status_code == 200
        assert not {doc["document_id"]: doc for doc in client.get("/api/v1/documents").json()}[ids[0]]["external_ok"]
