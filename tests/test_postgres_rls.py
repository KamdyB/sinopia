"""PostgreSQL integration tests; CI supplies a restricted non-owner test role."""
import os
import uuid
import pytest

from backend.data.db import connect

URL = os.environ.get("SINOPIA_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="PostgreSQL integration URL not configured")


def test_rls_hides_other_teams_without_where_clause_and_allows_token_scoped_lookup():
    suffix = uuid.uuid4().hex
    player_a, player_b = "a-" + suffix, "b-" + suffix
    token_a, token_b = "ta-" + suffix, "tb-" + suffix
    for player_id, team_id, token in ((player_a, "team-a", token_a), (player_b, "team-b", token_b)):
        with connect(URL, team_id=team_id) as conn:
            conn.execute(
                "INSERT INTO players (player_id, name, team_type, registered_date, team_id, checkin_token, name_hash, consent_confirmed_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (player_id, "synthetic", "girls", "2026-10-15", team_id, token, player_id, "2026-10-15T00:00:00+00:00"),
            )

    try:
        with connect(URL, team_id="team-a") as conn:
            rows = conn.execute("SELECT player_id, team_id FROM players").fetchall()
            assert player_a in {row["player_id"] for row in rows}
            assert player_b not in {row["player_id"] for row in rows}
            changed = conn.execute("UPDATE players SET name = ? WHERE player_id = ?", ("tampered", player_b))
            assert changed.rowcount == 0

        with connect(URL, checkin_token_hash=token_b) as conn:
            rows = conn.execute("SELECT player_id, team_id FROM players").fetchall()
            assert [row["player_id"] for row in rows] == [player_b]
    finally:
        for player_id, team_id in ((player_a, "team-a"), (player_b, "team-b")):
            with connect(URL, team_id=team_id) as conn:
                conn.execute("DELETE FROM players WHERE player_id = ?", (player_id,))
