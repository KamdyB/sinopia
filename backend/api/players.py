"""Athlete registration, roster listing, and per-athlete history."""
from backend.timeutil import service_date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.api.auth import require_accepted_coach, require_onboarded_coach
from backend.data.checkin_store import checkin_store
from backend.data.player_store import DuplicatePlayerError, player_store
from backend.data.session_store import session_store
from backend.scoring.history import history_points

router = APIRouter()
TeamType = Literal["girls", "boys", "mixed"]


class PlayerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=80)
    team_type: TeamType
    consent_confirmed: bool

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("Athlete label cannot be blank.")
        return cleaned

    @field_validator("consent_confirmed")
    @classmethod
    def _consent_required(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("Consent confirmation is required.")
        return value


class PlayerResponse(BaseModel):
    player_id: str
    name: str
    team_type: TeamType
    registered_date: str


class CheckinTokenResponse(BaseModel):
    token: str


class HistoryPoint(BaseModel):
    date: str
    session_load: float
    session_count: int
    level: str
    reasons: list[str]
    numbers: dict
    pain: bool = False
    pain_area: str | None = None
    pain_acknowledged: bool = False
    wellness_score: float | None = None


@router.post("/players", response_model=PlayerResponse, status_code=201)
def register_player(req: PlayerRequest, coach: dict = Depends(require_onboarded_coach)) -> PlayerResponse:
    try:
        player = player_store.register(req.name, coach["team_type"], service_date().isoformat(), coach["team_id"])
    except DuplicatePlayerError:
        raise HTTPException(status_code=409, detail="An athlete label is already registered for this team.")
    return PlayerResponse(**player)


@router.get("/players", response_model=list[PlayerResponse])
def list_players(team_type: TeamType, coach: dict = Depends(require_accepted_coach)) -> list[PlayerResponse]:
    return [PlayerResponse(**p) for p in player_store.list_for_team(coach["team_type"], coach["team_id"])]


@router.get("/players/{player_id}", response_model=PlayerResponse)
def get_player(player_id: str, coach: dict = Depends(require_accepted_coach)) -> PlayerResponse:
    player = player_store.get(player_id, coach["team_id"])
    if player is None:
        raise HTTPException(status_code=404, detail="Athlete not found.")
    return PlayerResponse(**player)


@router.get("/players/{player_id}/history", response_model=list[HistoryPoint])
def player_history(player_id: str, coach: dict = Depends(require_accepted_coach)) -> list[HistoryPoint]:
    if player_store.get(player_id, coach["team_id"]) is None:
        raise HTTPException(status_code=404, detail="Athlete not found.")
    sessions = session_store.get_sessions(player_id, coach["team_id"])
    checkins = checkin_store.get_checkins(player_id, coach["team_id"])
    return [HistoryPoint(**point) for point in history_points(sessions, checkins)]



@router.post("/players/{player_id}/checkin-token", response_model=CheckinTokenResponse)
def regenerate_checkin_token(
    player_id: str, coach: dict = Depends(require_accepted_coach)
) -> CheckinTokenResponse:
    token = player_store.regenerate_checkin_token(player_id, coach["team_id"])
    if token is None:
        raise HTTPException(status_code=404, detail="Athlete not found.")
    from backend.data.auth_store import auth_store
    auth_store.log_event("checkin_token_regenerated", coach["team_id"])
    return CheckinTokenResponse(token=token)



@router.post("/players/{player_id}/acknowledge-pain")
def acknowledge_pain(
    player_id: str, coach: dict = Depends(require_accepted_coach)
) -> dict[str, bool]:
    if player_store.get(player_id, coach["team_id"]) is None:
        raise HTTPException(status_code=404, detail="Athlete not found.")
    checkin_store.acknowledge_pain(player_id, coach["team_id"])
    from backend.data.auth_store import auth_store
    auth_store.log_event("pain_report_acknowledged", coach["team_id"])
    return {"acknowledged": True}



@router.delete("/players/{player_id}", status_code=204)
def delete_player(player_id: str, coach: dict = Depends(require_accepted_coach)) -> Response:
    if player_store.get(player_id, coach["team_id"]) is None:
        raise HTTPException(status_code=404, detail="Athlete not found.")
    if not player_store.delete_with_history(player_id, coach["team_id"]):
        raise HTTPException(status_code=404, detail="Athlete not found.")
    from backend.data.auth_store import auth_store
    auth_store.log_event("athlete_deleted", coach["team_id"])
    return Response(status_code=204)
