"""Tests für AnalysisAgent – Mock-Modus."""

import pytest
from src.agents.analysis_agent import AnalysisAgent, AnalysisConfig, ModelBackend
from src.agents.intake_agent import IntakeAgent
from src.agents.triage_agent import TriageAgent
from src.models.schemas import DocumentType, EingabeDokument, ProcessPriority


@pytest.fixture
def pipeline():
    intake   = IntakeAgent()
    triage   = TriageAgent()
    analysis = AnalysisAgent(AnalysisConfig(backend=ModelBackend.MOCK))
    return intake, triage, analysis


def test_full_pipeline_mock(pipeline):
    intake, triage, analysis = pipeline
    text = (
        "Wartungsauftrag WA-2024-001\n"
        "Fahrzeug: Tourismo M, Bj. 2019\n"
        "Kilometerstand: 145000\n"
        "Fehlercode: P0171 – Gemisch zu mager\n"
        "Maßnahme: Lambdasonde prüfen"
    )
    ir = intake.process(text)
    tr = triage.classify(ir.dokument)
    ar = analysis.analyze(ir.dokument, ir.kvtc, tr)

    assert ar.eingabe_checksum == ir.kvtc.checksum
    assert ar.prioritaet in ProcessPriority.__members__.values()
    assert ar.zusammenfassung
    assert ar.latenz_ms >= 0
    assert 0.0 <= ar.konfidenz <= 1.0


def test_token_einsparung_property(pipeline):
    intake, triage, analysis = pipeline
    text = "\n".join([f"Historischer Eintrag {i}" for i in range(50)])
    ir = intake.process(text)
    tr = triage.classify(ir.dokument)
    ar = analysis.analyze(ir.dokument, ir.kvtc, tr)

    assert ar.token_original > 0
    assert ar.token_einsparung_pct >= 0.0


def test_p1_priority_propagation(pipeline):
    intake, triage, analysis = pipeline
    text = "Kritischer Fehler: Bremsenausfall – Fahrzeug sofort sperren"
    ir = intake.process(text)
    tr = triage.classify(ir.dokument)
    assert tr.prioritaet == ProcessPriority.P1_KRITISCH
    ar = analysis.analyze(ir.dokument, ir.kvtc, tr)
    assert ar.prioritaet == ProcessPriority.P1_KRITISCH


def test_mock_returns_valid_json_structure(pipeline):
    intake, triage, analysis = pipeline
    ir = intake.process("Routineinspektion abgeschlossen.")
    tr = triage.classify(ir.dokument)
    ar = analysis.analyze(ir.dokument, ir.kvtc, tr)
    assert isinstance(ar.massnahmen, list)
    assert isinstance(ar.erkannte_fehlercodes, list)
