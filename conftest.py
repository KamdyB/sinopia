"""Puts the repo root on sys.path for backend.* imports and gives every
test a fresh throwaway database, patched into every store reference the
API modules imported, so no test ever touches real data."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pytest
from fastapi.testclient import TestClient

import backend.api.checkins as checkins_api
import backend.api.players as players_api
import backend.api.sessions as sessions_api
import backend.api.statuses as statuses_api
from backend.data.checkin_store import CheckinStore
from backend.data.player_store import PlayerStore
from backend.data.session_store import SessionStore
from backend.main import app

_ROUTE_MODULES = (players_api, sessions_api, checkins_api, statuses_api)
_STORE_TYPES = (PlayerStore, SessionStore, CheckinStore)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    fresh = {store_type: store_type(db_path) for store_type in _STORE_TYPES}
    for module in _ROUTE_MODULES:
        for attr, value in vars(module).items():
            store_type = next(
                (t for t in _STORE_TYPES if isinstance(value, t)), None
            )
            if store_type is not None:
                monkeypatch.setattr(module, attr, fresh[store_type])
    return TestClient(app)
