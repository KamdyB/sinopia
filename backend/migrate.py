"""Run once with DATABASE_OWNER_URL, before deploying the restricted app role.

Usage:
  DATABASE_OWNER_URL='postgresql://...' SINOPIA_DB_APP_ROLE='sinopia_app' python -m backend.migrate

The migration role must be the database owner (or have permission to create tables,
policies, and grants). The running API must use DATABASE_URL with the restricted role.
"""
import os
import re

from sqlalchemy import text

from backend.data.db import _METADATA, _normalise_url, create_engine
from backend.security.encryption import decrypt_text, label_digest, reencrypt_text, validate_encryption_config

owner_url = os.environ.get("DATABASE_OWNER_URL", "").strip()
if not owner_url:
    raise SystemExit("DATABASE_OWNER_URL is required. Do not use the restricted app URL for migrations.")

app_role = os.environ.get("SINOPIA_DB_APP_ROLE", "sinopia_app")
if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]{0,62}", app_role):
    raise SystemExit("SINOPIA_DB_APP_ROLE must be a simple PostgreSQL role name.")

try:
    validate_encryption_config()
except RuntimeError as exc:
    raise SystemExit(str(exc)) from exc

engine = create_engine(_normalise_url(owner_url), pool_pre_ping=True)
if engine.dialect.name != "postgresql":
    raise SystemExit("This migration command is only for PostgreSQL.")

with engine.begin() as connection:
    _METADATA.create_all(connection)
    connection.execute(text("ALTER TABLE teams ADD COLUMN IF NOT EXISTS team_type VARCHAR(16)"))
    protected_tables = ("players", "team_sessions", "open_team_sessions", "sessions", "checkins", "audit_log")
    # Temporarily disable existing policies inside this single DDL/data transaction
    # so the owner can rotate every row; a failure rolls back the entire transaction.
    for table in protected_tables:
        connection.execute(text(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY'))
    # Re-encrypt stored sensitive fields and rebuild the keyed duplicate-label digest.
    # This also makes rerunning the migration the supported key-rotation operation.
    for row in connection.execute(text("SELECT player_id, name FROM players")).mappings():
        plaintext = decrypt_text(row["name"])
        connection.execute(
            text("UPDATE players SET name = :name, name_hash = :digest WHERE player_id = :player_id"),
            {"name": reencrypt_text(row["name"]), "digest": label_digest(plaintext), "player_id": row["player_id"]},
        )
    for row in connection.execute(text("SELECT id, pain_area FROM checkins WHERE pain_area IS NOT NULL")).mappings():
        connection.execute(
            text("UPDATE checkins SET pain_area = :pain_area WHERE id = :id"),
            {"pain_area": reencrypt_text(row["pain_area"]), "id": row["id"]},
        )
    # Enable and FORCE row-level security. Context values are set transaction-locally
    # by backend.data.db.connect(), never persisted across pooled connections.
    policies = {
        "players": "team_id = NULLIF(current_setting('app.team_id', true), '')",
        "sessions": "team_id = NULLIF(current_setting('app.team_id', true), '')",
        "checkins": "team_id = NULLIF(current_setting('app.team_id', true), '')",
        "team_sessions": "team_id = NULLIF(current_setting('app.team_id', true), '')",
        "open_team_sessions": "team_id = NULLIF(current_setting('app.team_id', true), '')",
        "audit_log": "team_id = NULLIF(current_setting('app.team_id', true), '')",
    }
    for table, predicate in policies.items():
        connection.execute(text(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY'))
        connection.execute(text(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY'))
        connection.execute(text(f'DROP POLICY IF EXISTS "{table}_team_isolation" ON "{table}"'))
        connection.execute(text(
            f'CREATE POLICY "{table}_team_isolation" ON "{table}" '
            f'USING ({predicate}) WITH CHECK (team_id = NULLIF(current_setting(\'app.team_id\', true), \'\'))'
        ))
    # A check-in token grants SELECT access to exactly one matching player row;
    # it must never authorize UPDATE or DELETE.
    connection.execute(text('DROP POLICY IF EXISTS "players_checkin_token_select" ON players'))
    connection.execute(text(
        "CREATE POLICY players_checkin_token_select ON players FOR SELECT "
        "USING (checkin_token = NULLIF(current_setting('app.checkin_token_hash', true), ''))"
    ))
    connection.execute(text(f'GRANT USAGE ON SCHEMA public TO "{app_role}"'))
    for table in ("coaches", "teams", "coach_sessions", "players", "sessions", "checkins",
                  "team_sessions", "open_team_sessions", "audit_log", "rate_limit_buckets"):
        connection.execute(text(f'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE "{table}" TO "{app_role}"'))
    connection.execute(text(
        f'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "{app_role}"'
    ))
    connection.execute(text(
        f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "{app_role}"'
    ))
    connection.execute(text(
        f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO "{app_role}"'
    ))
engine.dispose()
print("PostgreSQL schema and RLS policies installed. Verify the app role is not a table owner and does not have BYPASSRLS.")
