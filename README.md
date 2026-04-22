# Daimler Buses – CompText Prozessautomatisierung

> Industrielle KI-Token-Komprimierung für Daimler Buses Prozessdokumente.  
> Adaptiert aus [MedGemma-CompText](https://github.com/ProfRandom92/Medgemma-CompText) &
> [CompText-Monorepo-X](https://github.com/ProfRandom92/comptext-monorepo-X).

---

## Was ist das?

CompText ist eine 3-Layer-Pipeline, die lange Prozessdokumente (Wartungsprotokolle,
OBD-Fehlercodes, QA-Berichte, Produktionsaufträge) **DSGVO-konform bereinigt,
um bis zu ~90% komprimiert** und anschließend per lokalem LLM (Gemma 2B via Ollama)
oder Cloud-LLM (Claude Haiku) analysiert.

### Analogie: MedGemma → Daimler Buses

| MedGemma-CompText       | Daimler Buses CompText           |
|-------------------------|----------------------------------|
| PHI-Bereinigung         | FIN-Maskierung, Personalr.-Hash  |
| Patientenakten (EHR)    | Wartungsprotokolle, OBD-Daten   |
| Nurse Agent             | IntakeAgent                      |
| Triage P1/P2/P3         | Prozesspriorität P1/P2/P3        |
| Doctor Agent (MedGemma) | AnalysisAgent (Gemma / Claude)   |
| Klinische Diagnose      | Predictive Maintenance, QA       |

---

## Architektur

```
Eingabe (Rohdokument)
       │
       ▼
┌──────────────┐
│ IntakeAgent  │  Layer 1: DSGVO-Bereinigung + 4-Layer KVTC-Kompression
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ TriageAgent  │  Layer 2: Regelbasierte P1/P2/P3 Priorität
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ AnalysisAgent    │  Layer 3: LLM-Analyse (Gemma 2B / Claude)
└──────┬───────────┘
       │
       ▼
  Analyseergebnis (Zusammenfassung, Maßnahmen, OBD-Codes, Konfidenz)
```

### KVTC 4-Layer (aus Monorepo-X)

| Layer | Bedeutung | Inhalt |
|-------|-----------|--------|
| **K** | Key       | Feldbezeichner |
| **V** | Value     | Feldwerte |
| **T** | Type      | DATE, NUMERIC, OBD_CODE, ENUM, TEXT |
| **C** | Code      | OBD-Codes, SAP-Nummern, FIN-Fragmente |

**Sandwich-Zonen:**
- **Header** → Lossless (SOPs, Fahrzeugstammdaten)
- **Middle** → Aggressiv komprimiert (historische Einträge)
- **Window** → Lossless (aktuelle Diagnosedaten)

---

## Anwendungsfälle

- **Predictive Maintenance** – Wartungsbedarf aus Sensor-/Protokolldaten erkennen
- **OBD-Analyse** – Fehlercodes priorisieren und Maßnahmen ableiten
- **QA-Prüfberichte** – Beanstandungen klassifizieren und eskalieren
- **Produktionsoptimierung** – Taktabweichungen und Engpässe analysieren
- **Lieferkette** – Lieferscheine und Teileengpässe verarbeiten

---

## Schnellstart

```bash
# Abhängigkeiten installieren
pip install -r requirements.txt

# Dashboard starten (Mock-Modus, kein LLM nötig)
streamlit run dashboard.py

# Mit lokalem Gemma (Ollama muss laufen)
LLM_BACKEND=ollama_gemma OLLAMA_MODEL=gemma2:2b streamlit run dashboard.py

# Mit Claude Haiku (API-Key nötig)
LLM_BACKEND=anthropic ANTHROPIC_API_KEY=sk-ant-... streamlit run dashboard.py
```

---

## Tests

```bash
pytest tests/ -v --cov=src
```

---

## Projektstruktur

```
src/
├── core/kvtc.py           → IndustrialKVTCStrategy (4-Layer + serializeFrame)
├── agents/
│   ├── intake_agent.py    → DSGVO-Bereinigung & Aufnahme
│   ├── triage_agent.py    → P1/P2/P3 Priorität (regelbasiert)
│   └── analysis_agent.py  → LLM-Inferenz (Gemma / Claude)
└── models/schemas.py      → Daimler-Datenmodelle

dashboard.py               → Streamlit UI
config.py                  → Konfiguration
tests/                     → pytest Test-Suite
```

---

## Datenschutz (DSGVO Art. 25)

Der IntakeAgent entfernt/anonymisiert folgende Daten **bevor** sie das LLM erreichen:

| Datentyp | Maßnahme |
|----------|---------|
| FIN / VIN (vollständig) | Letzten 6 Zeichen behalten: `FIN_***XXXXXX` |
| Personalfummer | One-Way-MD5-Hash: `PERS_A1B2C3D4` |
| E-Mail-Adressen | `[EMAIL_ENTFERNT]` |
| Telefonnummern | `[TEL_ENTFERNT]` |
| Kundenzeilen | `[KUNDE_ENTFERNT]` |

---

## Lizenz

Apache 2.0 – siehe [LICENSE](LICENSE)

---

*Basiert auf MedGemma-CompText & CompText-Monorepo-X von ProfRandom92.*
