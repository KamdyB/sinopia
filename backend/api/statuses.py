"""One request returning the current status of every athlete on a team,
sorted most urgent first. Built for a slow connection: the dashboard
needs a single call, not one per athlete."""
from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel

from backend.api.players import TeamType
from backend.data.checkin_store import checkin_store
from backend.data.player_store import player_store
from backend.data.session_store import session_store
from backend.scoring.athlete_status import status_from_records

router = APIRouter()


class AthleteStatus(BaseModel):
    player_id: str
    name: str
    level: str
    reasons: list[str]
    numbers: dict


@router.get("/statuses", response_model=list[AthleteStatus])
def team_statuses(team_type: TeamType) -> list[AthleteStatus]:
    today = date.today()
    statuses: list[AthleteStatus] = []
    for player in player_store.list_for_team(team_type):
        sessions = session_store.get_sessions(player["player_id"])
        checkins = checkin_store.get_checkins(player["player_id"])
        status = status_from_records(sessions, checkins, today)
        statuses.append(
            AthleteStatus(
                player_id=player["player_id"],
                name=player["name"],
                **status,
            )
        )
    order = {"refer": 0, "act": 1, "watch": 2, "ok": 3}
    statuses.sort(key=lambda s: order.get(s.level, 9))
    return statuses
