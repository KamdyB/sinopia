"""Database-backed shared rate limiting in production; in-memory only for local tests."""
import hashlib
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
    if os.environ.get("SINOPIA_ENV", "production").lower() == "production" and os.environ.get("DATABASE_URL", "").strip():
        from backend.data.db import connect
        now = int(time.time())
        window_start = now - (now % window)
        bucket_key = hashlib.sha256("\0".join(key).encode()).hexdigest()
        with connect() as conn:
            row = conn.execute(
                "INSERT INTO rate_limit_buckets (bucket_key, window_start, count) VALUES (?, ?, 1) "
                "ON CONFLICT(bucket_key) DO UPDATE SET "
                "count = CASE WHEN rate_limit_buckets.window_start = excluded.window_start "
                "THEN rate_limit_buckets.count + 1 ELSE 1 END, "
                "window_start = excluded.window_start RETURNING count",
                (bucket_key, window_start),
            ).fetchone()
        count = int(row["count"])
        if count > maximum:
            return max(1, window_start + window - now)
        return None

    now = time.monotonic()
    with _LOCK:
        events = _EVENTS[key]
        while events and events[0] <= now - window:
            events.popleft()
        if len(events) >= maximum:
            return max(1, int(window - (now - events[0])))
        events.append(now)
    return None
