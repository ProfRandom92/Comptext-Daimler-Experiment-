"""Tests für POST /batch/analyze und /health-Erweiterungen."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


def test_batch_single_document():
    resp = client.post("/batch/analyze", json={
        "documents": [{"text": "Wartungsauftrag: Routineinspektion abgeschlossen.", "quelle": "Test"}]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["succeeded"] == 1
    assert data["failed"] == 0
    assert data["results"][0]["index"] == 0
    assert data["results"][0]["success"] is True


def test_batch_multiple_documents():
    docs = [
        {"text": f"Dokument {i}: Kilometerstand {i * 10000}", "quelle": "Test"}
        for i in range(3)
    ]
    resp = client.post("/batch/analyze", json={"documents": docs})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert data["succeeded"] == 3
    assert data["failed"] == 0


def test_batch_max_10_enforced():
    docs = [{"text": f"Dokument {i}", "quelle": "T"} for i in range(11)]
    resp = client.post("/batch/analyze", json={"documents": docs})
    assert resp.status_code == 422


def test_batch_empty_list_rejected():
    resp = client.post("/batch/analyze", json={"documents": []})
    assert resp.status_code == 422


def test_batch_preserves_index_order():
    docs = [{"text": f"Dok {i} – Routinearbeit", "quelle": "Test"} for i in range(5)]
    resp = client.post("/batch/analyze", json={"documents": docs})
    data = resp.json()
    for i, item in enumerate(data["results"]):
        assert item["index"] == i


def test_batch_result_has_required_fields():
    resp = client.post("/batch/analyze", json={
        "documents": [{"text": "Fehler P0300 erkannt – Zündaussetzer", "quelle": "SAP"}]
    })
    assert resp.status_code == 200
    result = resp.json()["results"][0]["result"]
    assert "prioritaet" in result
    assert "zusammenfassung" in result
    assert "token_original" in result
    assert "konfidenz" in result


def test_health_includes_cache_stats():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "cache_size" in data
    assert "cache_hit_rate" in data
    assert data["status"] == "ok"
