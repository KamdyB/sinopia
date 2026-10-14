"""Token-authenticated athlete check-ins. The date is set by the server."""
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.api.auth import require_accepted_coach
from backend.data.checkin_store import DuplicateCheckinError, checkin_store
from backend.data.player_store import player_store

router = APIRouter()
PainArea = Literal[
    "Head", "Shoulder", "Chest or back", "Hip or groin", "Thigh",
    "Knee", "Ankle or foot", "Other",
]


class CheckinRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    token: str = Field(min_length=30, max_length=128)
    sleep: int = Field(ge=1, le=5)
    energy: int = Field(ge=1, le=5)
    soreness: int = Field(ge=1, le=5)
    stress: int = Field(ge=1, le=5)
    pain: bool = False
    pain_area: PainArea | None = None

    @model_validator(mode="after")
    def _pain_needs_area(self) -> "CheckinRequest":
        if self.pain and self.pain_area is None:
            raise ValueError("Choose a pain area when reporting pain.")
        if not self.pain:
            self.pain_area = None
        return self


@router.get("/checkin/{token}")
def validate_checkin_link(token: str) -> dict:
    if len(token) < 30 or len(token) > 128 or player_store.get_by_checkin_token(token) is None:
        raise HTTPException(status_code=404, detail="Check-in link is not valid.")
    return {"valid": True}


@router.post("/checkins", status_code=201)
def log_checkin(req: CheckinRequest) -> dict:
    player = player_store.get_by_checkin_token(req.token)
    if player is None:
        raise HTTPException(status_code=404, detail="Check-in link is not valid.")
    try:
        checkin_store.log_checkin(
            player["player_id"],
            {
                "date": date.today().isoformat(),
                "sleep": req.sleep,
                "energy": req.energy,
                "soreness": req.soreness,
                "stress": req.stress,
                "pain": req.pain,
                "pain_area": req.pain_area,
            },
            player["team_id"],
        )
    except DuplicateCheckinError:
        raise HTTPException(status_code=409, detail="A check-in has already been submitted today.")
    return {"status": "recorded"}



@router.delete("/players/{player_id}/checkins/{checkin_id}")
def delete_checkin(
    player_id: str, checkin_id: int, coach: dict = Depends(require_accepted_coach)
) -> dict[str, bool]:
    if player_store.get(player_id, coach["team_id"]) is None:
        raise HTTPException(status_code=404, detail="Athlete not found.")
    if not checkin_store.delete_checkin(checkin_id, player_id, coach["team_id"]):
        raise HTTPException(status_code=404, detail="Check-in not found.")
    return {"deleted": True}
