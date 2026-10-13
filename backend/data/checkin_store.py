"""Persistence for athlete check-ins. One responsibility: the checkins
table. No joins, no scoring, no HTTP. Every query is filtered by
team_id, which the server derives from the athlete's own record, never
from anything the client sends.
"""
from backend.data.db import DB_PATH, auto_id, connect, run_script

SCHEMA = f"""
CREATE TABLE IF NOT EXISTS checkins (
    {auto_id()},
    player_id TEXT NOT NULL,
    team_id TEXT NOT NULL,
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
            run_script(conn, SCHEMA)

    def log_checkin(self, player_id: str, team_id: str, checkin: dict) -> None:
        with connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO checkins "
                "(player_id, team_id, date, sleep, energy, soreness, stress, pain, pain_area) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    player_id,
                    team_id,
                    checkin["date"],
                    checkin["sleep"],
                    checkin["energy"],
                    checkin["soreness"],
                    checkin["stress"],
                    int(checkin["pain"]),
                    checkin["pain_area"],
                ),
            )

    def get_checkins(self, player_id: str, team_id: str) -> list[dict]:
        with connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT date, sleep, energy, soreness, stress, pain, pain_area "
                "FROM checkins WHERE player_id = ? AND team_id = ? ORDER BY date, id",
                (player_id, team_id),
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
