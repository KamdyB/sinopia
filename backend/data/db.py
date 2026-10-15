"""Shared SQLAlchemy engine/session helpers. Stores own their test engines."""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def normalize_database_url(value: str | None = None) -> str:
    url = value or os.environ.get("DATABASE_URL") or os.environ.get("SINOPIA_TEST_DATABASE_URL")
    if not url:
        if os.environ.get("VERCEL") == "1":
            raise RuntimeError("DATABASE_URL must be configured for deployed Sinopia; ephemeral serverless storage is not supported.")
        url = "sqlite:///./sinopia-local.db"
    # Existing tests historically passed a filesystem path; keep that API working.
    if "://" not in url:
        url = "sqlite:///" + str(Path(url).resolve())
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    if url.startswith("postgresql") and "sslmode=" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return url

def make_engine(database_url: str | None = None):
    url = normalize_database_url(database_url)
    options = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **options)

engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def make_session_factory(database_url: str | None = None):
    db_engine = make_engine(database_url)
    create_tables(db_engine)
    return db_engine, sessionmaker(bind=db_engine, autoflush=False, expire_on_commit=False)

def create_tables(target_engine=None):
    from sqlalchemy import inspect, text
    from backend.data.models import Base
    db_engine = target_engine or engine
    # Upgrade the original pre-team schema before create_all builds indexes.
    inspector = inspect(db_engine)
    if "players" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("players")}
        if "team_id" not in columns:
            with db_engine.begin() as connection:
                connection.execute(text("ALTER TABLE players ADD COLUMN team_id VARCHAR(64) NOT NULL DEFAULT 'legacy'"))
                connection.execute(text("UPDATE players SET team_id = 'legacy-' || team_type"))
        with db_engine.begin() as connection:
            connection.execute(text("DROP INDEX IF EXISTS uq_players_team_name"))
            connection.execute(text("DROP INDEX IF EXISTS uq_players_team_name_ci"))
    Base.metadata.create_all(bind=db_engine)
