"""Rules engine: turns load and wellness signals into one level per athlete.

Levels are ok, watch, act, refer. Every triggered rule contributes its
reason; the level is the highest triggered one. Pain always refers,
regardless of load. All outputs carry the numbers behind them.
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

LEVELS = ("ok", "watch", "act", "refer")


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
                "Pain was reported. Stop play and refer to a physiotherapist or doctor, "
                "regardless of training load.",
            )
        )

    building_baseline = weeks_available < MIN_BASELINE_WEEKS or baseline <= 0
    if building_baseline:
        triggered.append(
            (
                "ok",
                f"Building baseline: fewer than {MIN_BASELINE_WEEKS} weeks of her own "
                "history, so no load flag is raised yet.",
            )
        )
    elif weekly > baseline * LOAD_JUMP_RATIO:
        triggered.append(
            (
                "act",
                f"Weekly load {weekly:.0f} exceeds her own baseline {baseline:.0f} "
                f"by more than the provisional {LOAD_JUMP_RATIO:g}x threshold. "
                "Modify the next session.",
            )
        )

    if wellness_drift(wellness_scores):
        triggered.append(
            (
                "watch",
                "Recent check-in scores are meaningfully worse than her own earlier "
                "average. Worth a conversation.",
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
    """One athlete's status at a date, from her sessions and check-ins.

    Pure composition: storage happens elsewhere, HTTP happens elsewhere."""
    relevant = [c for c in checkins if c["date"] <= as_of.isoformat()]
    wellness_scores = [
        (c["sleep"] + c["energy"] + c["soreness"] + c["stress"]) / 4
        for c in relevant
    ]
    # The latest check-in is her current self-report; a no-pain check-in
    # clears an earlier pain report.
    pain = relevant[-1]["pain"] if relevant else False

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
