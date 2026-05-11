"""Dependency-light KVTC V7 compression engine.

This module is a local, deterministic adaptation of the Comptext V7 idea for the
Daimler experiment repository. It intentionally stores only synthetic-safe
metadata (counts, categories, hashes, and frame statistics) in the compressed
frame rather than raw input lines.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

FrameType = Literal["micro-frame", "sandwich-frame"]

_SEVERITY_PATTERN = re.compile(r"\b(CRITICAL|ERROR|ERR|WARN(?:ING)?|INFO|DEBUG|TRACE)\b", re.IGNORECASE)
_OBD_PATTERN = re.compile(r"\b[PBCU]\d{4}\b")
_KEY_VALUE_PATTERN = re.compile(r"\b([A-Za-z_][\w .\-/]{1,32})\s*[:=]")
_TIMESTAMP_PATTERN = re.compile(
    r"\b(?:\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}|\d{2}[./-]\d{2}[./-]\d{2,4})\b"
)
_NUMERIC_PATTERN = re.compile(r"\b\d+(?:[.,]\d+)?\b")
_WHITESPACE_PATTERN = re.compile(r"\s+")


@dataclass(frozen=True)
class StructuredLogEvent:
    """Sanitized event summary used inside a KVTC V7 frame."""

    index: int
    severity: str
    fingerprint: str
    token_estimate: int
    code_count: int = 0
    numeric_count: int = 0
    key_count: int = 0
    has_timestamp: bool = False


@dataclass(frozen=True)
class CompressionResult:
    """Raw V7 compression output before repository compatibility mapping."""

    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    frame_type: FrameType
    frame: dict[str, Any]
    checksum: str
    latency_ms: float
    event_count: int
    severity_counts: dict[str, int] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def token_reduction_pct(self) -> float:
        return round((1 - self.compression_ratio) * 100, 2)


class KVTCV7Engine:
    """Deterministic KVTC V7 compressor for synthetic benchmark/demo data.

    V7 favors structured, low-risk frame metadata over payload retention:
    * very short inputs become a compact ``micro-frame``;
    * longer inputs become a ``sandwich-frame`` with header/window summaries and
      a middle aggregate;
    * each event is represented by a stable fingerprint and safe counters.
    """

    _CHARS_PER_TOKEN = 4

    def __init__(self, micro_frame_token_threshold: int = 12, header_events: int = 3, window_events: int = 3) -> None:
        self.micro_frame_token_threshold = micro_frame_token_threshold
        self.header_events = header_events
        self.window_events = window_events

    def compress(self, text: str) -> CompressionResult:
        t0 = time.perf_counter()
        normalized = self._normalize_text(text)
        original_tokens = self.estimate_tokens(text)
        events = self._extract_events(normalized)
        severity_counts = self._count_severities(events)
        frame_type: FrameType = "micro-frame" if original_tokens <= self.micro_frame_token_threshold else "sandwich-frame"
        frame = self._build_micro_frame(normalized, events, severity_counts) if frame_type == "micro-frame" else self._build_sandwich_frame(normalized, events, severity_counts)
        serialized = self.serialize_frame(frame)
        compressed_tokens = self.estimate_tokens(serialized)
        ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0
        checksum = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        return CompressionResult(
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=round(ratio, 4),
            frame_type=frame_type,
            frame=frame,
            checksum=checksum,
            latency_ms=round((time.perf_counter() - t0) * 1000, 3),
            event_count=len(events),
            severity_counts=severity_counts,
            metadata={
                "engine": "kvtc-v7-local",
                "payload_policy": "no-raw-lines",
                "source_repository": "ProfRandom92/Comptextv7",
            },
        )

    def _build_micro_frame(
        self, text: str, events: list[StructuredLogEvent], severity_counts: dict[str, int]
    ) -> dict[str, Any]:
        return {
            "version": "7-local",
            "frame_type": "micro-frame",
            "payload_policy": "no-raw-lines",
            "text_fingerprint": self._fingerprint(text),
            "char_count": len(text),
            "event_count": len(events),
            "severity_counts": severity_counts,
            "signals": self._signal_counts(text),
        }

    def _build_sandwich_frame(
        self, text: str, events: list[StructuredLogEvent], severity_counts: dict[str, int]
    ) -> dict[str, Any]:
        header = events[: self.header_events]
        window = events[-self.window_events :] if self.window_events else []
        middle = events[self.header_events : len(events) - self.window_events if self.window_events else len(events)]
        return {
            "version": "7-local",
            "frame_type": "sandwich-frame",
            "payload_policy": "no-raw-lines",
            "fingerprint": self._fingerprint(text),
            "event_count": len(events),
            "severity_counts": severity_counts,
            "signals": self._signal_counts(text),
            "zones": {
                "header": [asdict(event) for event in header],
                "middle": self._summarize_middle(middle),
                "window": [asdict(event) for event in window],
            },
        }

    def _extract_events(self, text: str) -> list[StructuredLogEvent]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines and text.strip():
            lines = [text.strip()]
        return [self._event_from_line(index, line) for index, line in enumerate(lines)]

    def _event_from_line(self, index: int, line: str) -> StructuredLogEvent:
        severity_match = _SEVERITY_PATTERN.search(line)
        severity = self._normalize_severity(severity_match.group(1) if severity_match else "INFO")
        return StructuredLogEvent(
            index=index,
            severity=severity,
            fingerprint=self._fingerprint(line),
            token_estimate=self.estimate_tokens(line),
            code_count=len(_OBD_PATTERN.findall(line)),
            numeric_count=len(_NUMERIC_PATTERN.findall(line)),
            key_count=len(_KEY_VALUE_PATTERN.findall(line)),
            has_timestamp=bool(_TIMESTAMP_PATTERN.search(line)),
        )

    def _summarize_middle(self, events: list[StructuredLogEvent]) -> dict[str, Any]:
        return {
            "event_count": len(events),
            "severity_counts": self._count_severities(events),
            "code_count": sum(event.code_count for event in events),
            "numeric_count": sum(event.numeric_count for event in events),
            "key_count": sum(event.key_count for event in events),
            "timestamp_count": sum(1 for event in events if event.has_timestamp),
            "fingerprint": self._fingerprint("|".join(event.fingerprint for event in events)),
        }

    @staticmethod
    def _signal_counts(text: str) -> dict[str, int]:
        return {
            "obd_codes": len(_OBD_PATTERN.findall(text)),
            "key_values": len(_KEY_VALUE_PATTERN.findall(text)),
            "numbers": len(_NUMERIC_PATTERN.findall(text)),
            "timestamps": len(_TIMESTAMP_PATTERN.findall(text)),
        }

    @staticmethod
    def _count_severities(events: list[StructuredLogEvent]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for event in events:
            counts[event.severity] = counts.get(event.severity, 0) + 1
        return dict(sorted(counts.items()))

    @staticmethod
    def _normalize_severity(value: str) -> str:
        severity = value.upper()
        if severity in {"ERR", "ERROR"}:
            return "ERROR"
        if severity in {"WARN", "WARNING"}:
            return "WARN"
        if severity in {"CRITICAL", "DEBUG", "TRACE", "INFO"}:
            return severity
        return "INFO"

    @staticmethod
    def _normalize_text(text: str) -> str:
        return "\n".join(_WHITESPACE_PATTERN.sub(" ", line.strip()) for line in text.splitlines()).strip()

    @staticmethod
    def _fingerprint(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        return max(1, len(text) // cls._CHARS_PER_TOKEN)

    @staticmethod
    def serialize_frame(frame: dict[str, Any]) -> str:
        return json.dumps(frame, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
