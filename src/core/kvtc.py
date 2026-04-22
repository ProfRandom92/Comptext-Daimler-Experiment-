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
from enum import Enum
from typing import Any


class CompressionZone(str, Enum):
    HEADER = "header"
    MIDDLE = "middle"
    WINDOW = "window"


@dataclass
class KVTCResult:
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    zones: dict[str, Any]
    frame: str                  # kompaktes DSL-Frame (serializeFrame)
    checksum: str
    latency_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def token_reduction_pct(self) -> float:
        return round((1 - self.compression_ratio) * 100, 2)


class IndustrialKVTCStrategy:
    """
    4-Layer KVTC Compression für industrielle Prozessdokumente.

    Übertrag aus CompText-Monorepo-X:
      - Key-Value-Type-Code Extraktion
      - serializeFrame() DSL
      - One-Way-Hash für vertrauliche Identifikatoren

    Tuning für Daimler Buses:
      - Wartungsprotokolle, OBD-Codes, QA-Berichte
      - Produktionsdaten, Arbeitspläne, Lieferscheine
    """

    _CHARS_PER_TOKEN = 4
    _MIDDLE_KEEP_RATIO = 0.25

    # Regex-Patterns für Code-Extraktion (Layer C)
    _OBD_PATTERN       = re.compile(r"\b[PBCU]\d{4}\b")
    _SAP_PATTERN       = re.compile(r"\b\d{7,10}\b")
    _FIN_FRAGMENT      = re.compile(r"\b[A-Z]{3}\d{6,8}\b")
    _DATE_PATTERN      = re.compile(r"\d{2}[.\-/]\d{2}[.\-/]\d{2,4}")
    _KV_PAIR           = re.compile(r"([\w\s]{2,30})\s*[:=]\s*(\S[^\n]*)")
    _NUMBER_PATTERN    = re.compile(r"\b\d+[\.,]?\d*\b")

    def __init__(
        self,
        header_lines: int = 10,
        window_lines: int = 15,
    ) -> None:
        self.header_lines = header_lines
        self.window_lines = window_lines

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compress(self, text: str, context_metadata: dict[str, Any] | None = None) -> KVTCResult:
        t0 = time.perf_counter()
        lines = text.splitlines()
        original_tokens = self._estimate_tokens(text)

        # Zone-Split
        header_lines, middle_lines, window_lines = self._split_zones(lines)

        compressed_header = "\n".join(header_lines)
        compressed_middle = self._compress_middle(middle_lines)
        compressed_window = "\n".join(window_lines)

        zones = {
            CompressionZone.HEADER: compressed_header,
            CompressionZone.MIDDLE: compressed_middle,
            CompressionZone.WINDOW: compressed_window,
        }

        full_compressed = "\n\n".join(
            f"[{zone.value.upper()}]\n{content}"
            for zone, content in zones.items()
            if content.strip()
        )

        # 4-Layer KVTC extraction
        kvtc_layers = self._extract_kvtc(full_compressed)

        # DSL Frame (aus Monorepo-X: serializeFrame)
        frame = self._serialize_frame(kvtc_layers, context_metadata or {})

        compressed_tokens = self._estimate_tokens(frame)
        ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0
        checksum = hashlib.md5(frame.encode()).hexdigest()
        latency_ms = (time.perf_counter() - t0) * 1000

        return KVTCResult(
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=round(ratio, 4),
            zones={k.value: v for k, v in zones.items()},
            frame=frame,
            checksum=checksum,
            latency_ms=round(latency_ms, 3),
            metadata=context_metadata or {},
        )

    def compress_structured(self, record: dict[str, Any]) -> KVTCResult:
        serialized = json.dumps(record, ensure_ascii=False, indent=2)
        return self.compress(serialized, context_metadata={"source": "structured_record"})

    # ------------------------------------------------------------------
    # 4-Layer KVTC Extraction
    # ------------------------------------------------------------------

    def _extract_kvtc(self, text: str) -> dict[str, list[str]]:
        """Extract Key / Value / Type / Code layers from compressed text."""
        keys, values, types, codes = [], [], [], []

        for match in self._KV_PAIR.finditer(text):
            k, v = match.group(1).strip(), match.group(2).strip()
            keys.append(k)
            values.append(v)
            types.append(self._classify_type(v))

        codes.extend(self._OBD_PATTERN.findall(text))
        codes.extend(self._SAP_PATTERN.findall(text))
        codes.extend(self._FIN_FRAGMENT.findall(text))

        return {
            "K": list(dict.fromkeys(keys)),       # deduplicated
            "V": list(dict.fromkeys(values)),
            "T": list(dict.fromkeys(types)),
            "C": list(dict.fromkeys(codes)),
        }

    def _classify_type(self, value: str) -> str:
        if self._DATE_PATTERN.search(value):
            return "DATE"
        if self._OBD_PATTERN.search(value):
            return "OBD_CODE"
        if re.fullmatch(r"[\d.,\s]+", value.strip()):
            return "NUMERIC"
        if value.isupper() and len(value) <= 20:
            return "ENUM"
        return "TEXT"

    # ------------------------------------------------------------------
    # serializeFrame – DSL Output (adapted from Monorepo-X)
    # ------------------------------------------------------------------

    def _serialize_frame(
        self, layers: dict[str, list[str]], meta: dict[str, Any]
    ) -> str:
        """
        Produces a compact pipe-delimited DSL frame, e.g.:
          K:Modell,Kilometerstand|V:Tourismo,125000|T:TEXT,NUMERIC|C:P0300,U0100
        """
        parts = []
        for layer_key, items in layers.items():
            if items:
                parts.append(f"{layer_key}:{','.join(str(i) for i in items[:20])}")

        if meta:
            meta_str = ";".join(f"{k}={v}" for k, v in list(meta.items())[:5])
            parts.append(f"M:{meta_str}")

        return "|".join(parts)

    # ------------------------------------------------------------------
    # Zone helpers
    # ------------------------------------------------------------------

    def _split_zones(
        self, lines: list[str]
    ) -> tuple[list[str], list[str], list[str]]:
        total = len(lines)
        h = min(self.header_lines, total)
        w = min(self.window_lines, total - h)
        w = max(w, 0)
        m_end = total - w

        header = lines[:h]
        middle = lines[h:m_end] if m_end > h else []
        window = lines[m_end:] if w > 0 else []
        return header, middle, window

    def _compress_middle(self, lines: list[str]) -> str:
        if not lines:
            return ""

        scored = [(self._information_density(line), line) for line in lines]
        scored.sort(key=lambda x: x[0], reverse=True)

        keep_n = max(1, int(len(scored) * self._MIDDLE_KEEP_RATIO))
        kept_lines = [line for _, line in scored[:keep_n]]

        original_order = {line: idx for idx, line in enumerate(lines)}
        kept_lines.sort(key=lambda l: original_order.get(l, 0))

        return "\n".join(kept_lines)

    def _information_density(self, line: str) -> float:
        if not line.strip():
            return 0.0

        score = 0.0
        score += len(self._NUMBER_PATTERN.findall(line)) * 2.0
        score += len(self._OBD_PATTERN.findall(line)) * 4.0
        score += len(self._SAP_PATTERN.findall(line)) * 3.0
        score += len(self._KV_PAIR.findall(line)) * 1.5
        score += len(self._DATE_PATTERN.findall(line)) * 2.0

        if len(line.strip()) < 10:
            score *= 0.5
        return score

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return max(1, len(text) // IndustrialKVTCStrategy._CHARS_PER_TOKEN)


# ---------------------------------------------------------------------------
# Pipeline with Benchmarking (from Monorepo-X pattern)
# ---------------------------------------------------------------------------

def run_benchmark(test_cases: list[dict[str, str]]) -> dict[str, Any]:
    """Run KVTC compression over a list of test cases and return aggregate metrics."""
    strategy = IndustrialKVTCStrategy()
    results = []

    for case in test_cases:
        r = strategy.compress(case["text"], context_metadata={"label": case.get("label", "")})
        results.append({
            "label": case.get("label", ""),
            "original_tokens": r.original_tokens,
            "compressed_tokens": r.compressed_tokens,
            "reduction_pct": r.token_reduction_pct,
            "latency_ms": r.latency_ms,
            "checksum": r.checksum,
        })

    avg_reduction = sum(r["reduction_pct"] for r in results) / len(results) if results else 0
    avg_latency   = sum(r["latency_ms"]    for r in results) / len(results) if results else 0

    return {
        "cases": results,
        "avg_token_reduction_pct": round(avg_reduction, 2),
        "avg_latency_ms": round(avg_latency, 3),
        "total_cases": len(results),
    }
