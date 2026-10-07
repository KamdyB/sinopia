"""Shared SQLite connection mechanics. No schema and no queries live here."""
import os
import sqlite3

DB_PATH = os.environ.get("FEMFIT_DB_PATH", "femfit.db")


def connect(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
