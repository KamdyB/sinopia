"""Persistence for a team's currently open athlete-effort window."""
from datetime import datetime, timezone
from backend.data.db import DB_PATH, connect, init_schema

class OpenTeamSessionStore:
    def __init__(self, db_path: str = DB_PATH):
        self._db_path = db_path
        init_schema(self._db_path)

    def current(self, team_id: str) -> dict | None:
        with connect(self._db_path, team_id=team_id) as conn:
            row = conn.execute(
                "SELECT team_id, session_date, duration_minutes, is_open, created_at "
                "FROM open_team_sessions WHERE team_id = ? AND is_open = 1",
                (team_id,),
            ).fetchone()
        return dict(row) if row else None

    def open(self, team_id: str, session_date: str, duration_minutes: float) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        with connect(self._db_path, team_id=team_id) as conn:
            current = conn.execute(
                "SELECT is_open FROM open_team_sessions WHERE team_id = ?", (team_id,)
            ).fetchone()
            if current and current["is_open"]:
                raise ValueError("A team session is already open. Close it before opening another.")
            result = conn.execute(
                "INSERT INTO open_team_sessions (team_id, session_date, duration_minutes, is_open, created_at) "
                "VALUES (?, ?, ?, 1, ?) ON CONFLICT(team_id) DO UPDATE SET "
                "session_date = excluded.session_date, duration_minutes = excluded.duration_minutes, "
                "is_open = 1, created_at = excluded.created_at "
                "WHERE open_team_sessions.is_open = 0",
                (team_id, session_date, duration_minutes, now),
            )
            # The conditional upsert is the concurrency guard: even if two serverless
            # requests pass the initial read simultaneously, only one can open the row.
            if result.rowcount == 0:
                raise ValueError("A team session is already open. Close it before opening another.")
        return {"team_id":team_id,"session_date":session_date,
                "duration_minutes":duration_minutes,"is_open":True,"created_at":now}

    def close(self, team_id: str) -> dict | None:
        with connect(self._db_path, team_id=team_id) as conn:
            current = conn.execute(
                "SELECT team_id, session_date, duration_minutes, is_open, created_at "
                "FROM open_team_sessions WHERE team_id = ? AND is_open = 1",
                (team_id,),
            ).fetchone()
            if current is None:
                return None
            conn.execute("UPDATE open_team_sessions SET is_open = 0 WHERE team_id = ?", (team_id,))
        result = dict(current)
        result["is_open"] = 0
        return result

open_team_session_store = OpenTeamSessionStore()
