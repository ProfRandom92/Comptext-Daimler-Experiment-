"""Tests für IntakeAgent – Bereinigung und Dokumenttyp-Erkennung."""

import pytest

from src.agents.intake_agent import IntakeAgent
from src.models.schemas import DocumentType


@pytest.fixture
def agent():
    return IntakeAgent()


def test_fin_masking(agent):
    text = "FIN: WDB906232N3123456 – Fahrzeug in Werkstatt"
    result = agent.process(text)
    assert "WDB906232N3123456" not in result.dokument.raw_text
    assert "FIN_***" in result.dokument.raw_text
    assert any("FIN" in b for b in result.bereinigungen)


def test_email_removal(agent):
    text = "Kontakt: max.mustermann@daimler.com für Rückfragen"
    result = agent.process(text)
    assert "@daimler.com" not in result.dokument.raw_text
    assert "[EMAIL_ENTFERNT]" in result.dokument.raw_text
    assert any("E-Mail" in b for b in result.bereinigungen)


def test_kunden_zeile_removal(agent):
    text = "Kunde: Mustermann GmbH\nFahrzeug: Citaro"
    result = agent.process(text)
    assert "Mustermann GmbH" not in result.dokument.raw_text
    assert "[KUNDE_ENTFERNT]" in result.dokument.raw_text


def test_detect_wartungsprotokoll(agent):
    text = "Wartungsauftrag Nr. 123\nInspektion durchgeführt"
    result = agent.process(text)
    assert result.dokument.doc_type == DocumentType.WARTUNGSPROTOKOLL


def test_detect_obd(agent):
    text = "Fehler im Steuergerät: P0300 Zündaussetzer erkannt"
    result = agent.process(text)
    assert result.dokument.doc_type == DocumentType.OBD_FEHLERCODE


def test_detect_qa(agent):
    text = "QA Prüfbericht – Beanstandung: Lackfehler an Karosserie"
    result = agent.process(text)
    assert result.dokument.doc_type == DocumentType.QA_PRUEFBERICHT


def test_detect_freitext(agent):
    text = "Allgemeine Notiz ohne erkennbaren Dokumenttyp."
    result = agent.process(text)
    assert result.dokument.doc_type == DocumentType.FREITEXT


def test_kvtc_result_present(agent):
    text = "\n".join([f"Eintrag {i}: Kilometerstand {i*1000}" for i in range(20)])
    result = agent.process(text)
    assert result.kvtc.original_tokens > 0
    assert result.kvtc.checksum


def test_latency_tracked(agent):
    result = agent.process("Testdokument")
    assert result.latenz_ms >= 0


def test_no_crash_on_empty(agent):
    result = agent.process("")
    assert result.dokument is not None
