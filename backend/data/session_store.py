"""Persistence for logged training sessions."""
from sqlalchemy import select
from backend.data.db import SessionLocal, create_tables, make_session_factory
from backend.data.models import TrainingSession
from backend.scoring.load_calculator import Session

class SessionStore:
    def __init__(self, db_url: str | None = None):
        if db_url is None:
            self._engine, self._sessions = None, SessionLocal
            create_tables()
        else:
            self._engine, self._sessions = make_session_factory(db_url)

    def log_session(self, player_id: str, session: Session) -> None:
        with self._sessions.begin() as db:
            db.add(TrainingSession(player_id=player_id, date=session["date"], duration_minutes=session["duration_minutes"], rpe=session["rpe"]))

    def get_sessions(self, player_id: str) -> list[Session]:
        with self._sessions() as db:
            rows = db.scalars(select(TrainingSession).where(TrainingSession.player_id == player_id).order_by(TrainingSession.date, TrainingSession.id)).all()
            return [{"date":r.date,"duration_minutes":r.duration_minutes,"rpe":r.rpe} for r in rows]

session_store = SessionStore()
