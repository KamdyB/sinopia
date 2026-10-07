"""Athlete registration, team roster listing, and per-athlete status history.
Orchestration and HTTP concerns only; storage and scoring live below it."""
from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from backend.data.player_store import DuplicatePlayerError, player_store
from backend.data.session_store import session_store
from backend.scoring.history import history_points

router = APIRouter()
TeamType = Literal["girls", "boys", "mixed"]


class PlayerRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    team_type: TeamType

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


class HistoryPoint(BaseModel):
    date: str
    session_load: float
    level: str
    reasons: list[str]
    numbers: dict


@router.post("/players", response_model=PlayerResponse, status_code=201)
def register_player(req: PlayerRequest) -> PlayerResponse:
    try:
        player = player_store.register(req.name, req.team_type, date.today().isoformat())
    except DuplicatePlayerError:
        raise HTTPException(
            status_code=409,
            detail=f'An athlete named "{req.name}" is already registered for this team.',
        )
    return PlayerResponse(**player)


@router.get("/players", response_model=list[PlayerResponse])
def list_players(team_type: TeamType) -> list[PlayerResponse]:
    return [PlayerResponse(**p) for p in player_store.list_for_team(team_type)]


@router.get("/players/{player_id}", response_model=PlayerResponse)
def get_player(player_id: str) -> PlayerResponse:
    player = player_store.get(player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="Athlete not found.")
    return PlayerResponse(**player)


@router.get("/players/{player_id}/history", response_model=list[HistoryPoint])
def player_history(player_id: str) -> list[HistoryPoint]:
    if player_store.get(player_id) is None:
        raise HTTPException(status_code=404, detail="Athlete not found.")
    sessions = session_store.get_sessions(player_id)
    return [HistoryPoint(**p) for p in history_points(sessions)]
