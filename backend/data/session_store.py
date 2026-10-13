"""Persistence for logged training sessions.

One responsibility: the sessions table. The old profiles table carried
cycle and growth context that the current scoring spec no longer uses,
so the schema migration drops it rather than leaving dormant data about
minors in storage. Every query is filtered by team_id: the athlete id
alone is never trusted as a scoping key.
"""
from typing import List

from backend.data.db import DB_PATH, auto_id, connect, run_script
from backend.scoring.load_calculator import Session

SCHEMA = f"""
CREATE TABLE IF NOT EXISTS sessions (
    {auto_id()},
    player_id TEXT NOT NULL,
    team_id TEXT NOT NULL,
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
            run_script(conn, SCHEMA)

    def log_session(self, player_id: str, team_id: str, session: Session) -> None:
        with connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO sessions (player_id, team_id, date, "
                "duration_minutes, rpe) VALUES (?, ?, ?, ?, ?)",
                (player_id, team_id, session["date"], session["duration_minutes"], session["rpe"]),
            )

    def get_sessions(self, player_id: str, team_id: str) -> List[Session]:
        # Ordering by id as a tiebreak makes same-day sessions deterministic
        # for the walk-forward history computation.
        with connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT date, duration_minutes, rpe FROM sessions "
                "WHERE player_id = ? AND team_id = ? ORDER BY date, id",
                (player_id, team_id),
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
