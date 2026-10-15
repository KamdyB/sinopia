"""SQLAlchemy database layer. Production requires TLS PostgreSQL and a restricted app role."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import os
import re
from threading import Lock
from typing import Any, Iterator

from sqlalchemy import (
    Column, Float, Index, Integer, MetaData, String, Table, Text, create_engine,
    event, inspect, text,
)
from sqlalchemy.engine import Connection, CursorResult, Engine

DB_PATH = os.environ.get("DATABASE_URL", "").strip() or os.environ.get("SINOPIA_DB_PATH", "sinopia.db")
_METADATA = MetaData()
_ENGINES: dict[str, Engine] = {}
_ENGINE_LOCK = Lock()

coaches = Table(
    "coaches", _METADATA,
    Column("email", String(320), primary_key=True),
    Column("display_name", String(120), nullable=False),
    Column("created_at", Text, nullable=False),
    Column("accepted_at", Text),
    Column("terms_version", String(80)),
    Column("privacy_version", String(80)),
)
teams = Table(
    "teams", _METADATA,
    Column("team_id", String(128), primary_key=True),
    Column("coach_email", String(320), nullable=False, unique=True),
    Column("team_name", String(120), nullable=False),
    Column("team_type", String(16)),
    Column("created_at", Text, nullable=False),
)
coach_sessions = Table(
    "coach_sessions", _METADATA,
    Column("session_hash", String(64), primary_key=True),
    Column("coach_email", String(320), nullable=False),
    Column("expires_at", Text, nullable=False),
    Column("created_at", Text, nullable=False),
)
players = Table(
    "players", _METADATA,
    Column("player_id", String(80), primary_key=True),
    Column("name", Text, nullable=False),
    Column("team_type", String(16), nullable=False),
    Column("registered_date", String(10), nullable=False),
    Column("team_id", String(128)),
    Column("checkin_token", String(64)),
    Column("name_hash", String(64)),
    Column("consent_confirmed_at", Text),
)
Index("idx_players_team_name_hash", players.c.team_id, players.c.team_type, players.c.name_hash, unique=True)
Index("idx_players_checkin_token", players.c.checkin_token, unique=True)

sessions = Table(
    "sessions", _METADATA,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("player_id", String(80), nullable=False),
    Column("date", String(10), nullable=False),
    Column("duration_minutes", Float, nullable=False),
    Column("rpe", Float, nullable=False),
    Column("team_id", String(128)),
)
checkins = Table(
    "checkins", _METADATA,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("player_id", String(80), nullable=False),
    Column("date", String(10), nullable=False),
    Column("sleep", Integer, nullable=False),
    Column("energy", Integer, nullable=False),
    Column("soreness", Integer, nullable=False),
    Column("stress", Integer, nullable=False),
    Column("pain", Integer, nullable=False),
    Column("pain_area", Text),
    Column("team_id", String(128)),
    Column("pain_acknowledged", Integer, nullable=False, server_default="0"),
)
Index("idx_checkins_player_date", checkins.c.player_id, checkins.c.date, unique=True)

audit_log = Table(
    "audit_log", _METADATA,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("event_type", String(80), nullable=False),
    Column("team_id", String(128)),
    Column("created_at", Text, nullable=False),
)
rate_limit_buckets = Table(
    "rate_limit_buckets", _METADATA,
    Column("bucket_key", String(64), primary_key=True),
    Column("window_start", Integer, nullable=False),
    Column("count", Integer, nullable=False),
)
team_sessions = Table(
    "team_sessions", _METADATA,
    Column("team_session_id", String(80), primary_key=True),
    Column("team_id", String(128), nullable=False),
    Column("session_date", String(10), nullable=False),
    Column("team_type", String(16), nullable=False),
    Column("duration_minutes", Float, nullable=False),
    Column("rpe", Float, nullable=False),
    Column("created_at", Text, nullable=False),
)
open_team_sessions = Table(
    "open_team_sessions", _METADATA,
    Column("team_id", String(128), primary_key=True),
    Column("session_date", String(10), nullable=False),
    Column("duration_minutes", Float, nullable=False),
    Column("is_open", Integer, nullable=False, server_default="1"),
    Column("created_at", Text, nullable=False),
)


def _normalise_url(value: str) -> str:
    value = value.strip()
    if value.startswith("postgres://"):
        value = "postgresql+psycopg://" + value[len("postgres://"):]
    elif value.startswith("postgresql://"):
        value = "postgresql+psycopg://" + value[len("postgresql://"):]
    if value.startswith("postgresql+psycopg://") and "sslmode=" not in value:
        value += ("&" if "?" in value else "?") + "sslmode=require"
    return value


def _database_url(db_path: str | Path | None = None) -> str:
    if db_path is not None:
        value = str(db_path)
        if "://" in value:
            return _normalise_url(value)
        return "sqlite:///" + str(Path(value).resolve())
    configured = os.environ.get("DATABASE_URL", "").strip()
    if configured:
        return _normalise_url(configured)
    if os.environ.get("SINOPIA_ENV", "production").lower() == "production":
        raise RuntimeError("DATABASE_URL is required in production; refusing local SQLite.")
    return "sqlite:///" + str(Path(DB_PATH).resolve())


def get_engine(db_path: str | Path | None = None) -> Engine:
    url = _database_url(db_path)
    with _ENGINE_LOCK:
        if url not in _ENGINES:
            engine = create_engine(
                url, pool_pre_ping=True,
                pool_recycle=300 if url.startswith("postgresql+") else -1,
            )
            if url.startswith("sqlite:"):
                @event.listens_for(engine, "connect")
                def _sqlite_pragmas(dbapi_connection, _connection_record):
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA foreign_keys = ON")
                    cursor.execute("PRAGMA busy_timeout = 5000")
                    cursor.close()
            _ENGINES[url] = engine
        return _ENGINES[url]


class _ResultAdapter:
    def __init__(self, result: CursorResult):
        self._result = result.mappings() if result.returns_rows else result

    def fetchone(self):
        return self._result.fetchone()

    def fetchall(self):
        return self._result.fetchall()

    @property
    def rowcount(self):
        return self._result.rowcount

    @property
    def lastrowid(self):
        return getattr(self._result, "lastrowid", None)


class _ConnectionAdapter:
    def __init__(self, connection: Connection):
        self._connection = connection

    def execute(self, statement: str, parameters: Any = None) -> _ResultAdapter:
        # Legacy store queries use qmark placeholders. Convert to named SQLAlchemy
        # binds without interpolating values into the SQL statement.
        if statement.lstrip().upper().startswith("PRAGMA "):
            return _ResultAdapter(self._connection.execute(text("SELECT 1")))
        if isinstance(parameters, (tuple, list)):
            index = 0
            def replace(_match):
                nonlocal index
                name = f"p{index}"
                index += 1
                return ":" + name
            statement = re.sub(r"\?", replace, statement)
            parameters = {f"p{i}": value for i, value in enumerate(parameters)}
        return _ResultAdapter(self._connection.execute(text(statement), parameters or {}))

    def executescript(self, script: str) -> None:
        if self._connection.dialect.name != "sqlite":
            raise RuntimeError("Production schema changes must use python -m backend.migrate.")
        for statement in script.split(";"):
            if statement.strip():
                self._connection.exec_driver_sql(statement)


@contextmanager
def connect(
    db_path: str | Path | None = None,
    *,
    team_id: str | None = None,
    checkin_token_hash: str | None = None,
) -> Iterator[_ConnectionAdapter]:
    """Open one transaction and set PostgreSQL RLS context transaction-locally."""
    engine = get_engine(db_path)
    with engine.begin() as connection:
        if connection.dialect.name == "postgresql":
            connection.execute(
                text("SELECT set_config('app.team_id', :value, true)"),
                {"value": team_id or ""},
            )
            connection.execute(
                text("SELECT set_config('app.checkin_token_hash', :value, true)"),
                {"value": checkin_token_hash or ""},
            )
        yield _ConnectionAdapter(connection)


def init_schema(db_path: str | Path | None = None) -> None:
    """Initialize development/test SQLite only; production schema uses owner migration."""
    engine = get_engine(db_path)
    if engine.dialect.name == "postgresql":
        if os.environ.get("SINOPIA_ENV", "production").lower() == "production":
            return
        _METADATA.create_all(engine)
        return
    _METADATA.create_all(engine)
    additions = {
        "players": {"team_id": "TEXT", "checkin_token": "TEXT", "name_hash": "TEXT", "consent_confirmed_at": "TEXT"},
        "checkins": {"team_id": "TEXT", "pain_acknowledged": "INTEGER NOT NULL DEFAULT 0"},
        "sessions": {"team_id": "TEXT"},
        "teams": {"team_type": "TEXT"},
    }
    with engine.begin() as connection:
        inspector = inspect(connection)
        for table_name, columns in additions.items():
            if not inspector.has_table(table_name):
                continue
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, column_type in columns.items():
                if column_name not in existing:
                    connection.exec_driver_sql(
                        f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {column_type}'
                    )
