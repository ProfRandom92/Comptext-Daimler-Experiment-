"""
AnalysisAgent – LLM-Inferenz für industrielle Prozessanalyse
Entspricht dem DoctorAgent aus MedGemma-CompText.

Modell-Unterstützung:
  - Gemma 2B / 7B via Ollama (lokaler Edge-Betrieb, kein Cloud-Zwang)
  - Claude Sonnet/Haiku via Anthropic API (höhere Qualität)
  - Mock-Modus für Tests und Demos

Input:  KVTCResult (komprimiertes Frame) + TriageResult (Priorität)
Output: Analyseergebnis (Zusammenfassung, Maßnahmen, Konfidenz)
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from src.core.kvtc import KVTCResult
from src.models.schemas import Analyseergebnis, DocumentType, EingabeDokument, ProcessPriority
from src.agents.triage_agent import TriageResult


class ModelBackend(str, Enum):
    OLLAMA_GEMMA  = "ollama_gemma"
    ANTHROPIC     = "anthropic"
    MOCK          = "mock"


@dataclass
class AnalysisConfig:
    backend: ModelBackend = ModelBackend.MOCK
    model_id: str = "gemma2:2b"           # Ollama-Modellname
    anthropic_model: str = "claude-haiku-4-5-20251001"
    ollama_base_url: str = "http://localhost:11434"
    max_tokens: int = 512
    temperature: float = 0.1              # Niedrig = deterministischer Output


_SYSTEM_PROMPT = """\
Du bist ein Expertenassistent für Prozessautomatisierung bei Daimler Buses.
Analysiere das folgende komprimierte Prozessdokument und antworte AUSSCHLIEẞLICH als JSON.

JSON-Schema:
{
  "zusammenfassung": "string (max 3 Sätze)",
  "massnahmen": ["Maßnahme 1", "Maßnahme 2", ...],
  "erkannte_fehlercodes": ["P0300", ...],
  "konfidenz": 0.0-1.0,
  "prioritaet_bestaetigung": "P1_KRITISCH|P2_DRINGEND|P3_ROUTINE"
}

Fokus: Predictive Maintenance, Qualitätssicherung, Produktionsoptimierung.
Keine Kundendaten, keine persönlichen Informationen im Output.
"""


class AnalysisAgent:
    """
    LLM-basierte Analyse des komprimierten KVTC-Frames.
    Nutzt entweder lokales Gemma (Ollama) oder Claude API.
    """

    def __init__(self, config: AnalysisConfig | None = None) -> None:
        self._config = config or AnalysisConfig()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def analyze(
        self,
        dokument: EingabeDokument,
        kvtc: KVTCResult,
        triage: TriageResult,
    ) -> Analyseergebnis:
        t0 = time.perf_counter()

        prompt = self._build_prompt(dokument, kvtc, triage)

        raw_output = self._infer(prompt)
        parsed     = self._parse_output(raw_output, triage.prioritaet)

        latenz_ms = (time.perf_counter() - t0) * 1000

        return Analyseergebnis(
            eingabe_checksum=kvtc.checksum,
            prioritaet=parsed.get("prioritaet", triage.prioritaet),
            zusammenfassung=parsed.get("zusammenfassung", ""),
            massnahmen=parsed.get("massnahmen", []),
            erkannte_fehlercodes=parsed.get("erkannte_fehlercodes", []),
            konfidenz=float(parsed.get("konfidenz", 0.7)),
            modell_id=self._config.model_id,
            latenz_ms=round(latenz_ms, 3),
            rohausgabe=raw_output,
            token_original=kvtc.original_tokens,
            token_komprimiert=kvtc.compressed_tokens,
        )

    # ------------------------------------------------------------------
    # Prompt Construction
    # ------------------------------------------------------------------

    def _build_prompt(
        self,
        dokument: EingabeDokument,
        kvtc: KVTCResult,
        triage: TriageResult,
    ) -> str:
        return (
            f"DOKUMENT-TYP: {dokument.doc_type.value}\n"
            f"PRIORITÄT (Triage): {triage.prioritaet.value}\n"
            f"TRIAGE-BEGRÜNDUNG: {triage.begruendung}\n"
            f"KOMPRIMIERTES FRAME:\n{kvtc.frame}\n\n"
            f"ZONE WINDOW (aktuell):\n{kvtc.zones.get('window', '')}\n\n"
            "Erstelle eine strukturierte JSON-Analyse."
        )

    # ------------------------------------------------------------------
    # Inference backends
    # ------------------------------------------------------------------

    def _infer(self, prompt: str) -> str:
        if self._config.backend == ModelBackend.MOCK:
            return self._mock_infer(prompt)
        if self._config.backend == ModelBackend.OLLAMA_GEMMA:
            return self._ollama_infer(prompt)
        if self._config.backend == ModelBackend.ANTHROPIC:
            return self._anthropic_infer(prompt)
        return self._mock_infer(prompt)

    def _mock_infer(self, prompt: str) -> str:
        """Deterministischer Mock für Tests und Demos."""
        priority = "P3_ROUTINE"
        if "P1_KRITISCH" in prompt:
            priority = "P1_KRITISCH"
        elif "P2_DRINGEND" in prompt:
            priority = "P2_DRINGEND"

        return json.dumps({
            "zusammenfassung": (
                "Mock-Analyse: Das Dokument wurde verarbeitet. "
                "Keine kritischen Muster erkannt (Mock-Modus). "
                "Bitte Produktionsmodus für reale Analyse aktivieren."
            ),
            "massnahmen": [
                "Dokument archivieren",
                "Nächste planmäßige Inspektion einhalten",
            ],
            "erkannte_fehlercodes": [],
            "konfidenz": 0.5,
            "prioritaet_bestaetigung": priority,
        }, ensure_ascii=False)

    def _ollama_infer(self, prompt: str) -> str:
        try:
            import requests  # type: ignore
            response = requests.post(
                f"{self._config.ollama_base_url}/api/generate",
                json={
                    "model": self._config.model_id,
                    "prompt": f"{_SYSTEM_PROMPT}\n\n{prompt}",
                    "stream": False,
                    "options": {
                        "temperature": self._config.temperature,
                        "num_predict": self._config.max_tokens,
                    },
                },
                timeout=60,
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            return json.dumps({
                "zusammenfassung": f"Ollama-Fehler: {e}",
                "massnahmen": [],
                "erkannte_fehlercodes": [],
                "konfidenz": 0.0,
                "prioritaet_bestaetigung": "P3_ROUTINE",
            })

    def _anthropic_infer(self, prompt: str) -> str:
        try:
            import anthropic  # type: ignore
            client = anthropic.Anthropic()
            message = client.messages.create(
                model=self._config.anthropic_model,
                max_tokens=self._config.max_tokens,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except Exception as e:
            return json.dumps({
                "zusammenfassung": f"Anthropic-API-Fehler: {e}",
                "massnahmen": [],
                "erkannte_fehlercodes": [],
                "konfidenz": 0.0,
                "prioritaet_bestaetigung": "P3_ROUTINE",
            })

    # ------------------------------------------------------------------
    # Output Parsing
    # ------------------------------------------------------------------

    def _parse_output(
        self, raw: str, fallback_priority: ProcessPriority
    ) -> dict[str, Any]:
        import re
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not json_match:
            return {
                "zusammenfassung": raw[:300],
                "massnahmen": [],
                "erkannte_fehlercodes": [],
                "konfidenz": 0.3,
                "prioritaet": fallback_priority,
            }

        try:
            data = json.loads(json_match.group(0))
            prio_str = data.get("prioritaet_bestaetigung", fallback_priority.value)
            try:
                data["prioritaet"] = ProcessPriority(prio_str)
            except ValueError:
                data["prioritaet"] = fallback_priority
            return data
        except json.JSONDecodeError:
            return {
                "zusammenfassung": raw[:300],
                "massnahmen": [],
                "erkannte_fehlercodes": [],
                "konfidenz": 0.2,
                "prioritaet": fallback_priority,
            }
