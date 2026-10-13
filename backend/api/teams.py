"""Team creation and profile. A coach owns exactly one team; creation is
blocked by a database-level unique constraint on the verified coach
email. The profile carries sport, age band and composition, never a
gender label.
"""
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from backend.auth import CoachContext, get_coach
from backend.data.team_store import TeamExistsError, team_store

router = APIRouter()
Sport = Literal["football", "basketball", "netball", "rugby", "athletics", "volleyball", "handball", "team-running", "other"]
AgeBand = Literal["under-10", "under-12", "under-14", "under-16", "under-18", "mixed-ages", "other"]
Composition = Literal["full-squad", "small-squad", "school-club", "community-club", "other"]


def _clean(value: str | None, label: str, limit: int) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.split())
    if not cleaned:
        raise ValueError(f"{label} cannot be blank.")
    return cleaned[:limit]


class TeamCreateRequest(BaseModel):
    team_name: str = Field(min_length=1, max_length=60)
    sport: Sport
    age_band: AgeBand
    composition: Composition

    @field_validator("team_name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        cleaned = _clean(value, "Team name", 60)
        assert cleaned is not None
        return cleaned


class TeamProfileRequest(BaseModel):
    team_name: str | None = Field(default=None, min_length=1, max_length=60)
    sport: Sport | None = None
    age_band: AgeBand | None = None
    composition: Composition | None = None


class TeamResponse(BaseModel):
    team_id: str
    coach_email: str
    team_name: str
    sport: str
    age_band: str
    composition: str
    created_date: str


class TeamStatus(BaseModel):
    has_team: bool
    team: TeamResponse | None


@router.get("/teams/me", response_model=TeamStatus)
def get_team(coach: CoachContext = Depends(get_coach)) -> TeamStatus:
    team = team_store.get_by_coach(coach.email)
    return TeamStatus(has_team=team is not None, team=TeamResponse(**team) if team else None)


@router.post("/teams", response_model=TeamResponse, status_code=201)
def create_team(req: TeamCreateRequest, coach: CoachContext = Depends(get_coach)) -> TeamResponse:
    if team_store.get_by_coach(coach.email) is not None:
        raise HTTPException(
            status_code=409,
            detail="This Google account already owns a team.",
        )
    try:
        team = team_store.create(
            coach_email=coach.email,
            team_name=req.team_name,
            sport=req.sport,
            age_band=req.age_band,
            composition=req.composition,
            created_date=date.today().isoformat(),
        )
    except TeamExistsError:
        raise HTTPException(
            status_code=409,
            detail="This Google account already owns a team.",
        )
    return TeamResponse(**team)


@router.patch("/teams/me/profile", response_model=TeamResponse)
def update_profile(
    req: TeamProfileRequest, coach: CoachContext = Depends(get_coach)
) -> TeamResponse:
    team = team_store.get_by_coach(coach.email)
    if team is None:
        raise HTTPException(status_code=404, detail="No team yet. Create your team first.")
    updated = team_store.update_profile(
        team_id=team["team_id"],
        team_name=_clean(req.team_name, "Team name", 60),
        sport=req.sport,
        age_band=req.age_band,
        composition=req.composition,
    )
    return TeamResponse(**updated)
