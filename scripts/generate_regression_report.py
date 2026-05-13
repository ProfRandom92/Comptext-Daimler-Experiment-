#!/usr/bin/env python3
"""Generate conservative Markdown and JSON benchmark regression summaries."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SOURCE_REPO = "ProfRandom92/Comptext-Daimler-Experiment-"
TARGET_REPO = "downstream-runtime"
METADATA_RE = re.compile(r"<!--\s*benchmark-metadata:\s*(\{.*?\})\s*-->")
SUMMARY_NAME = "regression-summary.md"
JSON_SUMMARY_NAME = "regression-summary.json"
THRESHOLDS = {
    "p95_latency_increase_percent": 25.0,
    "error_rate_increase_percentage_points": 1.0,
    "latest_error_rate_minimum_percent": 1.0,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate docs/reports/regression-summary.md and regression-summary.json.")
    parser.add_argument("--reports-dir", default="docs/reports", help="Directory containing benchmark reports.")
    return parser.parse_args()


def utc_iso_timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


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


def compared_run(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_at": run.get("generated_at_utc", "unknown"),
        "status": run.get("status", "unknown"),
        "endpoint": run.get("endpoint", "unknown"),
        "p95_ms": numeric(run.get("p95_ms")),
        "error_rate": numeric(run.get("error_rate")),
        "report_path": run.get("path", "unknown"),
    }


def compare_latest_to_baseline(runs: list[dict[str, Any]]) -> tuple[str, bool, list[str]]:
    if len(runs) < 2:
        return "insufficient_baseline", False, ["Fewer than two benchmark reports are available; CI should warn only."]
    baseline, latest = runs[-2], runs[-1]
    messages: list[str] = []
    clear_regression = False

    baseline_p95 = numeric(baseline.get("p95_ms"))
    latest_p95 = numeric(latest.get("p95_ms"))
    if baseline_p95 is None or latest_p95 is None or baseline_p95 <= 0:
        messages.append("p95 comparison unavailable; missing numeric baseline or latest values.")
    else:
        increase = ((latest_p95 - baseline_p95) / baseline_p95) * 100
        messages.append(f"p95 change versus previous run: {increase:.2f}%.")
        if increase >= THRESHOLDS["p95_latency_increase_percent"]:
            clear_regression = True

    baseline_error = numeric(baseline.get("error_rate"))
    latest_error = numeric(latest.get("error_rate"))
    if baseline_error is None or latest_error is None:
        messages.append("Error-rate comparison unavailable; missing numeric baseline or latest values.")
    else:
        increase = latest_error - baseline_error
        messages.append(f"Error-rate absolute change versus previous run: {increase:.2f} percentage points.")
        if (
            increase >= THRESHOLDS["error_rate_increase_percentage_points"]
            and latest_error > THRESHOLDS["latest_error_rate_minimum_percent"]
        ):
            clear_regression = True

    if clear_regression:
        return "clear_regression_candidate", True, messages
    return "no_clear_regression", False, messages


def build_json_summary(generated_at: str, runs: list[dict[str, Any]], decision: str, regression_detected: bool, notes: list[str]) -> dict[str, Any]:
    if len(runs) >= 2:
        compared_runs = [compared_run(runs[-2]), compared_run(runs[-1])]
    else:
        compared_runs = [compared_run(run) for run in runs]
    return {
        "source_repo": SOURCE_REPO,
        "target_repo": TARGET_REPO,
        "report_type": "regression_summary",
        "synthetic": True,
        "generated_at": generated_at,
        "baseline_available": len(runs) >= 2,
        "regression_detected": regression_detected,
        "compared_runs": compared_runs,
        "thresholds": THRESHOLDS,
        "decision": decision,
        "notes": notes,
    }


def write_summary(reports_dir: Path, runs: list[dict[str, Any]]) -> tuple[Path, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    summary_path = reports_dir / SUMMARY_NAME
    json_summary_path = reports_dir / JSON_SUMMARY_NAME
    generated_at = utc_iso_timestamp()
    decision, regression_detected, messages = compare_latest_to_baseline(runs)

    if runs:
        rows = []
        for run in runs:
            rows.append(
                "| {generated} | {status} | {host} | {endpoint} | {p50} | {p95} | {p99} | {rps} | {error} | {path} |".format(
                    generated=run.get("generated_at_utc", "unknown"),
                    status=run.get("status", "unknown"),
                    host=run.get("host", "unknown"),
                    endpoint=run.get("endpoint", "unknown"),
                    p50=run.get("p50_ms") if run.get("p50_ms") is not None else "unavailable",
                    p95=run.get("p95_ms") if run.get("p95_ms") is not None else "unavailable",
                    p99=run.get("p99_ms") if run.get("p99_ms") is not None else "unavailable",
                    rps=run.get("rps") if run.get("rps") is not None else "unavailable",
                    error=run.get("error_rate") if run.get("error_rate") is not None else "unavailable",
                    path=run.get("path", "unknown"),
                )
            )
        run_section = "\n".join(rows)
    else:
        run_section = "| No benchmark reports found. | | | | | | | | | |"
        messages = ["No benchmark reports were found; generate one with scripts/run_benchmarks.py when a synthetic test target is available."]
        decision = "insufficient_baseline"
        regression_detected = False

    message_lines = "\n".join(f"- {message}" for message in messages)
    summary_path.write_text(
        f"""# Regression Summary

Generated: {generated_at} UTC

## Conservative policy status

**Decision:** {decision}

{message_lines}

## Contract-compatible JSON summary

This run also writes `docs/reports/{JSON_SUMMARY_NAME}` for machine-readable contract validation.

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
    json_summary_path.write_text(
        json.dumps(build_json_summary(generated_at, runs, decision, regression_detected, messages), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary_path, json_summary_path


def main() -> int:
    args = parse_args()
    reports_dir = Path(args.reports_dir)
    runs = load_benchmark_runs(reports_dir) if reports_dir.exists() else []
    summary_path, json_summary_path = write_summary(reports_dir, runs)
    print(f"Wrote regression summary: {summary_path}")
    print(f"Wrote regression JSON summary: {json_summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
