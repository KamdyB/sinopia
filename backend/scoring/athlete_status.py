"""Rules engine: turns load and wellness signals into one level per athlete.

Levels are building, ok, watch, act, refer. Every triggered rule contributes its
reason; the level is the highest triggered one. Pain remains active until
a coach explicitly acknowledges the report.
"""
from datetime import date

from backend.scoring.config import (
    BASELINE_WEEKS,
    LOAD_JUMP_RATIO,
    MIN_BASELINE_WEEKS,
)
from backend.scoring.load_calculator import (
    Session,
    daily_loads,
    rolling_baseline,
    weeks_tracked,
    weekly_load,
)
from backend.scoring.wellness import wellness_drift

LEVELS = ("building", "ok", "watch", "act", "refer")


def athlete_status(
    weekly: float,
    baseline: float,
    weeks_available: int,
    wellness_scores: list[float],
    pain: bool,
) -> dict:
    triggered: list[tuple[str, str]] = []

    if pain:
        triggered.append(
            (
                "refer",
                "Pain was reported. A coach must acknowledge this report before it clears.",
            )
        )

    building_baseline = weeks_available < MIN_BASELINE_WEEKS or baseline <= 0
    if building_baseline:
        triggered.append(
            (
                "building",
                f"Building baseline: fewer than {MIN_BASELINE_WEEKS} weeks of training "
                "history, so no load flag is raised yet.",
            )
        )
    elif weekly > baseline * LOAD_JUMP_RATIO:
        triggered.append(
            (
                "act",
                f"Weekly load {weekly:.0f} exceeds the baseline {baseline:.0f} "
                f"by more than the provisional {LOAD_JUMP_RATIO:g}x threshold. "
                "Modify the next session.",
            )
        )

    if wellness_drift(wellness_scores):
        triggered.append(
            (
                "watch",
                "Recent check-in scores are meaningfully worse than the earlier average. "
                "Worth a conversation.",
            )
        )

    level = max((lvl for lvl, _ in triggered), key=LEVELS.index) if triggered else "ok"
    reasons = [reason for _, reason in triggered]
    numbers = {
        "weekly_load": round(weekly, 1),
        "baseline": round(baseline, 1),
        "weeks_available": weeks_available,
        "building_baseline": building_baseline,
        "wellness_entries": len(wellness_scores),
        "pain": pain,
    }
    return {"level": level, "reasons": reasons, "numbers": numbers}


def status_from_records(
    sessions: list[Session],
    checkins: list[dict],
    as_of: date,
) -> dict:
    """Compose an athlete's status from training and check-in records."""
    relevant = [c for c in checkins if c["date"] <= as_of.isoformat()]
    wellness_scores = [
        (c["sleep"] + c["energy"] + c["soreness"] + c["stress"]) / 4
        for c in relevant
    ]
    # A no-pain entry does not resolve a previous report.
    pain = any(c["pain"] and not c.get("pain_acknowledged", False) for c in relevant)

    daily = daily_loads(sessions)
    return athlete_status(
        weekly=weekly_load(daily, as_of),
        baseline=rolling_baseline(daily, as_of, BASELINE_WEEKS),
        weeks_available=weeks_tracked(daily, as_of),
        wellness_scores=wellness_scores,
        pain=pain,
    )


def status_from_sessions(sessions: list[Session], as_of: date) -> dict:
    """Status from sessions alone, for callers with no check-in data yet."""
    return status_from_records(sessions, [], as_of)
