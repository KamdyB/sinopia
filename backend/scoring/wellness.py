"""Wellness drift: recent check-in scores against her own earlier average.

Pure statistics over coach-entered 1 to 5 scores where 5 is best. No
machine learning and no external baseline, only her own numbers.
"""
from backend.scoring.config import (
    MIN_WELLNESS_ENTRIES,
    WELLNESS_DRIFT_MARGIN,
    WELLNESS_RECENT_ENTRIES,
)


def wellness_drift(scores: list[float]) -> bool:
    """True when the most recent entries are meaningfully worse than earlier ones.

    scores must be in chronological order.
    """
    if len(scores) < MIN_WELLNESS_ENTRIES:
        return False
    recent = scores[-WELLNESS_RECENT_ENTRIES:]
    earlier = scores[:-WELLNESS_RECENT_ENTRIES]
    if not earlier:
        return False
    earlier_mean = sum(earlier) / len(earlier)
    recent_mean = sum(recent) / len(recent)
    return earlier_mean - recent_mean > WELLNESS_DRIFT_MARGIN
