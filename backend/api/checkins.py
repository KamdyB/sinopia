"""Athlete check-in endpoint. No accounts: the athlete id comes from the
link the coach shared. The date is set by the server, never the client."""
from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from backend.data.checkin_store import checkin_store
from backend.data.player_store import player_store
from backend.data.session_store import session_store
from backend.data.team_session_store import team_session_store

router = APIRouter()


class CheckinRequest(BaseModel):
    checkin_token: str
    sleep: int = Field(ge=1, le=5)
    energy: int = Field(ge=1, le=5)
    soreness: int = Field(ge=1, le=5)
    stress: int = Field(ge=1, le=5)
    pain: bool = False
    pain_area: str | None = None
    rpe: int | None = Field(default=None, ge=0, le=10)

    @model_validator(mode="after")
    def _pain_needs_area(self) -> "CheckinRequest":
        if self.pain:
            if not (self.pain_area and self.pain_area.strip()):
                raise ValueError("Pain area is required when pain is reported.")
        else:
            self.pain_area = None
        return self


@router.post("/checkins", status_code=201)
def log_checkin(req: CheckinRequest) -> None:
    player = player_store.get_by_checkin_token(req.checkin_token)
    if player is None:
        raise HTTPException(status_code=404, detail="This check-in link is not valid.")
    open_session = team_session_store.current(player["team_id"])
    if open_session and req.rpe is None:
        raise HTTPException(status_code=422, detail="An effort rating is required while the team session is open.")
    if not open_session and req.rpe is not None:
        raise HTTPException(status_code=409, detail="There is no open team session for an effort rating.")
    if open_session:
        previous = session_store.get_sessions(player["player_id"])
        already_logged = any(s["date"] == open_session["date"] and s["duration_minutes"] == open_session["duration_minutes"] for s in previous)
        if not already_logged:
            session_store.log_session(player["player_id"], {"date": open_session["date"], "duration_minutes": open_session["duration_minutes"], "rpe": req.rpe})
    checkin_store.log_checkin(
        player["player_id"],
        {
            "date": date.today().isoformat(),
            "sleep": req.sleep,
            "energy": req.energy,
            "soreness": req.soreness,
            "stress": req.stress,
            "pain": req.pain,
            "pain_area": req.pain_area.strip() if req.pain_area else None,
        },
    )
