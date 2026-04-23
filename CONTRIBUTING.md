# 🤝 Contributing to CompText Daimler Buses

Vielen Dank für das Interesse, zu diesem Projekt beizutragen! Diese Richtlinien helfen uns, ein professionelles und sicheres Projekt zu pflegen.

---

## 📋 Code of Conduct

- ✅ Sei respektvoll und konstruktiv
- ✅ Fokussiere auf die Sache, nicht die Person
- ✅ Begrüße unterschiedliche Meinungen
- ✅ Halte dich an Datenschutz und Sicherheitsrichtlinien

---

## 🐛 Bug Reports

### Bevor du einen Bug reportierst:
1. **Suchbereich durchsuchen**: [Issues](https://github.com/ProfRandom92/comptext-daimler-experiment-/issues) durchsuchen
2. **Debug-Logs aktivieren**: `LOG_LEVEL=DEBUG python -m pytest`
3. **Minimales Reproduzierbares Beispiel (MRE) erstellen**

### Bug-Report Template:
```markdown
## Beschreibung
Kurzbeschreibung des Problems

## Reproduzierschritte
1. ...
2. ...
3. ...

## Erwartetes Verhalten
Was sollte passieren?

## Aktuelles Verhalten
Was passiert tatsächlich?

## Umgebung
- Python-Version: `python --version`
- OS: Linux/MacOS/Windows
- Backend: mock/ollama_gemma/anthropic
- `pip freeze > env.txt`

## Logs
```bash
LOG_LEVEL=DEBUG streamlit run dashboard.py
# ... copy output here ...
```

## Lösungsideen (optional)
```

---

## 💡 Feature Requests

### Feature-Request Template:
```markdown
## Beschreibung
Klare Beschreibung der neuen Funktionalität

## Motivation
Warum ist diese Funktion wichtig?

## Beispiel-Verwendung
```python
# Zeige, wie die Funktion verwendet würde
```

## Zusammenhang mit anderen Features
Welche bestehenden Features sind verwandt?

## Implementation Notes
Erste Ideen zur Umsetzung
```

---

## 🚀 Pull Requests

### Branching-Strategie

```
main (Production-Ready)
  └─ feature/FEATURE-NAME (Neue Features)
  └─ bugfix/BUG-NAME (Bug-Fixes)
  └─ docs/DOC-NAME (Dokumentation)
  └─ refactor/AREA-NAME (Code-Qualität)
```

### Vor einem PR:

1. **Fork & Clone**
   ```bash
   git clone https://github.com/YOUR-USERNAME/comptext-daimler-experiment-.git
   cd comptext-daimler-experiment-
   git checkout -b feature/my-awesome-feature
   ```

2. **Install Dev Dependencies**
   ```bash
   make install-dev
   ```

3. **Code schreiben & Tests**
   ```bash
   # Dein Code
   make lint-fix
   make format
   make audit
   ```

4. **Commit mit aussagekräftiger Nachricht**
   ```bash
   git commit -m "feat: Add awesome feature

   - Implement X functionality
   - Improve Y performance
   - Fix Z edge case
   
   Closes #123"
   ```

   **Commit-Message Format:**
   - `feat:` Neue Features
   - `fix:` Bug-Fixes
   - `docs:` Dokumentation
   - `refactor:` Code-Umstrukturierung
   - `test:` Test-Ergänzungen
   - `chore:` Dependencies, Tooling

5. **Tests bestätigen**
   ```bash
   make test
   make mypy
   make security-check
   ```

6. **Push & Create PR**
   ```bash
   git push origin feature/my-awesome-feature
   ```
   → GitHub zeigt auto "Create Pull Request" Button

### PR-Checklist:

```markdown
## PR Description
- [ ] Kurze Zusammenfassung des Changes
- [ ] Verlinke relevante Issue (#123)
- [ ] Beschreibe Breaking Changes (falls vorhanden)

## Tests
- [ ] Neue Tests für neue Funktionalität
- [ ] Alle existierenden Tests bestehen (`make test`)
- [ ] Coverage > 80% für neue Code-Zeilen

## Code Quality
- [ ] Linting bestanden (`make lint`)
- [ ] Type-Checking bestanden (`make mypy`)
- [ ] Code formatiert (`make format`)
- [ ] Keine Security-Warnings (`make security-check`)

## Documentation
- [ ] README updated (falls nötig)
- [ ] CHANGELOG.md updated
- [ ] Docstrings/Comments hinzugefügt (wo sinnvoll)

## Security
- [ ] Keine Secrets/API-Keys in Code
- [ ] DSGVO-Anforderungen berücksichtigt (falls PII-Handling)
- [ ] Injection/XSS-Anfälligkeit überprüft
```

---

## 🔧 Development Setup

### Mit Makefile (recommended):
```bash
make install-dev      # Install dependencies
make dev              # Run dashboard (Mock Mode)
make dev-api          # Run API server
make test             # Run all tests
make audit            # Full audit: lint + test + type-check
```

### Manuell:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install pytest pytest-cov mypy ruff black

# Development
streamlit run dashboard.py

# Testing
pytest tests/ -v --cov=src
```

---

## 📚 Code Style

### Python Style Guide
- **PEP 8** mit folgende Modifikationen:
  - Line Length: **100 Zeichen** (nicht 79)
  - String Quotes: **doppelt** (`"string"` nicht `'string'`)
  - Type Hints: **Mandatory** für Funktionssignaturen

### Beispiel:
```python
"""
Module description.
"""

from __future__ import annotations

from typing import Any
from dataclasses import dataclass

@dataclass
class Example:
    """Description of this class."""
    
    value: int
    
    def process(self, input_data: str) -> dict[str, Any]:
        """
        Brief description.
        
        Args:
            input_data: Description
            
        Returns:
            Dictionary with results
        """
        return {"result": len(input_data)}
```

### Tools:
```bash
make lint              # Ruff linter
make format            # Black formatter
make mypy              # Type checking
```

---

## 🧪 Testing Requirements

### Neue Features MÜSSEN Tests haben:

```python
# tests/test_my_feature.py

import pytest
from src.core.my_module import MyClass

class TestMyFeature:
    def test_basic_functionality(self):
        """Test X works correctly."""
        obj = MyClass()
        assert obj.method() == expected
    
    def test_edge_case_empty_input(self):
        """Test handling of empty input."""
        obj = MyClass()
        assert obj.method("") == expected
    
    def test_error_handling(self):
        """Test error cases."""
        obj = MyClass()
        with pytest.raises(ValueError):
            obj.method("invalid")
```

### Test-Abdeckung:
```bash
make test-cov          # Generate coverage report
# Minimum: 80% für neue Code-Zeilen
```

---

## 🔒 Security Guidelines

### Beim Handling von Sensitive Data:
- [ ] Keine FIN/VIN vollständig loggen
- [ ] Keine Personaldaten speichern
- [ ] Keine E-Mails/Telefonnummern in Logs
- [ ] Env-Variablen für API-Keys nutzen

### Sicherheits-Vulnerabilities:
**BITTE NICHT öffentlich melden!**

Schreib eine Private E-Mail zu: **security@example.com**
- Beschreibe die Vulnerability
- Poste KEINEN Proof-of-Concept öffentlich
- Gib uns 7 Tage Zeit zum Fixen

---

## 📖 Documentation

### Beim Hinzufügen neuer Features:

1. **Docstring** im Code:
   ```python
   def analyze(self, document: str) -> AnalysisResult:
       """
       Analyze document with 3-agent pipeline.
       
       Args:
           document: Raw text to analyze
           
       Returns:
           AnalysisResult with priority and recommendations
           
       Raises:
           ValueError: If document is empty
       """
   ```

2. **Update README.md** (falls öffentliche API)

3. **Update CHANGELOG.md**:
   ```markdown
   ### [X.Y.Z] - YYYY-MM-DD
   - feat: Add new feature
   - fix: Fix bug
   ```

4. **API-Docs** (Swagger/OpenAPI auto-generiert in FastAPI)

---

## 🤔 Community & Support

- 💬 **Discussions**: https://github.com/ProfRandom92/comptext-daimler-experiment-/discussions
- 🐛 **Issues**: https://github.com/ProfRandom92/comptext-daimler-experiment-/issues
- 📧 **Direct Contact**: Siehe README

---

## 📜 Lizenz

Indem du zu diesem Projekt beiträgst, stimmst du zu, dass deine Beiträge unter der [Apache 2.0 License](LICENSE) lizenziert werden.

---

## ✅ Danke!

Danke für dein Interesse und deinen Beitrag zu CompText! 🚀

*Dein Beitrag wird von der Community geschätzt.*
