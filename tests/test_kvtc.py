"""Tests für IndustrialKVTCStrategy."""

import pytest

from src.core.kvtc import IndustrialKVTCStrategy, run_benchmark


@pytest.fixture
def strategy():
    return IndustrialKVTCStrategy(header_lines=3, window_lines=3)


def test_compress_returns_result(strategy):
    text = "\n".join([f"Zeile {i}: Kilometerstand: {i * 1000}" for i in range(20)])
    result = strategy.compress(text)
    assert result.original_tokens > 0
    assert result.compressed_tokens > 0
    assert 0.0 <= result.compression_ratio <= 1.0
    assert result.checksum
    assert result.latency_ms >= 0


def test_token_reduction(strategy):
    long_text = "\n".join([f"Historischer Eintrag {i}: keine relevanten Informationen hier." for i in range(100)])
    result = strategy.compress(long_text)
    assert result.token_reduction_pct > 0


def test_frame_contains_layers(strategy):
    text = (
        "Wartungsauftrag 2024-001\n"
        "Kilometerstand: 125000\n"
        "Fehlercode: P0300\n"
        "SAP-Auftrag: 1234567\n"
        "Datum: 15.08.2024"
    )
    result = strategy.compress(text)
    assert "|" in result.frame or result.frame  # frame ist nicht leer


def test_obd_code_extraction(strategy):
    text = "Fehler erkannt: P0300 Zündaussetzer, U0100 CAN-Bus Fehler"
    result = strategy.compress(text)
    assert "P0300" in result.frame or "P0300" in str(result.zones)


def test_short_text_no_crash(strategy):
    result = strategy.compress("Kurztext")
    assert result.original_tokens >= 1


def test_empty_middle_zone():
    strat = IndustrialKVTCStrategy(header_lines=100, window_lines=100)
    text = "\n".join([f"Zeile {i}" for i in range(10)])
    result = strat.compress(text)
    assert result.zones["middle"] == ""


def test_benchmark():
    cases = [
        {"label": "Test 1", "text": "Kilometerstand: 50000\nFehlercode: P0171"},
        {"label": "Test 2", "text": "\n".join([f"Eintrag {i}" for i in range(50)])},
    ]
    report = run_benchmark(cases)
    assert report["total_cases"] == 2
    assert "avg_token_reduction_pct" in report
    assert "avg_latency_ms" in report


def test_compress_structured(strategy):
    record = {
        "auftrag": "WA-2024-001",
        "km": 125000,
        "fehler": "P0300",
        "modell": "Tourismo",
    }
    result = strategy.compress_structured(record)
    assert result.original_tokens > 0
    assert result.metadata.get("source") == "structured_record"
