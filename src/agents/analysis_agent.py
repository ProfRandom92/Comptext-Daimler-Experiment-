"""
AnalysisAgent – LLM-Inferenz für industrielle Prozessanalyse
Entspricht dem DoctorAgent aus MedGemma-CompText.

Modell-Unterstützung:
  - Gemma 2B / 7B via Ollama (lokaler Edge-Betrieb, kein Cloud-Zwang)
  - Claude Haiku/Sonnet via Anthropic API (höhere Qualität)
  - Mock-Modus für Tests und Demos
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from src.agents.triage_agent import TriageResult
from src.core.kvtc import KVTCResult
from src.models.schemas import Analyseergebnis, EingabeDokument, ProcessPriority


class ModelBackend(StrEnum):
    OLLAMA_GEMMA = "ollama_gemma"
    ANTHROPIC    = "anthropic"
    MOCK         = "mock"


@dataclass
class AnalysisConfig:
    backend: ModelBackend = ModelBackend.MOCK
    model_id: str = "gemma2:2b"
    anthropic_model: str = "claude-haiku-4-5-20251001"
    ollama_base_url: str = "http://localhost:11434"
    max_tokens: int = 512
    temperature: float = 0.1  # low = deterministic; LLMs for process docs should not hallucinate


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

# Module-level compiled patterns (fix: was compiled inside _parse_output per call)
_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)

_ERROR_PAYLOAD: dict[str, Any] = {
    "massnahmen": [],
    "erkannte_fehlercodes": [],
    "konfidenz": 0.0,
    "prioritaet_bestaetigung": ProcessPriority.P3_ROUTINE.value,
}


def _error_response(message: str) -> str:
    return json.dumps({**_ERROR_PAYLOAD, "zusammenfassung": message}, ensure_ascii=False)


class AnalysisAgent:
    def __init__(self, config: AnalysisConfig | None = None) -> None:
        self._config = config or AnalysisConfig()

    def analyze(
        self,
        dokument: EingabeDokument,
        kvtc: KVTCResult,
        triage: TriageResult,
    ) -> Analyseergebnis:
        t0 = time.perf_counter()
        raw_output = self._infer(self._build_prompt(dokument, kvtc, triage))
        parsed = self._parse_output(raw_output, triage.prioritaet)

        return Analyseergebnis(
            eingabe_checksum=kvtc.checksum,
            prioritaet=parsed.get("prioritaet", triage.prioritaet),
            zusammenfassung=parsed.get("zusammenfassung", ""),
            massnahmen=parsed.get("massnahmen", []),
            erkannte_fehlercodes=parsed.get("erkannte_fehlercodes", []),
            konfidenz=float(parsed.get("konfidenz", 0.7)),
            modell_id=self._config.model_id,
            latenz_ms=round((time.perf_counter() - t0) * 1000, 3),
            rohausgabe=raw_output,
            token_original=kvtc.original_tokens,
            token_komprimiert=kvtc.compressed_tokens,
        )

    def _build_prompt(self, dokument: EingabeDokument, kvtc: KVTCResult, triage: TriageResult) -> str:
        return (
            f"DOKUMENT-TYP: {dokument.doc_type.value}\n"
            f"PRIORITÄT (Triage): {triage.prioritaet.value}\n"
            f"TRIAGE-BEGRÜNDUNG: {triage.begruendung}\n"
            f"KOMPRIMIERTES FRAME:\n{kvtc.frame}\n\n"
            f"ZONE WINDOW (aktuell):\n{kvtc.zones.get('window', '')}\n\n"
            "Erstelle eine strukturierte JSON-Analyse."
        )

    def _infer(self, prompt: str) -> str:
        dispatch = {
            ModelBackend.MOCK:         self._mock_infer,
            ModelBackend.OLLAMA_GEMMA: self._ollama_infer,
            ModelBackend.ANTHROPIC:    self._anthropic_infer,
        }
        return dispatch.get(self._config.backend, self._mock_infer)(prompt)

    def _mock_infer(self, prompt: str) -> str:
        # Priority propagation: reflect triage result in mock output
        if ProcessPriority.P1_KRITISCH.value in prompt:
            prio = ProcessPriority.P1_KRITISCH.value
        elif ProcessPriority.P2_DRINGEND.value in prompt:
            prio = ProcessPriority.P2_DRINGEND.value
        else:
            prio = ProcessPriority.P3_ROUTINE.value

        return json.dumps({
            "zusammenfassung": (
                "Mock-Analyse: Das Dokument wurde verarbeitet. "
                "Keine kritischen Muster erkannt (Mock-Modus). "
                "Bitte Produktionsmodus für reale Analyse aktivieren."
            ),
            "massnahmen": ["Dokument archivieren", "Nächste planmäßige Inspektion einhalten"],
            "erkannte_fehlercodes": [],
            "konfidenz": 0.5,
            "prioritaet_bestaetigung": prio,
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
                    "options": {"temperature": self._config.temperature, "num_predict": self._config.max_tokens},
                },
                timeout=60,
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            return _error_response(f"Ollama-Fehler: {e}")

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
            return _error_response(f"Anthropic-API-Fehler: {e}")

    def _parse_output(self, raw: str, fallback_priority: ProcessPriority) -> dict[str, Any]:
        match = _JSON_BLOCK.search(raw)
        if not match:
            return {"zusammenfassung": raw[:300], "massnahmen": [], "erkannte_fehlercodes": [],
                    "konfidenz": 0.3, "prioritaet": fallback_priority}
        try:
            data = json.loads(match.group(0))
            prio_str = data.get("prioritaet_bestaetigung", fallback_priority.value)
            data["prioritaet"] = ProcessPriority(prio_str) if prio_str in ProcessPriority._value2member_map_ else fallback_priority
            return data
        except json.JSONDecodeError:
            return {"zusammenfassung": raw[:300], "massnahmen": [], "erkannte_fehlercodes": [],
                    "konfidenz": 0.2, "prioritaet": fallback_priority}
