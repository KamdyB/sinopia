import json
from io import BytesIO

import pytest
from fastapi import HTTPException

from backend.security import turnstile


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        return self.payload[:size]


def test_production_turnstile_fails_closed_when_not_configured(monkeypatch):
    monkeypatch.setenv("SINOPIA_ENV", "production")
    monkeypatch.delenv("TURNSTILE_SECRET_KEY", raising=False)
    monkeypatch.delenv("SINOPIA_TURNSTILE_HOSTNAMES", raising=False)
    with pytest.raises(HTTPException) as error:
        turnstile.require_turnstile("token", "login")
    assert error.value.status_code == 503


def test_turnstile_requires_valid_hostname_and_action(monkeypatch):
    monkeypatch.setenv("SINOPIA_ENV", "production")
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "test-secret")
    monkeypatch.setenv("SINOPIA_TURNSTILE_HOSTNAMES", "app.example.com")
    monkeypatch.setattr(turnstile, "urlopen", lambda request, timeout: FakeResponse({
        "success": True, "hostname": "app.example.com", "action": "login"
    }))
    turnstile.require_turnstile("one-time-token", "login")
    with pytest.raises(HTTPException) as error:
        turnstile.require_turnstile("one-time-token", "delete_account")
    assert error.value.status_code == 403


def test_turnstile_rejects_wrong_hostname(monkeypatch):
    monkeypatch.setenv("SINOPIA_ENV", "production")
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "test-secret")
    monkeypatch.setenv("SINOPIA_TURNSTILE_HOSTNAMES", "app.example.com")
    monkeypatch.setattr(turnstile, "urlopen", lambda request, timeout: FakeResponse({
        "success": True, "hostname": "attacker.example", "action": "login"
    }))
    with pytest.raises(HTTPException) as error:
        turnstile.require_turnstile("one-time-token", "login")
    assert error.value.status_code == 403


def test_turnstile_is_skipped_only_in_explicit_development(monkeypatch):
    monkeypatch.setenv("SINOPIA_ENV", "development")
    monkeypatch.delenv("TURNSTILE_SECRET_KEY", raising=False)
    turnstile.require_turnstile(None, "login")
