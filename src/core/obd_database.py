"""
OBD/EOBD Fehlercode-Datenbank – Daimler Buses Edition.
Deckt SAE J2012 Standard-Codes (P0xxx, U0xxx, B0xxx, C0xxx) und
daimler-relevante Netzwerkcodes ab.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from src.models.schemas import ProcessPriority


@dataclass(frozen=True)
class OBDCodeInfo:
    code: str
    beschreibung: str
    schweregrad: ProcessPriority
    komponente: str


# ~70 Codes: P0xxx Powertrain, U0xxx Netzwerk, B0xxx Karosserie, C0xxx Fahrwerk
OBD_DATABASE: Final[dict[str, OBDCodeInfo]] = {
    # ── P1: Zündung / Motoraussetzer ─────────────────────────────────────────
    "P0251": OBDCodeInfo("P0251", "Einspritzpumpe A – Steuerkreis Fehlfunktion",      ProcessPriority.P1_KRITISCH, "Einspritzpumpe"),
    "P0300": OBDCodeInfo("P0300", "Zündaussetzer erkannt – mehrere Zylinder",         ProcessPriority.P1_KRITISCH, "Zündanlage"),
    "P0301": OBDCodeInfo("P0301", "Zündaussetzer Zylinder 1",                         ProcessPriority.P1_KRITISCH, "Zündanlage"),
    "P0302": OBDCodeInfo("P0302", "Zündaussetzer Zylinder 2",                         ProcessPriority.P1_KRITISCH, "Zündanlage"),
    "P0303": OBDCodeInfo("P0303", "Zündaussetzer Zylinder 3",                         ProcessPriority.P1_KRITISCH, "Zündanlage"),
    "P0304": OBDCodeInfo("P0304", "Zündaussetzer Zylinder 4",                         ProcessPriority.P1_KRITISCH, "Zündanlage"),
    "P0305": OBDCodeInfo("P0305", "Zündaussetzer Zylinder 5",                         ProcessPriority.P1_KRITISCH, "Zündanlage"),
    "P0306": OBDCodeInfo("P0306", "Zündaussetzer Zylinder 6",                         ProcessPriority.P1_KRITISCH, "Zündanlage"),
    "P0335": OBDCodeInfo("P0335", "Kurbelwellenpositionssensor A – Signalkreis",      ProcessPriority.P1_KRITISCH, "Motorsensor"),
    # ── P1: Schmier- / Kühlsystem ─────────────────────────────────────────────
    "P0217": OBDCodeInfo("P0217", "Motorüberhitzung erkannt",                         ProcessPriority.P1_KRITISCH, "Kühlsystem"),
    "P0520": OBDCodeInfo("P0520", "Motoröldrucksensor – Signalkreis Fehlfunktion",    ProcessPriority.P1_KRITISCH, "Schmiersystem"),
    "P0521": OBDCodeInfo("P0521", "Motoröldruck – Bereich/Leistung",                  ProcessPriority.P1_KRITISCH, "Schmiersystem"),
    "P0524": OBDCodeInfo("P0524", "Motoröldruck zu niedrig",                          ProcessPriority.P1_KRITISCH, "Schmiersystem"),
    # ── P1: Steuergeräte / Kommunikation ─────────────────────────────────────
    "P0600": OBDCodeInfo("P0600", "CAN-Bus – Kommunikationsfehler allgemein",         ProcessPriority.P1_KRITISCH, "CAN-Bus"),
    "P0601": OBDCodeInfo("P0601", "Motorsteuergerät – interner Kontrollfehler",       ProcessPriority.P1_KRITISCH, "Steuergerät"),
    "P0605": OBDCodeInfo("P0605", "Motorsteuergerät – ROM-Fehler",                    ProcessPriority.P1_KRITISCH, "Steuergerät"),
    "P0606": OBDCodeInfo("P0606", "Motorsteuergerät – Prozessorfehler",               ProcessPriority.P1_KRITISCH, "Steuergerät"),
    # ── P2: Abgassystem / Emissionen ─────────────────────────────────────────
    "P0100": OBDCodeInfo("P0100", "Luftmassenmesser – Signalkreis Fehlfunktion",      ProcessPriority.P2_DRINGEND, "Luftmassenmesser"),
    "P0101": OBDCodeInfo("P0101", "Luftmassenmesser – Bereich/Leistung",              ProcessPriority.P2_DRINGEND, "Luftmassenmesser"),
    "P0115": OBDCodeInfo("P0115", "Kühlmitteltemperatur – Signalkreis Fehlfunktion",  ProcessPriority.P2_DRINGEND, "Kühlsystem"),
    "P0116": OBDCodeInfo("P0116", "Kühlmitteltemperatur – Bereich/Leistung",          ProcessPriority.P2_DRINGEND, "Kühlsystem"),
    "P0125": OBDCodeInfo("P0125", "Unzureichende Kühlmitteltemperatur",               ProcessPriority.P2_DRINGEND, "Kühlsystem"),
    "P0128": OBDCodeInfo("P0128", "Kühlmittelthermostat – unter Temperaturbereich",   ProcessPriority.P2_DRINGEND, "Thermostat"),
    "P0171": OBDCodeInfo("P0171", "Gemisch zu mager – Bank 1",                        ProcessPriority.P2_DRINGEND, "Kraftstoffsystem"),
    "P0172": OBDCodeInfo("P0172", "Gemisch zu fett – Bank 1",                         ProcessPriority.P2_DRINGEND, "Kraftstoffsystem"),
    "P0174": OBDCodeInfo("P0174", "Gemisch zu mager – Bank 2",                        ProcessPriority.P2_DRINGEND, "Kraftstoffsystem"),
    "P0175": OBDCodeInfo("P0175", "Gemisch zu fett – Bank 2",                         ProcessPriority.P2_DRINGEND, "Kraftstoffsystem"),
    "P0190": OBDCodeInfo("P0190", "Kraftstoffdrucksensor – Signalkreis Fehlfunktion", ProcessPriority.P2_DRINGEND, "Kraftstoffsystem"),
    "P0200": OBDCodeInfo("P0200", "Einspritzventil-Regelkreis Fehlfunktion",          ProcessPriority.P2_DRINGEND, "Einspritzanlage"),
    "P0340": OBDCodeInfo("P0340", "Nockenwellenpositionssensor – Signalkreis",        ProcessPriority.P2_DRINGEND, "Motorsensor"),
    "P0400": OBDCodeInfo("P0400", "Abgasrückführung – Durchflussfehlfunktion",        ProcessPriority.P2_DRINGEND, "Abgassystem"),
    "P0401": OBDCodeInfo("P0401", "Abgasrückführung – unzureichender Durchfluss",     ProcessPriority.P2_DRINGEND, "Abgassystem"),
    "P0404": OBDCodeInfo("P0404", "Abgasrückführung – Regelkreis außer Bereich",      ProcessPriority.P2_DRINGEND, "Abgassystem"),
    "P0420": OBDCodeInfo("P0420", "Katalysatorwirkungsgrad unter Schwellenwert",      ProcessPriority.P2_DRINGEND, "Abgasanlage"),
    "P0430": OBDCodeInfo("P0430", "Katalysatorwirkungsgrad unter Schwellenwert B2",   ProcessPriority.P2_DRINGEND, "Abgasanlage"),
    "P0440": OBDCodeInfo("P0440", "Kraftstoffverdunstungs-Emissionssystem",           ProcessPriority.P2_DRINGEND, "Kraftstoffanlage"),
    "P0480": OBDCodeInfo("P0480", "Kühlerlüfter 1 – Steuerkreis Fehlfunktion",        ProcessPriority.P2_DRINGEND, "Kühlsystem"),
    "P0500": OBDCodeInfo("P0500", "Fahrzeuggeschwindigkeitssensor Fehlfunktion",       ProcessPriority.P2_DRINGEND, "Fahrdynamik"),
    "P0562": OBDCodeInfo("P0562", "Systemspannung zu niedrig",                        ProcessPriority.P2_DRINGEND, "Elektrik"),
    "P0563": OBDCodeInfo("P0563", "Systemspannung zu hoch",                           ProcessPriority.P2_DRINGEND, "Elektrik"),
    "P0700": OBDCodeInfo("P0700", "Getriebesteuerung – Fehlfunktion erkannt",         ProcessPriority.P2_DRINGEND, "Getriebe"),
    "P0706": OBDCodeInfo("P0706", "Schaltbereichsensor – Bereich/Leistung",           ProcessPriority.P2_DRINGEND, "Getriebe"),
    "P0720": OBDCodeInfo("P0720", "Ausgangswellendrehzahlsensor – Fehlfunktion",      ProcessPriority.P2_DRINGEND, "Getriebe"),
    "P0730": OBDCodeInfo("P0730", "Falsche Übersetzungsstufe erkannt",                ProcessPriority.P2_DRINGEND, "Getriebe"),
    "P0740": OBDCodeInfo("P0740", "Drehmomentwandler-Überbrückungskupplung",          ProcessPriority.P2_DRINGEND, "Getriebe"),
    "P2200": OBDCodeInfo("P2200", "NOx-Sensor – Leitungsunterbrechung",               ProcessPriority.P2_DRINGEND, "Abgassystem"),
    "P2201": OBDCodeInfo("P2201", "NOx-Sensor – Bereichsfehler",                      ProcessPriority.P2_DRINGEND, "Abgassystem"),
    "P229F": OBDCodeInfo("P229F", "SCR-Reduktionsmittel (AdBlue) – zu niedrig",       ProcessPriority.P2_DRINGEND, "SCR-System"),
    "P20EE": OBDCodeInfo("P20EE", "SCR-Katalysator Wirkungsgrad unterschritten",      ProcessPriority.P2_DRINGEND, "SCR-System"),
    # ── P3: Routine ───────────────────────────────────────────────────────────
    "P0030": OBDCodeInfo("P0030", "Lambdasonde vor Kat – Heizkreis Fehler",           ProcessPriority.P3_ROUTINE,  "Lambdasonde"),
    "P0102": OBDCodeInfo("P0102", "Luftmassenmesser – Signal zu niedrig",             ProcessPriority.P3_ROUTINE,  "Luftmassenmesser"),
    "P0110": OBDCodeInfo("P0110", "Ansauglufttemperatur – Signalkreis Fehlfunktion",  ProcessPriority.P3_ROUTINE,  "Temperatursensor"),
    "P0130": OBDCodeInfo("P0130", "Lambdasonde – Bereich/Leistung (Bank 1, S1)",      ProcessPriority.P3_ROUTINE,  "Lambdasonde"),
    "P0320": OBDCodeInfo("P0320", "Zündanlage / Drehzahlsensor – kein Signal",       ProcessPriority.P3_ROUTINE,  "Zündanlage"),
    "P0410": OBDCodeInfo("P0410", "Sekundärlufteinblasung – Fehlfunktion",            ProcessPriority.P3_ROUTINE,  "Abgassystem"),
    "P1000": OBDCodeInfo("P1000", "OBD-Systemprüfung nicht abgeschlossen",           ProcessPriority.P3_ROUTINE,  "OBD-System"),
    # ── C0xxx: Fahrwerk / Bremse ─────────────────────────────────────────────
    "C0031": OBDCodeInfo("C0031", "Vorderrad rechts – Radgeschwindigkeitssensor",     ProcessPriority.P1_KRITISCH, "ABS/ESP"),
    "C0034": OBDCodeInfo("C0034", "Vorderrad links – Radgeschwindigkeitssensor",      ProcessPriority.P1_KRITISCH, "ABS/ESP"),
    "C0037": OBDCodeInfo("C0037", "Hinterrad rechts – Radgeschwindigkeitssensor",    ProcessPriority.P1_KRITISCH, "ABS/ESP"),
    "C0040": OBDCodeInfo("C0040", "Hinterrad links – Radgeschwindigkeitssensor",     ProcessPriority.P1_KRITISCH, "ABS/ESP"),
    "C0045": OBDCodeInfo("C0045", "ABS – Regelkreis Fehlfunktion",                   ProcessPriority.P1_KRITISCH, "ABS"),
    "C0051": OBDCodeInfo("C0051", "Lenkwinkelsensor – Signalkreis Fehlfunktion",     ProcessPriority.P1_KRITISCH, "Lenkung"),
    "C0110": OBDCodeInfo("C0110", "Bremsdruck – Steuerventil Fehlfunktion",          ProcessPriority.P1_KRITISCH, "Bremsanlage"),
    "C0121": OBDCodeInfo("C0121", "ABS-Ventil – Relaisfehler",                       ProcessPriority.P1_KRITISCH, "ABS"),
    # ── B0xxx: Karosserie / SRS ───────────────────────────────────────────────
    "B0001": OBDCodeInfo("B0001", "Airbag – Zünder Fahrseite Fehlfunktion",          ProcessPriority.P1_KRITISCH, "SRS/Airbag"),
    "B0002": OBDCodeInfo("B0002", "Airbag – Zünder Beifahrerseite Fehlfunktion",     ProcessPriority.P1_KRITISCH, "SRS/Airbag"),
    "B0051": OBDCodeInfo("B0051", "SRS-Steuergerät – interner Fehler",               ProcessPriority.P1_KRITISCH, "SRS/Airbag"),
    "B0084": OBDCodeInfo("B0084", "Gurtstraffer Fahrseite – Steuerkreis Fehler",     ProcessPriority.P1_KRITISCH, "SRS"),
    "B1000": OBDCodeInfo("B1000", "BCM – Hauptsteuergerät Fehlfunktion",             ProcessPriority.P2_DRINGEND, "Karosserie-SG"),
    # ── U0xxx: Netzwerk / CAN ─────────────────────────────────────────────────
    "U0001": OBDCodeInfo("U0001", "CAN-Bus Hochgeschwindigkeit – Kommunikationsfehler", ProcessPriority.P1_KRITISCH, "CAN-Bus"),
    "U0010": OBDCodeInfo("U0010", "CAN-Bus Mittelgeschwindigkeit – Kommunikationsfehler", ProcessPriority.P1_KRITISCH, "CAN-Bus"),
    "U0020": OBDCodeInfo("U0020", "CAN-Bus Niedriggeschwindigkeit – Kommunikationsfehler", ProcessPriority.P1_KRITISCH, "CAN-Bus"),
    "U0073": OBDCodeInfo("U0073", "CAN-Bus A – Kommunikation unterbrochen",          ProcessPriority.P1_KRITISCH, "CAN-Bus"),
    "U0100": OBDCodeInfo("U0100", "Kommunikationsverlust mit Motorsteuergerät",      ProcessPriority.P1_KRITISCH, "Motorsteuergerät"),
    "U0101": OBDCodeInfo("U0101", "Kommunikationsverlust mit Getriebesteuergerät",   ProcessPriority.P1_KRITISCH, "Getriebe-SG"),
    "U0121": OBDCodeInfo("U0121", "Kommunikationsverlust mit ABS-Steuergerät",       ProcessPriority.P1_KRITISCH, "ABS-SG"),
    "U0126": OBDCodeInfo("U0126", "Kommunikationsverlust mit Lenkwinkel-SG",         ProcessPriority.P1_KRITISCH, "Lenkung-SG"),
    "U0131": OBDCodeInfo("U0131", "Kommunikationsverlust mit Servolenkung-SG",       ProcessPriority.P1_KRITISCH, "Servolenkung"),
    "U0140": OBDCodeInfo("U0140", "Kommunikationsverlust mit Karosserie-SG",         ProcessPriority.P2_DRINGEND, "Karosserie-SG"),
    "U0155": OBDCodeInfo("U0155", "Kommunikationsverlust mit Instrumentencluster",   ProcessPriority.P2_DRINGEND, "Instrumente"),
    "U0184": OBDCodeInfo("U0184", "Kommunikationsverlust mit Radio-SG",              ProcessPriority.P3_ROUTINE,  "Infotainment"),
    "U1100": OBDCodeInfo("U1100", "FlexRay-Bus Kommunikationsfehler",                ProcessPriority.P1_KRITISCH, "FlexRay-Bus"),
}

_CODE_RE = re.compile(r"\b([PBCU][0-9A-F]{4})\b", re.I)


def lookup(code: str) -> OBDCodeInfo | None:
    """Gibt OBDCodeInfo zurück oder None wenn unbekannt."""
    return OBD_DATABASE.get(code.upper().strip())


def lookup_severity(code: str) -> ProcessPriority | None:
    """Gibt nur den Schweregrad zurück – optimiert für TriageAgent."""
    info = lookup(code)
    return info.schweregrad if info else None


def find_codes_in_text(text: str) -> list[OBDCodeInfo]:
    """
    Extrahiert alle bekannten OBD-Codes aus Freitext.
    Unbekannte Codes werden ignoriert. Rückgabe ist dedupliziert.
    """
    found: list[OBDCodeInfo] = []
    seen: set[str] = set()
    for m in _CODE_RE.finditer(text):
        code = m.group(1).upper()
        if code not in seen:
            seen.add(code)
            info = OBD_DATABASE.get(code)
            if info:
                found.append(info)
    return found
