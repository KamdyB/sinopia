"""Persistence for a team's currently open training session."""
import uuid
from sqlalchemy import select
from backend.data.db import SessionLocal, create_tables, make_session_factory
from backend.data.models import OpenTeamSession

class TeamSessionStore:
    def __init__(self, db_url: str | None = None):
        if db_url is None:
            self._engine, self._sessions = None, SessionLocal
            create_tables()
        else:
            self._engine, self._sessions = make_session_factory(db_url)

    @staticmethod
    def _dict(row):
        return {"session_id":row.session_id,"team_id":row.team_id,"date":row.date,
                "duration_minutes":row.duration_minutes,"is_open":bool(row.is_open)}

    def current(self, team_id: str) -> dict | None:
        with self._sessions() as db:
            row = db.scalar(select(OpenTeamSession).where(
                OpenTeamSession.team_id == team_id, OpenTeamSession.is_open.is_(True)
            ).order_by(OpenTeamSession.session_id.desc()))
            return self._dict(row) if row else None

    def open(self, team_id: str, date: str, duration_minutes: float) -> dict:
        with self._sessions.begin() as db:
            existing = db.scalar(select(OpenTeamSession).where(
                OpenTeamSession.team_id == team_id, OpenTeamSession.is_open.is_(True)
            ))
            if existing:
                raise ValueError("A team session is already open. Close it before opening another.")
            row = OpenTeamSession(session_id=uuid.uuid4().hex, team_id=team_id,
                                  date=date, duration_minutes=duration_minutes, is_open=True)
            db.add(row)
            db.flush()
            return self._dict(row)

    def close(self, team_id: str) -> dict | None:
        with self._sessions.begin() as db:
            row = db.scalar(select(OpenTeamSession).where(
                OpenTeamSession.team_id == team_id, OpenTeamSession.is_open.is_(True)
            ))
            if not row:
                return None
            row.is_open = False
            db.flush()
            return self._dict(row)

team_session_store = TeamSessionStore()
