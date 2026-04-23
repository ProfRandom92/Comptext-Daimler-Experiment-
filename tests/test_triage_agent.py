"""Tests für TriageAgent – P1/P2/P3 Klassifizierung."""

import pytest

from src.agents.triage_agent import TriageAgent
from src.models.schemas import DocumentType, EingabeDokument, ProcessPriority


@pytest.fixture
def triage():
    return TriageAgent()


def _doc(text: str, doc_type=DocumentType.FREITEXT) -> EingabeDokument:
    return EingabeDokument(raw_text=text, doc_type=doc_type)


def test_bremsenausfall_ist_p1(triage):
    doc = _doc("Fehler: Bremsenausfall an Achse 2")
    result = triage.classify(doc)
    assert result.prioritaet == ProcessPriority.P1_KRITISCH


def test_produktionsstopp_ist_p1(triage):
    doc = _doc("Meldung: Produktionsstopp an Linie 3 wegen Materialfehler")
    result = triage.classify(doc)
    assert result.prioritaet == ProcessPriority.P1_KRITISCH


def test_sperrung_ist_p1(triage):
    doc = _doc("Gesamt-Bewertung: SPERRUNG – kritischer Mangel", DocumentType.QA_PRUEFBERICHT)
    result = triage.classify(doc)
    assert result.prioritaet == ProcessPriority.P1_KRITISCH


def test_obd_p0300_ist_p1(triage):
    doc = _doc("Fehlercode P0300 erkannt – Zündaussetzer Zylinder 1", DocumentType.OBD_FEHLERCODE)
    result = triage.classify(doc)
    assert result.prioritaet == ProcessPriority.P1_KRITISCH


def test_ueberfaelliger_service_ist_p2(triage):
    doc = _doc("Kilometerstand: 165.000\nnächster Service: 160.000 km")
    result = triage.classify(doc)
    assert result.prioritaet == ProcessPriority.P2_DRINGEND


def test_teileengpass_ist_p2(triage):
    doc = _doc("Fehlteile: Sitzgestell PN 9876543 – Teileengpass")
    result = triage.classify(doc)
    assert result.prioritaet == ProcessPriority.P2_DRINGEND


def test_rueckruf_ist_p2(triage):
    doc = _doc("Rückruf Aktion 2024-DB-001 betrifft Fahrzeuge Bj. 2020-2022")
    result = triage.classify(doc)
    assert result.prioritaet == ProcessPriority.P2_DRINGEND


def test_routine_wartung_ist_p3(triage):
    doc = _doc("Routineinspektion durchgeführt, alle Werte im Normbereich.", DocumentType.WARTUNGSPROTOKOLL)
    result = triage.classify(doc)
    assert result.prioritaet == ProcessPriority.P3_ROUTINE


def test_p1_hat_eskalationshinweis(triage):
    doc = _doc("Fahrzeugbrand gemeldet!")
    result = triage.classify(doc)
    assert result.eskalations_hinweis != ""


def test_p1_hat_ausgeloeste_regeln(triage):
    doc = _doc("Lenkungsausfall bei 90 km/h")
    result = triage.classify(doc)
    assert len(result.ausgeloeste_regeln) > 0
