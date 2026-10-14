"""Persistence for registered players, scoped to the owning team."""
import hashlib
import secrets
import sqlite3
import uuid

from backend.data.db import DB_PATH, connect

CREATE_PLAYERS = """
CREATE TABLE IF NOT EXISTS players (
    player_id TEXT PRIMARY KEY,
    name TEXT NOT NULL COLLATE NOCASE,
    team_type TEXT NOT NULL,
    registered_date TEXT NOT NULL,
    team_id TEXT,
    checkin_token TEXT
);
"""


class DuplicatePlayerError(Exception):
    def __init__(self, name: str, team_type: str):
        super().__init__("An athlete label is already registered for this team.")


class PlayerStore:
    def __init__(self, db_path: str = DB_PATH):
        self._db_path = db_path
        with connect(self._db_path) as conn:
            conn.executescript(CREATE_PLAYERS)
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(players)")}
            if "team_id" not in columns:
                conn.execute("ALTER TABLE players ADD COLUMN team_id TEXT")
            if "checkin_token" not in columns:
                conn.execute("ALTER TABLE players ADD COLUMN checkin_token TEXT")
            # Existing player rows get independent random tokens; player IDs are never check-in credentials.
            rows = conn.execute(
                "SELECT player_id FROM players WHERE checkin_token IS NULL"
            ).fetchall()
            for row in rows:
                token = secrets.token_urlsafe(32)
                digest = hashlib.sha256(token.encode()).hexdigest()
                conn.execute(
                    "UPDATE players SET checkin_token = ? WHERE player_id = ?",
                    (digest, row["player_id"]),
                )
            conn.execute("DROP INDEX IF EXISTS idx_players_team_name")
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_players_team_name "
                "ON players (team_id, team_type, name)"
            )
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_players_checkin_token "
                "ON players (checkin_token)"
            )

    def register(
        self, name: str, team_type: str, registered_date: str,
        team_id: str = "development-team",
    ) -> dict:
        player_id = uuid.uuid4().hex
        checkin_token = secrets.token_urlsafe(32)
        try:
            with connect(self._db_path) as conn:
                conn.execute(
                    "INSERT INTO players "
                    "(player_id, name, team_type, registered_date, team_id, checkin_token) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (player_id, name, team_type, registered_date, team_id, hashlib.sha256(checkin_token.encode()).hexdigest()),
                )
        except sqlite3.IntegrityError as exc:
            raise DuplicatePlayerError(name, team_type) from exc
        return {
            "player_id": player_id,
            "name": name,
            "team_type": team_type,
            "registered_date": registered_date,
            "team_id": team_id,
        }

    def get(self, player_id: str, team_id: str | None = None) -> dict | None:
        query = (
            "SELECT player_id, name, team_type, registered_date, team_id "
            "FROM players WHERE player_id = ?"
        )
        params: tuple = (player_id,)
        if team_id is not None:
            query += " AND team_id = ?"
            params += (team_id,)
        with connect(self._db_path) as conn:
            row = conn.execute(query, params).fetchone()
        return dict(row) if row else None

    def get_by_checkin_token(self, token: str) -> dict | None:
        digest = hashlib.sha256(token.encode()).hexdigest()
        with connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT player_id, team_id FROM players WHERE checkin_token = ?",
                (digest,),
            ).fetchone()
        return dict(row) if row else None

    def regenerate_checkin_token(self, player_id: str, team_id: str) -> str | None:
        token = secrets.token_urlsafe(32)
        digest = hashlib.sha256(token.encode()).hexdigest()
        with connect(self._db_path) as conn:
            cursor = conn.execute(
                "UPDATE players SET checkin_token = ? WHERE player_id = ? AND team_id = ?",
                (digest, player_id, team_id),
            )
        return token if cursor.rowcount else None

    def list_for_team(self, team_type: str, team_id: str | None = None) -> list[dict]:
        query = (
            "SELECT player_id, name, team_type, registered_date, team_id "
            "FROM players WHERE team_type = ?"
        )
        params: tuple = (team_type,)
        if team_id is not None:
            query += " AND team_id = ?"
            params += (team_id,)
        query += " ORDER BY name COLLATE NOCASE"
        with connect(self._db_path) as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def delete(self, player_id: str, team_id: str | None = None) -> bool:
        query = "DELETE FROM players WHERE player_id = ?"
        params: tuple = (player_id,)
        if team_id is not None:
            query += " AND team_id = ?"
            params += (team_id,)
        with connect(self._db_path) as conn:
            cursor = conn.execute(query, params)
        return cursor.rowcount > 0


player_store = PlayerStore()
