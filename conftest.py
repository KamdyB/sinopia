"""Puts the repo root on sys.path for backend.* imports and gives every
test a fresh throwaway database, patched into every store reference the
API modules imported, so no test ever touches real data."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("SINOPIA_ENV", "development")

import pytest
from fastapi.testclient import TestClient

import backend.api.auth as auth_api
import backend.api.checkins as checkins_api
import backend.api.players as players_api
import backend.api.privacy as privacy_api
import backend.api.sessions as sessions_api
import backend.api.statuses as statuses_api
import backend.api.team_sessions as team_sessions_api
from backend.data.auth_store import AuthStore
from backend.data.checkin_store import CheckinStore
from backend.data.open_team_session_store import OpenTeamSessionStore
from backend.data.player_store import PlayerStore
from backend.data.session_store import SessionStore
from backend.main import app
from backend.security.rate_limit import _EVENTS, _LOCK

_ROUTE_MODULES = (auth_api, players_api, sessions_api, checkins_api, statuses_api, privacy_api, team_sessions_api)
_STORE_TYPES = (AuthStore, PlayerStore, SessionStore, CheckinStore, OpenTeamSessionStore)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    with _LOCK:
        _EVENTS.clear()
    db_path = str(tmp_path / "test.db")
    fresh = {store_type: store_type(db_path) for store_type in _STORE_TYPES}
    test_auth = fresh[AuthStore]
    test_auth.ensure_coach("dev@localhost", "Local development coach")
    test_auth.update_team("dev@localhost", "Test Team", "girls")
    test_auth.accept_policies("dev@localhost", "test-terms", "test-privacy")
    for module in _ROUTE_MODULES:
        for attr, value in vars(module).items():
            store_type = next(
                (t for t in _STORE_TYPES if isinstance(value, t)), None
            )
            if store_type is not None:
                monkeypatch.setattr(module, attr, fresh[store_type])
    return TestClient(app, headers={"X-Sinopia-Request": "1"}, raise_server_exceptions=False)
