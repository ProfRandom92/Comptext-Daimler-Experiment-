"""
Strukturiertes Logging für Daimler Buses CompText.
JSON-Format für Log-Aggregation (ELK, Azure Monitor, etc.).
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts":      datetime.now(timezone.utc).isoformat(),
            "level":   record.levelname,
            "logger":  record.name,
            "msg":     record.getMessage(),
            "module":  record.module,
            "line":    record.lineno,
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        if hasattr(record, "extra"):
            payload.update(record.extra)  # type: ignore[attr-defined]
        return json.dumps(payload, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    fmt = os.getenv("LOG_FORMAT", "json")
    handler.setFormatter(_JsonFormatter() if fmt == "json" else logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s – %(message)s"
    ))

    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, level, logging.INFO))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


# Convenience: module-level root logger for the application
log = get_logger("comptext.daimler")
