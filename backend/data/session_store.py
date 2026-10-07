import sqlite3
from typing import List

from backend.data.db import DB_PATH, connect
from backend.scoring.load_calculator import Session

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
id INTEGER PRIMARY KEY AUTOINCREMENT,
player_id TEXT NOT NULL,
date TEXT NOT NULL,
duration_minutes REAL NOT NULL,
rpe REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS profiles (
player_id TEXT PRIMARY KEY,
menstruating INTEGER,
height_cm REAL,
height_cm_6mo_ago REAL
);
"""


class SessionStore:
    def __init__(self, db_path: str = DB_PATH):
        self._db_path = db_path
        with connect(self._db_path) as conn:
            conn.executescript(SCHEMA)

    def log_session(self, player_id: str, session: Session) -> None:
        with connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO sessions (player_id, date, duration_minutes, rpe) "
                "VALUES (?, ?, ?, ?)",
                (player_id, session["date"], session["duration_minutes"], session["rpe"]),
            )

    def get_sessions(self, player_id: str) -> List[Session]:
        # Ordering by id as a tiebreak makes same-day sessions deterministic
        # for the walk-forward history computation.
        with connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT date, duration_minutes, rpe FROM sessions "
                "WHERE player_id = ? ORDER BY date, id",
                (player_id,),
            ).fetchall()
        return [
            {"date": row["date"], "duration_minutes": row["duration_minutes"], "rpe": row["rpe"]}
            for row in rows
        ]

    def update_profile(
        self,
        player_id: str,
        menstruating: bool | None,
        height_cm: float | None,
        height_cm_6mo_ago: float | None,
    ) -> None:
        existing = self.get_profile(player_id)
        merged = {
            "menstruating": menstruating if menstruating is not None else existing.get("menstruating"),
            "height_cm": height_cm if height_cm is not None else existing.get("height_cm"),
            "height_cm_6mo_ago": height_cm_6mo_ago if height_cm_6mo_ago is not None else existing.get("height_cm_6mo_ago"),
        }
        with connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO profiles (player_id, menstruating, height_cm, height_cm_6mo_ago) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT(player_id) DO UPDATE SET "
                "menstruating = excluded.menstruating, "
                "height_cm = excluded.height_cm, "
                "height_cm_6mo_ago = excluded.height_cm_6mo_ago",
                (
                    player_id,
                    None if merged["menstruating"] is None else int(merged["menstruating"]),
                    merged["height_cm"],
                    merged["height_cm_6mo_ago"],
                ),
            )

    def get_profile(self, player_id: str) -> dict:
        with connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT menstruating, height_cm, height_cm_6mo_ago FROM profiles WHERE player_id = ?",
                (player_id,),
            ).fetchone()
        if row is None:
            return {}
        return {
            "menstruating": None if row["menstruating"] is None else bool(row["menstruating"]),
            "height_cm": row["height_cm"],
            "height_cm_6mo_ago": row["height_cm_6mo_ago"],
        }


session_store = SessionStore()
