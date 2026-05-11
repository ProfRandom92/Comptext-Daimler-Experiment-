#!/usr/bin/env python3
"""Smoke-test the public demo deployment without requiring secrets.

This script intentionally performs only safe public checks. It does not use API
keys, cookies, tokens, or real Daimler data. POST validation uses a synthetic
fixture payload only.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

DEFAULT_URL = "https://comptext-daimler-api-jules.onrender.com"
EXPECTED_MARKERS = (
    "Benchmark evidence center",
    "Document analysis",
    "CompText Daimler Experiment",
)
SYNTHETIC_ANALYZE_PAYLOAD = {
    "text": "Wartungsauftrag DEMO-001\nFehlercode: P0300\nKilometerstand: 80000 km\nMassnahme: synthetische Demo pruefen",
    "quelle": "demo-live-smoke",
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
        "User-Agent": "comptext-demo-live-smoke/1.0",
        "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - public deployment smoke test
        body = response.read(250_000).decode("utf-8", errors="replace")
        return HttpResult(
            url=url,
            status=response.status,
            content_type=response.headers.get("content-type", ""),
            body=body,
        )


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


def check_health(base_url: str, timeout: float, attempts: int, delay: float) -> None:
    result = retry_fetch(f"{base_url}/health", timeout, attempts, delay)
    if result.status != 200:
        raise AssertionError(f"/health expected 200, got {result.status}")
    payload = parse_json(result.body, "/health")
    if payload.get("status") != "ok":
        raise AssertionError(f"/health expected status=ok, got {payload!r}")
    print(f"OK /health status=200 json.status=ok content-type={result.content_type}")


def check_root(base_url: str, timeout: float, attempts: int, delay: float, *, require_markers: bool) -> None:
    result = retry_fetch(base_url, timeout, attempts, delay)
    if result.status != 200:
        raise AssertionError(f"/ expected 200, got {result.status}")
    if "text/html" not in result.content_type:
        raise AssertionError(f"/ expected text/html content type, got {result.content_type!r}")
    if require_markers:
        missing = [marker for marker in EXPECTED_MARKERS if marker not in result.body]
        if missing:
            sample = result.body[:500].replace("\n", " ")
            raise AssertionError(f"/ missing expected showcase markers {missing}; body sample={sample!r}")
        print("OK / status=200 html contains benchmark/showcase markers")
    else:
        print("OK / status=200 html")


def check_benchmark(base_url: str, timeout: float, attempts: int, delay: float) -> None:
    result = retry_fetch(f"{base_url}/benchmark", timeout, attempts, delay)
    if result.status != 200:
        raise AssertionError(f"/benchmark expected 200, got {result.status}")
    payload = parse_json(result.body, "/benchmark")
    if not payload:
        raise AssertionError("/benchmark returned an empty JSON object")
    print("OK /benchmark status=200 json returned")


def check_analyze(base_url: str, timeout: float, attempts: int, delay: float) -> None:
    result = retry_fetch(
        f"{base_url}/analyze",
        timeout,
        attempts,
        delay,
        method="POST",
        payload=SYNTHETIC_ANALYZE_PAYLOAD,
    )
    if result.status != 200:
        raise AssertionError(f"POST /analyze expected 200, got {result.status}")
    payload = parse_json(result.body, "POST /analyze")
    required = {"token_original", "token_komprimiert", "token_einsparung_pct", "zusammenfassung"}
    missing = sorted(required - set(payload))
    if missing:
        raise AssertionError(f"POST /analyze missing expected keys: {missing}; payload={payload!r}")
    print("OK POST /analyze status=200 synthetic payload returned expected keys")


def check_api_fallback(base_url: str, timeout: float, attempts: int, delay: float) -> None:
    try:
        retry_fetch(f"{base_url}/api/does-not-exist", timeout, attempts, delay)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            print("OK /api/does-not-exist returns 404 and is not masked by SPA fallback")
            return
        raise AssertionError(f"/api/does-not-exist expected 404, got {exc.code}") from exc
    raise AssertionError("/api/does-not-exist unexpectedly returned 2xx")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test public demo deployment")
    parser.add_argument("--url", default=DEFAULT_URL, help="Base service URL")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--delay", type=float, default=8.0)
    parser.add_argument(
        "--no-root-markers",
        action="store_true",
        help="Only require / to serve HTML, not specific showcase markers. Useful for API-only backends.",
    )
    parser.add_argument("--skip-root", action="store_true", help="Skip / HTML check")
    parser.add_argument("--skip-analyze", action="store_true", help="Skip synthetic POST /analyze check")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    print(f"Checking public demo deployment: {base_url}")
    check_health(base_url, args.timeout, args.attempts, args.delay)
    if not args.skip_root:
        check_root(base_url, args.timeout, args.attempts, args.delay, require_markers=not args.no_root_markers)
    check_benchmark(base_url, args.timeout, args.attempts, args.delay)
    if not args.skip_analyze:
        check_analyze(base_url, args.timeout, args.attempts, args.delay)
    check_api_fallback(base_url, args.timeout, args.attempts, args.delay)
    print("Public demo live smoke checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
