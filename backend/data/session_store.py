"""Persistence for logged training sessions."""
from typing import List

from backend.data.db import DB_PATH, connect
from backend.scoring.load_calculator import Session

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id TEXT NOT NULL,
    date TEXT NOT NULL,
    duration_minutes REAL NOT NULL,
    rpe REAL NOT NULL,
    team_id TEXT
);
"""


class SessionStore:
    def __init__(self, db_path: str = DB_PATH):
        self._db_path = db_path
        with connect(self._db_path) as conn:
            conn.executescript(SCHEMA)
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(sessions)")}
            if "team_id" not in columns:
                conn.execute("ALTER TABLE sessions ADD COLUMN team_id TEXT")

    def log_session(self, player_id: str, session: Session, team_id: str | None = None) -> None:
        with connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO sessions (player_id, date, duration_minutes, rpe, team_id) "
                "VALUES (?, ?, ?, ?, ?)",
                (player_id, session["date"], session["duration_minutes"], session["rpe"], team_id),
            )

    def get_sessions(self, player_id: str, team_id: str | None = None) -> List[Session]:
        query = (
            "SELECT date, duration_minutes, rpe FROM sessions WHERE player_id = ?"
        )
        params: tuple = (player_id,)
        if team_id is not None:
            query += " AND team_id = ?"
            params += (team_id,)
        query += " ORDER BY date, id"
        with connect(self._db_path) as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            {
                "date": row["date"],
                "duration_minutes": row["duration_minutes"],
                "rpe": row["rpe"],
            }
            for row in rows
        ]

    def delete_for_player(self, player_id: str, team_id: str | None = None) -> None:
        query = "DELETE FROM sessions WHERE player_id = ?"
        params: tuple = (player_id,)
        if team_id is not None:
            query += " AND team_id = ?"
            params += (team_id,)
        with connect(self._db_path) as conn:
            conn.execute(query, params)


session_store = SessionStore()
