"""Compatibility wrapper for the local KVTC V7 engine."""

from __future__ import annotations

from typing import Any

from src.core.kvtc import KVTCResult
from src.core.kvtc_v7 import KVTCV7Engine


class KVTCV7Strategy:
    """Expose KVTC V7 through the same result shape as IndustrialKVTCStrategy."""

    def __init__(self, engine: KVTCV7Engine | None = None) -> None:
        self.engine = engine or KVTCV7Engine()

    def compress(self, text: str, context_metadata: dict[str, Any] | None = None) -> KVTCResult:
        result = self.engine.compress(text)
        frame = self.engine.serialize_frame(result.frame)
        metadata = {
            **result.metadata,
            "frame_type": result.frame_type,
            "event_count": result.event_count,
            "severity_counts": result.severity_counts,
        }
        if context_metadata:
            metadata["context"] = dict(sorted(context_metadata.items()))
        return KVTCResult(
            original_tokens=result.original_tokens,
            compressed_tokens=result.compressed_tokens,
            compression_ratio=result.compression_ratio,
            zones={"v7": result.frame},
            frame=frame,
            checksum=result.checksum,
            latency_ms=result.latency_ms,
            metadata=metadata,
        )

    def estimate_tokens(self, text: str) -> int:
        return self.engine.estimate_tokens(text)
