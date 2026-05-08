"""
Telemetry – TinybirdTracker für CompText Industrial Endpoints.
Sendet Token-Metriken an Tinybird Events API (fire-and-forget).
"""

from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import requests

from src.utils.logging import get_logger

log = get_logger("comptext.telemetry")

_TINYBIRD_URL  = "https://api.tinybird.co/v0/events"
_TINYBIRD_TOKEN = os.getenv("TINYBIRD_TOKEN", "")
_TIMEOUT_SEC   = 2.0


class TinybirdTracker:
    """Fire-and-forget telemetry tracker. Sendet keine Daimler-spezifischen Rohdaten."""

    def __init__(self, datasource: str = "comptext_metrics") -> None:
        self._datasource = datasource
        self._enabled    = bool(_TINYBIRD_TOKEN)
        self._executor   = ThreadPoolExecutor(max_workers=4)
        if not self._enabled:
            log.info("TinybirdTracker disabled – TINYBIRD_TOKEN not set")

    def track(
        self,
        endpoint: str,
        original_tokens: int,
        compressed_tokens: int,
        savings_percentage: float,
        latency_ms: float = 0.0,
        extra: dict[str, Any] | None = None,
    ) -> bool:
        """
        Queues a telemetry event. Returns True if successfully queued.
        Never raises – failures are logged silently.
        """
        if not self._enabled:
            return False

        payload: dict[str, Any] = {
            "endpoint":           endpoint,
            "original_tokens":    original_tokens,
            "compressed_tokens":  compressed_tokens,
            "savings_percentage": round(savings_percentage, 4),
            "latency_ms":         round(latency_ms, 2),
            "timestamp":          int(time.time() * 1000),
        }
        if extra:
            # Sanitise: never forward raw text or PII fields
            safe_keys = {"doc_type", "quelle_system", "scenario", "priority"}
            payload.update({k: v for k, v in extra.items() if k in safe_keys})

        self._executor.submit(self._send, payload)
        return True

    def _send(self, payload: dict[str, Any]) -> None:
        try:
            ndjson = __import__("json").dumps(payload, ensure_ascii=False)
            resp = requests.post(
                _TINYBIRD_URL,
                params={"name": self._datasource, "token": _TINYBIRD_TOKEN},
                data=ndjson,
                headers={"Content-Type": "application/json"},
                timeout=_TIMEOUT_SEC,
            )
            if resp.status_code >= 300:
                log.warning("Tinybird non-2xx", extra={"status": resp.status_code})
        except Exception:
            log.debug("Tinybird send failed (non-critical)")


# Module-level singleton
tracker = TinybirdTracker()
