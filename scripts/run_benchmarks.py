#!/usr/bin/env python3
"""Run a safe Comptext/Daimler benchmark and write a Markdown report.

The script is intentionally conservative: it uses synthetic requests only, avoids
printing payloads, and degrades to a useful report when Locust is unavailable.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPORT_PREFIX = "benchmark-report-"


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a synthetic benchmark and write a Markdown report.")
    parser.add_argument("--host", default="http://localhost:8000", help="Target host for the benchmark.")
    parser.add_argument("--users", type=int, default=50, help="Number of concurrent Locust users.")
    parser.add_argument("--spawn-rate", type=float, default=10, help="Users spawned per second.")
    parser.add_argument("--duration", default="15s", help="Benchmark duration, for example 15s or 1m.")
    parser.add_argument("--endpoint", default="/analyze", help="Endpoint path to exercise with synthetic traffic.")
    parser.add_argument("--output-dir", default="docs/reports", help="Directory for Markdown reports.")
    return parser.parse_args()


def synthetic_locustfile(endpoint: str) -> str:
    """Return a Locust file that sends only a tiny synthetic JSON payload."""
    endpoint_json = json.dumps(endpoint)
    return f'''
from locust import HttpUser, between, task

class SyntheticComptextUser(HttpUser):
    wait_time = between(0.05, 0.1)

    @task
    def analyze_synthetic_case(self):
        payload = {{
            "source": "synthetic-benchmark",
            "case_id": "synthetic-case-0001",
            "description": "Synthetic benchmark payload; contains no customer data.",
            "signals": ["P0000", "BENCHMARK_ONLY"],
        }}
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


def error_rate(stats: dict[str, str]) -> str:
    try:
        failures = float(stats.get("failure_count") or 0)
        requests = float(stats.get("request_count") or 0)
    except ValueError:
        return "unavailable"
    if requests <= 0:
        return "unavailable"
    return f"{(failures / requests) * 100:.2f}%"


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
            status = f"completed with locust exit code {completed.returncode}"
            notes.append("Locust returned a non-zero exit code; this often means the target server was unavailable or returned errors.")
        if completed.stderr:
            notes.append("Locust emitted diagnostic output; raw output is intentionally not copied into the report.")
        stats = read_locust_stats(Path(f"{csv_prefix}_stats.csv"))
    return status, stats, notes


def markdown_report(args: argparse.Namespace, status: str, stats: dict[str, str], notes: list[str], report_name: str) -> str:
    metadata: dict[str, Any] = {
        "report": report_name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "host": args.host,
        "endpoint": args.endpoint,
        "users": args.users,
        "spawn_rate": args.spawn_rate,
        "duration": args.duration,
        "status": status,
        "p50_ms": stats.get("p50") or None,
        "p95_ms": stats.get("p95") or None,
        "p99_ms": stats.get("p99") or None,
        "rps": stats.get("rps") or None,
        "error_rate": error_rate(stats),
    }
    rows = [
        ("Host", args.host),
        ("Endpoint", args.endpoint),
        ("Users", str(args.users)),
        ("Spawn rate", str(args.spawn_rate)),
        ("Duration", args.duration),
        ("Status", status),
        ("p50", stats.get("p50") or "unavailable"),
        ("p95", stats.get("p95") or "unavailable"),
        ("p99", stats.get("p99") or "unavailable"),
        ("RPS", stats.get("rps") or "unavailable"),
        ("Error rate", metadata["error_rate"]),
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

    locust_bin = shutil.which("locust")
    if not locust_bin:
        status = "tool unavailable"
        stats: dict[str, str] = {}
        notes = ["Locust is not installed or is not on PATH; install it locally to run load benchmarks."]
    else:
        status, stats, notes = run_locust(args, locust_bin)

    report_path.write_text(markdown_report(args, status, stats, notes, report_name), encoding="utf-8")
    print(f"Wrote benchmark report: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
