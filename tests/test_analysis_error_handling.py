"""Tests for AnalysisAgent error paths."""

import sys
from unittest.mock import MagicMock

# Local mock for nh3 to allow tests to run in environments where it is missing
# We do this here instead of conftest.py to avoid global side effects if possible,
# though since src.agents.intake_agent is often imported at module level in other tests,
# it might still be needed. For this specific test file, we ensure it's mocked.
if "nh3" not in sys.modules:
    mock_nh3 = MagicMock()
    mock_nh3.clean.side_effect = lambda x: x
    sys.modules["nh3"] = mock_nh3

import pytest
from src.agents.analysis_agent import AnalysisAgent, AnalysisConfig, ModelBackend
from src.models.schemas import ProcessPriority, EingabeDokument
from src.core.kvtc import KVTCResult
from src.agents.triage_agent import TriageResult

def test_parse_output_no_json_block():
    """Test _parse_output when no JSON block is found in the raw output."""
    agent = AnalysisAgent()
    raw_output = "This is a plain text response without any JSON."
    fallback = ProcessPriority.P2_DRINGEND

    result = agent._parse_output(raw_output, fallback)

    assert result["zusammenfassung"] == raw_output[:300]
    assert result["massnahmen"] == []
    assert result["erkannte_fehlercodes"] == []
    assert result["konfidenz"] == 0.3
    assert result["prioritaet"] == fallback

def test_parse_output_invalid_json():
    """Test _parse_output when a JSON-like block is found but it's invalid JSON."""
    agent = AnalysisAgent()
    # Matches regex {.*} but is invalid JSON (unquoted keys, single quotes)
    raw_output = "The result is: { invalid: 'json', missing_quotes: 123 }"
    fallback = ProcessPriority.P1_KRITISCH

    result = agent._parse_output(raw_output, fallback)

    assert result["zusammenfassung"] == raw_output[:300]
    assert result["massnahmen"] == []
    assert result["erkannte_fehlercodes"] == []
    assert result["konfidenz"] == 0.2
    assert result["prioritaet"] == fallback

def test_analyze_with_invalid_json_infer(monkeypatch):
    """Test the full analyze method when the inference returns invalid JSON."""
    agent = AnalysisAgent(AnalysisConfig(backend=ModelBackend.MOCK))

    # Mock _infer to return invalid JSON
    # Must contain both { and } to be considered a JSON block by the greedy regex
    invalid_raw = "Incomplete response: { \"zusammenfassung\": \"incomplete\" }"
    # Make it invalid JSON by removing a colon
    invalid_raw = invalid_raw.replace("\":", "\"")

    monkeypatch.setattr(agent, "_infer", lambda prompt: invalid_raw)

    doc = EingabeDokument(raw_text="test data")
    kvtc = KVTCResult(
        original_tokens=100,
        compressed_tokens=50,
        compression_ratio=0.5,
        zones={},
        frame="compressed_data",
        checksum="test_sum",
        latency_ms=1.5
    )
    triage = TriageResult(
        prioritaet=ProcessPriority.P3_ROUTINE,
        begruendung="test triage",
        ausgeloeste_regeln=[]
    )

    result = agent.analyze(doc, kvtc, triage)

    assert result.konfidenz == 0.2
    assert result.zusammenfassung == invalid_raw[:300]
    assert result.prioritaet == ProcessPriority.P3_ROUTINE
    assert result.rohausgabe == invalid_raw
