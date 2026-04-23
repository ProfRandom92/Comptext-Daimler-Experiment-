"""Tests für AnalysisResultCache (LRU, thread-safe)."""

from __future__ import annotations

import pytest

from src.core.result_cache import AnalysisResultCache
from src.models.schemas import Analyseergebnis, ProcessPriority


def _make_result(checksum: str) -> Analyseergebnis:
    return Analyseergebnis(
        eingabe_checksum=checksum,
        prioritaet=ProcessPriority.P3_ROUTINE,
        zusammenfassung="Test",
        massnahmen=[],
        erkannte_fehlercodes=[],
        konfidenz=0.5,
        modell_id="mock",
        latenz_ms=1.0,
        rohausgabe="{}",
        token_original=100,
        token_komprimiert=10,
    )


def test_cache_miss_returns_none():
    cache = AnalysisResultCache()
    assert cache.get("nonexistent") is None


def test_cache_hit_after_put():
    cache = AnalysisResultCache()
    r = _make_result("abc123")
    cache.put("abc123", r)
    assert cache.get("abc123") is r


def test_cache_stats_tracking():
    cache = AnalysisResultCache()
    cache.get("x")               # miss
    cache.put("x", _make_result("x"))
    cache.get("x")               # hit
    assert cache.stats.hits == 1
    assert cache.stats.misses == 1


def test_cache_hit_rate():
    cache = AnalysisResultCache()
    cache.put("a", _make_result("a"))
    cache.get("a")               # hit
    cache.get("b")               # miss
    assert cache.stats.hit_rate == pytest.approx(0.5)


def test_lru_eviction():
    cache = AnalysisResultCache(max_size=2)
    cache.put("a", _make_result("a"))
    cache.put("b", _make_result("b"))
    cache.put("c", _make_result("c"))   # evicts "a" (LRU)
    assert cache.get("a") is None
    assert cache.get("b") is not None
    assert cache.get("c") is not None
    assert cache.stats.evictions == 1


def test_lru_access_updates_order():
    cache = AnalysisResultCache(max_size=2)
    cache.put("a", _make_result("a"))
    cache.put("b", _make_result("b"))
    cache.get("a")               # access "a" → "b" becomes LRU
    cache.put("c", _make_result("c"))  # evicts "b", not "a"
    assert cache.get("a") is not None
    assert cache.get("b") is None


def test_invalidate():
    cache = AnalysisResultCache()
    cache.put("x", _make_result("x"))
    assert cache.invalidate("x") is True
    assert cache.get("x") is None
    assert cache.invalidate("x") is False  # already gone


def test_cache_prevents_duplicate_llm_call():
    """AnalysisAgent uses cache to return same object on second call."""
    from src.agents.analysis_agent import AnalysisAgent, AnalysisConfig, ModelBackend
    from src.agents.intake_agent import IntakeAgent
    from src.agents.triage_agent import TriageAgent

    cache = AnalysisResultCache()
    agent = AnalysisAgent(AnalysisConfig(backend=ModelBackend.MOCK), cache=cache)
    intake = IntakeAgent()
    triage = TriageAgent()

    text = "Wartungsprotokoll: Routineinspektion abgeschlossen. km: 50000"
    ir = intake.process(text)
    tr = triage.classify(ir.dokument)

    r1 = agent.analyze(ir.dokument, ir.kvtc, tr)
    r2 = agent.analyze(ir.dokument, ir.kvtc, tr)   # cache hit

    assert r1 is r2
    assert cache.stats.hits == 1
    assert cache.stats.misses == 1


def test_cache_none_disables_caching():
    """AnalysisAgent with cache=None falls through to LLM every time."""
    from src.agents.analysis_agent import AnalysisAgent, AnalysisConfig, ModelBackend
    from src.agents.intake_agent import IntakeAgent
    from src.agents.triage_agent import TriageAgent

    agent = AnalysisAgent(AnalysisConfig(backend=ModelBackend.MOCK), cache=None)
    ir = IntakeAgent().process("Test-Dokument km: 10000")
    tr = TriageAgent().classify(ir.dokument)
    result = agent.analyze(ir.dokument, ir.kvtc, tr)
    assert result is not None
