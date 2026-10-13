import pytest

from backend.data.player_store import DuplicatePlayerError, PlayerStore


@pytest.fixture()
def store(tmp_path):
    return PlayerStore(str(tmp_path / "players.db"))


def test_register_store_athlete_code_only(store):
    record = store.register("ATH-01", "team-one", "2026-01-05")
    assert set(record.keys()) == {"player_id", "code", "team_id", "registered_date"}
    assert record["code"] == "ATH-01"
    assert record["team_id"] == "team-one"


def test_registered_player_is_retrievable_by_id(store):
    record = store.register("ATH-01", "team-one", "2026-01-05")
    fetched = store.get(record["player_id"])
    assert fetched is not None
    assert fetched["code"] == "ATH-01"


def test_unknown_id_returns_none(store):
    assert store.get("no-such-id") is None


def test_same_code_on_different_teams_is_two_players(store):
    one = store.register("ATH-01", "team-one", "2026-01-05")
    two = store.register("ATH-01", "team-two", "2026-01-05")
    assert one["player_id"] != two["player_id"]


def test_duplicate_code_on_same_team_is_rejected(store):
    store.register("ATH-01", "team-one", "2026-01-05")
    with pytest.raises(DuplicatePlayerError):
        store.register("ATH-01", "team-one", "2026-01-06")


def test_list_for_team_scopes_by_team_id(store):
    store.register("ATH-01", "team-one", "2026-01-05")
    store.register("ATH-02", "team-one", "2026-01-05")
    store.register("ATH-09", "team-two", "2026-01-05")
    codes = [p["code"] for p in store.list_for_team("team-one")]
    assert codes == ["ATH-01", "ATH-02"]
