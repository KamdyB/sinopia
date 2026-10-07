"""Reconstructs an athlete's status as it stood at every past session by
walking forward through the session list and re-running the rules at each
date. No second copy of past statuses is stored, so the sessions table
stays the single source of truth."""
from datetime import date

from backend.scoring.athlete_status import status_from_records
from backend.scoring.load_calculator import Session, session_load


def history_points(
    sessions: list[Session],
    checkins: list[dict] | None = None,
) -> list[dict]:
    ordered = sorted(sessions, key=lambda s: s["date"])
    all_checkins = checkins or []
    points: list[dict] = []
    past: list[Session] = []
    for s in ordered:
        past.append(s)
        past_checkins = [c for c in all_checkins if c["date"] <= s["date"]]
        status = status_from_records(past, past_checkins, date.fromisoformat(s["date"]))
        points.append(
            {
                "date": s["date"],
                "session_load": round(session_load(s["duration_minutes"], s["rpe"]), 1),
                "level": status["level"],
                "reasons": status["reasons"],
                "numbers": status["numbers"],
            }
        )
    return points
