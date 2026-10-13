"""Athlete check-in endpoint. No accounts: the athlete reaches it from
the link the coach shared. The team id is derived server side from the
athlete's own record, so the request itself cannot cross teams. The
date is set by the server, never the client."""
from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from backend.data.checkin_store import checkin_store
from backend.data.player_store import player_store

router = APIRouter()


class CheckinRequest(BaseModel):
    player_id: str
    sleep: int = Field(ge=1, le=5)
    energy: int = Field(ge=1, le=5)
    soreness: int = Field(ge=1, le=5)
    stress: int = Field(ge=1, le=5)
    pain: bool = False
    pain_area: str | None = None

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
    player = player_store.get(req.player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="Athlete not found.")
    # The team id comes from the athlete's record on the server side.
    checkin_store.log_checkin(
        req.player_id,
        player["team_id"],
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
