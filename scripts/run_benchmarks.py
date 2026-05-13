#!/usr/bin/env python3
"""Run a safe Comptext/Daimler benchmark and write Markdown and JSON reports.

The script is intentionally conservative: it uses synthetic requests only, avoids
printing payloads, and degrades to useful reports when Locust is unavailable.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SOURCE_REPO = "ProfRandom92/Comptext-Daimler-Experiment-"
TARGET_REPO = "downstream-runtime"
REPORT_PREFIX = "benchmark-report-"
SUMMARY_NAME = "benchmark-summary.json"


def utc_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def utc_iso_timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a synthetic benchmark and write Markdown/JSON reports.")
    parser.add_argument("--host", default="http://localhost:8000", help="Target host for the benchmark.")
    parser.add_argument("--users", type=int, default=50, help="Number of concurrent Locust users.")
    parser.add_argument("--spawn-rate", type=float, default=10, help="Users spawned per second.")
    parser.add_argument("--duration", default="15s", help="Benchmark duration, for example 15s or 1m.")
    parser.add_argument("--endpoint", default="/analyze", help="Endpoint path to exercise with synthetic traffic.")
    parser.add_argument("--output-dir", default="docs/reports", help="Directory for generated reports.")
    return parser.parse_args()


def synthetic_payload() -> dict[str, Any]:
    """Return the synthetic benchmark payload without sensitive data."""
    return {
        "source": "synthetic-benchmark",
        "case_id": "synthetic-case-0001",
        "description": "Synthetic benchmark payload; contains no customer data.",
        "signals": ["P0000", "BENCHMARK_ONLY"],
    }


def synthetic_payload_size_bytes() -> int:
    return len(json.dumps(synthetic_payload(), sort_keys=True, separators=(",", ":")).encode("utf-8"))


def synthetic_locustfile(endpoint: str) -> str:
    """Return a Locust file that sends only a tiny synthetic JSON payload."""
    endpoint_json = json.dumps(endpoint)
    payload_json = json.dumps(synthetic_payload(), sort_keys=True)
    return f'''
from locust import HttpUser, between, task

class SyntheticComptextUser(HttpUser):
    wait_time = between(0.05, 0.1)

    @task
    def analyze_synthetic_case(self):
        payload = {payload_json}
        self.client.post({endpoint_json}, json=payload, name={endpoint_json})
'''.lstrip()


def read_locust_stats(csv_stats_path: Path) -> dict[str, str]:
    if not csv_stats_path.exists():
        return {}
    with csv_stats_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    aggregate = next((row for row in rows if row.get("Name") == "Aggregated"), rows[-1] if rows else None)
    if not aggregate:
        return {}
    return {
        "p50": aggregate.get("Median Response Time", ""),
        "p95": aggregate.get("95%", ""),
        "p99": aggregate.get("99%", ""),
        "rps": aggregate.get("Requests/s", ""),
        "failure_count": aggregate.get("Failure Count", ""),
        "request_count": aggregate.get("Request Count", ""),
        "failures_per_second": aggregate.get("Failures/s", ""),
    }


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


def error_rate_percent(stats: dict[str, str]) -> float | None:
    try:
        failures = float(stats.get("failure_count") or 0)
        requests = float(stats.get("request_count") or 0)
    except ValueError:
        return None
    if requests <= 0:
        return None
    return round((failures / requests) * 100, 4)


def display_metric(value: float | int | None, suffix: str = "") -> str:
    if value is None:
        return "unavailable"
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return f"{value}{suffix}"


def run_locust(args: argparse.Namespace, locust_bin: str) -> tuple[str, dict[str, str], list[str]]:
    notes: list[str] = []
    with tempfile.TemporaryDirectory(prefix="comptext-benchmark-") as temp_dir:
        temp_path = Path(temp_dir)
        locustfile_path = temp_path / "locustfile.py"
        csv_prefix = temp_path / "locust"
        locustfile_path.write_text(synthetic_locustfile(args.endpoint), encoding="utf-8")
        command = [
            locust_bin,
            "--headless",
            "--locustfile",
            str(locustfile_path),
            "--host",
            args.host,
            "--users",
            str(args.users),
            "--spawn-rate",
            str(args.spawn_rate),
            "--run-time",
            args.duration,
            "--csv",
            str(csv_prefix),
            "--only-summary",
        ]
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
        if completed.returncode == 0:
            status = "completed"
        else:
            status = "completed_with_errors"
            notes.append("Locust returned a non-zero exit code; this often means the target server was unavailable or returned errors.")
        if completed.stderr:
            notes.append("Locust emitted diagnostic output; raw output is intentionally not copied into the report.")
        stats = read_locust_stats(Path(f"{csv_prefix}_stats.csv"))
    return status, stats, notes


def build_metrics(stats: dict[str, str]) -> dict[str, float | int | None]:
    return {
        "p50_ms": numeric(stats.get("p50")),
        "p95_ms": numeric(stats.get("p95")),
        "p99_ms": numeric(stats.get("p99")),
        "rps": numeric(stats.get("rps")),
        "error_rate": error_rate_percent(stats),
        "payload_size_bytes": synthetic_payload_size_bytes(),
    }


def benchmark_summary(
    args: argparse.Namespace,
    generated_at: str,
    status: str,
    metrics: dict[str, float | int | None],
    notes: list[str],
) -> dict[str, Any]:
    return {
        "source_repo": SOURCE_REPO,
        "target_repo": TARGET_REPO,
        "report_type": "benchmark_summary",
        "synthetic": True,
        "generated_at": generated_at,
        "endpoint": args.endpoint,
        "metrics": metrics,
        "status": status,
        "notes": notes or ["Synthetic-only benchmark summary; no raw payloads, secrets, or customer data included."],
    }


def markdown_report(
    args: argparse.Namespace,
    status: str,
    metrics: dict[str, float | int | None],
    notes: list[str],
    report_name: str,
    generated_at: str,
) -> str:
    metadata: dict[str, Any] = {
        "report": report_name,
        "generated_at_utc": generated_at,
        "host": args.host,
        "endpoint": args.endpoint,
        "users": args.users,
        "spawn_rate": args.spawn_rate,
        "duration": args.duration,
        "status": status,
        "p50_ms": metrics["p50_ms"],
        "p95_ms": metrics["p95_ms"],
        "p99_ms": metrics["p99_ms"],
        "rps": metrics["rps"],
        "error_rate": metrics["error_rate"],
    }
    rows = [
        ("Host", args.host),
        ("Endpoint", args.endpoint),
        ("Users", str(args.users)),
        ("Spawn rate", str(args.spawn_rate)),
        ("Duration", args.duration),
        ("Status", status),
        ("p50", display_metric(metrics["p50_ms"], " ms")),
        ("p95", display_metric(metrics["p95_ms"], " ms")),
        ("p99", display_metric(metrics["p99_ms"], " ms")),
        ("RPS", display_metric(metrics["rps"])),
        ("Error rate", display_metric(metrics["error_rate"], "%")),
        ("Payload size", display_metric(metrics["payload_size_bytes"], " bytes")),
    ]
    note_lines = notes or ["Synthetic-only benchmark; no raw payloads, secrets, or customer data are included."]
    table = "\n".join(f"| {key} | {value} |" for key, value in rows)
    safe_metadata = json.dumps(metadata, sort_keys=True)
    notes_md = "\n".join(f"- {note}" for note in note_lines)
    return f"""# Benchmark Report

<!-- benchmark-metadata: {safe_metadata} -->

| Field | Value |
| --- | --- |
{table}

## Contract-compatible JSON summary

This run also writes `docs/reports/{SUMMARY_NAME}` for machine-readable contract validation.

## Environment notes

{notes_md}

## Safety

- This report was generated with synthetic benchmark payloads only.
- Raw request bodies, secrets, cookies, bearer tokens, and proprietary customer data are intentionally excluded.
"""


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_name = f"{REPORT_PREFIX}{utc_timestamp()}.md"
    report_path = output_dir / report_name
    summary_path = output_dir / SUMMARY_NAME
    generated_at = utc_iso_timestamp()

    locust_bin = shutil.which("locust")
    if not locust_bin:
        status = "tool_unavailable"
        stats: dict[str, str] = {}
        notes = ["Locust is not installed or is not on PATH; metrics are null except deterministic payload size."]
    else:
        status, stats, notes = run_locust(args, locust_bin)

    metrics = build_metrics(stats)
    report_path.write_text(markdown_report(args, status, metrics, notes, report_name, generated_at), encoding="utf-8")
    summary_path.write_text(
        json.dumps(benchmark_summary(args, generated_at, status, metrics, notes), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote benchmark report: {report_path}")
    print(f"Wrote benchmark summary: {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
