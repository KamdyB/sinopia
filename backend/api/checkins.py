"""Athlete check-in endpoint. The date is set by the server."""
from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.data.checkin_store import DuplicateCheckinError, checkin_store
from backend.data.player_store import player_store

router = APIRouter()
PainArea = Literal[
    "Head", "Shoulder", "Chest or back", "Hip or groin", "Thigh",
    "Knee", "Ankle or foot", "Other",
]


class CheckinRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    player_id: str = Field(min_length=1, max_length=80)
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


@router.post("/checkins", status_code=201)
def log_checkin(req: CheckinRequest) -> dict:
    if player_store.get(req.player_id) is None:
        raise HTTPException(status_code=404, detail="Athlete not found.")
    try:
        checkin_store.log_checkin(
            req.player_id,
            {
                "date": date.today().isoformat(),
                "sleep": req.sleep,
                "energy": req.energy,
                "soreness": req.soreness,
                "stress": req.stress,
                "pain": req.pain,
                "pain_area": req.pain_area,
            },
        )
    except DuplicateCheckinError:
        raise HTTPException(status_code=409, detail="A check-in has already been submitted today.")
    return {"status": "recorded"}
