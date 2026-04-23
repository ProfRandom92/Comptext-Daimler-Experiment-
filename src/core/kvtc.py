"""
KVTC (Key-Value-Type-Code) Compression – Industrial Edition
Adapted from MedGemma-CompText / CompText-Monorepo-X for Daimler Buses.

4-Layer architecture (from Monorepo-X):
  K (Key)   → Feldbezeichner extrahieren
  V (Value) → Feldwerte extrahieren
  T (Type)  → Datentypkategorien (Zahl, Code, Text, Datum)
  C (Code)  → Strukturierte Codes (OBD, SAP-Nr, FIN-Fragmente)

Sandwich-Zonen:
  Header → Lossless  (SOPs, Fahrzeugstammdaten, Systemkontext)
  Middle → Aggressiv (Historische Wartungseinträge, alte Produktionsdaten)
  Window → Lossless  (Aktuelle Diagnosedaten, offene Aufträge)
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class CompressionZone(StrEnum):
    HEADER = "header"
    MIDDLE = "middle"
    WINDOW = "window"


@dataclass
class KVTCResult:
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    zones: dict[str, Any]
    frame: str
    checksum: str
    latency_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def token_reduction_pct(self) -> float:
        return round((1 - self.compression_ratio) * 100, 2)


# Module-level compiled patterns (fix: was re-compiled per call in _classify_type)
_OBD_PATTERN    = re.compile(r"\b[PBCU]\d{4}\b")
_SAP_PATTERN    = re.compile(r"\b\d{7,10}\b")
_FIN_FRAGMENT   = re.compile(r"\b[A-Z]{3}\d{6,8}\b")
_DATE_PATTERN   = re.compile(r"\d{2}[.\-/]\d{2}[.\-/]\d{2,4}")
_KV_PAIR        = re.compile(r"([\w\s]{2,30})\s*[:=]\s*(\S[^\n]*)")
_NUMBER_PATTERN = re.compile(r"\b\d+[\.,]?\d*\b")
_NUMERIC_VALUE  = re.compile(r"^[\d.,\s]+$")


class IndustrialKVTCStrategy:
    _CHARS_PER_TOKEN  = 4
    _MIDDLE_KEEP_RATIO = 0.25

    def __init__(self, header_lines: int = 10, window_lines: int = 15) -> None:
        self.header_lines = header_lines
        self.window_lines = window_lines

    def compress(self, text: str, context_metadata: dict[str, Any] | None = None) -> KVTCResult:
        t0 = time.perf_counter()
        lines = text.splitlines()
        original_tokens = self._estimate_tokens(text)

        header_lines, middle_lines, window_lines = self._split_zones(lines)

        # Build zones with string keys directly (fix: was built twice, once with enum keys)
        zones = {
            CompressionZone.HEADER.value: "\n".join(header_lines),
            CompressionZone.MIDDLE.value: self._compress_middle(middle_lines),
            CompressionZone.WINDOW.value: "\n".join(window_lines),
        }

        full_compressed = "\n\n".join(
            f"[{zone.upper()}]\n{content}"
            for zone, content in zones.items()
            if content.strip()
        )

        frame = self._serialize_frame(self._extract_kvtc(full_compressed), context_metadata or {})
        compressed_tokens = self._estimate_tokens(frame)
        ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0

        return KVTCResult(
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=round(ratio, 4),
            zones=zones,
            frame=frame,
            checksum=hashlib.md5(frame.encode()).hexdigest(),
            latency_ms=round((time.perf_counter() - t0) * 1000, 3),
            metadata=context_metadata or {},
        )

    def compress_structured(self, record: dict[str, Any]) -> KVTCResult:
        return self.compress(
            json.dumps(record, ensure_ascii=False, indent=2),
            context_metadata={"source": "structured_record"},
        )

    def _extract_kvtc(self, text: str) -> dict[str, list[str]]:
        keys, values, types = [], [], []
        for match in _KV_PAIR.finditer(text):
            k, v = match.group(1).strip(), match.group(2).strip()
            keys.append(k)
            values.append(v)
            types.append(self._classify_type(v))

        codes = (
            _OBD_PATTERN.findall(text)
            + _SAP_PATTERN.findall(text)
            + _FIN_FRAGMENT.findall(text)
        )

        return {
            "K": list(dict.fromkeys(keys)),
            "V": list(dict.fromkeys(values)),
            "T": list(dict.fromkeys(types)),
            "C": list(dict.fromkeys(codes)),
        }

    @staticmethod
    def _classify_type(value: str) -> str:
        if _DATE_PATTERN.search(value):
            return "DATE"
        if _OBD_PATTERN.search(value):
            return "OBD_CODE"
        if _NUMERIC_VALUE.match(value.strip()):  # fix: was re.fullmatch() compiled per call
            return "NUMERIC"
        if value.isupper() and len(value) <= 20:
            return "ENUM"
        return "TEXT"

    def _serialize_frame(self, layers: dict[str, list[str]], meta: dict[str, Any]) -> str:
        parts = [
            f"{layer_key}:{','.join(str(i) for i in items[:20])}"
            for layer_key, items in layers.items()
            if items
        ]
        if meta:
            parts.append("M:" + ";".join(f"{k}={v}" for k, v in list(meta.items())[:5]))
        return "|".join(parts)

    def _split_zones(self, lines: list[str]) -> tuple[list[str], list[str], list[str]]:
        total = len(lines)
        h = min(self.header_lines, total)
        w = max(min(self.window_lines, total - h), 0)
        m_end = total - w
        return lines[:h], (lines[h:m_end] if m_end > h else []), (lines[m_end:] if w > 0 else [])

    def _compress_middle(self, lines: list[str]) -> str:
        if not lines:
            return ""
        scored = sorted(
            ((self._information_density(line), line) for line in lines),
            key=lambda x: x[0],
            reverse=True,
        )
        keep_n = max(1, int(len(scored) * self._MIDDLE_KEEP_RATIO))
        original_order = {line: idx for idx, line in enumerate(lines)}
        kept = sorted(
            (line for _, line in scored[:keep_n]),
            key=lambda line: original_order.get(line, 0),
        )
        return "\n".join(kept)

    @staticmethod
    def _information_density(line: str) -> float:
        stripped = line.strip()
        if not stripped:
            return 0.0
        score = (
            len(_NUMBER_PATTERN.findall(line)) * 2.0
            + len(_OBD_PATTERN.findall(line))  * 4.0
            + len(_SAP_PATTERN.findall(line))  * 3.0
            + len(_KV_PAIR.findall(line))       * 1.5
            + len(_DATE_PATTERN.findall(line))  * 2.0
        )
        return score * 0.5 if len(stripped) < 10 else score

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return max(1, len(text) // IndustrialKVTCStrategy._CHARS_PER_TOKEN)


def run_benchmark(test_cases: list[dict[str, str]]) -> dict[str, Any]:
    strategy = IndustrialKVTCStrategy()
    results = [
        {
            "label": case.get("label", ""),
            "original_tokens": r.original_tokens,
            "compressed_tokens": r.compressed_tokens,
            "reduction_pct": r.token_reduction_pct,
            "latency_ms": r.latency_ms,
            "checksum": r.checksum,
        }
        for case in test_cases
        for r in [strategy.compress(case["text"], context_metadata={"label": case.get("label", "")})]
    ]
    count = len(results)
    return {
        "cases": results,
        "avg_token_reduction_pct": round(sum(r["reduction_pct"] for r in results) / count, 2) if count else 0,
        "avg_latency_ms": round(sum(r["latency_ms"] for r in results) / count, 3) if count else 0,
        "total_cases": count,
    }
