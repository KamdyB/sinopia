import sqlite3
import time

from backend.api import auth as auth_api
from backend.api import privacy as privacy_api
from backend.data.auth_store import AuthStore
from backend.data.session_store import SessionStore


def test_export_contains_only_the_authenticated_coachs_team(client):
    from backend.api.players import player_store

    own_id = client.post(
        "/players",
        json={"name": "Own athlete", "team_type": "girls", "consent_confirmed": True},
    ).json()["player_id"]
    player_store.register("Foreign athlete", "girls", "2026-01-01", "another-team")

    response = client.get("/privacy/export?format=json")
    assert response.status_code == 200
    labels = [item["label"] for item in response.json()["players"]]
    assert "Own athlete" in labels
    assert "Foreign athlete" not in labels
    assert own_id


def test_account_deletion_hard_deletes_team_data_and_coach_records(
    client, tmp_path, monkeypatch
):
    from backend.api.players import player_store
    from backend.api.sessions import session_store
    from backend.api.checkins import checkin_store

    db_path = str(tmp_path / "test.db")
    test_auth_store = AuthStore(db_path)
    monkeypatch.setattr(auth_api, "auth_store", test_auth_store)
    monkeypatch.setattr(privacy_api, "DB_PATH", db_path)
    monkeypatch.setenv("SINOPIA_ENV", "production")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client")

    email = "delete-me@example.com"
    coach = test_auth_store.ensure_coach(email, "Delete Me")
    player = player_store.register("To delete", "girls", "2026-01-01", coach["team_id"])
    session_store.log_session(
        player["player_id"],
        {"date": "2026-01-01", "duration_minutes": 60, "rpe": 5},
        coach["team_id"],
    )
    checkin_store.log_checkin(
        player["player_id"],
        {"date": "2026-01-01", "sleep": 3, "energy": 3, "soreness": 3,
         "stress": 3, "pain": True, "pain_area": "Knee"},
        coach["team_id"],
    )
    client.cookies.set("sinopia_session", test_auth_store.create_session(email))
    monkeypatch.setattr(
        privacy_api.id_token,
        "verify_oauth2_token",
        lambda *args, **kwargs: {
            "iss": "https://accounts.google.com",
            "aud": "test-client",
            "email_verified": True,
            "email": email,
            "iat": time.time(),
        },
    )

    response = client.post(
        "/privacy/delete-account",
        json={"credential": "fresh-google-credential-placeholder", "confirm": True},
    )
    assert response.status_code == 200
    assert response.json() == {"deleted": True}

    with sqlite3.connect(db_path) as conn:
        for table in ("coaches", "teams", "coach_sessions", "players", "sessions", "checkins"):
            assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
