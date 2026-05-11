"""API tests for optional KVTC V7 endpoints."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


def test_existing_compress_still_works():
    resp = client.post("/compress", json={"text": "Wartungsauftrag: Routineinspektion abgeschlossen."})

    assert resp.status_code == 200
    data = resp.json()
    assert data["original_tokens"] > 0
    assert data["checksum"]


def test_compress_v7_returns_expected_fields():
    resp = client.post(
        "/compress/v7",
        json={"text": "2026-05-11T08:02:00 ERROR code=P0300 module=engine value=91"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert set(data) == {
        "original_tokens",
        "compressed_tokens",
        "token_reduction_pct",
        "frame",
        "checksum",
        "latency_ms",
    }
    frame = json.loads(data["frame"])
    assert frame["payload_policy"] == "no-raw-lines"
    assert "severity_counts" in frame


def test_benchmark_v7_returns_cases():
    resp = client.get("/benchmark/v7")

    assert resp.status_code == 200
    data = resp.json()
    assert data["data_policy"] == "synthetic-only"
    assert data["total_cases"] >= 1
    assert data["cases"]
    assert "v7_frame_type" in data["cases"][0]


def test_benchmark_compare_returns_industrial_and_v7_metrics():
    resp = client.get("/benchmark/compare")

    assert resp.status_code == 200
    data = resp.json()
    assert data["data_policy"] == "synthetic-only"
    assert data["cases"]
    first = data["cases"][0]
    assert "industrial_original_tokens" in first
    assert "industrial_compressed_tokens" in first
    assert "industrial_reduction_pct" in first
    assert "v7_original_tokens" in first
    assert "v7_compressed_tokens" in first
    assert "v7_reduction_pct" in first
    assert "delta_reduction_pct" in first
    assert first["decision"] in {"pass", "warn", "fail"}


def test_benchmark_compare_includes_v7_diagnostic_metadata():
    resp = client.get("/benchmark/compare")

    assert resp.status_code == 200
    diagnostic = next(case for case in resp.json()["cases"] if case["label"] == "Synthetic diagnostic log")
    assert diagnostic["v7_event_count"] >= 3
    assert diagnostic["v7_severity_counts"]["ERROR"] == 1
    assert diagnostic["v7_severity_counts"]["WARN"] == 1
