#!/usr/bin/env python3
"""Smoke-test the public demo frontend and backend without secrets."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

DEFAULT_FRONTEND_URL = "https://comptext-daimler-experiment.vercel.app"
DEFAULT_BACKEND_URL = "https://comptext-daimler-api-jules.onrender.com"
SYNTHETIC_ANALYZE_PAYLOAD = {
    "text": "Wartungsauftrag DEMO-URL-001\nFehlercode: P0300\nKilometerstand: 80000 km\nMassnahme: synthetische Demo pruefen",
    "quelle": "demo-url-smoke",
}


@dataclass(frozen=True)
class HttpResult:
    url: str
    status: int
    content_type: str
    body: str


def fetch(url: str, timeout: float, *, method: str = "GET", payload: dict[str, Any] | None = None) -> HttpResult:
    data = None
    headers = {
        "User-Agent": "comptext-demo-url-smoke/1.0",
        "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - public smoke test
        body = response.read(500_000).decode("utf-8", errors="replace")
        return HttpResult(url=url, status=response.status, content_type=response.headers.get("content-type", ""), body=body)


def retry_fetch(
    url: str,
    timeout: float,
    attempts: int,
    delay: float,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
) -> HttpResult:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return fetch(url, timeout, method=method, payload=payload)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            print(f"Attempt {attempt}/{attempts} failed for {method} {url}: {exc}", file=sys.stderr)
            if attempt < attempts:
                time.sleep(delay)
    assert last_error is not None
    raise last_error


def parse_json(body: str, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"{label} did not return JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise AssertionError(f"{label} returned non-object JSON: {type(payload).__name__}")
    return payload


def check_frontend(frontend_url: str, timeout: float, attempts: int, delay: float) -> None:
    result = retry_fetch(frontend_url, timeout, attempts, delay)
    if result.status != 200:
        raise AssertionError(f"frontend / expected 200, got {result.status}")
    if "text/html" not in result.content_type:
        raise AssertionError(f"frontend / expected text/html, got {result.content_type!r}")
    if "<script" not in result.body or "</html>" not in result.body.lower():
        sample = result.body[:500].replace("\n", " ")
        raise AssertionError(f"frontend / did not look like a built SPA document; sample={sample!r}")
    print(f"OK frontend {frontend_url} status=200 content-type={result.content_type}")


def check_backend(backend_url: str, timeout: float, attempts: int, delay: float) -> None:
    health = retry_fetch(f"{backend_url}/health", timeout, attempts, delay)
    if health.status != 200:
        raise AssertionError(f"backend /health expected 200, got {health.status}")
    health_payload = parse_json(health.body, "backend /health")
    if health_payload.get("status") != "ok":
        raise AssertionError(f"backend /health expected status=ok, got {health_payload!r}")
    print("OK backend /health status=200 json.status=ok")

    benchmark = retry_fetch(f"{backend_url}/benchmark", timeout, attempts, delay)
    if benchmark.status != 200:
        raise AssertionError(f"backend /benchmark expected 200, got {benchmark.status}")
    benchmark_payload = parse_json(benchmark.body, "backend /benchmark")
    if not benchmark_payload:
        raise AssertionError("backend /benchmark returned empty JSON")
    print("OK backend /benchmark status=200 json returned")

    analyze = retry_fetch(
        f"{backend_url}/analyze",
        timeout,
        attempts,
        delay,
        method="POST",
        payload=SYNTHETIC_ANALYZE_PAYLOAD,
    )
    if analyze.status != 200:
        raise AssertionError(f"backend POST /analyze expected 200, got {analyze.status}")
    analyze_payload = parse_json(analyze.body, "backend POST /analyze")
    required = {"token_original", "token_komprimiert", "token_einsparung_pct", "zusammenfassung"}
    missing = sorted(required - set(analyze_payload))
    if missing:
        raise AssertionError(f"backend POST /analyze missing expected keys: {missing}; payload={analyze_payload!r}")
    print("OK backend POST /analyze status=200 synthetic payload returned expected keys")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test public Vercel frontend and API backend")
    parser.add_argument("--frontend-url", default=DEFAULT_FRONTEND_URL)
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--timeout", type=float, default=25.0)
    parser.add_argument("--attempts", type=int, default=4)
    parser.add_argument("--delay", type=float, default=12.0)
    args = parser.parse_args()

    frontend_url = args.frontend_url.rstrip("/")
    backend_url = args.backend_url.rstrip("/")
    print(f"Checking demo frontend: {frontend_url}")
    check_frontend(frontend_url, args.timeout, args.attempts, args.delay)
    print(f"Checking demo backend: {backend_url}")
    check_backend(backend_url, args.timeout, args.attempts, args.delay)
    print("Demo URL smoke checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
