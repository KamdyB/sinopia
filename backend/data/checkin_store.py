"""Persistence for athlete check-ins. One check-in per athlete per day."""
from sqlalchemy.exc import IntegrityError

from backend.data.db import DB_PATH, connect, init_schema
from backend.security.encryption import decrypt_text, encrypt_text, reencrypt_text


class DuplicateCheckinError(Exception):
    """Raised when an athlete already checked in on the same day."""


class CheckinStore:
    def __init__(self, db_path: str = DB_PATH):
        self._db_path = db_path
        init_schema(self._db_path)
        # Compatibility migration for existing local SQLite databases only.
        from backend.data.db import get_engine
        if get_engine(self._db_path).dialect.name == "sqlite":
            with connect(self._db_path) as conn:
                rows = conn.execute("SELECT id, pain_area FROM checkins WHERE pain_area IS NOT NULL").fetchall()
                for row in rows:
                    conn.execute("UPDATE checkins SET pain_area = ? WHERE id = ?",
                                 (reencrypt_text(row["pain_area"]), row["id"]))

    def log_checkin(self, player_id: str, checkin: dict, team_id: str | None = None, workload: dict | None = None) -> None:
        try:
            with connect(self._db_path, team_id=team_id) as conn:
                conn.execute(
                    "INSERT INTO checkins (player_id, date, sleep, energy, soreness, stress, pain, pain_area, team_id) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (player_id, checkin["date"], checkin["sleep"], checkin["energy"], checkin["soreness"],
                     checkin["stress"], int(checkin["pain"]),
                     encrypt_text(checkin["pain_area"]) if checkin["pain_area"] is not None else None, team_id),
                )
                # Check-in and session effort share one transaction. If recording
                # workload fails, the check-in is rolled back rather than stranded.
                if workload is not None:
                    existing = conn.execute(
                        "SELECT 1 FROM sessions WHERE player_id = ? AND team_id = ? "
                        "AND date = ? AND duration_minutes = ? LIMIT 1",
                        (player_id, team_id, workload["date"], workload["duration_minutes"]),
                    ).fetchone()
                    if existing is None:
                        conn.execute(
                            "INSERT INTO sessions (player_id, date, duration_minutes, rpe, team_id) "
                            "VALUES (?, ?, ?, ?, ?)",
                            (player_id, workload["date"], workload["duration_minutes"],
                             workload["rpe"], team_id),
                        )
        except IntegrityError as exc:
            if "checkins.player_id" in str(exc) or "idx_checkins_player_date" in str(exc) or "uq_checkins_player_date" in str(exc):
                raise DuplicateCheckinError from exc
            raise

    def get_checkins(self, player_id: str, team_id: str | None = None) -> list[dict]:
        query = "SELECT date, sleep, energy, soreness, stress, pain, pain_area, pain_acknowledged FROM checkins WHERE player_id = ?"
        params: tuple = (player_id,)
        if team_id is not None:
            query += " AND team_id = ?"
            params += (team_id,)
        query += " ORDER BY date, id"
        with connect(self._db_path, team_id=team_id) as conn:
            rows = conn.execute(query, params).fetchall()
        return [{"date": r["date"], "sleep": r["sleep"], "energy": r["energy"], "soreness": r["soreness"],
                 "stress": r["stress"], "pain": bool(r["pain"]), "pain_area": decrypt_text(r["pain_area"]),
                 "pain_acknowledged": bool(r["pain_acknowledged"])} for r in rows]

    def acknowledge_pain(self, player_id: str, team_id: str | None = None) -> None:
        query = "UPDATE checkins SET pain_acknowledged = 1 WHERE player_id = ? AND pain = 1"
        params: tuple = (player_id,)
        if team_id is not None:
            query += " AND team_id = ?"
            params += (team_id,)
        with connect(self._db_path, team_id=team_id) as conn:
            conn.execute(query, params)

    def purge_before(self, cutoff_date: str, team_id: str) -> int:
        """Delete old wellness check-ins only within the specified team."""
        with connect(self._db_path, team_id=team_id) as conn:
            result = conn.execute(
                "DELETE FROM checkins WHERE team_id = ? AND date < ?",
                (team_id, cutoff_date),
            )
        return max(0, result.rowcount)

    def delete_checkin(self, checkin_id: int, player_id: str, team_id: str) -> bool:
        with connect(self._db_path, team_id=team_id) as conn:
            result = conn.execute(
                "DELETE FROM checkins WHERE id = ? AND player_id = ? AND team_id = ?",
                (checkin_id, player_id, team_id),
            )
        return result.rowcount > 0

    def delete_for_player(self, player_id: str, team_id: str | None = None) -> None:
        query = "DELETE FROM checkins WHERE player_id = ?"
        params: tuple = (player_id,)
        if team_id is not None:
            query += " AND team_id = ?"
            params += (team_id,)
        with connect(self._db_path, team_id=team_id) as conn:
            conn.execute(query, params)


checkin_store = CheckinStore()
