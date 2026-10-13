"""Persistence for registered athletes. One row per real athlete,
created once, independent of any session. Team scoping travels with
every row. Only an opaque athlete code is ever stored, never a full
name, so a leak of this table exposes nothing personal about minors.
"""
import sqlite3
import uuid

from backend.data.db import DB_PATH, connect, run_script

CREATE_PLAYERS = """
CREATE TABLE IF NOT EXISTS players (
    player_id TEXT PRIMARY KEY,
    code TEXT NOT NULL,
    team_id TEXT NOT NULL,
    registered_date TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_players_team_code
ON players (team_id, code);
"""


class DuplicatePlayerError(Exception):
    def __init__(self, code: str, team_id: str):
        super().__init__(f'"{code}" is already registered for this team.')


def _is_unique_violation(exc: Exception) -> bool:
    return type(exc).__name__ in {"IntegrityError", "UniqueViolation"}


class PlayerStore:
    def __init__(self, db_path: str = DB_PATH):
        self._db_path = db_path
        with connect(self._db_path) as conn:
            run_script(conn, CREATE_PLAYERS)

    def register(self, code: str, team_id: str, registered_date: str) -> dict:
        player_id = uuid.uuid4().hex
        try:
            with connect(self._db_path) as conn:
                conn.execute(
                    "INSERT INTO players (player_id, code, team_id, registered_date) "
                    "VALUES (?, ?, ?, ?)",
                    (player_id, code, team_id, registered_date),
                )
        except Exception as exc:
            if _is_unique_violation(exc):
                raise DuplicatePlayerError(code, team_id) from exc
            raise
        return {
            "player_id": player_id,
            "code": code,
            "team_id": team_id,
            "registered_date": registered_date,
        }

    def get(self, player_id: str) -> dict | None:
        with connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT player_id, code, team_id, registered_date "
                "FROM players WHERE player_id = ?",
                (player_id,),
            ).fetchone()
        return dict(row) if row else None

    def list_for_team(self, team_id: str) -> list[dict]:
        with connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT player_id, code, team_id, registered_date "
                "FROM players WHERE team_id = ? ORDER BY UPPER(code)",
                (team_id,),
            ).fetchall()
        return [dict(row) for row in rows]


player_store = PlayerStore()
