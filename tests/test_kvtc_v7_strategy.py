"""Tests for optional KVTC V7 compression strategy."""

from __future__ import annotations

import json

from src.core.kvtc_v7_strategy import KVTCV7Strategy


def test_v7_compression_is_deterministic():
    strategy = KVTCV7Strategy()
    text = "2026-05-11T08:02:00 ERROR code=P0300 module=engine value=91"

    first = strategy.compress(text)
    second = strategy.compress(text)

    assert first.frame == second.frame
    assert first.checksum == second.checksum
    assert first.original_tokens == second.original_tokens
    assert first.compressed_tokens == second.compressed_tokens


def test_v7_frame_is_deterministic_json_without_raw_line():
    strategy = KVTCV7Strategy()
    text = "2026-05-11T08:02:00 WARN code=P0300 module=engine"
    result = strategy.compress(text)

    parsed = json.loads(result.frame)
    assert parsed["payload_policy"] == "no-raw-lines"
    assert result.frame == json.dumps(parsed, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert text not in result.frame


def test_v7_diagnostic_metadata_includes_severity_counts():
    strategy = KVTCV7Strategy()
    text = "\n".join(
        [
            "2026-05-11T08:00:00 INFO bus=demo event=start",
            "2026-05-11T08:01:00 WARN sensor=temp value=91",
            "2026-05-11T08:02:00 ERROR code=P0300 module=engine",
        ]
    )

    result = strategy.compress(text)

    assert result.metadata["event_count"] == 3
    assert result.metadata["severity_counts"]["ERROR"] == 1
    assert result.metadata["severity_counts"]["WARN"] == 1


def test_v7_very_short_input_uses_micro_frame():
    strategy = KVTCV7Strategy()

    result = strategy.compress("OK")
    parsed = json.loads(result.frame)

    assert parsed["frame_type"] == "micro-frame"
    assert result.original_tokens >= 1
    assert result.compressed_tokens >= 1
