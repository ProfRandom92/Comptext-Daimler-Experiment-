"""
IntakeAgent – Daten-Aufnahme & Bereinigung
Entspricht dem NurseAgent aus MedGemma-CompText.

Aufgaben:
  1. Vertrauliche Geschäftsdaten entfernen / anonymisieren (DSGVO Art. 25)
  2. Dokument-Typ erkennen
  3. KVTC-Kompression anwenden
  4. Valides EingabeDokument + KVTCResult zurückgeben

Vertrauliche Daten (analog zu PHI im medizinischen Kontext):
  - Vollständige FIN / VIN           → letzten 6 Zeichen behalten
  - Mitarbeiter-IDs / Personalnummern → One-Way-Hash (MD5, 8 Zeichen)
  - Kundennamen / Firmennamen        → [KUNDE_ENTFERNT]
  - Interne SAP-Auftragsnummern      → optional maskierbar
  - E-Mail-Adressen, Telefonnummern  → vollständig entfernt
"""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass

from src.core.kvtc import IndustrialKVTCStrategy, KVTCResult
from src.models.schemas import DocumentType, EingabeDokument


# ---------------------------------------------------------------------------
# Regex-Definitionen
# ---------------------------------------------------------------------------

# Vollständige FIN (17 Zeichen, ISO 3779)
_FIN_FULL    = re.compile(r"\b([A-HJ-NPR-Z0-9]{11})([A-HJ-NPR-Z0-9]{6})\b")
# Personal-/Mitarbeiternummern (P + 5-8 Ziffern, oder nur 6-8 Ziffern allein)
_PERSONAL_NR = re.compile(r"\bP\d{5,8}\b|\b(?<!\d)\d{6,8}(?!\d)\b")
# E-Mail
_EMAIL       = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
# Telefon (diverse Formate)
_TELEFON     = re.compile(r"(\+49|0)\s?[\d\s\-/]{8,18}")
# Kundennamen-Hinweise (Zeilen die mit "Kunde:", "Auftraggeber:" beginnen)
_KUNDEN_ZEILE = re.compile(
    r"(Kunde|Auftraggeber|Besteller|Halter)\s*:\s*.+", re.IGNORECASE
)

# Typ-Erkennung nach Schlüsselwörtern
_TYPE_PATTERNS: list[tuple[re.Pattern[str], DocumentType]] = [
    (re.compile(r"Wartungsauftrag|Werkstattauftrag|Inspektion|Service", re.I), DocumentType.WARTUNGSPROTOKOLL),
    (re.compile(r"\b[PBCU]\d{4}\b"),                                          DocumentType.OBD_FEHLERCODE),
    (re.compile(r"Prüfbericht|QA|Qualitätsprüfung|Beanstandung",   re.I),    DocumentType.QA_PRUEFBERICHT),
    (re.compile(r"Produktionsauftrag|Fertigungsauftrag|Takt",       re.I),    DocumentType.PRODUKTIONSAUFTRAG),
    (re.compile(r"Lieferschein|Wareneingang|Lieferant",             re.I),    DocumentType.LIEFERSCHEIN),
    (re.compile(r"Arbeitsplan|Arbeitsschritte|Montageanleitung",    re.I),    DocumentType.ARBEITSPLAN),
]


@dataclass
class IntakeResult:
    dokument: EingabeDokument
    kvtc: KVTCResult
    bereinigungen: list[str]       # Log welche Daten entfernt wurden
    latenz_ms: float


class IntakeAgent:
    """
    Erster Layer der Pipeline: Bereinigung und Aufnahme.
    DSGVO-konform durch One-Way-Hashing und Feldentfernung.
    """

    def __init__(self, kvtc: IndustrialKVTCStrategy | None = None) -> None:
        self._kvtc = kvtc or IndustrialKVTCStrategy()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def process(self, raw_text: str, quelle: str = "") -> IntakeResult:
        t0 = time.perf_counter()
        bereinigungen: list[str] = []

        cleaned = self._sanitize(raw_text, bereinigungen)
        doc_type = self._detect_type(cleaned)

        kvtc_result = self._kvtc.compress(
            cleaned,
            context_metadata={"quelle": quelle, "doc_type": doc_type.value},
        )

        dokument = EingabeDokument(
            raw_text=cleaned,
            doc_type=doc_type,
            quelle=quelle,
            metadaten={
                "checksum": kvtc_result.checksum,
                "original_tokens": kvtc_result.original_tokens,
                "compressed_tokens": kvtc_result.compressed_tokens,
            },
        )

        latenz_ms = (time.perf_counter() - t0) * 1000

        return IntakeResult(
            dokument=dokument,
            kvtc=kvtc_result,
            bereinigungen=bereinigungen,
            latenz_ms=round(latenz_ms, 3),
        )

    # ------------------------------------------------------------------
    # Sanitization (analog zu PHI-Scrubbing in NurseAgent)
    # ------------------------------------------------------------------

    def _sanitize(self, text: str, log: list[str]) -> str:
        text = self._mask_fin(text, log)
        text = self._hash_personal_nr(text, log)
        text = self._remove_email(text, log)
        text = self._remove_telefon(text, log)
        text = self._remove_kunden_zeile(text, log)
        return text

    def _mask_fin(self, text: str, log: list[str]) -> str:
        """Behält nur die letzten 6 Zeichen der FIN (eindeutige Seriennummer)."""
        def replacer(m: re.Match) -> str:
            log.append("FIN maskiert")
            return f"FIN_***{m.group(2)}"

        return _FIN_FULL.sub(replacer, text)

    def _hash_personal_nr(self, text: str, log: list[str]) -> str:
        """Ersetzt Personalnummern durch 8-stelligen MD5-Hash (One-Way, aus Monorepo-X)."""
        def replacer(m: re.Match) -> str:
            log.append("Personalnummer gehasht")
            hashed = hashlib.md5(m.group(0).encode()).hexdigest()[:8].upper()
            return f"PERS_{hashed}"

        return _PERSONAL_NR.sub(replacer, text)

    def _remove_email(self, text: str, log: list[str]) -> str:
        count = len(_EMAIL.findall(text))
        if count:
            log.append(f"{count}x E-Mail entfernt")
        return _EMAIL.sub("[EMAIL_ENTFERNT]", text)

    def _remove_telefon(self, text: str, log: list[str]) -> str:
        count = len(_TELEFON.findall(text))
        if count:
            log.append(f"{count}x Telefon entfernt")
        return _TELEFON.sub("[TEL_ENTFERNT]", text)

    def _remove_kunden_zeile(self, text: str, log: list[str]) -> str:
        lines = text.splitlines()
        cleaned_lines = []
        for line in lines:
            if _KUNDEN_ZEILE.match(line.strip()):
                log.append("Kundenzeile entfernt")
                cleaned_lines.append("[KUNDE_ENTFERNT]")
            else:
                cleaned_lines.append(line)
        return "\n".join(cleaned_lines)

    # ------------------------------------------------------------------
    # Type Detection
    # ------------------------------------------------------------------

    def _detect_type(self, text: str) -> DocumentType:
        for pattern, doc_type in _TYPE_PATTERNS:
            if pattern.search(text):
                return doc_type
        return DocumentType.FREITEXT
