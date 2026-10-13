"""Shared database connection mechanics. No schema and no queries live
here, beyond the dialect switch between SQLite and PostgreSQL.

SQLite is used for local development and the whole test suite, which
needs throwaway per-test database files with zero setup. PostgreSQL is
used when DATABASE_URL points at an external managed database such as
the free Tiger Cloud tier used on Render deployments (deliberately not
Render's own Postgres). Store SQL stays portable '?'-style so a thin
wrapper translates placeholders for psycopg2.
"""
import os
import sqlite3
from typing import Callable

DATABASE_URL = os.environ.get("DATABASE_URL", "")


def is_postgres() -> bool:
    return bool(DATABASE_URL)


def auto_id() -> str:
    """Column fragment for the auto-incrementing id, per dialect."""
    if is_postgres():
        return "id BIGSERIAL PRIMARY KEY"
    return "id INTEGER PRIMARY KEY AUTOINCREMENT"


def run_script(conn, script: str) -> None:
    """Execute a multi-statement DDL script on either engine."""
    if is_postgres():
        # psycopg2 happily runs several semicolon-separated statements
        # in one call, unlike sqlite3 which needs executescript.
        conn.execute(script)
    else:
        conn.executescript(script)


def connect(db_path: str | None = None):
    if is_postgres():
        import psycopg2
        return psycopg2.connect(DATABASE_URL)
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


DB_PATH = os.environ.get("SINOPIA_DB_PATH", "sinopia.db")


class _Row(dict):
    """Dict row so stores can index by column name on both engines."""


class _PgCursor:
    """Translates '?' placeholders to psycopg2 '%s' and returns dict rows."""

    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, sql, params=None):
        translated = sql.replace("?", "%s")
        self._cursor.execute(translated, params or ())
        self._cols = None
        if self._cursor.description is not None:
            self._cols = [d[0] for d in self._cursor.description]
        return self

    @staticmethod
    def _dumb(rows, cols):
        if cols is None:
            return rows
        return [_Row(zip(cols, row)) for row in rows]

    def fetchone(self):
        row = self._cursor.fetchone()
        return self._dumb([row], self._cols)[0] if row else None

    def fetchall(self):
        return self._dumb(self._cursor.fetchall(), self._cols)

    def __iter__(self):
        return iter(self.fetchall())


class _PgConn:
    """Connection wrapper with the sqlite-with-context-manager surface the
    stores already rely on (commit on successful with-block exit)."""

    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return _PgCursor(self._conn.cursor())

    def execute(self, sql, params=None):
        cur = self.cursor()
        return cur.execute(sql, params)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def _exit(self, exc_type):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self._exit(exc_type)
        return False


def wrapper() -> Callable:
    return _PgConn
