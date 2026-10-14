"""Persistence for coach accounts and opaque server-side sessions."""
from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from backend.data.db import DB_PATH, connect

SCHEMA = """
CREATE TABLE IF NOT EXISTS coaches (
    email TEXT PRIMARY KEY COLLATE NOCASE,
    display_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    accepted_at TEXT,
    terms_version TEXT,
    privacy_version TEXT
);
CREATE TABLE IF NOT EXISTS teams (
    team_id TEXT PRIMARY KEY,
    coach_email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    team_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (coach_email) REFERENCES coaches(email) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS coach_sessions (
    session_hash TEXT PRIMARY KEY,
    coach_email TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (coach_email) REFERENCES coaches(email) ON DELETE CASCADE
);
"""


class AuthStore:
    def __init__(self, db_path: str = DB_PATH):
        self._db_path = db_path
        with connect(self._db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.executescript(SCHEMA)

    def ensure_coach(self, email: str, display_name: str) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        with connect(self._db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute(
                "INSERT INTO coaches (email, display_name, created_at) VALUES (?, ?, ?) "
                "ON CONFLICT(email) DO UPDATE SET display_name = excluded.display_name",
                (email.lower(), display_name[:120], now),
            )
            row = conn.execute(
                "SELECT email, display_name, accepted_at, terms_version, privacy_version "
                "FROM coaches WHERE email = ?",
                (email.lower(),),
            ).fetchone()
            team = conn.execute(
                "SELECT team_id, team_name FROM teams WHERE coach_email = ?",
                (email.lower(),),
            ).fetchone()
            if team is None:
                team_id = secrets.token_urlsafe(18)
                conn.execute(
                    "INSERT INTO teams (team_id, coach_email, team_name, created_at) "
                    "VALUES (?, ?, ?, ?)",
                    (team_id, email.lower(), "My team", now),
                )
                team = conn.execute(
                    "SELECT team_id, team_name FROM teams WHERE coach_email = ?",
                    (email.lower(),),
                ).fetchone()
        result = dict(row)
        result.update(dict(team))
        return result

    def create_session(self, email: str, lifetime_hours: int = 8) -> str:
        token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        with connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO coach_sessions (session_hash, coach_email, expires_at, created_at) "
                "VALUES (?, ?, ?, ?)",
                (
                    hashlib.sha256(token.encode()).hexdigest(),
                    email.lower(),
                    (now + timedelta(hours=lifetime_hours)).isoformat(),
                    now.isoformat(),
                ),
            )
        return token

    def get_session(self, token: str) -> dict | None:
        digest = hashlib.sha256(token.encode()).hexdigest()
        now = datetime.now(timezone.utc).isoformat()
        with connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT c.email, c.display_name, c.accepted_at, c.terms_version, "
                "c.privacy_version, t.team_id, t.team_name "
                "FROM coach_sessions s JOIN coaches c ON c.email = s.coach_email "
                "JOIN teams t ON t.coach_email = c.email "
                "WHERE s.session_hash = ? AND s.expires_at > ?",
                (digest, now),
            ).fetchone()
        return dict(row) if row else None

    def delete_session(self, token: str) -> None:
        digest = hashlib.sha256(token.encode()).hexdigest()
        with connect(self._db_path) as conn:
            conn.execute("DELETE FROM coach_sessions WHERE session_hash = ?", (digest,))

    def accept_policies(self, email: str, terms_version: str, privacy_version: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with connect(self._db_path) as conn:
            conn.execute(
                "UPDATE coaches SET accepted_at = ?, terms_version = ?, privacy_version = ? "
                "WHERE email = ?",
                (now, terms_version, privacy_version, email.lower()),
            )


auth_store = AuthStore()
