"""Persistence for registered players. One row per real player, created once,
independent of any session. Opaque ids keep names out of URLs and keep two
same-named players on different teams structurally separate forever."""
import sqlite3
import uuid

from backend.data.db import DB_PATH, connect

CREATE_PLAYERS = """
CREATE TABLE IF NOT EXISTS players (
    player_id TEXT PRIMARY KEY,
    name TEXT NOT NULL COLLATE NOCASE,
    team_type TEXT NOT NULL,
    registered_date TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_players_team_name
    ON players (team_type, name);
"""


class DuplicatePlayerError(Exception):
    def __init__(self, name: str, team_type: str):
        super().__init__(f'"{name}" is already registered for this team.')


class PlayerStore:
    def __init__(self, db_path: str = DB_PATH):
        self._db_path = db_path
        with connect(self._db_path) as conn:
            conn.executescript(CREATE_PLAYERS)

    def register(self, name: str, team_type: str, registered_date: str) -> dict:
        player_id = uuid.uuid4().hex
        try:
            with connect(self._db_path) as conn:
                conn.execute(
                    "INSERT INTO players (player_id, name, team_type, registered_date) "
                    "VALUES (?, ?, ?, ?)",
                    (player_id, name, team_type, registered_date),
                )
        except sqlite3.IntegrityError as exc:
            raise DuplicatePlayerError(name, team_type) from exc
        return {
            "player_id": player_id,
            "name": name,
            "team_type": team_type,
            "registered_date": registered_date,
        }

    def get(self, player_id: str) -> dict | None:
        with connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT player_id, name, team_type, registered_date "
                "FROM players WHERE player_id = ?",
                (player_id,),
            ).fetchone()
        return dict(row) if row else None

    def list_for_team(self, team_type: str) -> list[dict]:
        with connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT player_id, name, team_type, registered_date "
                "FROM players WHERE team_type = ? ORDER BY name COLLATE NOCASE",
                (team_type,),
            ).fetchall()
        return [dict(row) for row in rows]


player_store = PlayerStore()
