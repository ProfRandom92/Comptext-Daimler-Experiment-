#!/usr/bin/env python3
"""Scan likely fixture paths and write a safe sanitization report.

The scanner is non-destructive by default and never prints full suspicious
values. It is designed as a CI guardrail, not a replacement for human review.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

SOURCE_REPO = "ProfRandom92/Comptext-Daimler-Experiment-"
DEFAULT_PATHS = ["fixtures", "data", "samples", "docs/reports"]
REPORT_PATH = Path("docs/reports/sanitization-report.md")
SUMMARY_PATH = Path("docs/reports/sanitization-summary.json")
MAX_FILE_BYTES = 1_000_000


@dataclass(frozen=True)
class PatternRule:
    name: str
    regex: re.Pattern[str]


RULES = [
    PatternRule("bearer token", re.compile(r"(?i)\bbearer\s+([A-Za-z0-9._~+/=-]{12,})")),
    PatternRule("api key assignment", re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*['\"]?([^'\"\s]{8,})")),
    PatternRule("cookie header", re.compile(r"(?i)\bcookie\s*[:=]\s*([^\n;]{8,})")),
    PatternRule("email address", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    PatternRule("long credential-like string", re.compile(r"\b[A-Za-z0-9_]{32,}\b")),
    PatternRule("vin-like customer identifier", re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b")),
    PatternRule("customer id assignment", re.compile(r"(?i)\b(customer|client|account)[_-]?id\b\s*[:=]\s*['\"]?([A-Za-z0-9._-]{6,})")),
]


@dataclass
class Finding:
    path: Path
    line_number: int
    rule: str
    masked: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan fixture-like paths for suspicious strings.")
    parser.add_argument("paths", nargs="*", default=DEFAULT_PATHS, help="Paths to scan; defaults to fixture/report locations.")
    parser.add_argument("--report", default=str(REPORT_PATH), help="Markdown report path.")
    return parser.parse_args()


def is_probably_text(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
        return False
    try:
        chunk = path.read_bytes()[:4096]
    except OSError:
        return False
    return b"\x00" not in chunk


def iter_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if not path.exists():
            continue
        if path.is_file() and is_probably_text(path):
            files.append(path)
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if is_probably_text(child):
                    files.append(child)
    return sorted(set(files))


def mask_value(value: str) -> str:
    compact = value.strip()
    if len(compact) <= 4:
        return "[REDACTED]"
    return f"{compact[:2]}...[REDACTED]...{compact[-2:]} (len={len(compact)})"


def selected_match_text(match: re.Match[str]) -> str:
    groups = [group for group in match.groups() if group]
    return groups[-1] if groups else match.group(0)


def scan_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return findings
    for index, line in enumerate(lines, start=1):
        for rule in RULES:
            for match in rule.regex.finditer(line):
                matched_text = selected_match_text(match)
                if rule.name == "long credential-like string" and line.strip().startswith(f'"{matched_text}":'):
                    continue
                findings.append(Finding(path=path, line_number=index, rule=rule.name, masked=mask_value(matched_text)))
    return findings


def write_report(report_path: Path, scanned_files: list[Path], findings: list[Finding], generated_at: str) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if findings:
        rows = "\n".join(
            f"| {finding.path.as_posix()} | {finding.line_number} | {finding.rule} | `{finding.masked}` |"
            for finding in findings
        )
    else:
        rows = "| No suspicious strings detected. | | | |"
    report_path.write_text(
        f"""# Sanitization Report

Generated: {generated_at} UTC

Scanned files: {len(scanned_files)}
Findings: {len(findings)}

## Findings

| File | Line | Rule | Masked value |
| --- | ---: | --- | --- |
{rows}

## Safety notes

- This scanner is non-destructive and report-only.
- Suspicious values are masked; raw secrets and raw customer identifiers are never printed in full.
- Treat findings as review prompts and replace real data with synthetic fixtures before committing.
- A contract-compatible JSON summary is written to `docs/reports/sanitization-summary.json`.
""",
        encoding="utf-8",
    )


def write_json_summary(summary_path: Path, scanned_paths: list[str], findings: list[Finding], generated_at: str) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "source_repo": SOURCE_REPO,
        "report_type": "sanitization_summary",
        "synthetic": True,
        "generated_at": generated_at,
        "scanned_paths": scanned_paths,
        "findings_count": len(findings),
        "findings_masked": len(findings),
        "status": "review_required" if findings else "pass",
        "notes": [
            "Report-only scan; raw suspicious findings, secrets, and customer identifiers are never written to JSON.",
            "Use synthetic fixtures only and review masked Markdown findings before committing.",
        ],
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    scanned_files = iter_files(args.paths)
    findings: list[Finding] = []
    for path in scanned_files:
        findings.extend(scan_file(path))
    report_path = Path(args.report)
    generated_at = datetime.now(UTC).isoformat(timespec="seconds")
    write_report(report_path, scanned_files, findings, generated_at)
    write_json_summary(SUMMARY_PATH, list(args.paths), findings, generated_at)
    print(f"Wrote sanitization report: {report_path}")
    print(f"Wrote sanitization summary: {SUMMARY_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
