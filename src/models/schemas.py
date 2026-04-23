"""
Daimler Buses – Datenmodelle für die Prozessautomatisierung.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProcessPriority(str, Enum):
    P1_KRITISCH = "P1_KRITISCH"  # Sicherheitsrelevant / Produktionsstopp
    P2_DRINGEND = "P2_DRINGEND"  # Qualitätsproblem / Wartung überfällig
    P3_ROUTINE  = "P3_ROUTINE"   # Planmäßige Wartung / Dokumentation


class DocumentType(str, Enum):
    WARTUNGSPROTOKOLL  = "WARTUNGSPROTOKOLL"
    OBD_FEHLERCODE     = "OBD_FEHLERCODE"
    QA_PRUEFBERICHT    = "QA_PRUEFBERICHT"
    PRODUKTIONSAUFTRAG = "PRODUKTIONSAUFTRAG"
    LIEFERSCHEIN       = "LIEFERSCHEIN"
    ARBEITSPLAN        = "ARBEITSPLAN"
    FREITEXT           = "FREITEXT"


class FahrzeugStatus(str, Enum):
    IN_BETRIEB     = "IN_BETRIEB"
    IN_WERKSTATT   = "IN_WERKSTATT"
    AUSSER_BETRIEB = "AUSSER_BETRIEB"
    NEUPRODUKTION  = "NEUPRODUKTION"


class QABewertung(str, Enum):
    OK         = "OK"
    NACHARBEIT = "NACHARBEIT"
    SPERRUNG   = "SPERRUNG"


class ProduktionsStatus(str, Enum):
    OFFEN         = "OFFEN"
    IN_ARBEIT     = "IN_ARBEIT"
    ABGESCHLOSSEN = "ABGESCHLOSSEN"
    GESPERRT      = "GESPERRT"


@dataclass
class Fahrzeugdaten:
    fin: str
    modell: str
    baujahr: int
    kilometerstand: int
    status: FahrzeugStatus = FahrzeugStatus.IN_BETRIEB
    letzter_service: datetime | None = None
    naechster_service_km: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not (1886 <= self.baujahr <= datetime.now(timezone.utc).year + 1):
            raise ValueError(f"baujahr={self.baujahr} außerhalb des gültigen Bereichs")
        if self.kilometerstand < 0:
            raise ValueError(f"kilometerstand={self.kilometerstand} darf nicht negativ sein")

    def kurzform(self) -> str:
        return f"{self.modell} ({self.baujahr}) | {self.kilometerstand:,} km"


@dataclass
class OBDFehlercode:
    code: str
    beschreibung: str
    schweregrad: ProcessPriority
    steuergeraet: str
    ersterfasst: datetime = field(default_factory=_utcnow)
    behoben: bool = False


@dataclass
class Wartungsprotokoll:
    auftragsnummer: str
    fahrzeug: Fahrzeugdaten
    fehler_codes: list[OBDFehlercode] = field(default_factory=list)
    arbeitsschritte: list[str] = field(default_factory=list)
    verwendete_teile: list[str] = field(default_factory=list)
    techniker_kuerzel: str = ""  # anonymised by IntakeAgent before storage
    beginn: datetime = field(default_factory=_utcnow)
    abschluss: datetime | None = None
    prioritaet: ProcessPriority = ProcessPriority.P3_ROUTINE
    notizen: str = ""

    @property
    def ist_abgeschlossen(self) -> bool:
        return self.abschluss is not None


@dataclass
class QAPruefbericht:
    pruef_id: str
    fahrzeug_fin: str
    pruefpunkte: list[dict[str, Any]] = field(default_factory=list)
    beanstandungen: list[str] = field(default_factory=list)
    gesamt_bewertung: QABewertung = QABewertung.OK
    pruefer_kuerzel: str = ""
    pruef_datum: datetime = field(default_factory=_utcnow)
    prioritaet: ProcessPriority = ProcessPriority.P3_ROUTINE


@dataclass
class Produktionsauftrag:
    auftrag_id: str
    fahrzeug_typ: str
    arbeitsstation: str
    soll_takt_minuten: float
    ist_takt_minuten: float | None = None
    status: ProduktionsStatus = ProduktionsStatus.OFFEN
    abweichungen: list[str] = field(default_factory=list)
    prioritaet: ProcessPriority = ProcessPriority.P3_ROUTINE
    erstellt: datetime = field(default_factory=_utcnow)


@dataclass
class EingabeDokument:
    raw_text: str
    doc_type: DocumentType = DocumentType.FREITEXT
    quelle: str = ""
    metadaten: dict[str, Any] = field(default_factory=dict)
    eingabe_zeitstempel: datetime = field(default_factory=_utcnow)


@dataclass
class Analyseergebnis:
    eingabe_checksum: str
    prioritaet: ProcessPriority
    zusammenfassung: str
    massnahmen: list[str] = field(default_factory=list)
    erkannte_fehlercodes: list[str] = field(default_factory=list)
    konfidenz: float = 0.0
    modell_id: str = ""
    latenz_ms: float = 0.0
    rohausgabe: str = ""
    token_original: int = 0
    token_komprimiert: int = 0

    def __post_init__(self) -> None:
        if not (0.0 <= self.konfidenz <= 1.0):
            raise ValueError(f"konfidenz={self.konfidenz} muss im Bereich [0.0, 1.0] liegen")
        if self.token_komprimiert > self.token_original and self.token_original > 0:
            raise ValueError(
                f"token_komprimiert={self.token_komprimiert} > token_original={self.token_original}"
            )

    @property
    def token_einsparung_pct(self) -> float:
        if self.token_original == 0:
            return 0.0
        return round((1 - self.token_komprimiert / self.token_original) * 100, 2)
