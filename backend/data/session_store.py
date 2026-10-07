"""Persistence for logged training sessions.

One responsibility: the sessions table. The old profiles table carried
cycle and growth context that the current scoring spec no longer uses,
so the schema migration drops it rather than leaving dormant data about
minors in storage.
"""
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
DROP TABLE IF EXISTS profiles;
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
            {
                "date": row["date"],
                "duration_minutes": row["duration_minutes"],
                "rpe": row["rpe"],
            }
            for row in rows
        ]


session_store = SessionStore()
