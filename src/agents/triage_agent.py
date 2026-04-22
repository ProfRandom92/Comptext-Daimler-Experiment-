"""
TriageAgent – Prozesspriorität-Klassifizierung
Entspricht dem TriageAgent aus MedGemma-CompText (P1/P2/P3).

Klassifizierungsregeln (regelbasiert, deterministisch):
  P1 Kritisch  – Sicherheitsrelevant, Produktionsstopp, Fahrzeugausfall
  P2 Dringend  – Qualitätsproblem, Wartung überfällig, Teileengpass
  P3 Routine   – Planmäßige Wartung, Dokumentation, Kleinreparaturen

Analog zu ESC/AHA/SSC-Leitlinien aus Monorepo-X,
aber statt klinischer Leitlinien: Daimler Buses Prozessrichtlinien.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.models.schemas import DocumentType, EingabeDokument, ProcessPriority


# ---------------------------------------------------------------------------
# Kritikalitäts-Regeln
# ---------------------------------------------------------------------------

# P1: Sicherheitskritisch / sofortiger Handlungsbedarf
_P1_PATTERNS = [
    re.compile(r"\bBremsenausfall|Bremsversagen|Bremsanlage\s+defekt\b",        re.I),
    re.compile(r"\bLenkungsausfall|Lenkung\s+defekt\b",                         re.I),
    re.compile(r"\bFahrzeugbrand|Brand|Feuer\b",                                re.I),
    re.compile(r"\bProduktionsstopp|Bandstillstand|Linienstopp\b",              re.I),
    re.compile(r"\bSicherheitsrelevant|safety.critical|sicherheitskritisch\b",  re.I),
    re.compile(r"\bUnfall|Kollision|Personenschaden\b",                         re.I),
    re.compile(r"\bSperrung\b",                                                 re.I),  # QA-Sperrung
    re.compile(r"\bP0300|P0301|P0302|P0303|P0304\b"),                          # Mehrfachzündaussetzer
    re.compile(r"\bU0100|U0073\b"),                                             # CAN-Bus-Ausfall
    re.compile(r"\bAirbag\s+defekt|SRS\s+Fehler\b",                            re.I),
    re.compile(r"\bKühlmittelaustritt|Überhitzung\b",                          re.I),
]

# P2: Dringend, baldige Maßnahme erforderlich
_P2_PATTERNS = [
    re.compile(r"\bÜberfällig|überfällig|Fälligkeit\s+überschritten\b",        re.I),
    re.compile(r"\bQualitätsmangel|Nacharbeit\s+erforderlich\b",                re.I),
    re.compile(r"\bTeileengpass|Materialengpass|Fehlteile\b",                   re.I),
    re.compile(r"\bReifenverschleiß|Verschleiß\s+kritisch\b",                  re.I),
    re.compile(r"\bMotorwarnleuchte|MIL\s+an\b",                               re.I),
    re.compile(r"\bKupplungsverschleiß|Kupplungsschlupf\b",                    re.I),
    re.compile(r"\bGetriebefehler|Getriebeöl\s+alt\b",                        re.I),
    re.compile(r"\bP0171|P0172|P0420|P0440\b"),                                # Emissionen/Katalysator
    re.compile(r"\bRückruf|Recall\b",                                          re.I),
    re.compile(r"\b(Takt|Zykluszeit)\s+(überschritten|\+\d+%)\b",              re.I),
]

# Kilometerstand-basierte Eskalation
_KM_UEBERFAELLIG = re.compile(r"Kilometerstand\s*[:\s]+([\d.,]+)", re.I)
_SERVICE_FAELLIG  = re.compile(r"nächster\s+Service\s*[:\s]+([\d.,]+)\s*km", re.I)


@dataclass
class TriageResult:
    prioritaet: ProcessPriority
    begruendung: str
    ausgeloeste_regeln: list[str]
    eskalations_hinweis: str = ""


class TriageAgent:
    """
    Regelbasierte Prioritätsklassifizierung für Daimler Buses Prozesse.
    Deterministisch und nachvollziehbar – kein LLM-Overhead für diese Schicht.
    """

    def classify(self, dokument: EingabeDokument) -> TriageResult:
        text = dokument.raw_text
        ausgeloeste: list[str] = []

        # P1-Check
        for p in _P1_PATTERNS:
            match = p.search(text)
            if match:
                ausgeloeste.append(f"P1-Regel: '{match.group(0)}'")

        if ausgeloeste:
            return TriageResult(
                prioritaet=ProcessPriority.P1_KRITISCH,
                begruendung="Sicherheitskritisches Muster erkannt",
                ausgeloeste_regeln=ausgeloeste,
                eskalations_hinweis="Sofortige Eskalation an Werkstattleitung / Produktionsleiter",
            )

        # P2-Check
        for p in _P2_PATTERNS:
            match = p.search(text)
            if match:
                ausgeloeste.append(f"P2-Regel: '{match.group(0)}'")

        # Kilometerstand-Prüfung
        km_hinweis = self._check_km_faelligkeit(text)
        if km_hinweis:
            ausgeloeste.append(km_hinweis)

        # Dokumenttyp-basierte Basis-Priorität
        type_prio = self._type_based_priority(dokument.doc_type)

        if ausgeloeste:
            return TriageResult(
                prioritaet=ProcessPriority.P2_DRINGEND,
                begruendung="Dringendes Muster oder Fälligkeit erkannt",
                ausgeloeste_regeln=ausgeloeste,
                eskalations_hinweis="Einplanung innerhalb 24h empfohlen",
            )

        return TriageResult(
            prioritaet=type_prio,
            begruendung="Keine kritischen Muster – Routineverarbeitung",
            ausgeloeste_regeln=[],
            eskalations_hinweis="",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _check_km_faelligkeit(self, text: str) -> str | None:
        km_match      = _KM_UEBERFAELLIG.search(text)
        service_match = _SERVICE_FAELLIG.search(text)

        if km_match and service_match:
            km_aktuell  = int(km_match.group(1).replace(".", "").replace(",", ""))
            km_faellig  = int(service_match.group(1).replace(".", "").replace(",", ""))
            if km_aktuell > km_faellig:
                ueberzug = km_aktuell - km_faellig
                return f"Service überfällig um {ueberzug:,} km"
        return None

    def _type_based_priority(self, doc_type: DocumentType) -> ProcessPriority:
        mapping = {
            DocumentType.OBD_FEHLERCODE:     ProcessPriority.P2_DRINGEND,
            DocumentType.QA_PRUEFBERICHT:    ProcessPriority.P2_DRINGEND,
            DocumentType.WARTUNGSPROTOKOLL:  ProcessPriority.P3_ROUTINE,
            DocumentType.PRODUKTIONSAUFTRAG: ProcessPriority.P3_ROUTINE,
            DocumentType.LIEFERSCHEIN:       ProcessPriority.P3_ROUTINE,
            DocumentType.ARBEITSPLAN:        ProcessPriority.P3_ROUTINE,
            DocumentType.FREITEXT:           ProcessPriority.P3_ROUTINE,
        }
        return mapping.get(doc_type, ProcessPriority.P3_ROUTINE)
