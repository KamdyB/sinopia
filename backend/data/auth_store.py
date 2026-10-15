"""Persistence for coach accounts and opaque server-side sessions."""
from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from backend.data.db import DB_PATH, connect, init_schema


class AuthStore:
    def __init__(self, db_path: str = DB_PATH):
        self._db_path = db_path
        init_schema(self._db_path)

    def ensure_coach(self, email: str, display_name: str) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        email = email.lower()
        with connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO coaches (email, display_name, created_at) VALUES (?, ?, ?) "
                "ON CONFLICT(email) DO UPDATE SET display_name = excluded.display_name",
                (email, display_name[:120], now),
            )
            row = conn.execute(
                "SELECT email, display_name, accepted_at, terms_version, privacy_version FROM coaches WHERE email = ?",
                (email,),
            ).fetchone()
            team = conn.execute(
                "SELECT team_id, team_name, team_type FROM teams WHERE coach_email = ?", (email,)
            ).fetchone()
            if team is None:
                team_id = secrets.token_urlsafe(18)
                conn.execute(
                    "INSERT INTO teams (team_id, coach_email, team_name, created_at) VALUES (?, ?, ?, ?)",
                    (team_id, email, "My team", now),
                )
                team = conn.execute(
                    "SELECT team_id, team_name, team_type FROM teams WHERE coach_email = ?", (email,)
                ).fetchone()
        result = dict(row)
        result.update(dict(team))
        return result


    def update_team(self, email: str, team_name: str, team_type: str) -> dict:
        with connect(self._db_path) as conn:
            row = conn.execute("SELECT team_id, team_type FROM teams WHERE coach_email = ?", (email.lower(),)).fetchone()
            if row is None:
                raise ValueError("Coach team was not found.")
            if row["team_type"] is not None:
                raise ValueError("Team composition has already been set.")
            conn.execute(
                "UPDATE teams SET team_name = ?, team_type = ? WHERE coach_email = ? AND team_type IS NULL",
                (" ".join(team_name.split())[:120], team_type, email.lower()),
            )
            updated = conn.execute("SELECT team_id, team_name, team_type FROM teams WHERE coach_email = ?", (email.lower(),)).fetchone()
            conn.execute("UPDATE players SET team_type = ? WHERE team_id = ?", (team_type, updated["team_id"]))
        return dict(updated)

    def create_session(self, email: str, lifetime_hours: int = 8) -> str:
        token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        with connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO coach_sessions (session_hash, coach_email, expires_at, created_at) VALUES (?, ?, ?, ?)",
                (hashlib.sha256(token.encode()).hexdigest(), email.lower(),
                 (now + timedelta(hours=lifetime_hours)).isoformat(), now.isoformat()),
            )
        return token

    def get_session(self, token: str) -> dict | None:
        digest = hashlib.sha256(token.encode()).hexdigest()
        now = datetime.now(timezone.utc).isoformat()
        with connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT c.email, c.display_name, c.accepted_at, c.terms_version, c.privacy_version, "
                "t.team_id, t.team_name, t.team_type FROM coach_sessions s JOIN coaches c ON c.email = s.coach_email "
                "JOIN teams t ON t.coach_email = c.email WHERE s.session_hash = ? AND s.expires_at > ?",
                (digest, now),
            ).fetchone()
        return dict(row) if row else None

    def delete_session(self, token: str) -> None:
        with connect(self._db_path) as conn:
            conn.execute("DELETE FROM coach_sessions WHERE session_hash = ?",
                         (hashlib.sha256(token.encode()).hexdigest(),))

    def delete_sessions_for_coach(self, email: str) -> None:
        with connect(self._db_path) as conn:
            conn.execute("DELETE FROM coach_sessions WHERE coach_email = ?", (email.lower(),))

    def accept_policies(self, email: str, terms_version: str, privacy_version: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with connect(self._db_path) as conn:
            conn.execute(
                "UPDATE coaches SET accepted_at = ?, terms_version = ?, privacy_version = ? WHERE email = ?",
                (now, terms_version, privacy_version, email.lower()),
            )

    def log_event(self, event_type: str, team_id: str | None = None) -> None:
        allowed = {
            "coach_signed_in", "policies_accepted", "team_created", "team_session_opened", "team_session_closed", "checkin_token_regenerated",
            "checkin_submitted", "pain_report_acknowledged", "athlete_deleted",
            "session_deleted", "checkin_deleted", "team_exported", "account_deleted",
        }
        if event_type not in allowed:
            raise ValueError("Unknown audit event type.")
        with connect(self._db_path, team_id=team_id) as conn:
            conn.execute(
                "INSERT INTO audit_log (event_type, team_id, created_at) VALUES (?, ?, ?)",
                (event_type, team_id, datetime.now(timezone.utc).isoformat()),
            )


auth_store = AuthStore()
