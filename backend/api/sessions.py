"""Logs a training session after validating the submitted values."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from backend.api.auth import require_accepted_coach
from backend.data.player_store import player_store
from backend.data.session_store import session_store
from backend.scoring.athlete_status import status_from_sessions

router = APIRouter()
MAX_SESSION_MINUTES = 600


class StatusResponse(BaseModel):
    player_id: str
    level: str
    reasons: list[str]
    numbers: dict
    previous_level: str | None


class SessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    player_id: str = Field(min_length=1, max_length=80)
    date_str: str = Field(min_length=10, max_length=10, pattern=r"^\d{4}-\d{2}-\d{2}$")
    duration_minutes: float = Field(ge=1, le=MAX_SESSION_MINUTES, allow_inf_nan=False)
    rpe: float = Field(ge=0, le=10, allow_inf_nan=False)


@router.post("/sessions", response_model=StatusResponse)
def log_session(req: SessionRequest, coach: dict = Depends(require_accepted_coach)) -> StatusResponse:
    player = player_store.get(req.player_id, coach["team_id"])
    if player is None:
        raise HTTPException(status_code=404, detail="Athlete not found.")

    try:
        session_date = date.fromisoformat(req.date_str)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid session date.")

    if session_date > date.today():
        raise HTTPException(status_code=422, detail="Session date cannot be in the future.")

    prior_sessions = session_store.get_sessions(req.player_id, coach["team_id"])
    previous_level: str | None = None
    if prior_sessions:
        last_prior_date = date.fromisoformat(max(s["date"] for s in prior_sessions))
        previous_level = status_from_sessions(prior_sessions, last_prior_date)["level"]

    session_store.log_session(
        req.player_id,
        {"date": req.date_str, "duration_minutes": req.duration_minutes, "rpe": req.rpe},
        coach["team_id"],
    )
    sessions = session_store.get_sessions(req.player_id, coach["team_id"])
    status = status_from_sessions(sessions, session_date)
    return StatusResponse(
        player_id=req.player_id,
        level=status["level"],
        reasons=status["reasons"],
        numbers=status["numbers"],
        previous_level=previous_level,
    )



@router.delete("/players/{player_id}/sessions/{session_id}")
def delete_session(
    player_id: str, session_id: int, coach: dict = Depends(require_accepted_coach)
) -> dict[str, bool]:
    if player_store.get(player_id, coach["team_id"]) is None:
        raise HTTPException(status_code=404, detail="Athlete not found.")
    if not session_store.delete_session(session_id, player_id, coach["team_id"]):
        raise HTTPException(status_code=404, detail="Session not found.")
    from backend.data.auth_store import auth_store
    auth_store.log_event("session_deleted", coach["team_id"])
    return {"deleted": True}
