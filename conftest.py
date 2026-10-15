"""Give every API test its own isolated SQLite database."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import pytest
from fastapi.testclient import TestClient
from backend.api.auth import get_current_coach, get_current_team
import backend.api.checkins as checkins_api
import backend.api.players as players_api
import backend.api.sessions as sessions_api
import backend.api.statuses as statuses_api
import backend.api.team_sessions as team_sessions_api
from backend.data.checkin_store import CheckinStore
from backend.data.player_store import PlayerStore
from backend.data.session_store import SessionStore
from backend.data.team_session_store import TeamSessionStore
from backend.main import app

_ROUTE_MODULES = (players_api, sessions_api, checkins_api, statuses_api, team_sessions_api)
_STORE_TYPES = (PlayerStore, SessionStore, CheckinStore, TeamSessionStore)

@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_url = "sqlite:///" + str(tmp_path / "test.db")
    fresh = {store_type: store_type(db_url) for store_type in _STORE_TYPES}
    for module in _ROUTE_MODULES:
        for attr, value in vars(module).items():
            store_type = next((t for t in _STORE_TYPES if isinstance(value, t)), None)
            if store_type is not None:
                monkeypatch.setattr(module, attr, fresh[store_type])
    app.dependency_overrides[get_current_coach] = lambda: {"google_sub": "test-coach", "email": "coach@example.test", "display_name": "Test Coach"}
    app.dependency_overrides[get_current_team] = lambda: {"team_id": "test-team", "coach_id": "test-coach", "name": "Test Team", "team_type": "girls"}
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_current_coach, None)
    app.dependency_overrides.pop(get_current_team, None)
