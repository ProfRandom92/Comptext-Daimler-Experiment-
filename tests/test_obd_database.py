"""Tests für OBD-Datenbank und TriageAgent-Integration."""

from __future__ import annotations

import pytest

from src.core.obd_database import OBD_DATABASE, find_codes_in_text, lookup, lookup_severity
from src.models.schemas import ProcessPriority


def test_known_p1_code_lookup():
    info = lookup("P0300")
    assert info is not None
    assert info.schweregrad == ProcessPriority.P1_KRITISCH
    assert info.code == "P0300"


def test_known_p2_code_lookup():
    info = lookup("P0171")
    assert info is not None
    assert info.schweregrad == ProcessPriority.P2_DRINGEND


def test_known_p3_code_lookup():
    info = lookup("U0184")
    assert info is not None
    assert info.schweregrad == ProcessPriority.P3_ROUTINE


def test_unknown_code_returns_none():
    assert lookup("P9999") is None


def test_lookup_case_insensitive():
    assert lookup("p0300") == lookup("P0300")


def test_lookup_severity_p1():
    assert lookup_severity("P0300") == ProcessPriority.P1_KRITISCH


def test_lookup_severity_unknown_returns_none():
    assert lookup_severity("P9999") is None


def test_find_codes_in_text_detects_multiple():
    text = "Fehlercode P0300 und U0100 erkannt, außerdem P0171."
    hits = find_codes_in_text(text)
    codes = [h.code for h in hits]
    assert "P0300" in codes
    assert "U0100" in codes
    assert "P0171" in codes


def test_find_codes_deduplicates():
    text = "P0300 tritt auf. Erneut P0300 bestätigt."
    hits = find_codes_in_text(text)
    assert len([h for h in hits if h.code == "P0300"]) == 1


def test_find_codes_ignores_unknown():
    text = "Fehlercode P9999 und Z1234 unbekannt."
    hits = find_codes_in_text(text)
    assert hits == []


def test_database_minimum_coverage():
    assert len(OBD_DATABASE) >= 60


def test_triage_agent_uses_obd_database_for_p1():
    from src.agents.triage_agent import TriageAgent
    from src.models.schemas import EingabeDokument

    # P0520 (Öldrucksensor) ist in der DB als P1, aber NICHT in den bestehenden triage Regex-Patterns
    triage = TriageAgent()
    doc = EingabeDokument(raw_text="Fehler P0520 – Öldrucksensor Signalkreis außer Bereich")
    result = triage.classify(doc)
    assert result.prioritaet == ProcessPriority.P1_KRITISCH


def test_triage_agent_uses_obd_database_for_p2():
    from src.agents.triage_agent import TriageAgent
    from src.models.schemas import EingabeDokument

    # P0700 (Getriebesteuerung) ist in der DB als P2
    triage = TriageAgent()
    doc = EingabeDokument(raw_text="Getriebefehler P0700 erkannt bei letzter Prüfung.")
    result = triage.classify(doc)
    assert result.prioritaet == ProcessPriority.P2_DRINGEND


def test_triage_existing_p1_regex_still_works():
    from src.agents.triage_agent import TriageAgent
    from src.models.schemas import EingabeDokument

    triage = TriageAgent()
    doc = EingabeDokument(raw_text="Bremsversagen am Vorderrad – sofortige Sperrung eingeleitet")
    result = triage.classify(doc)
    assert result.prioritaet == ProcessPriority.P1_KRITISCH
