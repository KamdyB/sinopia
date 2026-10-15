"""Token-authenticated athlete check-ins. The date is set by the server."""
import hashlib
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.api.auth import require_accepted_coach
from backend.timeutil import service_date
from backend.data.checkin_store import DuplicateCheckinError, checkin_store
from backend.data.player_store import player_store
from backend.data.session_store import session_store
from backend.data.open_team_session_store import open_team_session_store
from backend.security.rate_limit import client_ip, enforce_rate_limit

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
    rpe: int | None = Field(default=None, ge=0, le=10)

    @model_validator(mode="after")
    def _pain_needs_area(self) -> "CheckinRequest":
        if self.pain and self.pain_area is None:
            raise ValueError("Choose a pain area when reporting pain.")
        if not self.pain:
            self.pain_area = None
        return self


class CheckinValidationResponse(BaseModel):
    valid: bool
    session_open: bool = False
    session_date: str | None = None
    session_duration_minutes: float | None = None


class CheckinCreatedResponse(BaseModel):
    status: Literal["recorded"]


class CheckinTokenValidationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    token: str = Field(min_length=30, max_length=128)


@router.post("/checkin/validate", response_model=CheckinValidationResponse)
def validate_checkin_link(payload: CheckinTokenValidationRequest, request: Request) -> dict:
    ip = client_ip(request)
    token_digest = hashlib.sha256(payload.token.encode()).hexdigest()
    retry_after = enforce_rate_limit(("checkin-token-validation", ip, token_digest), 10, 60)
    if retry_after is not None:
        raise HTTPException(status_code=429, detail="Too many link validation attempts. Try again later.",
                            headers={"Retry-After": str(retry_after)})
    player = player_store.get_by_checkin_token(payload.token)
    if player is None:
        raise HTTPException(status_code=404, detail="Check-in link is not valid.")
    session = open_team_session_store.current(player["team_id"])
    return {"valid": True, "session_open": bool(session),
            "session_date": session["session_date"] if session else None,
            "session_duration_minutes": session["duration_minutes"] if session else None}


@router.post("/checkins", status_code=201, response_model=CheckinCreatedResponse)
def log_checkin(req: CheckinRequest, request: Request) -> dict:
    ip = client_ip(request)
    token_digest = hashlib.sha256(req.token.encode()).hexdigest()
    retry_after = enforce_rate_limit(("checkin-token", ip, token_digest), 10, 60)
    if retry_after is not None:
        raise HTTPException(status_code=429, detail="Too many check-in attempts. Try again later.",
                            headers={"Retry-After": str(retry_after)})
    player = player_store.get_by_checkin_token(req.token)
    if player is None:
        raise HTTPException(status_code=404, detail="Check-in link is not valid.")
    open_session = open_team_session_store.current(player["team_id"])
    if open_session and req.rpe is None:
        raise HTTPException(status_code=422, detail="Add an effort rating while the team session is open.")
    if not open_session and req.rpe is not None:
        raise HTTPException(status_code=409, detail="There is no open team session for an effort rating.")
    try:
        checkin_store.log_checkin(
            player["player_id"],
            {"date": service_date().isoformat(), "sleep": req.sleep, "energy": req.energy,
             "soreness": req.soreness, "stress": req.stress, "pain": req.pain, "pain_area": req.pain_area},
            player["team_id"],
        )
    except DuplicateCheckinError:
        raise HTTPException(status_code=409, detail="A check-in has already been submitted today.")
    if open_session and req.rpe is not None:
        previous = session_store.get_sessions(player["player_id"], player["team_id"])
        already_logged = any(
            item["date"] == open_session["session_date"]
            and item["duration_minutes"] == open_session["duration_minutes"]
            for item in previous
        )
        if not already_logged:
            session_store.log_session(
                player["player_id"],
                {"date": open_session["session_date"], "duration_minutes": open_session["duration_minutes"], "rpe": req.rpe},
                player["team_id"],
            )
    from backend.data.auth_store import auth_store
    auth_store.log_event("checkin_submitted", player["team_id"])
    return {"status": "recorded"}


@router.delete("/players/{player_id}/checkins/{checkin_id}")
def delete_checkin(
    player_id: str, checkin_id: int, coach: dict = Depends(require_accepted_coach)
) -> dict[str, bool]:
    if player_store.get(player_id, coach["team_id"]) is None:
        raise HTTPException(status_code=404, detail="Athlete not found.")
    if not checkin_store.delete_checkin(checkin_id, player_id, coach["team_id"]):
        raise HTTPException(status_code=404, detail="Check-in not found.")
    from backend.data.auth_store import auth_store
    auth_store.log_event("checkin_deleted", coach["team_id"])
    return {"deleted": True}
