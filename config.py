"""
Zentrale Konfiguration – Daimler Buses CompText
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from src.agents.analysis_agent import AnalysisConfig, ModelBackend


def _env_int(name: str, default: int, min_val: int = 1) -> int:
    raw = os.getenv(name, str(default))
    try:
        val = int(raw)
    except ValueError:
        raise ValueError(f"Env var {name}={raw!r} muss eine ganze Zahl sein") from None
    if val < min_val:
        raise ValueError(f"Env var {name}={val} muss ≥ {min_val} sein")
    return val


def _env_float(name: str, default: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    raw = os.getenv(name, str(default))
    try:
        val = float(raw)
    except ValueError:
        raise ValueError(f"Env var {name}={raw!r} muss eine Dezimalzahl sein") from None
    if not (min_val <= val <= max_val):
        raise ValueError(f"Env var {name}={val} muss zwischen {min_val} und {max_val} liegen")
    return val


@dataclass
class AppConfig:
    # LLM-Backend
    analysis: AnalysisConfig = field(
        default_factory=lambda: AnalysisConfig(
            backend=ModelBackend(os.getenv("LLM_BACKEND", ModelBackend.MOCK.value)),
            model_id=os.getenv("OLLAMA_MODEL", "gemma2:2b"),
            anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
            ollama_base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            max_tokens=_env_int("MAX_TOKENS", 512, min_val=1),
            temperature=_env_float("TEMPERATURE", 0.1, min_val=0.0, max_val=2.0),
        )
    )

    # KVTC-Zonen
    kvtc_header_lines: int = field(default_factory=lambda: _env_int("KVTC_HEADER_LINES", 10))
    kvtc_window_lines: int = field(default_factory=lambda: _env_int("KVTC_WINDOW_LINES", 15))

    # Dashboard
    dashboard_title: str = "Daimler Buses – Prozessautomatisierung CompText"
    dashboard_port: int = field(default_factory=lambda: _env_int("DASHBOARD_PORT", 8501, min_val=1024))

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


DEFAULT_CONFIG = AppConfig()
