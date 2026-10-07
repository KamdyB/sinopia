"""Session load math using the Foster et al. session-RPE method.

Everything here is transparent, rules-based statistics computed from
what the coach logged. No part of this is machine learning.
"""
from datetime import date, timedelta
from typing import TypedDict


class Session(TypedDict):
    date: str  # ISO format, e.g. "2026-09-10"
    duration_minutes: float
    rpe: float


def session_load(duration_minutes: float, rpe: float) -> float:
    return duration_minutes * rpe


def daily_loads(sessions: list[Session]) -> dict[date, float]:
    daily: dict[date, float] = {}
    for s in sessions:
        d = date.fromisoformat(s["date"])
        daily[d] = daily.get(d, 0.0) + session_load(s["duration_minutes"], s["rpe"])
    return daily


def weekly_load(daily: dict[date, float], as_of: date) -> float:
    """Total load across the 7 days ending on as_of, missing days as zero."""
    return sum(daily.get(as_of - timedelta(days=i), 0.0) for i in range(7))


def weeks_tracked(daily: dict[date, float], as_of: date) -> int:
    """Complete 7-day windows of tracked history before as_of."""
    if not daily:
        return 0
    tracked_days = (as_of - min(daily)).days
    return max(0, tracked_days // 7)


def rolling_baseline(
    daily: dict[date, float],
    as_of: date,
    weeks: int,
) -> float:
    """Mean of her own weekly loads over the trailing complete weeks.

    A week counts only when all seven of its days fall inside tracked
    history; days before tracking began are unknown, not zero. Zero-load
    tracked weeks count as zero. Returns 0.0 when no complete week
    exists; callers treat that as building baseline.
    """
    if not daily:
        return 0.0
    first = min(daily)
    windows: list[float] = []
    for k in range(1, weeks + 1):
        end = as_of - timedelta(days=7 * k)
        if end - timedelta(days=6) < first:
            break
        windows.append(weekly_load(daily, end))
    if not windows:
        return 0.0
    return sum(windows) / len(windows)
