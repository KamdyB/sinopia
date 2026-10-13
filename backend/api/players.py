"""Athlete registration, team roster listing, and per-athlete status
history, all scoped to the signed-in coach's team. Athletes carry an
opaque code only; no names are accepted or stored anywhere. Storage
and scoring live below this module, untouched.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from backend.auth import CoachContext, get_coach, require_team
from backend.data.player_store import DuplicatePlayerError, player_store
from backend.data.session_store import session_store

router = APIRouter()

CODE_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,23}$"


def _clean_code(value: str) -> str:
    cleaned = " ".join(value.split())
    if not cleaned:
        raise ValueError("Athlete code cannot be blank.")
    cleaned = cleaned.replace(" ", "-").upper()
    return cleaned


class PlayerRequest(BaseModel):
    code: str = Field(min_length=1, max_length=24, pattern=CODE_PATTERN)

    @field_validator("code")
    @classmethod
    def _normalise_code(cls, value: str) -> str:
        return _clean_code(value)


class PlayerResponse(BaseModel):
    player_id: str
    code: str
    registered_date: str


class PublicPlayerResponse(BaseModel):
    """Served to the athlete's check-in page from a shared link: code only."""

    player_id: str
    code: str
    registered_date: str


class HistoryPoint(BaseModel):
    date: str
    session_load: float
    level: str
    reasons: list[str]
    numbers: dict


@router.post("/players", response_model=PlayerResponse, status_code=201)
def register_player(
    req: PlayerRequest, coach: CoachContext = Depends(get_coach)
) -> PlayerResponse:
    team = require_team(coach)
    try:
        player = player_store.register(req.code, team["team_id"], date.today().isoformat())
    except DuplicatePlayerError:
        raise HTTPException(
            status_code=409,
            detail=f'An athlete with the code "{req.code}" is already registered for this team.',
        )
    return PlayerResponse(**player)


@router.get("/players", response_model=list[PlayerResponse])
def list_players(coach: CoachContext = Depends(get_coach)) -> list[PlayerResponse]:
    team = require_team(coach)
    return [
        PlayerResponse(**p)
        for p in player_store.list_for_team(team["team_id"])
    ]


@router.get("/players/{player_id}", response_model=PublicPlayerResponse)
def get_player(player_id: str) -> PublicPlayerResponse:
    # Public by design: reached from the check-in link the coach shared.
    # Deliberately returns the code, never the team id or any roster.
    player = player_store.get(player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="Athlete not found.")
    return PublicPlayerResponse(**player)


@router.get("/players/{player_id}/history", response_model=list[HistoryPoint])
def player_history(
    player_id: str, coach: CoachContext = Depends(get_coach)
) -> list[HistoryPoint]:
    team = require_team(coach)
    player = player_store.get(player_id)
    if player is None or player["team_id"] != team["team_id"]:
        raise HTTPException(status_code=404, detail="Athlete not found.")
    # Scoping travels with the team id resolved from the coach above.
    sessions = session_store.get_sessions(player_id, team["team_id"])
    from backend.scoring.history import history_points  # scoring module, untouched
    return [HistoryPoint(**p) for p in history_points(sessions)]
