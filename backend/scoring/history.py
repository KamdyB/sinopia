"""Build a date-aggregated, walk-forward workload history from source records."""
from collections import defaultdict
from datetime import date

from backend.scoring.athlete_status import status_from_records
from backend.scoring.load_calculator import Session, session_load


def history_points(sessions: list[Session], checkins: list[dict] | None = None) -> list[dict]:
    """Return one point per date with activity; combine multiple sessions on a date."""
    ordered = sorted(sessions, key=lambda item: item["date"])
    all_checkins = sorted(checkins or [], key=lambda item: item["date"])
    by_date: dict[str, list[Session]] = defaultdict(list)
    for session in ordered:
        by_date[session["date"]].append(session)
    days = sorted(set(by_date) | {item["date"] for item in all_checkins})
    points: list[dict] = []
    for day in days:
        as_of = date.fromisoformat(day)
        past_sessions = [item for item in ordered if item["date"] <= day]
        past_checkins = [item for item in all_checkins if item["date"] <= day]
        daily_checkins = [item for item in all_checkins if item["date"] == day]
        status = status_from_records(past_sessions, past_checkins, as_of)
        pain_checkin = next((item for item in daily_checkins if item.get("pain")), None)
        wellness_score = None
        if daily_checkins:
            latest = daily_checkins[-1]
            wellness_score = round(sum(latest[key] for key in ("sleep", "energy", "soreness", "stress")) / 4, 2)
        points.append({
            "date": day,
            "session_load": round(sum(session_load(item["duration_minutes"], item["rpe"]) for item in by_date.get(day, [])), 1),
            "session_count": len(by_date.get(day, [])),
            "level": status["level"],
            "reasons": status["reasons"],
            "numbers": status["numbers"],
            "pain": bool(pain_checkin),
            "pain_area": pain_checkin.get("pain_area") if pain_checkin else None,
            "pain_acknowledged": bool(pain_checkin and pain_checkin.get("pain_acknowledged", False)),
            "wellness_score": wellness_score,
        })
    return points
