"""Persistence for logged training sessions."""
from typing import List
from backend.data.db import DB_PATH, connect, init_schema
from backend.scoring.load_calculator import Session

class SessionStore:
    def __init__(self, db_path: str = DB_PATH):
        self._db_path = db_path
        init_schema(self._db_path)

    def log_session(self, player_id: str, session: Session, team_id: str | None = None) -> None:
        with connect(self._db_path, team_id=team_id) as conn:
            conn.execute("INSERT INTO sessions (player_id, date, duration_minutes, rpe, team_id) VALUES (?, ?, ?, ?, ?)",
                (player_id, session["date"], session["duration_minutes"], session["rpe"], team_id))

    def get_sessions(self, player_id: str, team_id: str | None = None) -> List[Session]:
        query = "SELECT date, duration_minutes, rpe FROM sessions WHERE player_id = ?"
        params: tuple = (player_id,)
        if team_id is not None:
            query += " AND team_id = ?"
            params += (team_id,)
        query += " ORDER BY date, id"
        with connect(self._db_path, team_id=team_id) as conn:
            rows = conn.execute(query, params).fetchall()
        return [{"date": row["date"], "duration_minutes": row["duration_minutes"], "rpe": row["rpe"]} for row in rows]

    def delete_session(self, session_id: int, player_id: str, team_id: str) -> bool:
        with connect(self._db_path, team_id=team_id) as conn:
            result = conn.execute("DELETE FROM sessions WHERE id = ? AND player_id = ? AND team_id = ?",
                (session_id, player_id, team_id))
        return result.rowcount > 0

    def purge_before(self, cutoff_date: str, team_id: str) -> int:
        """Delete old session history only within the specified team."""
        with connect(self._db_path, team_id=team_id) as conn:
            result = conn.execute(
                "DELETE FROM sessions WHERE team_id = ? AND date < ?",
                (team_id, cutoff_date),
            )
        return max(0, result.rowcount)

    def delete_for_player(self, player_id: str, team_id: str | None = None) -> None:
        query = "DELETE FROM sessions WHERE player_id = ?"
        params: tuple = (player_id,)
        if team_id is not None:
            query += " AND team_id = ?"
            params += (team_id,)
        with connect(self._db_path, team_id=team_id) as conn:
            conn.execute(query, params)

session_store = SessionStore()
