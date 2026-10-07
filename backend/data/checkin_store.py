"""Persistence for athlete check-ins. One responsibility: the checkins
table. No joins, no scoring, no HTTP."""
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
    pain_area TEXT
);
"""


class CheckinStore:
    def __init__(self, db_path: str = DB_PATH):
        self._db_path = db_path
        with connect(self._db_path) as conn:
            conn.executescript(SCHEMA)

    def log_checkin(self, player_id: str, checkin: dict) -> None:
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


checkin_store = CheckinStore()
