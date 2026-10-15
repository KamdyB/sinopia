"""SQLAlchemy engine and session factory shared by persistence stores."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def _database_url():
    url = os.environ.get("DATABASE_URL")
    if not url:
        # SQLite is supported only when explicitly selected for local/tests.
        url = os.environ.get("SINOPIA_TEST_DATABASE_URL", "sqlite:///:memory:")
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    if url.startswith("postgresql") and "sslmode=" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return url

DATABASE_URL = _database_url()
_engine_options = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    _engine_options["connect_args"] = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, **_engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def create_tables():
    from backend.data.models import Base
    Base.metadata.create_all(bind=engine)
