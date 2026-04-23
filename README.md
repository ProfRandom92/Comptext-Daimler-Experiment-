# Daimler Buses – CompText Prozessautomatisierung

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?logo=streamlit)
![License](https://img.shields.io/badge/License-Apache%202.0-green)
![Tests](https://img.shields.io/badge/Tests-62%20passing-brightgreen)
![DSGVO](https://img.shields.io/badge/DSGVO-Art.%2025-blue)

**Industrielle KI-Token-Komprimierung für Daimler Buses Prozessdokumente**

*Adaptiert aus [MedGemma-CompText](https://github.com/ProfRandom92/Medgemma-CompText) & [CompText-Monorepo-X](https://github.com/ProfRandom92/comptext-monorepo-X)*

</div>

---

## Überblick

CompText ist eine **3-Agent-Pipeline**, die industrielle Prozessdokumente (Wartungsprotokolle, OBD-Fehlercodes, QA-Berichte, Produktionsaufträge) **DSGVO-konform bereinigt, um bis zu ~90% komprimiert** und anschließend per lokalem LLM (Gemma 2B via Ollama) oder Cloud-LLM (Claude Haiku) analysiert.

### Analogie: MedGemma → Daimler Buses

| MedGemma-CompText | Daimler Buses CompText |
|---|---|
| PHI-Bereinigung | FIN-Maskierung, Personalr.-Hash |
| Patientenakten (EHR) | Wartungsprotokolle, OBD-Daten |
| Nurse Agent | IntakeAgent |
| Triage P1/P2/P3 | Prozesspriorität P1/P2/P3 |
| Doctor Agent (MedGemma) | AnalysisAgent (Gemma / Claude) |
| Klinische Diagnose | Predictive Maintenance, QA |

---

## Architektur

```mermaid
flowchart TD
    A[📄 Rohdokument\nWartungsprotokoll / OBD / QA / Produktion] --> B

    subgraph Layer1["Layer 1 – IntakeAgent"]
        B[🔒 DSGVO-Sanitisierung\nFIN maskieren · E-Mail entfernen · ID hashen]
        B --> C[📦 KVTC-Kompression\n4-Layer Sandwich-Algorithmus]
        C --> D[IntakeResult\ndokument + kvtc_frame + bereinigungen]
    end

    D --> E

    subgraph Layer2["Layer 2 – TriageAgent"]
        E[🔎 Regelbasierte Klassifizierung\nRegex-Patterns + OBD-Datenbank 70+ Codes]
        E --> F{Priorität?}
        F -->|Sicherheitskritisch| G[🔴 P1_KRITISCH\nSofortige Eskalation]
        F -->|Dringend| H[🟠 P2_DRINGEND\nEinplanung 24h]
        F -->|Routine| I[🟢 P3_ROUTINE\nNächste Inspektion]
    end

    G & H & I --> J

    subgraph Layer3["Layer 3 – AnalysisAgent"]
        J[🤖 LLM-Inferenz\nOllama Gemma 2B · Claude Haiku · Mock]
        J --> K[💾 Ergebnis-Cache\nMD5-basiertes LRU · 256 Einträge]
        K --> L[Analyseergebnis\nZusammenfassung · Maßnahmen · Konfidenz]
    end

    L --> M[📊 Streamlit Dashboard\n+ JSON/CSV Export]
    L --> N[🌐 FastAPI REST\n/analyze · /batch/analyze · /health]

    style Layer1 fill:#E3F2FD,stroke:#1565C0
    style Layer2 fill:#FFF3E0,stroke:#E65100
    style Layer3 fill:#E8F5E9,stroke:#2E7D32
```

---

## KVTC 4-Layer Kompression

```mermaid
flowchart LR
    subgraph Input["Eingabedokument"]
        T[Roher Text\n~1000 Tokens]
    end

    subgraph Sandwich["Sandwich-Zonen"]
        H[🔒 Header-Zone\nLossless\nSOPs · Stammdaten]
        M[⚡ Middle-Zone\nAggressiv\nnur Top 25% Dichte]
        W[🔒 Window-Zone\nLossless\nAktuelle Diagnose]
    end

    subgraph KVTC["KVTC 4-Layer Frame"]
        K["K: Feldname1, Feldname2"]
        V["V: Wert1, Wert2"]
        Ty["T: DATE, NUMERIC, OBD_CODE"]
        C["C: P0300, SAP-12345, FIN_***ABC123"]
    end

    subgraph Output["Komprimiertes Ergebnis"]
        R[KVTC-Frame\n~100 Tokens\n✅ MD5-Checksum]
    end

    T --> H & M & W
    H & M & W --> K & V & Ty & C
    K & V & Ty & C --> R

    style Input fill:#FFEBEE
    style Output fill:#E8F5E9
    style Sandwich fill:#FFF8E1
    style KVTC fill:#E3F2FD
```

### Informationsdichte-Scoring

| Signal | Gewichtung |
|--------|-----------|
| OBD-Code (P0300, U0100) | 4.0× |
| SAP-Nummer | 3.0× |
| Numerischer Wert / Datum | 2.0× |
| Key-Value-Paar | 1.5× |
| Freitext | 1.0× |

---

## OBD-Code-Datenbank

```mermaid
graph TD
    Text[📄 Dokumenttext] --> Extractor["_CODE_RE = r'[PBCU][0-9A-F]{4}'"]
    Extractor --> DB[(OBD_DATABASE\n70+ Codes)]

    DB --> P1["🔴 P1_KRITISCH\nP0300-P0306 Zündaussetzer\nU0073/U0100 CAN-Bus-Ausfall\nC0110 Bremsventil\nB0001 Airbag\nP0524 Öldruck kritisch\n..."]
    DB --> P2["🟠 P2_DRINGEND\nP0171/P0172 Gemisch\nP0420 Katalysator\nP0700 Getriebe\nP229F AdBlue\nP20EE SCR-System\n..."]
    DB --> P3["🟢 P3_ROUTINE\nP0030 Lambdasonde\nP1000 OBD-Prüfung\nU0184 Radio-SG\n..."]
    DB --> UNK["⚪ Unbekannt\n→ Regex-Fallback"]
```

---

## DSGVO Art. 25 – Privacy by Design

```mermaid
sequenceDiagram
    participant SAP as SAP / MES
    participant IA as IntakeAgent
    participant LLM as LLM (Gemma/Claude)

    SAP->>IA: Rohdokument mit FIN, Personal-ID, E-Mail

    Note over IA: DSGVO-Sanitisierung
    IA->>IA: FIN WDB906232N3123456 → FIN_***123456
    IA->>IA: P12345 → PERS_A1B2C3D4 (MD5)
    IA->>IA: max.muster@daimler.com → [EMAIL_ENTFERNT]
    IA->>IA: +49 711 1234 → [TEL_ENTFERNT]
    IA->>IA: Kunde: Müller → [KUNDE_ENTFERNT]

    Note over IA: KVTC-Kompression
    IA->>LLM: Komprimiertes KVTC-Frame (kein PII)
    LLM->>IA: JSON-Analyse
    IA->>SAP: Analyseergebnis (sanitisiert)
```

| Datentyp | Methode | Ergebnis |
|----------|---------|---------|
| FIN / VIN (vollständig) | Letzten 6 Zeichen behalten | `FIN_***XXXXXX` |
| Personalnummer | One-Way-MD5-Hash (8 Zeichen) | `PERS_A1B2C3D4` |
| E-Mail-Adressen | Entfernen | `[EMAIL_ENTFERNT]` |
| Telefonnummern | Entfernen | `[TEL_ENTFERNT]` |
| Kundenzeilen | Entfernen | `[KUNDE_ENTFERNT]` |

---

## LLM-Backend-Vergleich

```mermaid
graph LR
    Doc[Komprimiertes\nDokument] --> Dispatch{Backend-\nAuswahl}

    Dispatch -->|LLM_BACKEND=mock| Mock["🧪 Mock\n• Deterministisch\n• Kein GPU/Netz\n• Für Tests"]
    Dispatch -->|LLM_BACKEND=ollama_gemma| Ollama["🏠 Ollama Gemma 2B\n• Lokal / Air-Gap\n• Kein Cloud-Zwang\n• DSGVO-Maximum"]
    Dispatch -->|LLM_BACKEND=anthropic| Claude["☁️ Claude Haiku\n• Höchste Qualität\n• Prompt Caching\n• API-Key nötig"]

    Mock & Ollama & Claude --> Cache["💾 Ergebnis-Cache\nMD5 LRU 256 Slots"]
    Cache --> Result[Analyseergebnis]
```

### Anthropic Prompt Caching

Der `AnalysisAgent` nutzt **ephemeral prompt caching** – der statische System-Prompt wird mit `cache_control: {"type": "ephemeral"}` markiert. Der Anthropic-Client wird als **Lazy Singleton** erstellt (einmalig pro `AnalysisAgent`-Instanz).

---

## API-Endpunkte

```mermaid
graph LR
    Client[Client / SAP / MES]

    Client -->|POST /analyze| A["Vollständige Pipeline\n→ AnalyzeResponse"]
    Client -->|POST /batch/analyze| B["Bis zu 10 Dokumente\n→ BatchAnalyzeResponse\n(Fehlertoleranz pro Item)"]
    Client -->|POST /compress| C["Nur KVTC-Kompression\n→ KVTCResponse"]
    Client -->|POST /triage| D["Nur Priorisierung\n→ TriageResponse"]
    Client -->|GET /health| E["Status + Cache-Stats\n→ {status, cache_size,\ncache_hit_rate}"]
    Client -->|GET /benchmark| F["Standard-Benchmark\n→ Kompressionswerte"]

    style B fill:#E8F5E9
    style E fill:#E3F2FD
```

---

## Projektstruktur

```
Comptext-Daimler-Experiment-/
│
├── config.py                    # AppConfig (Env-Vars: LLM_BACKEND, OLLAMA_URL, ...)
├── dashboard.py                 # Streamlit UI (3 Tabs + JSON/CSV-Export)
├── api.py                       # FastAPI REST (6 Endpunkte inkl. Batch)
│
├── src/
│   ├── core/
│   │   ├── kvtc.py              # IndustrialKVTCStrategy – Sandwich-Kompression
│   │   ├── obd_database.py      # 70+ OBD-Codes mit Schweregrad-Mapping
│   │   └── result_cache.py      # Thread-sicherer LRU-Cache (OrderedDict)
│   ├── agents/
│   │   ├── intake_agent.py      # DSGVO-Sanitisierung + Typdetection + KVTC
│   │   ├── triage_agent.py      # P1/P2/P3 Regex + OBD-DB Integration
│   │   └── analysis_agent.py    # LLM-Dispatch + Prompt Caching + Cache
│   ├── models/
│   │   └── schemas.py           # Enums, Dataclasses (Fahrzeug, OBD, Audit, ...)
│   └── utils/
│       └── logging.py           # JSON Structured Logging (ELK/Azure-kompatibel)
│
├── tests/
│   ├── test_kvtc.py             # 8 Tests – Kompressionsalgorithmus
│   ├── test_intake_agent.py     # 11 Tests – Sanitisierung + Typdetection
│   ├── test_triage_agent.py     # 10 Tests – P1/P2/P3 Priorisierung
│   ├── test_analysis_agent.py   # 4 Tests – LLM-Dispatch + Mock
│   ├── test_obd_database.py     # 13 Tests – OBD-Lookup + Triage-Integration
│   ├── test_result_cache.py     # 9 Tests – LRU-Cache + Thread-Safety
│   └── test_api_batch.py        # 7 Tests – Batch-Endpoint + Health
│
├── .github/workflows/ci.yml     # GitHub Actions (Python 3.11/3.12)
├── Dockerfile                   # Python 3.11-slim, non-root User
├── docker-compose.yml           # Dashboard + API + Ollama Services
└── pyproject.toml               # Packaging + ruff + mypy + pytest
```

---

## Schnellstart

### Lokal (Mock-Modus)

```bash
git clone https://github.com/ProfRandom92/comptext-daimler-experiment-
cd comptext-daimler-experiment-
pip install -r requirements.txt

# Dashboard (Port 8501)
streamlit run dashboard.py

# REST API (Port 8000)
uvicorn api:app --reload
```

### Mit Ollama Gemma 2B (lokal, DSGVO-Maximum)

```bash
# Ollama installieren: https://ollama.ai
ollama pull gemma2:2b

LLM_BACKEND=ollama_gemma \
OLLAMA_URL=http://localhost:11434 \
streamlit run dashboard.py
```

### Mit Claude Haiku (Cloud)

```bash
LLM_BACKEND=anthropic \
ANTHROPIC_API_KEY=sk-ant-... \
streamlit run dashboard.py
```

### Docker Compose (alles inkl. Ollama)

```bash
docker-compose up
# Dashboard: http://localhost:8501
# API:       http://localhost:8000
# Docs:      http://localhost:8000/docs
```

---

## Batch-Analyse (API)

```bash
curl -X POST http://localhost:8000/batch/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {"text": "Fehler P0300 – Zündaussetzer Zylinder 1", "quelle": "SAP"},
      {"text": "Wartungsprotokoll km 80000 – Routineinspektion", "quelle": "MES"},
      {"text": "QA-Bericht: Sperrung eingeleitet – Bremsanlage", "quelle": "QA"}
    ]
  }'
```

Response:
```json
{
  "total": 3,
  "succeeded": 3,
  "failed": 0,
  "results": [
    {"index": 0, "success": true, "result": {"prioritaet": "P1_KRITISCH", ...}},
    {"index": 1, "success": true, "result": {"prioritaet": "P3_ROUTINE", ...}},
    {"index": 2, "success": true, "result": {"prioritaet": "P1_KRITISCH", ...}}
  ]
}
```

---

## Tests

```bash
# Alle Tests
pytest tests/ -v

# Mit Coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Einzelne Test-Dateien
pytest tests/test_obd_database.py -v
pytest tests/test_result_cache.py -v
pytest tests/test_api_batch.py -v
```

**62 Tests · 0 Fehler · ~0.5s Laufzeit**

---

## Umgebungsvariablen

| Variable | Standard | Beschreibung |
|----------|---------|-------------|
| `LLM_BACKEND` | `mock` | `mock` · `ollama_gemma` · `anthropic` |
| `OLLAMA_MODEL` | `gemma2:2b` | Ollama-Modell-ID |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama-Basis-URL |
| `ANTHROPIC_MODEL` | `claude-haiku-4-5-20251001` | Anthropic-Modell-ID |
| `ANTHROPIC_API_KEY` | – | API-Schlüssel (Anthropic) |
| `ANTHROPIC_PROMPT_CACHE` | `true` | Prompt Caching an/aus |
| `MAX_TOKENS` | `512` | Maximale Ausgabe-Tokens |
| `TEMPERATURE` | `0.1` | Temperatur (niedrig = deterministisch) |
| `CACHE_MAX_SIZE` | `256` | Max. Einträge im LRU-Ergebnis-Cache |
| `LOG_LEVEL` | `INFO` | Logging-Level |
| `LOG_FORMAT` | `json` | `json` (strukturiert) · `text` |

---

## Termux (Android)

Für mobile Einsatzszenarien oder On-Device-Debugging:

```bash
# 1. Termux-Pakete installieren
pkg update && pkg upgrade -y
pkg install python git -y

# 2. Repository klonen
git clone https://github.com/ProfRandom92/comptext-daimler-experiment-
cd comptext-daimler-experiment-

# 3. Abhängigkeiten (ohne GUI-Pakete)
pip install anthropic requests fastapi uvicorn pytest pytest-cov httpx

# 4. REST API starten (Mock-Modus, kein LLM nötig)
LLM_BACKEND=mock uvicorn api:app --host 0.0.0.0 --port 8000

# 5. Analyse-Test
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Fehler P0300 Zündaussetzer – Kilometerstand 80000", "quelle": "Termux"}'

# 6. Batch-Test (3 Dokumente)
curl -X POST http://localhost:8000/batch/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {"text": "P0300 Zündaussetzer", "quelle": "OBD"},
      {"text": "Bremsversagen festgestellt", "quelle": "Werkstatt"},
      {"text": "Kilometerstand 80000 nächster Service 75000", "quelle": "SAP"}
    ]
  }'

# 7. OBD-Triage direkt testen
curl -X POST http://localhost:8000/triage \
  -H "Content-Type: application/json" \
  -d '{"text": "Fehlercode U0100 – CAN-Bus Kommunikationsverlust ECM"}'

# 8. Tests ausführen
pytest tests/ -v --tb=short

# 9. Mit Anthropic Claude (API-Key erforderlich)
ANTHROPIC_API_KEY=sk-ant-... LLM_BACKEND=anthropic uvicorn api:app --port 8000
```

> **Hinweis**: Streamlit läuft nicht nativ in Termux. Für das Dashboard wird ein Desktop-System empfohlen. Die FastAPI REST-API funktioniert vollständig in Termux.

---

## Lizenz

Apache 2.0 – siehe [LICENSE](LICENSE)

---

<div align="center">

*Basiert auf [MedGemma-CompText](https://github.com/ProfRandom92/Medgemma-CompText) & [CompText-Monorepo-X](https://github.com/ProfRandom92/comptext-monorepo-X) von ProfRandom92*

</div>
