"""
Daimler Buses – Datenmodelle für die Prozessautomatisierung.

Abdeckung:
  - Fahrzeugdaten & FIN
  - Wartungsprotokoll (Werkstattauftrag)
  - OBD-Fehlercode
  - QA-Prüfbericht
  - Produktionsauftrag
  - Analyseergebnis (LLM-Output)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ProcessPriority(str, Enum):
    P1_KRITISCH = "P1_KRITISCH"    # Sicherheitsrelevant / Produktionsstopp
    P2_DRINGEND = "P2_DRINGEND"    # Qualitätsproblem / Wartung überfällig
    P3_ROUTINE  = "P3_ROUTINE"     # Planmäßige Wartung / Dokumentation


class DocumentType(str, Enum):
    WARTUNGSPROTOKOLL  = "WARTUNGSPROTOKOLL"
    OBD_FEHLERCODE     = "OBD_FEHLERCODE"
    QA_PRUEFBERICHT    = "QA_PRUEFBERICHT"
    PRODUKTIONSAUFTRAG = "PRODUKTIONSAUFTRAG"
    LIEFERSCHEIN       = "LIEFERSCHEIN"
    ARBEITSPLAN        = "ARBEITSPLAN"
    FREITEXT           = "FREITEXT"


class FahrzeugStatus(str, Enum):
    IN_BETRIEB         = "IN_BETRIEB"
    IN_WERKSTATT       = "IN_WERKSTATT"
    AUSSER_BETRIEB     = "AUSSER_BETRIEB"
    NEUPRODUKTION      = "NEUPRODUKTION"


# ---------------------------------------------------------------------------
# Fahrzeug
# ---------------------------------------------------------------------------

@dataclass
class Fahrzeugdaten:
    fin: str                          # Fahrzeug-Identifikationsnummer (VIN)
    modell: str                       # z. B. "Tourismo M", "Citaro G"
    baujahr: int
    kilometerstand: int
    status: FahrzeugStatus = FahrzeugStatus.IN_BETRIEB
    letzter_service: datetime | None = None
    naechster_service_km: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def kurzform(self) -> str:
        return f"{self.modell} ({self.baujahr}) | {self.kilometerstand:,} km"


# ---------------------------------------------------------------------------
# OBD-Fehlercode
# ---------------------------------------------------------------------------

@dataclass
class OBDFehlercode:
    code: str           # z. B. "P0300", "U0100"
    beschreibung: str
    schweregrad: ProcessPriority
    steuergeraet: str   # z. B. "Motor", "Getriebe", "Bremse"
    ersterfasst: datetime = field(default_factory=datetime.now)
    behoben: bool = False


# ---------------------------------------------------------------------------
# Wartungsprotokoll
# ---------------------------------------------------------------------------

@dataclass
class Wartungsprotokoll:
    auftragsnummer: str
    fahrzeug: Fahrzeugdaten
    fehler_codes: list[OBDFehlercode] = field(default_factory=list)
    arbeitsschritte: list[str] = field(default_factory=list)
    verwendete_teile: list[str] = field(default_factory=list)
    techniker_kuerzel: str = ""        # Anonymisiert via IntakeAgent
    beginn: datetime = field(default_factory=datetime.now)
    abschluss: datetime | None = None
    prioritaet: ProcessPriority = ProcessPriority.P3_ROUTINE
    notizen: str = ""

    @property
    def ist_abgeschlossen(self) -> bool:
        return self.abschluss is not None


# ---------------------------------------------------------------------------
# QA-Prüfbericht
# ---------------------------------------------------------------------------

@dataclass
class QAPruefbericht:
    pruef_id: str
    fahrzeug_fin: str
    pruefpunkte: list[dict[str, Any]] = field(default_factory=list)
    beanstandungen: list[str] = field(default_factory=list)
    gesamt_bewertung: str = "OK"       # "OK" | "NACHARBEIT" | "SPERRUNG"
    pruefer_kuerzel: str = ""
    pruef_datum: datetime = field(default_factory=datetime.now)
    prioritaet: ProcessPriority = ProcessPriority.P3_ROUTINE


# ---------------------------------------------------------------------------
# Produktionsauftrag
# ---------------------------------------------------------------------------

@dataclass
class Produktionsauftrag:
    auftrag_id: str
    fahrzeug_typ: str
    arbeitsstation: str
    soll_takt_minuten: float
    ist_takt_minuten: float | None = None
    status: str = "OFFEN"              # "OFFEN" | "IN_ARBEIT" | "ABGESCHLOSSEN" | "GESPERRT"
    abweichungen: list[str] = field(default_factory=list)
    prioritaet: ProcessPriority = ProcessPriority.P3_ROUTINE
    erstellt: datetime = field(default_factory=datetime.now)


# ---------------------------------------------------------------------------
# Generisches Eingabedokument (für den IntakeAgent)
# ---------------------------------------------------------------------------

@dataclass
class EingabeDokument:
    raw_text: str
    doc_type: DocumentType = DocumentType.FREITEXT
    quelle: str = ""
    metadaten: dict[str, Any] = field(default_factory=dict)
    eingabe_zeitstempel: datetime = field(default_factory=datetime.now)


# ---------------------------------------------------------------------------
# Analyseergebnis (Output des AnalysisAgent)
# ---------------------------------------------------------------------------

@dataclass
class Analyseergebnis:
    eingabe_checksum: str
    prioritaet: ProcessPriority
    zusammenfassung: str
    massnahmen: list[str] = field(default_factory=list)
    erkannte_fehlercodes: list[str] = field(default_factory=list)
    konfidenz: float = 0.0             # 0.0 – 1.0
    modell_id: str = ""
    latenz_ms: float = 0.0
    rohausgabe: str = ""
    token_original: int = 0
    token_komprimiert: int = 0

    @property
    def token_einsparung_pct(self) -> float:
        if self.token_original == 0:
            return 0.0
        return round((1 - self.token_komprimiert / self.token_original) * 100, 2)
