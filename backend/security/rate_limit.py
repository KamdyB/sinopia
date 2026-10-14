"""Shared process-local request throttling primitives.

Production multi-worker deployments must also configure a shared edge limiter.
"""
import os
import time
from collections import defaultdict, deque
from threading import Lock
from fastapi import Request

_EVENTS: dict[tuple[str, ...], deque[float]] = defaultdict(deque)
_LOCK = Lock()


def client_ip(request: Request) -> str:
    if os.environ.get("SINOPIA_TRUST_PROXY", "").lower() == "true":
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded.strip():
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce_rate_limit(key: tuple[str, ...], maximum: int, window: int) -> int | None:
    now = time.monotonic()
    with _LOCK:
        events = _EVENTS[key]
        while events and events[0] <= now - window:
            events.popleft()
        if len(events) >= maximum:
            return max(1, int(window - (now - events[0])))
        events.append(now)
    return None
