# CLAUDE.md – Daimler Buses CompText

Dieses Dokument beschreibt alles, was Claude Code über dieses Repository wissen muss.

---

## Projektübersicht

**Comptext-Daimler-Experiment** ist eine industrielle KI-Pipeline für Daimler Buses. Sie verarbeitet Prozessdokumente (Wartungsprotokolle, OBD-Fehlercodes, QA-Berichte, Produktionsaufträge) in drei Schritten:

1. **DSGVO-Sanitisierung** – PII (FIN, Personalnummern, E-Mails) wird maskiert/gehasht
2. **KVTC-Kompression** – proprietärer 4-Layer-Algorithmus, ~88% Token-Reduktion
3. **LLM-Analyse** – lokale (Ollama Gemma) oder Cloud-LLM (Claude Haiku) Inferenz

Das Projekt ist ein Port von [MedGemma-CompText](https://github.com/ProfRandom92/Medgemma-CompText) (medizinisch) auf den industriellen Automotive-Kontext.

---

## Repository-Struktur

```
Comptext-Daimler-Experiment-/
├── api.py                        # FastAPI REST-Einstiegspunkt (6 Endpunkte)
├── dashboard.py                  # Streamlit Dashboard (3 Tabs)
├── config.py                     # AppConfig – alle Env-Vars zentral
├── requirements.txt              # Runtime-Dependencies
├── pyproject.toml                # Build, ruff, mypy, pytest Konfiguration
├── Dockerfile                    # Python 3.11-slim, non-root User
├── docker-compose.yml            # Dashboard + API + Ollama
│
├── src/
│   ├── agents/
│   │   ├── intake_agent.py       # Layer 1: DSGVO-Sanitisierung + KVTC
│   │   ├── triage_agent.py       # Layer 2: P1/P2/P3 Priorisierung per Regex + OBD-DB
│   │   └── analysis_agent.py     # Layer 3: LLM-Dispatch + Prompt Caching
│   ├── core/
│   │   ├── kvtc.py               # IndustrialKVTCStrategy (Sandwich-Kompression)
│   │   ├── obd_database.py       # 70+ OBD-Codes mit Schweregrad-Mapping
│   │   └── result_cache.py       # Thread-sicherer LRU-Cache (OrderedDict + Lock)
│   ├── models/
│   │   └── schemas.py            # Alle Dataclasses und Enums
│   └── utils/
│       └── logging.py            # JSON Structured Logging (ELK-kompatibel)
│
├── tests/
│   ├── test_kvtc.py              # 8 Tests – Kompressionsalgorithmus
│   ├── test_intake_agent.py      # 11 Tests – Sanitisierung + Typ-Erkennung
│   ├── test_triage_agent.py      # 10 Tests – P1/P2/P3 Priorisierung
│   ├── test_analysis_agent.py    # 4 Tests – LLM-Dispatch + Mock
│   ├── test_obd_database.py      # 13 Tests – OBD-Lookup
│   ├── test_result_cache.py      # 9 Tests – LRU-Cache + Thread-Safety
│   └── test_api_batch.py         # 7 Tests – Batch-Endpunkt + Health
│
├── showcase/                     # React/Vite Präsentations-App (Daimler Video-Call)
└── daimler_fleet/                # Eigenständiges Fleet-Diagnose-Paket (Python)
```

---

## Befehle

### Tests ausführen
```bash
pytest tests/ -v
pytest tests/ -v --cov=src --cov-report=term-missing
pytest tests/test_kvtc.py -v              # Einzelne Test-Datei
```

### Linting & Formatting
```bash
ruff check .                              # Linting prüfen
ruff check . --fix                        # Auto-Fix
ruff format .                             # Formatierung
```

### API starten
```bash
uvicorn api:app --reload                  # Development (Port 8000)
uvicorn api:app --host 0.0.0.0 --port 8000  # Production
```

### Dashboard starten
```bash
streamlit run dashboard.py               # Port 8501
```

### Docker
```bash
docker-compose up                        # Alles inkl. Ollama
docker build -t comptext-daimler .
```

---

## Umgebungsvariablen

| Variable | Standard | Werte |
|----------|---------|-------|
| `LLM_BACKEND` | `mock` | `mock` · `ollama_gemma` · `anthropic` |
| `OLLAMA_MODEL` | `gemma2:2b` | Ollama-Modell-ID |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama-Basis-URL |
| `ANTHROPIC_MODEL` | `claude-haiku-4-5-20251001` | Anthropic-Modell-ID |
| `ANTHROPIC_API_KEY` | – | Pflicht für anthropic-Backend |
| `ANTHROPIC_PROMPT_CACHE` | `true` | Ephemeral Prompt Caching |
| `MAX_TOKENS` | `512` | Max. Output-Tokens |
| `TEMPERATURE` | `0.1` | Niedrig = deterministisch |
| `CACHE_MAX_SIZE` | `256` | LRU-Cache-Slots |
| `KVTC_HEADER_LINES` | `10` | Lossless Header-Zone |
| `KVTC_WINDOW_LINES` | `15` | Lossless Window-Zone |
| `CORS_ORIGINS` | `` | Erlaubte Origins (kommagetrennt) |
| `LOG_LEVEL` | `INFO` | `DEBUG` · `INFO` · `WARNING` |
| `LOG_FORMAT` | `json` | `json` · `text` |

---

## Architektur & Datenfluss

```
Rohdokument
    │
    ▼
IntakeAgent (src/agents/intake_agent.py)
  • DSGVO: FIN → FIN_***XXXXXX, P12345 → PERS_ABCD1234, E-Mails/Tel entfernt
  • Typ-Erkennung: WARTUNGSPROTOKOLL / OBD_FEHLERCODE / QA_PRUEFBERICHT / ...
  • KVTC-Kompression: 4-Layer Sandwich (~88% Token-Reduktion)
    │
    ▼
TriageAgent (src/agents/triage_agent.py)
  • Regex + OBD-Datenbank (70+ Codes)
  • Klassifizierung: P1_KRITISCH / P2_DRINGEND / P3_ROUTINE
    │
    ▼
AnalysisAgent (src/agents/analysis_agent.py)
  • LRU-Cache-Lookup (result_cache.py)
  • LLM-Inferenz: mock | ollama_gemma | anthropic
  • Anthropic: ephemeral Prompt Caching aktiviert
    │
    ▼
Analyseergebnis (JSON)
  • zusammenfassung, empfohlene_massnahmen, konfidenz, tokens_original/komprimiert
```

---

## Wichtige Implementierungsdetails

### KVTC-Algorithmus (`src/core/kvtc.py`)
- **Sandwich-Zonen**: Header (lossless) → Middle (aggressiv, Top-25%-Dichte) → Window (lossless)
- **4-Layer Frame**: K (Feldnamen) · V (Werte) · T (Typen) · C (Codes)
- **Dichte-Scoring**: OBD-Code=4.0×, SAP=3.0×, Numerisch=2.0×, KV-Paar=1.5×, Freitext=1.0×
- Checksum im Frame: SHA-256 (nicht MD5 – Sicherheitsanforderung)

### DSGVO-Sanitisierung (`src/agents/intake_agent.py`)
- FIN (ISO 3779, 17 Zeichen): letzte 6 Zeichen behalten → `FIN_***XXXXXX`
- Personalnummern mit Präfix P/MA/EMP: SHA-256-Hash (8 Zeichen) → `PERS_ABCD1234`
- E-Mails, Telefonnummern, Kundenzeilen: vollständig entfernt
- **Wichtig**: Keine rohen Ziffernfolgen maskieren (verursacht Falsch-Positive bei Datum/Mengen)

### LRU-Cache (`src/core/result_cache.py`)
- Thread-sicher via `threading.Lock`
- `OrderedDict` für O(1) LRU-Eviction
- Cache-Key: SHA-256 des komprimierten KVTC-Frames

### Anthropic-Integration (`src/agents/analysis_agent.py`)
- Client als Lazy Singleton pro `AnalysisAgent`-Instanz
- Ephemeral Prompt Caching: `cache_control: {"type": "ephemeral"}` auf System-Prompt
- Modell: `claude-haiku-4-5-20251001` (Standard, konfigurierbar)

### API (`api.py`)
- FastAPI mit Lifespan-Manager für saubere Agent-Initialisierung
- CORS über `CORS_ORIGINS` Env-Var (leer = kein Allow, nicht `*`)
- Singleton-Agents werden einmalig beim Start erzeugt
- Endpunkte: `POST /analyze` · `POST /batch/analyze` · `POST /compress` · `POST /triage` · `GET /health` · `GET /benchmark`

---

## Branches (aktiv)

| Branch | Inhalt |
|--------|--------|
| `main` | Stabiler Stand, 9 Commits |
| `claude/analyze-consolidate-branches-6FDmr` | Entwicklungs-Branch (aktuell) |
| `claude/daimler-showcase-video-NPnWG` | React Showcase-App (`showcase/`) |
| `claude/setup-project-structure-gUJZh` | Fleet-Diagnose-Paket (`daimler_fleet/`) |
| `claude/comptext-security-hardening-CQpYW` | Security-Fixes (SHA-256, Prompt-Injection) |

---

## Code-Konventionen

- **Python 3.11+**, Type Hints überall
- **ruff** für Linting + Formatting (`line-length = 110`)
- **Imports**: `from __future__ import annotations` in allen Modulen
- **Dataclasses** für Konfiguration und Ergebnisse (keine Dicts durchreichen)
- **Enums** als `StrEnum` (Python 3.11)
- **Logging**: immer `get_logger("comptext.<modul>")` aus `src/utils/logging.py`
- **Keine `print()`** in Produktionscode – nur `log.info()` / `log.warning()` etc.
- **Keine rohen Dicts** als Rückgabewerte von Agenten – Dataclasses verwenden
- Tests nutzen Mock-Backend (`LLM_BACKEND=mock`), kein echter API-Key nötig

---

## Bekannte Einschränkungen

- `dashboard.py` läuft nicht in Termux (kein Streamlit-Support) – REST-API funktioniert
- Batch-Endpunkt: max. 10 Dokumente pro Request
- OBD-Regex kann False-Positives bei unbekannten Codes erzeugen (Fallback auf `P3_ROUTINE`)
- `showcase/` benötigt Node.js 18+ (`npm install && npm run dev`)
