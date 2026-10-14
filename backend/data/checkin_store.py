"""Persistence for athlete check-ins. One check-in per athlete per day."""
import sqlite3

from backend.data.db import DB_PATH, connect

SCHEMA = """
CREATE TABLE IF NOT EXISTS checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id TEXT NOT NULL,
    date TEXT NOT NULL,
    sleep INTEGER NOT NULL,
    energy INTEGER NOT NULL,
    soreness INTEGER NOT NULL,
    stress INTEGER NOT NULL,
    pain INTEGER NOT NULL,
    pain_area TEXT,
    team_id TEXT,
    pain_acknowledged INTEGER NOT NULL DEFAULT 0,
    UNIQUE (player_id, date)
);
"""


class DuplicateCheckinError(Exception):
    """Raised when an athlete already checked in on the same day."""


class CheckinStore:
    def __init__(self, db_path: str = DB_PATH):
        self._db_path = db_path
        with connect(self._db_path) as conn:
            conn.executescript(SCHEMA)
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(checkins)")}
            if "team_id" not in columns:
                conn.execute("ALTER TABLE checkins ADD COLUMN team_id TEXT")
            if "pain_acknowledged" not in columns:
                conn.execute(
                    "ALTER TABLE checkins ADD COLUMN pain_acknowledged INTEGER NOT NULL DEFAULT 0"
                )
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_checkins_player_date "
                "ON checkins (player_id, date)"
            )

    def log_checkin(self, player_id: str, checkin: dict, team_id: str | None = None) -> None:
        try:
            with connect(self._db_path) as conn:
                conn.execute(
                    "INSERT INTO checkins "
                    "(player_id, date, sleep, energy, soreness, stress, pain, pain_area, team_id) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        player_id, checkin["date"], checkin["sleep"], checkin["energy"],
                        checkin["soreness"], checkin["stress"], int(checkin["pain"]),
                        checkin["pain_area"], team_id,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            if "checkins.player_id, checkins.date" in str(exc) or "idx_checkins_player_date" in str(exc):
                raise DuplicateCheckinError from exc
            raise

    def get_checkins(self, player_id: str, team_id: str | None = None) -> list[dict]:
        query = (
            "SELECT date, sleep, energy, soreness, stress, pain, pain_area "
            "FROM checkins WHERE player_id = ?"
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
                "date": row["date"], "sleep": row["sleep"], "energy": row["energy"],
                "soreness": row["soreness"], "stress": row["stress"],
                "pain": bool(row["pain"]), "pain_area": row["pain_area"],
            }
            for row in rows
        ]

    def acknowledge_pain(self, player_id: str, team_id: str | None = None) -> None:
        query = "UPDATE checkins SET pain_acknowledged = 1 WHERE player_id = ? AND pain = 1"
        params: tuple = (player_id,)
        if team_id is not None:
            query += " AND team_id = ?"
            params += (team_id,)
        with connect(self._db_path) as conn:
            conn.execute(query, params)

    def delete_for_player(self, player_id: str, team_id: str | None = None) -> None:
        query = "DELETE FROM checkins WHERE player_id = ?"
        params: tuple = (player_id,)
        if team_id is not None:
            query += " AND team_id = ?"
            params += (team_id,)
        with connect(self._db_path) as conn:
            conn.execute(query, params)


checkin_store = CheckinStore()
