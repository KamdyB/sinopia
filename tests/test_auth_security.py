import pytest
from fastapi import HTTPException, Response

import backend.api.auth as auth_api


class FakeAuthStore:
    def __init__(self):
        self.calls = []

    def delete_sessions_for_coach(self, email):
        self.calls.append(("rotate", email))

    def ensure_coach(self, email, name):
        self.calls.append(("ensure", email))
        return {
            "email": email.lower(), "display_name": name, "team_id": "team-1",
            "team_name": "Team", "accepted_at": None, "terms_version": None,
            "privacy_version": None,
        }

    def create_session(self, email):
        self.calls.append(("create_session", email))
        return "opaque-session-token"

    def log_event(self, event, team_id):
        self.calls.append(("audit", event, team_id))


def setup_valid_google_claims(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client-id")
    monkeypatch.setattr(auth_api, "require_turnstile", lambda token, action: None)
    monkeypatch.setattr(auth_api.id_token, "verify_oauth2_token", lambda *args, **kwargs: {
        "iss": "https://accounts.google.com", "aud": "client-id",
        "email_verified": True, "email": "coach@example.com", "name": "Coach",
    })


def test_verified_google_coach_can_register_without_hardcoded_allowlist(monkeypatch):
    monkeypatch.setenv("SINOPIA_ENV", "production")
    monkeypatch.delenv("SINOPIA_COACH_ALLOWLIST", raising=False)
    setup_valid_google_claims(monkeypatch)
    store = FakeAuthStore()
    monkeypatch.setattr(auth_api, "auth_store", store)
    response = Response()
    payload = auth_api.GoogleCredential(credential="x" * 30, turnstile_token="valid")

    result = auth_api.google_sign_in(payload, response)

    assert result["email"] == "coach@example.com"
    assert result["display_name"] == "Coach"
    assert response.headers["set-cookie"]
    assert [call[0] for call in store.calls] == ["rotate", "ensure", "create_session", "audit"]


def test_optional_allowlist_can_still_restrict_a_private_pilot(monkeypatch):
    monkeypatch.setenv("SINOPIA_ENV", "production")
    monkeypatch.setenv("SINOPIA_COACH_ALLOWLIST", "another@example.com")
    setup_valid_google_claims(monkeypatch)
    store = FakeAuthStore()
    monkeypatch.setattr(auth_api, "auth_store", store)
    payload = auth_api.GoogleCredential(credential="x" * 30, turnstile_token="valid")

    with pytest.raises(HTTPException) as error:
        auth_api.google_sign_in(payload, Response())

    assert error.value.status_code == 403
    assert store.calls == []


def test_allowed_coach_gets_secure_httponly_lax_session_cookie(monkeypatch):
    monkeypatch.setenv("SINOPIA_ENV", "production")
    monkeypatch.setenv("SINOPIA_COACH_ALLOWLIST", "COACH@example.com")
    setup_valid_google_claims(monkeypatch)
    store = FakeAuthStore()
    monkeypatch.setattr(auth_api, "auth_store", store)
    response = Response()
    payload = auth_api.GoogleCredential(credential="x" * 30, turnstile_token="valid")
    result = auth_api.google_sign_in(payload, response)
    cookie = response.headers["set-cookie"].lower()
    assert result["email"] == "coach@example.com"
    assert "httponly" in cookie and "secure" in cookie and "samesite=lax" in cookie
    assert [call[0] for call in store.calls] == ["rotate", "ensure", "create_session", "audit"]
