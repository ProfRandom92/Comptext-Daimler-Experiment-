#!/usr/bin/env python3
"""Validate generated report summaries against local machine-readable contracts.

The contracts are intentionally local and structural. This script does not import
or call Comptextv7 and never prints raw sanitizer findings or secrets.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPORTS_DIR = Path("docs/reports")
VALIDATION_REPORT = REPORTS_DIR / "report-contract-validation-report.md"
SUMMARY_PATHS = {
    "benchmark": REPORTS_DIR / "benchmark-summary.json",
    "regression": REPORTS_DIR / "regression-summary.json",
    "sanitization": REPORTS_DIR / "sanitization-summary.json",
}

TYPE_NAMES = {
    "string": str,
    "boolean": bool,
    "object": dict,
    "array": list,
    "integer": int,
    "number": (int, float),
}

COMMON_FIELDS = {
    "source_repo": "string",
    "report_type": "string",
    "synthetic": "boolean",
    "generated_at": "string",
    "notes": "array",
}

CONTRACTS = {
    "benchmark": {
        **COMMON_FIELDS,
        "target_repo": "string",
        "endpoint": "string",
        "metrics": "object",
        "status": "string",
    },
    "regression": {
        **COMMON_FIELDS,
        "target_repo": "string",
        "baseline_available": "boolean",
        "regression_detected": "boolean",
        "compared_runs": "array",
        "thresholds": "object",
        "decision": "string",
    },
    "sanitization": {
        **COMMON_FIELDS,
        "scanned_paths": "array",
        "findings_count": "integer",
        "findings_masked": "integer",
        "status": "string",
    },
}

BENCHMARK_METRICS = {
    "p50_ms": "number",
    "p95_ms": "number",
    "p99_ms": "number",
    "rps": "number",
    "error_rate": "number",
    "payload_size_bytes": "integer",
}


def is_type(value: Any, expected: str, *, allow_null: bool = False) -> bool:
    if value is None:
        return allow_null
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, TYPE_NAMES[expected])


def load_json(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"Missing summary file: {path.as_posix()}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"Invalid JSON in {path.as_posix()}: line {exc.lineno} column {exc.colno}"]
    if not isinstance(data, dict):
        return None, [f"Summary must be a JSON object: {path.as_posix()}"]
    return data, []


def validate_required_fields(name: str, data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field, expected in CONTRACTS[name].items():
        if field not in data:
            errors.append(f"{name}: missing required field `{field}`")
            continue
        if not is_type(data[field], expected):
            errors.append(f"{name}: field `{field}` must be {expected}")
    if data.get("synthetic") is not True:
        errors.append(f"{name}: field `synthetic` must be true")
    return errors


def validate_benchmark(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    metrics = data.get("metrics")
    if not isinstance(metrics, dict):
        return ["benchmark: `metrics` must be an object"]
    for field, expected in BENCHMARK_METRICS.items():
        if field not in metrics:
            errors.append(f"benchmark: metrics missing `{field}`")
            continue
        if not is_type(metrics[field], expected, allow_null=field != "payload_size_bytes"):
            errors.append(f"benchmark: metrics `{field}` must be {expected} or null")
    return errors


def validate_regression(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    thresholds = data.get("thresholds")
    if not isinstance(thresholds, dict):
        return ["regression: `thresholds` must be an object"]
    if not thresholds:
        errors.append("regression: `thresholds` must not be empty")
    for key, value in thresholds.items():
        if not isinstance(key, str) or not is_type(value, "number"):
            errors.append("regression: threshold keys must be strings and values must be numbers")
            break
    return errors


def validate_sanitization(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    scanned_paths = data.get("scanned_paths")
    if not isinstance(scanned_paths, list):
        return ["sanitization: `scanned_paths` must be an array"]
    if not all(isinstance(path, str) for path in scanned_paths):
        errors.append("sanitization: `scanned_paths` values must be strings")
    return errors


def validate_summary(name: str, path: Path) -> tuple[str, list[str]]:
    data, errors = load_json(path)
    if data is None:
        return "fail", errors
    errors.extend(validate_required_fields(name, data))
    if name == "benchmark":
        errors.extend(validate_benchmark(data))
    elif name == "regression":
        errors.extend(validate_regression(data))
    elif name == "sanitization":
        errors.extend(validate_sanitization(data))
    return ("fail" if errors else "pass"), errors


def write_validation_report(results: dict[str, tuple[Path, str, list[str]]]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = []
    detail_sections = []
    for name, (path, status, errors) in results.items():
        rows.append(f"| {name} | `{path.as_posix()}` | {status} | {len(errors)} |")
        if errors:
            safe_errors = "\n".join(f"- {error}" for error in errors)
        else:
            safe_errors = "- No structural violations detected."
        detail_sections.append(f"### {name.title()}\n\n{safe_errors}")
    VALIDATION_REPORT.write_text(
        f"""# Report Contract Validation Report

Generated: {generated_at} UTC

This report validates local synthetic JSON summaries for compatibility with the Comptextv7 machine-readable report contracts. It performs structural checks only and does not import or call Comptextv7.

| Summary | Path | Status | Violations |
| --- | --- | --- | ---: |
{chr(10).join(rows)}

## Details

{chr(10).join(detail_sections)}

## Safety

- Validation output names structural fields only.
- Raw suspicious findings, secrets, cookies, customer data, and production payloads are not printed.
""",
        encoding="utf-8",
    )


def main() -> int:
    results: dict[str, tuple[Path, str, list[str]]] = {}
    for name, path in SUMMARY_PATHS.items():
        status, errors = validate_summary(name, path)
        results[name] = (path, status, errors)
    write_validation_report(results)
    print(f"Wrote report contract validation report: {VALIDATION_REPORT}")
    failures = sum(1 for _, status, _ in results.values() if status == "fail")
    if failures:
        print(f"Report contract validation failed for {failures} summary file(s).")
        return 1
    print("Report contract validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
