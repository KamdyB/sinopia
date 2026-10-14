"""Athlete registration, roster listing, and per-athlete history."""
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.api.auth import require_accepted_coach
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
    level: str
    reasons: list[str]
    numbers: dict


@router.post("/players", response_model=PlayerResponse, status_code=201)
def register_player(req: PlayerRequest, coach: dict = Depends(require_accepted_coach)) -> PlayerResponse:
    try:
        player = player_store.register(req.name, req.team_type, date.today().isoformat(), coach["team_id"])
    except DuplicatePlayerError:
        raise HTTPException(status_code=409, detail="An athlete label is already registered for this team.")
    return PlayerResponse(**player)


@router.get("/players", response_model=list[PlayerResponse])
def list_players(team_type: TeamType, coach: dict = Depends(require_accepted_coach)) -> list[PlayerResponse]:
    return [PlayerResponse(**p) for p in player_store.list_for_team(team_type, coach["team_id"])]


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
    return [HistoryPoint(**p) for p in history_points(session_store.get_sessions(player_id, coach["team_id"]))]



@router.post("/players/{player_id}/checkin-token", response_model=CheckinTokenResponse)
def regenerate_checkin_token(
    player_id: str, coach: dict = Depends(require_accepted_coach)
) -> CheckinTokenResponse:
    token = player_store.regenerate_checkin_token(player_id, coach["team_id"])
    if token is None:
        raise HTTPException(status_code=404, detail="Athlete not found.")
    return CheckinTokenResponse(token=token)
