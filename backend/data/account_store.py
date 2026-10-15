"""Persistence for coach accounts and their single team."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from backend.data.db import SessionLocal, create_tables, make_session_factory
from backend.data.models import Coach, Team

class AccountStore:
    def __init__(self, db_url: str | None = None):
        if db_url is None:
            self._engine, self._sessions = None, SessionLocal
            create_tables()
        else:
            self._engine, self._sessions = make_session_factory(db_url)

    def upsert_coach(self, google_sub: str, email: str, display_name: str, declarations: bool = False) -> dict:
        with self._sessions.begin() as db:
            coach = db.get(Coach, google_sub)
            if coach is None:
                coach = Coach(google_sub=google_sub, email=email, display_name=display_name)
                db.add(coach)
            else:
                coach.email = email
                coach.display_name = display_name
            if declarations:
                now = datetime.now(timezone.utc).isoformat()
                coach.adult_confirmed_at = now
                coach.authorization_confirmed_at = now
            db.flush()
            return {"google_sub":coach.google_sub,"email":coach.email,"display_name":coach.display_name,"adult_confirmed_at":coach.adult_confirmed_at,"authorization_confirmed_at":coach.authorization_confirmed_at}

    def get_coach(self, google_sub: str) -> dict | None:
        with self._sessions() as db:
            coach = db.get(Coach, google_sub)
            return {"google_sub":coach.google_sub,"email":coach.email,"display_name":coach.display_name} if coach else None

    def create_team(self, coach_id: str, name: str, team_type: str) -> dict:
        with self._sessions.begin() as db:
            existing = db.scalar(select(Team).where(Team.coach_id == coach_id))
            if existing:
                raise ValueError("A team has already been created for this coach.")
            team = Team(team_id=uuid.uuid4().hex, coach_id=coach_id, name=name, team_type=team_type, terms_accepted_at=datetime.now(timezone.utc).isoformat())
            db.add(team)
            db.flush()
            return {"team_id":team.team_id,"coach_id":team.coach_id,"name":team.name,"team_type":team.team_type,"terms_accepted_at":team.terms_accepted_at}

    def get_team(self, coach_id: str) -> dict | None:
        with self._sessions() as db:
            team = db.scalar(select(Team).where(Team.coach_id == coach_id))
            return {"team_id":team.team_id,"coach_id":team.coach_id,"name":team.name,"team_type":team.team_type} if team else None

account_store = AccountStore()
