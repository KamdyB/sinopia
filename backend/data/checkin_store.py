"""Persistence for athlete check-ins; no joins, scoring, or HTTP."""
from sqlalchemy import select
from backend.data.db import SessionLocal, create_tables
from backend.data.models import Checkin

class CheckinStore:
    def __init__(self, db_url: str | None = None):
        create_tables()

    def log_checkin(self, player_id: str, checkin: dict) -> None:
        with SessionLocal.begin() as db:
            db.add(Checkin(player_id=player_id, date=checkin["date"], sleep=checkin["sleep"], energy=checkin["energy"], soreness=checkin["soreness"], stress=checkin["stress"], pain=bool(checkin["pain"]), pain_area=checkin["pain_area"]))

    def get_checkins(self, player_id: str) -> list[dict]:
        with SessionLocal() as db:
            rows = db.scalars(select(Checkin).where(Checkin.player_id == player_id).order_by(Checkin.date, Checkin.id)).all()
            return [{"date":r.date,"sleep":r.sleep,"energy":r.energy,"soreness":r.soreness,"stress":r.stress,"pain":bool(r.pain),"pain_area":r.pain_area} for r in rows]

checkin_store = CheckinStore()
