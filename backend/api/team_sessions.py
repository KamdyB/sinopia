"""Coach controls for opening and closing an athlete RPE check-in window."""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from backend.api.auth import get_current_coach, get_current_team
from backend.data.team_session_store import team_session_store

router = APIRouter(prefix="/team-sessions", tags=["team-sessions"])

class OpenSessionRequest(BaseModel):
    date_str: str
    duration_minutes: float = Field(gt=0, le=180)

@router.get("/current")
def get_current_session(coach: dict = Depends(get_current_coach), team: dict = Depends(get_current_team)):
    return {"session": team_session_store.current(team["team_id"])}

@router.post("/open", status_code=201)
def open_session(req: OpenSessionRequest, coach: dict = Depends(get_current_coach), team: dict = Depends(get_current_team)):
    try:
        session_date = date.fromisoformat(req.date_str)
    except ValueError:
        raise HTTPException(status_code=422, detail="Enter a valid session date.")
    if session_date > date.today():
        raise HTTPException(status_code=422, detail="Session date cannot be in the future.")
    try:
        return team_session_store.open(team["team_id"], req.date_str, req.duration_minutes)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

@router.post("/close")
def close_session(coach: dict = Depends(get_current_coach), team: dict = Depends(get_current_team)):
    session = team_session_store.close(team["team_id"])
    if not session:
        raise HTTPException(status_code=409, detail="There is no open team session.")
    return session
