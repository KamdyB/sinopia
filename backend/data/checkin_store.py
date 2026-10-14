"""Persistence for athlete check-ins. One responsibility: the checkins table."""
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
            # Upgrade existing SQLite databases without discarding check-in data.
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(checkins)")}
            if "pain_acknowledged" not in columns:
                conn.execute(
                    "ALTER TABLE checkins ADD COLUMN pain_acknowledged INTEGER NOT NULL DEFAULT 0"
                )
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_checkins_player_date "
                "ON checkins (player_id, date)"
            )

    def log_checkin(self, player_id: str, checkin: dict) -> None:
        try:
            with connect(self._db_path) as conn:
                conn.execute(
                    "INSERT INTO checkins "
                    "(player_id, date, sleep, energy, soreness, stress, pain, pain_area) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        player_id,
                        checkin["date"],
                        checkin["sleep"],
                        checkin["energy"],
                        checkin["soreness"],
                        checkin["stress"],
                        int(checkin["pain"]),
                        checkin["pain_area"],
                    ),
                )
        except sqlite3.IntegrityError as exc:
            if "checkins.player_id, checkins.date" in str(exc) or "idx_checkins_player_date" in str(exc):
                raise DuplicateCheckinError from exc
            raise

    def get_checkins(self, player_id: str) -> list[dict]:
        with connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT date, sleep, energy, soreness, stress, pain, pain_area "
                "FROM checkins WHERE player_id = ? ORDER BY date, id",
                (player_id,),
            ).fetchall()
        return [
            {
                "date": row["date"],
                "sleep": row["sleep"],
                "energy": row["energy"],
                "soreness": row["soreness"],
                "stress": row["stress"],
                "pain": bool(row["pain"]),
                "pain_area": row["pain_area"],
            }
            for row in rows
        ]

    def acknowledge_pain(self, player_id: str) -> None:
        with connect(self._db_path) as conn:
            conn.execute(
                "UPDATE checkins SET pain_acknowledged = 1 "
                "WHERE player_id = ? AND pain = 1",
                (player_id,),
            )

    def delete_for_player(self, player_id: str) -> None:
        with connect(self._db_path) as conn:
            conn.execute("DELETE FROM checkins WHERE player_id = ?", (player_id,))
