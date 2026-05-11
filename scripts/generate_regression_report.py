#!/usr/bin/env python3
"""Generate a conservative benchmark regression summary."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


METADATA_RE = re.compile(r"<!--\s*benchmark-metadata:\s*(\{.*?\})\s*-->")
SUMMARY_NAME = "regression-summary.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate docs/reports/regression-summary.md.")
    parser.add_argument("--reports-dir", default="docs/reports", help="Directory containing benchmark reports.")
    return parser.parse_args()


def load_benchmark_runs(reports_dir: Path) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for path in sorted(reports_dir.glob("benchmark-report-*.md")):
        match = METADATA_RE.search(path.read_text(encoding="utf-8", errors="replace"))
        if not match:
            continue
        try:
            metadata = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        metadata["path"] = path.as_posix()
        runs.append(metadata)
    return runs


def numeric(value: Any) -> float | None:
    if value in (None, "", "unavailable"):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().rstrip("%")
    try:
        return float(text)
    except ValueError:
        return None


def compare_latest_to_baseline(runs: list[dict[str, Any]]) -> tuple[str, list[str]]:
    if len(runs) < 2:
        return "insufficient baseline", ["Fewer than two benchmark reports are available; CI should warn only."]
    baseline, latest = runs[-2], runs[-1]
    messages: list[str] = []
    clear_regression = False
    thresholds = {"p95_ms": 25.0, "error_rate": 1.0}

    baseline_p95 = numeric(baseline.get("p95_ms"))
    latest_p95 = numeric(latest.get("p95_ms"))
    if baseline_p95 is None or latest_p95 is None or baseline_p95 <= 0:
        messages.append("p95 comparison unavailable; missing numeric baseline or latest values.")
    else:
        increase = ((latest_p95 - baseline_p95) / baseline_p95) * 100
        messages.append(f"p95 change versus previous run: {increase:.2f}%.")
        if increase >= thresholds["p95_ms"]:
            clear_regression = True

    baseline_error = numeric(baseline.get("error_rate"))
    latest_error = numeric(latest.get("error_rate"))
    if baseline_error is None or latest_error is None:
        messages.append("Error-rate comparison unavailable; missing numeric baseline or latest values.")
    else:
        increase = latest_error - baseline_error
        messages.append(f"Error-rate absolute change versus previous run: {increase:.2f} percentage points.")
        if increase >= thresholds["error_rate"] and latest_error > 1.0:
            clear_regression = True

    if clear_regression:
        return "clear regression candidate", messages
    return "no clear regression", messages


def write_summary(reports_dir: Path, runs: list[dict[str, Any]]) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    summary_path = reports_dir / SUMMARY_NAME
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    status, messages = compare_latest_to_baseline(runs)

    if runs:
        rows = []
        for run in runs:
            rows.append(
                "| {generated} | {status} | {host} | {endpoint} | {p50} | {p95} | {p99} | {rps} | {error} | {path} |".format(
                    generated=run.get("generated_at_utc", "unknown"),
                    status=run.get("status", "unknown"),
                    host=run.get("host", "unknown"),
                    endpoint=run.get("endpoint", "unknown"),
                    p50=run.get("p50_ms") or "unavailable",
                    p95=run.get("p95_ms") or "unavailable",
                    p99=run.get("p99_ms") or "unavailable",
                    rps=run.get("rps") or "unavailable",
                    error=run.get("error_rate") or "unavailable",
                    path=run.get("path", "unknown"),
                )
            )
        run_section = "\n".join(rows)
    else:
        run_section = "| No benchmark reports found. | | | | | | | | | |"
        messages = ["No benchmark reports were found; generate one with scripts/run_benchmarks.py when a synthetic test target is available."]

    message_lines = "\n".join(f"- {message}" for message in messages)
    summary_path.write_text(
        f"""# Regression Summary

Generated: {generated_at} UTC

## Conservative policy status

**Status:** {status}

{message_lines}

## Benchmark runs

| Generated | Status | Host | Endpoint | p50 | p95 | p99 | RPS | Error rate | Report |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
{run_section}

## Regression policy

- Fail only on clear regressions when comparable baseline data exists.
- Treat missing baselines, unavailable tools, and non-numeric metrics as insufficient baseline rather than failure.
- Prefer warning and human review when benchmark changes may be caused by CI noise or missing local services.
- Keep all benchmark inputs synthetic and exclude raw payloads, secrets, cookies, and customer data.
""",
        encoding="utf-8",
    )
    return summary_path


def main() -> int:
    args = parse_args()
    reports_dir = Path(args.reports_dir)
    runs = load_benchmark_runs(reports_dir) if reports_dir.exists() else []
    summary_path = write_summary(reports_dir, runs)
    print(f"Wrote regression summary: {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
