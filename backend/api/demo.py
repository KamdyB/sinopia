"""No-login demo mode.

Serves a small set of fake athletes with clearly fake codes
(DEMO-A1, DEMO-B2, ...) and hand-built deterministic histories, run
through the same rules engine the real tool uses. Read-only: nothing
is written to the database, no coach account is involved, and none of
this mixes with real data because it never touches the stores.

The numbers here are invented on purpose (they are fake demo data,
labelled as such wherever they are shown). They make nothing in the
scoring engine behave differently.
"""
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.scoring.athlete_status import status_from_records
from backend.scoring.history import history_points

router = APIRouter()

# Hand-built demo patterns per fake athlete. Minutes and RPE only; the
# level comes out of the untouched rules engine.
_DEMO_SQUADS: dict[str, list[tuple[int, int]]] = {
    # (minutes, rpe) pairs per session, oldest first.
    # Steady team: nothing to flag.
    "DEMO-A1": [(60, 4), (75, 5), (45, 3), (80, 5), (70, 4), (60, 5), (75, 4), (65, 4)],
    # Small appetite for load, steady weeks.
    "DEMO-B2": [(45, 3), (50, 4), (40, 3), (55, 3), (45, 4), (50, 3), (45, 4), (55, 4)],
    # Sudden spike in the latest week: the load-jump rule can fire.
    "DEMO-C3": [(50, 4), (55, 4), (45, 3), (60, 4), (50, 4), (55, 5), (140, 8), (120, 8)],
    # Three days a week, moderate; no jumps.
    "DEMO-D4": [(90, 5), (90, 5), (75, 4), (90, 4), (75, 5), (90, 5), (75, 4), (90, 5)],
    # Two short typical sessions, then a reported pain check-in in the
    # tail: pain always refers, regardless of load.
    "DEMO-E5": [(70, 5), (70, 5), (60, 4), (75, 5), (70, 5), (65, 4), (70, 5), (80, 6)],
}

# Wellness entries (sleep, energy, soreness, stress; 1 to 5, higher is
# better), oldest first. DEMO-E5 ends tired with pain reported.
_DEMO_CHECKINS: dict[str, list[tuple[int, int, int, int, bool, str | None]]] = {
    "DEMO-A1": [(4, 4, 4, 4, False, None), (4, 5, 3, 4, False, None), (4, 4, 4, 4, False, None), (3, 4, 4, 4, False, None), (4, 4, 4, 4, False, None)],
    "DEMO-B2": [(4, 4, 4, 4, False, None), (4, 4, 4, 3, False, None), (4, 3, 4, 4, False, None), (4, 4, 4, 4, False, None), (4, 4, 4, 4, False, None)],
    "DEMO-C3": [(5, 5, 2, 3, False, None), (5, 5, 2, 3, False, None), (5, 4, 2, 3, False, None), (5, 4, 2, 3, False, None), (5, 4, 2, 3, False, None)],
    "DEMO-D4": [(3, 3, 3, 3, False, None), (3, 3, 3, 3, False, None), (3, 3, 3, 3, False, None), (3, 3, 3, 3, False, None), (3, 3, 3, 3, False, None)],
    "DEMO-E5": [(4, 4, 3, 4, False, None), (3, 3, 3, 3, False, None), (3, 3, 3, 3, False, None), (2, 2, 4, 3, True, "Knee"), (2, 2, 4, 3, True, "Knee")],
}


def _iso_days_ago(days: int) -> str:
    return (date.today() - timedelta(days=days)).isoformat()


def _demo_sessions(code: str) -> list[dict]:
    patterns = _DEMO_SQUADS[code]
    # Eight weekly sessions spread backwards from today, oldest first.
    count = len(patterns)
    return [
        {
            "date": _iso_days_ago((count - index) * 7),
            "duration_minutes": float(minutes),
            "rpe": float(rpe),
        }
        for index, (minutes, rpe) in enumerate(patterns, start=0)
    ]


def _demo_checkins(code: str) -> list[dict]:
    entries = _DEMO_CHECKINS[code]
    count = len(entries)
    return [
        {
            "date": _iso_days_ago((count - index) * 2),
            "sleep": sleep,
            "energy": energy,
            "soreness": soreness,
            "stress": stress,
            "pain": pain,
            "pain_area": area,
        }
        for index, (sleep, energy, soreness, stress, pain, area) in enumerate(entries, start=0)
    ]


class DemoStatus(BaseModel):
    player_id: str
    code: str
    level: str
    reasons: list[str]
    numbers: dict


class DemoHistoryPoint(BaseModel):
    date: str
    session_load: float
    level: str
    reasons: list[str]
    numbers: dict


@router.get("/demo/statuses", response_model=list[DemoStatus])
def demo_statuses() -> list[DemoStatus]:
    today = date.today()
    statuses: list[DemoStatus] = []
    for code in _DEMO_SQUADS:
        status = status_from_records(_demo_sessions(code), _demo_checkins(code), today)
        statuses.append(DemoStatus(player_id=code, code=code, **status))
    order = {"refer": 0, "act": 1, "watch": 2, "ok": 3}
    statuses.sort(key=lambda s: order.get(s.level, 9))
    return statuses


@router.get("/demo/athletes/{code}/history", response_model=list[DemoHistoryPoint])
def demo_history(code: str) -> list[DemoHistoryPoint]:
    code = code.upper()
    if code not in _DEMO_SQUADS:
        raise HTTPException(status_code=404, detail="Unknown demo athlete code.")
    return [DemoHistoryPoint(**p) for p in history_points(_demo_sessions(code))]
