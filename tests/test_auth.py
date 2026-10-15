import uuid

import backend.api.auth as auth_api
from backend.data.account_store import AccountStore
from backend.main import app


def test_google_signup_creates_secure_cookie_and_persists_team(client, tmp_path, monkeypatch):
    # Exercise real session dependencies against an isolated test database.
    app.dependency_overrides.pop(auth_api.get_current_coach, None)
    app.dependency_overrides.pop(auth_api.get_current_team, None)
    store = AccountStore("sqlite:///" + str(tmp_path / "accounts.db"))
    monkeypatch.setattr(auth_api, "account_store", store)
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-google-client")
    monkeypatch.setenv("SESSION_SECRET", "test-only-session-secret")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "false")
    sub = "test-sub-" + uuid.uuid4().hex
    monkeypatch.setattr(
        auth_api.id_token,
        "verify_oauth2_token",
        lambda credential, request, audience: {
            "sub": sub,
            "email": sub + "@example.test",
            "email_verified": True,
            "name": "Test Coach",
        },
    )

    signed_in = client.post(
        "/auth/google",
        json={
            "credential": "mocked-google-id-token-credential",
            "intent": "sign-up",
            "adult_confirmed": True,
            "authorized": True,
        },
    )
    assert signed_in.status_code == 200
    assert signed_in.headers["set-cookie"].lower().find("httponly") >= 0

    team_response = client.post(
        "/teams",
        json={"name": "U17 Team", "team_type": "mixed", "accepted_terms": True},
    )
    assert team_response.status_code == 201
    assert team_response.json()["team_type"] == "mixed"
    assert team_response.json()["terms_accepted_at"]

    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["team"]["team_id"] == team_response.json()["team_id"]

    logged_out = client.post("/auth/logout")
    assert logged_out.status_code == 200
    assert client.get("/auth/me").status_code == 401
