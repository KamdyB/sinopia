"""Logs a single training session for a registered athlete, then returns
her current status computed by the rules engine. HTTP orchestration only;
storage and scoring live below it."""
from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.data.player_store import player_store
from backend.data.session_store import session_store
from backend.scoring.athlete_status import status_from_sessions

router = APIRouter()

# There is no legitimate youth training session several hours long.
MAX_SESSION_MINUTES = 180


class StatusResponse(BaseModel):
    player_id: str
    level: str
    reasons: list[str]
    numbers: dict
    previous_level: str | None


class SessionRequest(BaseModel):
    player_id: str
    date_str: str
    duration_minutes: float = Field(gt=0, le=MAX_SESSION_MINUTES)
    rpe: float = Field(gt=0, le=10)


@router.post("/sessions", response_model=StatusResponse)
def log_session(req: SessionRequest) -> StatusResponse:
    if player_store.get(req.player_id) is None:
        raise HTTPException(
            status_code=404,
            detail="Athlete not found. Register the athlete first, then log sessions against their id.",
        )

    session_date = date.fromisoformat(req.date_str)
    if session_date > date.today():
        raise HTTPException(
            status_code=422,
            detail="Session date cannot be in the future. Log a session after it happens, not before.",
        )

    prior_sessions = session_store.get_sessions(req.player_id)
    previous_level: str | None = None
    if prior_sessions:
        last_prior_date = date.fromisoformat(max(s["date"] for s in prior_sessions))
        previous_level = status_from_sessions(prior_sessions, last_prior_date)["level"]

    session_store.log_session(
        req.player_id,
        {"date": req.date_str, "duration_minutes": req.duration_minutes, "rpe": req.rpe},
    )

    sessions = session_store.get_sessions(req.player_id)
    status = status_from_sessions(sessions, session_date)

    return StatusResponse(
        player_id=req.player_id,
        level=status["level"],
        reasons=status["reasons"],
        numbers=status["numbers"],
        previous_level=previous_level,
    )
