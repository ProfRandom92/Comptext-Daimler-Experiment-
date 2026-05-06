<div align="center">

# Daimler Buses CompText

**Industrielle KI-Prozessautomatisierung · DSGVO Art. 25 · 4-Layer Token-Kompression**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Anthropic](https://img.shields.io/badge/Claude-Haiku%20%2F%20Sonnet-D4A827?logo=anthropic)](https://anthropic.com)
[![License](https://img.shields.io/badge/License-Apache%202.0-green)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-62%20passing-brightgreen)](tests/)
[![Ruff](https://img.shields.io/badge/Linting-ruff-FCC21B)](https://docs.astral.sh/ruff/)
[![DSGVO](https://img.shields.io/badge/DSGVO-Art.%2025-blue)](#dsgvo-privacy-by-design)

**3-Agent-Pipeline** · **~88% Token-Reduktion** · **Air-Gap-Ready** · **Production-Audit**

*Portiert aus [MedGemma-CompText](https://github.com/ProfRandom92/Medgemma-CompText) – Healthcare-Architektur adaptiert für Automotive*

</div>

---

## Inhalt

- [Was ist CompText?](#was-ist-comptext)
- [Schnellstart](#schnellstart)
- [Architektur](#architektur)
- [KVTC-Algorithmus](#kvtc-algorithmus)
- [DSGVO Privacy by Design](#dsgvo-privacy-by-design)
- [OBD-Datenbank](#obd-datenbank)
- [API-Referenz](#api-referenz)
- [LLM-Backends](#llm-backends)
- [Performance](#performance)
- [Konfiguration](#konfiguration)
- [Tests](#tests)
- [Docker](#docker)
- [Projektstruktur](#projektstruktur)
- [Security](#security)
- [Lizenz](#lizenz)

---

## Was ist CompText?

CompText ist eine **3-stufige Multi-Agent-Pipeline**, die industrielle Prozessdokumente automatisch verarbeitet:

| Schritt | Agent | Funktion |
|---------|-------|----------|
| 1 | **IntakeAgent** | DSGVO-Sanitisierung (FIN, PII) + KVTC-Kompression |
| 2 | **TriageAgent** | Prioritätsklassifizierung P1/P2/P3 per Regex + OBD-DB |
| 3 | **AnalysisAgent** | LLM-Inferenz (Ollama / Claude / Mock) + LRU-Cache |

**Unterstützte Dokumenttypen**: Wartungsprotokolle · OBD-Fehlercodes · QA-Prüfberichte · Produktionsaufträge · Allgemeine Berichte

### Analogie: MedGemma → Daimler Buses

| MedGemma-CompText (Original) | Daimler Buses CompText |
|------------------------------|------------------------|
| PHI-Bereinigung | FIN-Maskierung, Personalr.-Hash |
| Patientenakten (EHR) | Wartungsprotokolle, OBD-Daten |
| Nurse Agent | IntakeAgent |
| Triage P1/P2/P3 | Prozesspriorität P1/P2/P3 |
| Doctor Agent (MedGemma) | AnalysisAgent (Gemma / Claude) |
| Klinische Diagnose | Predictive Maintenance, QA |

---

## Schnellstart

### Voraussetzungen

- Python 3.11+
- (Optional) [Ollama](https://ollama.ai) für lokale LLM-Inferenz
- (Optional) Anthropic API-Key für Claude

### Installation

```bash
git clone https://github.com/ProfRandom92/comptext-daimler-experiment-
cd comptext-daimler-experiment-
pip install -r requirements.txt
```

### Mock-Modus (kein LLM nötig)

```bash
# Streamlit Dashboard (Port 8501)
streamlit run dashboard.py

# REST API (Port 8000)
uvicorn api:app --reload
```

### Mit Ollama Gemma 2B (lokal, maximale DSGVO-Konformität)

```bash
ollama pull gemma2:2b

LLM_BACKEND=ollama_gemma \
OLLAMA_URL=http://localhost:11434 \
streamlit run dashboard.py
```

### Mit Claude Haiku (Cloud)

```bash
LLM_BACKEND=anthropic \
ANTHROPIC_API_KEY=sk-ant-... \
uvicorn api:app --reload
```

### Erste Analyse

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Fehler P0300 – Zündaussetzer Zylinder 1. FIN: WDB906232N3123456. Techniker P12345.", "quelle": "OBD"}'
```

---

## Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                       Eingabedokument                           │
│         Wartungsprotokoll / OBD / QA / Produktionsauftrag       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1 – IntakeAgent                                          │
│                                                                 │
│  1. DSGVO-Sanitisierung                                         │
│     FIN → FIN_***XXXXXX   P12345 → PERS_ABCD1234               │
│     max@daimler.com → [EMAIL_ENTFERNT]                          │
│                                                                 │
│  2. Dokumenttyp-Erkennung (Regex-Patterns)                      │
│                                                                 │
│  3. KVTC-Kompression (4-Layer Sandwich, ~88% Reduktion)         │
└──────────────────────────┬──────────────────────────────────────┘
                           │  EingabeDokument + KVTCResult
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 2 – TriageAgent                                          │
│                                                                 │
│  Regex-Patterns + OBD-Datenbank (70+ Codes)                     │
│                                                                 │
│  🔴 P1_KRITISCH  →  Sofortige Eskalation                        │
│  🟠 P2_DRINGEND  →  Einplanung innerhalb 24h                    │
│  🟢 P3_ROUTINE   →  Nächste reguläre Inspektion                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │  TriageResult
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 3 – AnalysisAgent                                        │
│                                                                 │
│  SHA-256 LRU-Cache (256 Slots) → Cache Hit?                     │
│                                                                 │
│  LLM-Inferenz:                                                  │
│  🧪 Mock      – deterministisch, kein GPU/Netz                  │
│  🏠 Ollama    – lokal, Air-Gap-fähig, DSGVO-Maximum             │
│  ☁️  Anthropic – höchste Qualität, Prompt Caching               │
└──────────────────────────┬──────────────────────────────────────┘
                           │  Analyseergebnis (JSON)
                           ▼
              ┌────────────┴────────────┐
              │                         │
     Streamlit Dashboard          FastAPI REST
      (Port 8501)                  (Port 8000)
```

---

## KVTC-Algorithmus

**Key-Value-Type-Code (KVTC)** ist ein industrieller Token-Kompressions-Algorithmus, der Prozessdokumente in ein dichtes Frame-Format umwandelt.

### Sandwich-Zonen

```
Eingabe (~1000 Tokens)
│
├── Header-Zone (lossless)    – SOPs, Stammdaten, Referenznummern
├── Middle-Zone (aggressiv)   – nur Top 25% nach Informationsdichte
└── Window-Zone (lossless)    – aktuelle Diagnose / Messwerte

→ KVTC-Frame (~100–150 Tokens)
   K: Feldname1, Feldname2
   V: Wert1, Wert2
   T: DATE, NUMERIC, OBD_CODE
   C: P0300, SAP-12345, FIN_***ABC123
```

### Informationsdichte-Scoring

| Signal | Gewicht |
|--------|---------|
| OBD-Code (P0300, U0100 …) | **4.0×** |
| SAP-Auftragsnummer | **3.0×** |
| Numerischer Wert / Datum | **2.0×** |
| Key-Value-Paar | **1.5×** |
| Freitext | **1.0×** |

### Kompressionsraten (Real-World)

| Szenario | Original | Komprimiert | Reduktion |
|----------|----------|-------------|-----------|
| Wartungsprotokoll (4 Seiten) | 12.485 B | 1.240 B | **90%** |
| OBD-Fehlermeldung (1 Zeile) | 256 B | 82 B | **68%** |
| QA-Bericht (6 Seiten) | 18.932 B | 1.456 B | **92%** |
| Produktionsauftrag (2 Seiten) | 8.764 B | 1.089 B | **87%** |
| **Durchschnitt** | – | – | **~88%** |

---

## DSGVO Privacy by Design

Alle PII-Daten werden **vor** der LLM-Verarbeitung unwiderruflich anonymisiert (Art. 25 DSGVO – Privacy by Design & Default).

| Datentyp | Methode | Beispiel |
|----------|---------|---------|
| FIN / VIN (ISO 3779, 17 Zeichen) | Letzten 6 Zeichen behalten | `FIN_***ABC123` |
| Personalnummer (P/MA/EMP-Präfix) | SHA-256, 8 Zeichen | `PERS_A1B2C3D4` |
| E-Mail-Adressen | Vollständig entfernt | `[EMAIL_ENTFERNT]` |
| Telefonnummern | Vollständig entfernt | `[TEL_ENTFERNT]` |
| Kundenzeilen (Kunde:, Halter: …) | Vollständig entfernt | `[KUNDE_ENTFERNT]` |

```
SAP/MES ──→ IntakeAgent ──→ LLM
              │
              ├── WDB906232N3123456  →  FIN_***123456
              ├── P12345             →  PERS_A1B2C3D4
              ├── max@daimler.com    →  [EMAIL_ENTFERNT]
              └── +49 711 1234       →  [TEL_ENTFERNT]
```

> Das LLM sieht niemals Rohdaten. Nur das anonymisierte KVTC-Frame wird übertragen.

---

## OBD-Datenbank

70+ OBD/EOBD-Codes (SAE J2012 + ISO 14229-1) mit Schweregrad-Mapping:

| Priorität | Beispiel-Codes | Bedeutung |
|-----------|---------------|-----------|
| 🔴 P1_KRITISCH | P0300–P0306, U0073, U0100, C0110, B0001, P0524 | Zündaussetzer, CAN-Bus-Ausfall, Bremsventil, Airbag, Öldruck |
| 🟠 P2_DRINGEND | P0171, P0172, P0420, P0700, P229F, P20EE | Gemischfehler, Katalysator, Getriebe, AdBlue, SCR |
| 🟢 P3_ROUTINE | P0030, P1000, U0184 | Lambdasonde, OBD-Prüfung, Radio-Steuergerät |
| ⚪ Unbekannt | Alle anderen | Regex-Fallback → P3_ROUTINE |

---

## API-Referenz

Basis-URL: `http://localhost:8000` · Dokumentation: `/docs` (Swagger) · `/redoc`

### POST `/analyze`

Vollständige Pipeline: Intake → Triage → Analyse.

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Fehler P0300 – Zündaussetzer. FIN: WDB906232N3123456.",
    "quelle": "SAP"
  }'
```

```json
{
  "prioritaet": "P1_KRITISCH",
  "zusammenfassung": "Kritischer Zündaussetzer erkannt – sofortige Werkstatt erforderlich.",
  "empfohlene_massnahmen": ["Sofortige Diagnose", "Zündkerzen prüfen"],
  "konfidenz": 0.92,
  "tokens_original": 45,
  "tokens_komprimiert": 12,
  "bereinigungen": ["FIN maskiert"]
}
```

### POST `/batch/analyze`

Bis zu 10 Dokumente in einem Request, fehlertolerantes Verhalten pro Item.

```bash
curl -X POST http://localhost:8000/batch/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {"text": "P0300 – Zündaussetzer Zylinder 1", "quelle": "OBD"},
      {"text": "Routineinspektion km 80000", "quelle": "MES"},
      {"text": "Sperrung eingeleitet – Bremsanlage", "quelle": "QA"}
    ]
  }'
```

```json
{
  "total": 3,
  "succeeded": 3,
  "failed": 0,
  "results": [
    {"index": 0, "success": true, "result": {"prioritaet": "P1_KRITISCH"}},
    {"index": 1, "success": true, "result": {"prioritaet": "P3_ROUTINE"}},
    {"index": 2, "success": true, "result": {"prioritaet": "P1_KRITISCH"}}
  ]
}
```

### Weitere Endpunkte

| Methode | Pfad | Funktion |
|---------|------|----------|
| `POST` | `/compress` | Nur KVTC-Kompression |
| `POST` | `/triage` | Nur Prioritätsklassifizierung |
| `GET` | `/health` | Status + Cache-Statistiken |
| `GET` | `/benchmark` | Kompressionsrate messen |

---

## LLM-Backends

| Backend | Env-Var | Eigenschaften |
|---------|---------|--------------|
| `mock` | `LLM_BACKEND=mock` | Deterministisch, kein Netz, für Tests |
| `ollama_gemma` | `LLM_BACKEND=ollama_gemma` | Lokal, Air-Gap, DSGVO-Maximum |
| `anthropic` | `LLM_BACKEND=anthropic` | Höchste Qualität, Prompt Caching |

### Anthropic Prompt Caching

Der System-Prompt wird mit `cache_control: {"type": "ephemeral"}` markiert. Der Client wird als Lazy Singleton pro `AnalysisAgent`-Instanz erstellt. Spart bis zu 90% der Input-Token-Kosten bei wiederholten Anfragen.

---

## Performance

### Latenz (Docker, i7-11700K, 16 GB RAM)

| Operation | Backend | P50 | P95 | P99 |
|-----------|---------|-----|-----|-----|
| KVTC-Kompression | – | 12 ms | 18 ms | 25 ms |
| Triage (Regex+OBD) | – | 8 ms | 12 ms | 15 ms |
| Analyse | mock | 15 ms | 22 ms | 30 ms |
| Analyse | ollama_gemma | 850 ms | 1.200 ms | 1.800 ms |
| Analyse | anthropic | 320 ms | 580 ms | 1.200 ms |
| Batch (10 Docs) | mock | 150 ms | 220 ms | 300 ms |
| Cache Hit | – | 1 ms | 2 ms | 3 ms |

### Cache (LRU, 256 Slots)

- Hit-Rate (Produktion): ~35–45%
- Memory: ~8–12 MB
- Thread-Safety: getestet mit 10 parallelen Threads

---

## Konfiguration

Alle Einstellungen über Umgebungsvariablen, zentral in `config.py`:

| Variable | Standard | Beschreibung |
|----------|---------|-------------|
| `LLM_BACKEND` | `mock` | `mock` · `ollama_gemma` · `anthropic` |
| `OLLAMA_MODEL` | `gemma2:2b` | Ollama-Modell-ID |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama-Basis-URL |
| `ANTHROPIC_MODEL` | `claude-haiku-4-5-20251001` | Anthropic-Modell |
| `ANTHROPIC_API_KEY` | – | Pflicht bei anthropic-Backend |
| `ANTHROPIC_PROMPT_CACHE` | `true` | Ephemeral Prompt Caching |
| `MAX_TOKENS` | `512` | Max. Output-Tokens |
| `TEMPERATURE` | `0.1` | 0.0 = deterministisch |
| `CACHE_MAX_SIZE` | `256` | LRU-Cache-Slots |
| `KVTC_HEADER_LINES` | `10` | Lossless Header-Zone |
| `KVTC_WINDOW_LINES` | `15` | Lossless Window-Zone |
| `CORS_ORIGINS` | `` | Erlaubte Origins, kommagetrennt |
| `LOG_LEVEL` | `INFO` | `DEBUG` · `INFO` · `WARNING` |
| `LOG_FORMAT` | `json` | `json` (ELK-kompatibel) · `text` |

---

## Tests

```bash
# Alle 62 Tests
pytest tests/ -v

# Mit Coverage-Report
pytest tests/ -v --cov=src --cov-report=term-missing

# Einzelne Bereiche
pytest tests/test_kvtc.py -v          # Kompressionsalgorithmus
pytest tests/test_intake_agent.py -v  # DSGVO-Sanitisierung
pytest tests/test_triage_agent.py -v  # P1/P2/P3 Priorisierung
pytest tests/test_obd_database.py -v  # OBD-Datenbank
pytest tests/test_result_cache.py -v  # LRU-Cache + Thread-Safety
pytest tests/test_api_batch.py -v     # Batch-Endpunkt
```

**62 Tests · 0 Fehler · ~0.5 s Laufzeit**

---

## Docker

```bash
# Alles starten (Dashboard + API + Ollama)
docker-compose up

# Nur API
docker build -t comptext-daimler .
docker run -p 8000:8000 -e LLM_BACKEND=mock comptext-daimler

# Endpunkte
# Dashboard: http://localhost:8501
# API:       http://localhost:8000
# Swagger:   http://localhost:8000/docs
```

---

## Projektstruktur

```
Comptext-Daimler-Experiment-/
│
├── api.py                     # FastAPI REST (6 Endpunkte, Lifespan-Manager)
├── dashboard.py               # Streamlit Dashboard (3 Tabs + JSON/CSV-Export)
├── config.py                  # AppConfig (alle Env-Vars zentral)
├── requirements.txt
├── pyproject.toml             # Build + ruff + mypy + pytest
├── Dockerfile                 # Python 3.11-slim, non-root User
├── docker-compose.yml         # Dashboard + API + Ollama
│
├── src/
│   ├── agents/
│   │   ├── intake_agent.py    # DSGVO-Sanitisierung + KVTC
│   │   ├── triage_agent.py    # Regex + OBD-DB → P1/P2/P3
│   │   └── analysis_agent.py  # LLM-Dispatch + Prompt Caching
│   ├── core/
│   │   ├── kvtc.py            # IndustrialKVTCStrategy (4-Layer Sandwich)
│   │   ├── obd_database.py    # 70+ OBD-Codes + Schweregrad-Mapping
│   │   └── result_cache.py    # SHA-256 LRU-Cache (thread-sicher)
│   ├── models/
│   │   └── schemas.py         # Dataclasses + Enums
│   └── utils/
│       └── logging.py         # JSON Structured Logging (ELK/Azure)
│
├── tests/                     # 62 Tests, ~0.5 s
├── showcase/                  # React/Vite Präsentations-App
├── daimler_fleet/             # Fleet-Diagnose-Paket (eigenständig)
│
├── .github/workflows/ci.yml   # GitHub Actions (Python 3.11 + 3.12)
├── CLAUDE.md                  # Kontext für Claude Code
└── SECURITY.md                # Security-Disclosure-Policy
```

---

## Security

### Implementiert

- DSGVO Art. 25: Privacy-by-Design (PII verlässt nie das System als Klartext)
- SHA-256 für alle Hashes (kein MD5)
- Prompt-Injection-Schutz im `AnalysisAgent`
- CORS nur über explizite `CORS_ORIGINS` Env-Var (kein Wildcard `*`)
- FastAPI Lifespan-Manager für saubere Initialisierung
- Thread-sicherer LRU-Cache
- Non-root Docker-User

### Sicherheitslücken melden

Bitte **nicht** öffentlich als Issue melden. Security-Disclosures über GitHub [Security Advisories](https://github.com/ProfRandom92/comptext-daimler-experiment-/security/advisories/new).

---

## Verwandte Projekte

- [MedGemma-CompText](https://github.com/ProfRandom92/Medgemma-CompText) – Healthcare-Variante (Ursprung)
- [CompText-Monorepo-X](https://github.com/ProfRandom92/comptext-monorepo-X) – Ursprüngliches Framework
- [Ollama](https://ollama.ai) – Lokale LLM-Inferenz

---

## Lizenz

[Apache License 2.0](LICENSE) – kommerzielle Nutzung, Modifikation und Verteilung erlaubt. Lizenz- und Copyright-Hinweis erforderlich.

---

<div align="center">

**Daimler Buses CompText** · v0.2.0 · Apache 2.0

*Adaptiert aus [MedGemma-CompText](https://github.com/ProfRandom92/Medgemma-CompText) von ProfRandom92*

</div>
