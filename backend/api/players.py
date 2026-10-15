"""Athlete registration, team roster listing, and per-athlete status history.
Orchestration and HTTP concerns only; storage and scoring live below it."""
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from backend.api.auth import get_current_coach, get_current_team
from backend.data.player_store import DuplicatePlayerError, player_store
from backend.data.session_store import session_store
from backend.scoring.history import history_points

router = APIRouter()
TeamType = Literal["girls", "boys", "mixed"]


class PlayerRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    team_type: TeamType | None = None

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("Athlete name cannot be blank.")
        return cleaned


class PlayerResponse(BaseModel):
    player_id: str
    name: str
    team_type: TeamType
    registered_date: str
    checkin_token: str
    team_id: str


class HistoryPoint(BaseModel):
    date: str
    session_load: float
    level: str
    reasons: list[str]
    numbers: dict


@router.post("/players", response_model=PlayerResponse, status_code=201)
def register_player(req: PlayerRequest, coach: dict = Depends(get_current_coach), team: dict = Depends(get_current_team)) -> PlayerResponse:
    try:
        player = player_store.register(req.name, team["team_type"], date.today().isoformat(), team["team_id"])
    except DuplicatePlayerError:
        raise HTTPException(
            status_code=409,
            detail=f'An athlete named "{req.name}" is already registered for this team.',
        )
    return PlayerResponse(**player)


@router.get("/players", response_model=list[PlayerResponse])
def list_players(team_type: TeamType | None = None, coach: dict = Depends(get_current_coach), team: dict = Depends(get_current_team)) -> list[PlayerResponse]:
    return [PlayerResponse(**p) for p in player_store.list_for_team(team["team_type"], team["team_id"])]


@router.get("/players/{player_id}", response_model=PlayerResponse)
def get_player(player_id: str, coach: dict = Depends(get_current_coach), team: dict = Depends(get_current_team)) -> PlayerResponse:
    player = player_store.get(player_id)
    if player is None or player["team_id"] != team["team_id"]:
        raise HTTPException(status_code=404, detail="Athlete not found.")
    return PlayerResponse(**player)


@router.get("/players/{player_id}/history", response_model=list[HistoryPoint])
def player_history(player_id: str, coach: dict = Depends(get_current_coach), team: dict = Depends(get_current_team)) -> list[HistoryPoint]:
    player = player_store.get(player_id)
    if player is None or player["team_id"] != team["team_id"]:
        raise HTTPException(status_code=404, detail="Athlete not found.")
    sessions = session_store.get_sessions(player_id)
    return [HistoryPoint(**p) for p in history_points(sessions)]


@router.get("/check-in/{token}", response_model=PlayerResponse)
def resolve_checkin_link(token: str) -> PlayerResponse:
    player = player_store.get_by_checkin_token(token)
    if player is None:
        raise HTTPException(status_code=404, detail="This check-in link is not valid.")
    return PlayerResponse(**player)
