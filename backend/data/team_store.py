"""Persistence for teams. One row per team, and a coach belongs to
exactly one team, enforced by a unique index on coach_email. The team
profile carries sport, age band and composition instead of any gender
labelling, so the tool fits any school or youth team.
"""
import uuid

from backend.data.db import DB_PATH, connect, run_script

CREATE_TEAMS = """
CREATE TABLE IF NOT EXISTS teams (
    team_id TEXT PRIMARY KEY,
    coach_email TEXT NOT NULL,
    team_name TEXT NOT NULL,
    sport TEXT NOT NULL,
    age_band TEXT NOT NULL,
    composition TEXT NOT NULL,
    created_date TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_teams_coach_email
ON teams (coach_email);
"""



class TeamExistsError(Exception):
    def __init__(self, email: str):
        super().__init__(f"An account for {email} already owns a team.")


def _is_unique_violation(exc: Exception) -> bool:
    # sqlite3.IntegrityError and psycopg2.errors.UniqueViolation have
    # different bases, so match on the documented class names.
    return type(exc).__name__ in {"IntegrityError", "UniqueViolation"}


class TeamStore:
    def __init__(self, db_path: str = DB_PATH):
        self._db_path = db_path
        with connect(self._db_path) as conn:
            run_script(conn, CREATE_TEAMS)

    def create(
        self,
        coach_email: str,
        team_name: str,
        sport: str,
        age_band: str,
        composition: str,
        created_date: str,
    ) -> dict:
        team_id = uuid.uuid4().hex
        try:
            with connect(self._db_path) as conn:
                conn.execute(
                    "INSERT INTO teams (team_id, coach_email, team_name, sport, "
                    "age_band, composition, created_date) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        team_id,
                        coach_email,
                        team_name,
                        sport,
                        age_band,
                        composition,
                        created_date,
                    ),
                )
        except Exception as exc:
            if _is_unique_violation(exc):
                raise TeamExistsError(coach_email) from exc
            raise
        return {
            "team_id": team_id,
            "coach_email": coach_email,
            "team_name": team_name,
            "sport": sport,
            "age_band": age_band,
            "composition": composition,
            "created_date": created_date,
        }

    def get_by_coach(self, coach_email: str) -> dict | None:
        with connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT team_id, coach_email, team_name, sport, age_band, "
                "composition, created_date FROM teams WHERE coach_email = ?",
                (coach_email,),
            ).fetchone()
        return dict(row) if row else None

    def update_profile(
        self,
        team_id: str,
        team_name: str | None,
        sport: str | None,
        age_band: str | None,
        composition: str | None,
    ) -> dict | None:
        updates: dict[str, str] = {}
        if team_name is not None:
            updates["team_name"] = team_name
        if sport is not None:
            updates["sport"] = sport
        if age_band is not None:
            updates["age_band"] = age_band
        if composition is not None:
            updates["composition"] = composition
        if not updates:
            return self.get_by_id(team_id)
        sets = ", ".join(f"{col} = ?" for col in updates)
        with connect(self._db_path) as conn:
            conn.execute(
                f"UPDATE teams SET {sets} WHERE team_id = ?",
                (*updates.values(), team_id),
            )
        return self.get_by_id(team_id)

    def get_by_id(self, team_id: str) -> dict | None:
        with connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT team_id, coach_email, team_name, sport, age_band, "
                "composition, created_date FROM teams WHERE team_id = ?",
                (team_id,),
            ).fetchone()
        return dict(row) if row else None


team_store = TeamStore()
