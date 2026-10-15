"""Shared SQLAlchemy engine/session helpers. Stores own their test engines."""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def normalize_database_url(value: str | None = None) -> str:
    url = value or os.environ.get("DATABASE_URL") or os.environ.get("SINOPIA_TEST_DATABASE_URL") or "sqlite:///./sinopia-local.db"
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

def make_session_factory(database_url: str | None = None):
    db_engine = make_engine(database_url)
    from backend.data.models import Base
    Base.metadata.create_all(bind=db_engine)
    return db_engine, sessionmaker(bind=db_engine, autoflush=False, expire_on_commit=False)

engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def create_tables(target_engine=None):
    from backend.data.models import Base
    Base.metadata.create_all(bind=target_engine or engine)
