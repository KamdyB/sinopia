"""Persistence for registered players; only this store accesses player rows."""
import uuid
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from backend.data.db import SessionLocal, create_tables, make_session_factory
from backend.data.models import CheckinLink, Player

class DuplicatePlayerError(Exception):
    def __init__(self, name: str, team_type: str):
        super().__init__(f'"{name}" is already registered for this team.')

class PlayerStore:
    def __init__(self, db_url: str | None = None):
        if db_url is None:
            self._engine, self._sessions = None, SessionLocal
            create_tables()
        else:
            self._engine, self._sessions = make_session_factory(db_url)

    @staticmethod
    def _dict(p, db):
        link = db.scalar(select(CheckinLink).where(CheckinLink.player_id == p.player_id))
        if link is None:
            link = CheckinLink(token=uuid.uuid4().hex + uuid.uuid4().hex, player_id=p.player_id)
            db.add(link)
            db.flush()
        return {"player_id":p.player_id,"name":p.name,"team_type":p.team_type,"registered_date":p.registered_date,"checkin_token":link.token}

    def register(self, name: str, team_type: str, registered_date: str) -> dict:
        p = Player(player_id=uuid.uuid4().hex, name=name, team_type=team_type, registered_date=registered_date)
        try:
            with self._sessions.begin() as db:
                db.add(p)
                db.flush()
                link = CheckinLink(token=uuid.uuid4().hex + uuid.uuid4().hex, player_id=p.player_id)
                db.add(link)
                db.flush()
                result = self._dict(p, db)
        except IntegrityError as exc:
            raise DuplicatePlayerError(name, team_type) from exc
        return result

    def get(self, player_id: str) -> dict | None:
        with self._sessions() as db:
            p = db.get(Player, player_id)
            return self._dict(p, db) if p else None

    def list_for_team(self, team_type: str) -> list[dict]:
        with self._sessions() as db:
            rows = db.scalars(select(Player).where(Player.team_type == team_type).order_by(func.lower(Player.name))).all()
            return [self._dict(p, db) for p in rows]

    def get_by_checkin_token(self, token: str) -> dict | None:
        with self._sessions() as db:
            link = db.get(CheckinLink, token)
            if link is None:
                return None
            p = db.get(Player, link.player_id)
            return self._dict(p, db) if p else None

player_store = PlayerStore()
