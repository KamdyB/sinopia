"""Small, read-only smoke test for a deployed Sinopia API.

Usage:
    python scripts/deployment_smoke_test.py https://your-api-domain.example

This checks process liveness and database readiness only. It does not claim
that OAuth, email delivery, or authenticated application workflows are valid.
"""
from __future__ import annotations

import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def check(base_url: str, path: str, expected_status: int, expected_value: str) -> bool:
    url = f"{base_url.rstrip('/')}{path}"
    request = Request(url, headers={"Accept": "application/json"}, method="GET")
    try:
        with urlopen(request, timeout=15) as response:
            status = response.status
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        print(f"FAIL {path}: HTTP {exc.code}")
        return False
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        print(f"FAIL {path}: {type(exc).__name__}")
        return False

    if status != expected_status or payload.get("status") != expected_value:
        print(f"FAIL {path}: HTTP {status}, payload status={payload.get('status')!r}")
        return False
    print(f"PASS {path}: HTTP {status}, status={expected_value}")
    return True


def main() -> int:
    if len(sys.argv) != 2 or not sys.argv[1].startswith("https://"):
        print("Usage: python scripts/deployment_smoke_test.py https://your-api-domain")
        return 2

    base_url = sys.argv[1].rstrip("/")
    checks = [
        check(base_url, "/health", 200, "ok"),
        check(base_url, "/ready", 200, "ready"),
    ]
    if all(checks):
        print("PASS deployment smoke checks. OAuth/email and signed-in workflows still need separate end-to-end tests.")
        return 0
    print("FAIL deployment smoke checks. Review the Vercel deployment and runtime logs.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
