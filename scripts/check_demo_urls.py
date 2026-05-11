#!/usr/bin/env python3
"""Check public demo URLs without making external outages fatal.

This script is intentionally conservative for CI/sandbox use: it prints a JSON
summary and exits zero even when a live URL is unreachable, because deployment
availability is external to a code-only validation run.
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from typing import Any


def _check_url(label: str, url: str, timeout: float) -> dict[str, Any]:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "comptext-demo-url-check/1.0"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {
                "label": label,
                "url": url,
                "reachable": 200 <= response.status < 400,
                "status": response.status,
                "warning": "" if 200 <= response.status < 400 else "non-2xx/3xx response",
            }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {
            "label": label,
            "url": url,
            "reachable": False,
            "status": None,
            "warning": f"external URL unavailable from this environment: {exc}",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check live CompText demo URLs.")
    parser.add_argument("--frontend-url", required=True)
    parser.add_argument("--backend-url", required=True)
    parser.add_argument("--timeout", type=float, default=8.0)
    args = parser.parse_args()

    results = [
        _check_url("frontend", args.frontend_url, args.timeout),
        _check_url("backend", args.backend_url.rstrip("/") + "/health", args.timeout),
    ]
    print(json.dumps({"checks": results}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
