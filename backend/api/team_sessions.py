"""Coach controls for an open team session and athlete effort check-ins."""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from backend.api.auth import require_onboarded_coach
from backend.timeutil import service_date
from backend.data.auth_store import auth_store
from backend.data.open_team_session_store import open_team_session_store

router = APIRouter(prefix="/team-sessions", tags=["team-sessions"])

class OpenSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    date_str: str = Field(min_length=10, max_length=10, pattern=r"^\d{4}-\d{2}-\d{2}$")
    duration_minutes: float = Field(gt=0, le=180, allow_inf_nan=False)

@router.get("/current")
def current_session(coach: dict = Depends(require_onboarded_coach)):
    return {"session": open_team_session_store.current(coach["team_id"])}

@router.post("/open", status_code=201)
def open_session(req: OpenSessionRequest, coach: dict = Depends(require_onboarded_coach)):
    try:
        session_date = date.fromisoformat(req.date_str)
    except ValueError:
        raise HTTPException(status_code=422, detail="Enter a valid session date.")
    if session_date > service_date():
        raise HTTPException(status_code=422, detail="Session date cannot be in the future.")
    try:
        session = open_team_session_store.open(coach["team_id"], req.date_str, req.duration_minutes)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    auth_store.log_event("team_session_opened", coach["team_id"])
    return session

@router.post("/close")
def close_session(coach: dict = Depends(require_onboarded_coach)):
    session = open_team_session_store.close(coach["team_id"])
    if session is None:
        raise HTTPException(status_code=409, detail="There is no open team session.")
    auth_store.log_event("team_session_closed", coach["team_id"])
    return session
