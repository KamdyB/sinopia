import pytest
from fastapi import HTTPException, Response

import backend.api.auth as auth_api


class FakeAuthStore:
    def __init__(self, existing=()):
        self.calls = []
        self.existing = set(existing)

    def coach_exists(self, email):
        self.calls.append(("exists", email.lower()))
        return email.lower() in self.existing

    def register_coach(self, email, name):
        self.calls.append(("register", email.lower()))
        if email.lower() in self.existing:
            return None
        self.existing.add(email.lower())
        return self._coach(email, name)

    def ensure_coach(self, email, name):
        self.calls.append(("ensure", email.lower()))
        return self._coach(email, name)

    def _coach(self, email, name):
        return {
            "email": email.lower(), "display_name": name, "team_id": "team-1",
            "team_name": "Team", "team_type": None, "accepted_at": None,
            "terms_version": None, "privacy_version": None,
        }

    def delete_sessions_for_coach(self, email):
        self.calls.append(("rotate", email.lower()))

    def create_session(self, email):
        self.calls.append(("create_session", email.lower()))
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


def test_any_verified_google_email_can_create_one_account_without_allowlist(monkeypatch):
    monkeypatch.setenv("SINOPIA_ENV", "production")
    monkeypatch.delenv("SINOPIA_COACH_ALLOWLIST", raising=False)
    setup_valid_google_claims(monkeypatch)
    store = FakeAuthStore()
    monkeypatch.setattr(auth_api, "auth_store", store)
    response = Response()
    payload = auth_api.GoogleCredential(credential="x" * 30, turnstile_token="valid", intent="signup")

    result = auth_api.google_sign_in(payload, response)

    assert result["email"] == "coach@example.com"
    assert result["display_name"] == "Coach"
    assert response.headers["set-cookie"]
    assert [call[0] for call in store.calls] == ["register", "rotate", "create_session", "audit"]


def test_duplicate_signup_is_rejected_and_does_not_create_a_session(monkeypatch):
    monkeypatch.setenv("SINOPIA_ENV", "production")
    setup_valid_google_claims(monkeypatch)
    store = FakeAuthStore(existing={"coach@example.com"})
    monkeypatch.setattr(auth_api, "auth_store", store)
    payload = auth_api.GoogleCredential(credential="x" * 30, turnstile_token="valid", intent="signup")

    with pytest.raises(HTTPException) as error:
        auth_api.google_sign_in(payload, Response())

    assert error.value.status_code == 409
    assert error.value.detail == "An account already exists for this email. Sign in instead."
    assert [call[0] for call in store.calls] == ["register"]


def test_sign_in_only_works_for_existing_account(monkeypatch):
    monkeypatch.setenv("SINOPIA_ENV", "production")
    setup_valid_google_claims(monkeypatch)
    store = FakeAuthStore()
    monkeypatch.setattr(auth_api, "auth_store", store)
    payload = auth_api.GoogleCredential(credential="x" * 30, turnstile_token="valid", intent="signin")

    with pytest.raises(HTTPException) as error:
        auth_api.google_sign_in(payload, Response())
    assert error.value.status_code == 404
    assert [call[0] for call in store.calls] == ["exists"]


def test_existing_coach_can_sign_in_with_secure_session_cookie(monkeypatch):
    monkeypatch.setenv("SINOPIA_ENV", "production")
    setup_valid_google_claims(monkeypatch)
    store = FakeAuthStore(existing={"coach@example.com"})
    monkeypatch.setattr(auth_api, "auth_store", store)
    response = Response()
    payload = auth_api.GoogleCredential(credential="x" * 30, turnstile_token="valid", intent="signin")

    result = auth_api.google_sign_in(payload, response)
    cookie = response.headers["set-cookie"].lower()
    assert result["email"] == "coach@example.com"
    assert "httponly" in cookie and "secure" in cookie and "samesite=lax" in cookie
    assert [call[0] for call in store.calls] == ["exists", "ensure", "rotate", "create_session", "audit"]


def test_email_signup_token_is_signed_and_verifiable(monkeypatch):
    monkeypatch.setenv("SINOPIA_EMAIL_TOKEN_SECRET", "x" * 40)
    token = auth_api._sign_email_token({
        "purpose": "coach-signup",
        "email": "coach@example.com",
        "name": "Coach Example",
        "exp": 4_000_000_000,
        "terms_version": "terms-v1",
        "privacy_version": "privacy-v1",
    })

    claims = auth_api._verify_email_token(token)

    assert claims["email"] == "coach@example.com"
    assert claims["name"] == "Coach Example"


def test_email_signup_token_rejects_expired_and_tampered_links(monkeypatch):
    monkeypatch.setenv("SINOPIA_EMAIL_TOKEN_SECRET", "x" * 40)
    expired = auth_api._sign_email_token({
        "purpose": "coach-signup",
        "email": "coach@example.com",
        "name": "Coach Example",
        "exp": 1,
    })
    with pytest.raises(HTTPException) as error:
        auth_api._verify_email_token(expired)
    assert error.value.status_code == 400

    token = auth_api._sign_email_token({
        "purpose": "coach-signup",
        "email": "coach@example.com",
        "name": "Coach Example",
        "exp": 4_000_000_000,
    })
    with pytest.raises(HTTPException) as error:
        auth_api._verify_email_token(token + "tampered")
    assert error.value.status_code == 400
