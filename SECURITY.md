# 🔒 Security Policy

Datenschutz und Sicherheit sind für CompText Daimler Buses zentral. Diese Richtlinie beschreibt, wie wir mit Sicherheitsvulnerabilitäten umgehen.

---

## ✅ Unterstützte Versionen

| Version | Status | Support |
|---------|--------|---------|
| 2.0.x | ✅ **Aktuell** | Vollständige Unterstützung |
| 1.0.x | ⚠️ **Legacy** | Nur kritische Security-Fixes |
| < 1.0 | ❌ **End of Life** | Keine Unterstützung |

---

## 🛡️ Sicherheits-Features

### Implementiert & Getestet:
- ✅ **DSGVO Art. 25** – Privacy-by-Design Architektur
- ✅ **PII-Masking** – FIN, Personaldaten, E-Mails automatisch bereinigt
- ✅ **Input Validation** – Regex-Fuzzing für OBD-Codes
- ✅ **SQL-Injection-Schutz** – Kein direktes SQL (SQLite nur für Tests)
- ✅ **XSS-Prävention** – Dashboard-Inputs sanitisiert (Streamlit-native)
- ✅ **CSRF-Token** – FastAPI-Session-Security
- ✅ **Rate-Limiting (Roadmap)** – In v2.1 geplant
- ✅ **Secrets Rotation** – Anthropic API-Key aus Env-Variablen
- ✅ **Audit Logging** – Strukturierte Logs für ELK/Splunk

---

## 🚨 Vulnerability Disclosure Policy

### Wenn du eine Sicherheitslücke entdeckst:

**BITTE MELDE SIE NICHT ÖFFENTLICH!**

1. **E-Mail schreiben** an: `security@example.com`
   - Betreff: `[SECURITY] Vulnerability in CompText`
   - Beschreibe das Problem **deutlich aber nicht zu detailliert**
   - **KEIN Code oder PoC** in der E-Mail!

2. **Warte auf Bestätigung** (ca. 48 Stunden)
   - Wir werden die Anfälligkeit bestätigen
   - Dir einen Zeitplan zum Fixen mitteilen

3. **Koordinierte Offenlegung** (7 Tage)
   - Wir fixen die Vulnerability
   - Erstellen eine Sicherheits-Patch-Version
   - Publish ein Security Advisory

4. **Öffentliche Offenlegung** (Nach Patch-Release)
   - CVE-ID wird zugewiesen (falls schwer)
   - Advisory wird veröffentlicht
   - Danksagung im CHANGELOG

### Beispiel E-Mail:
```
Betreff: [SECURITY] Prompt Injection Vulnerability in AnalysisAgent

Hallo,

ich habe eine Prompt-Injection-Anfälligkeit in der analysis_agent.py gefunden:

Der _build_prompt() Methode sanitisiert KVTC-Frames nicht ausreichend, 
was es ermöglicht, System-Prompts zu überschreiben.

Auswirkung: Ein Angreifer könnte das LLM-Verhalten ändern.
Schweregrad: Mittel

Ich bin bereit zu warten, während ihr das fixt.

Beste Grüße,
[Dein Name]
```

---

## 📊 Bekannte Sicherheits-Limitations

| Limitation | Schweregrad | Auswirkung | Status |
|-----------|-----------|-----------|--------|
| MD5-Checksummen (LRU-Cache) | 🟢 Niedrig | Theoretische Hash-Kollision möglich | Geplant: SHA-256 (v2.1) |
| Keine Cache-TTL | 🟡 Mittel | Alte Ergebnisse nie invalidiert | Geplant: Redis-TTL (v2.1) |
| Regex False-Positives | 🟡 Mittel | Fake OBD-Codes können P1-Eskalation erzwingen | Testing: Improved Regex (v2.0.1) |
| LLM-Hallucination | 🟡 Mittel | Claude/Gemma erfinden Fehlercodes | Mitigated: Confidence Threshold |
| Batch-Endpoint Rate-Limit | 🟡 Mittel | DoS via 10 Docs × 1sec = 6 req/min limit | Geplant: IP-Rate-Limit (v2.1) |
| Token Leakage in Logs | 🟠 Erhöht | Debug-Logs könnten Inhalte zeigen | Mitigated: LOG_LEVEL=INFO (Prod) |

---

## 🔐 Best Practices für Benutzer

### Setup:
```bash
# ✅ Nutze .env für API-Keys (NIEMALS hardcoden!)
export ANTHROPIC_API_KEY="sk-ant-..."

# ✅ Nutze Mock-Backend für Tests
export LLM_BACKEND=mock

# ✅ Aktiviere Structured Logging
export LOG_FORMAT=json
export LOG_LEVEL=INFO  # Nicht DEBUG in Production
```

### Datenschutz:
- ✅ **Sanitisierung ist automatisch** – Keine zusätzliche Vorbereitung nötig
- ✅ **Überprüfe Logs** – In prod sollten keine PIIs sichtbar sein
- ✅ **Lokale Verarbeitung** – Ollama-Backend respektiert DSGVO
- ✅ **Anthropic API** – Claude ist SOC-2 zertifiziert

### API-Sicherheit:
```python
# ❌ Falsch: API-Key in Code
api_key = "sk-ant-abc123"

# ✅ Richtig: Env-Variable
import os
api_key = os.getenv("ANTHROPIC_API_KEY")
```

---

## 🧪 Security Testing

### Lokal durchgeführt:
```bash
# Bandit Security Scan
bandit -r src/ -ll

# Dependency Audit
safety check

# Type Checking (verhindert Injection-Fehler)
mypy src/ --strict

# Unit Tests (Edge-Cases)
pytest tests/ -v
```

### Externe Audits:
- [ ] DSGVO-Konformität-Audit (geplant Q2 2026)
- [ ] Penetration-Testing (geplant Q3 2026)
- [ ] CVE-Scanning (laufend mit dependabot)

---

## 📋 Sicherheits-Checkliste für Releases

Vor jedem Release durchführen:

```markdown
- [ ] CHANGELOG.md updated
- [ ] Keine Secrets in Code/Commits
- [ ] `bandit -r src/ -ll` passed
- [ ] `mypy src/ --strict` passed
- [ ] `pytest tests/ -v` 100% passing
- [ ] SECURITY.md updated (known issues)
- [ ] Dependencies aktualisiert (`pip-audit`)
- [ ] CVE-Scan passed
- [ ] Security Advisory draft (falls nötig)
```

---

## 🔄 Incident Response Process

### Wenn eine Vulnerability öffentlich bekannt wird:

1. **Sofort (< 2h)**
   - Team notifizieren
   - Affected Versions identifizieren
   - Patch beginnen

2. **Schnell (< 24h)**
   - Fix implementiert & tested
   - Security Advisory draft

3. **Release (< 48h)**
   - Patch-Version released (z.B. 2.0.1)
   - Advisory veröffentlicht
   - Users notifiziert

4. **Follow-up (1 Woche)**
   - Post-Mortem durchgeführt
   - Preventing measures implementiert

---

## 📞 Security Contact

- 📧 **Email**: `security@example.com`
- 🔐 **PGP Key**: `fingerprint...` (kommt noch)
- 🐛 **Issues**: Bitte nicht hier für Security-Themen (Public!)

---

## 📚 References

- [OWASP Top 10 2023](https://owasp.org/www-project-top-ten/)
- [DSGVO Art. 25 - Privacy by Design](https://gdpr-info.eu/art-25-gdpr/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [FastAPI Security](https://fastapi.tiangolo.com/deployment/security/)

---

**Zuletzt aktualisiert**: 2026-04-23  
**Status**: ✅ Production-Ready
