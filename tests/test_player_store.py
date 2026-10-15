import pytest

from backend.data.player_store import DuplicatePlayerError, PlayerStore


@pytest.fixture()
def store(tmp_path):
    return PlayerStore(str(tmp_path / "players.db"))


def test_register_returns_a_complete_record(store):
    record = store.register("Amaka", "girls", "2026-01-05")
    assert set(record.keys()) == {"player_id", "name", "team_type", "registered_date", "checkin_token", "team_id"}
    assert record["name"] == "Amaka"
    assert record["team_type"] == "girls"


def test_registered_player_is_retrievable_by_id(store):
    record = store.register("Amaka", "girls", "2026-01-05")
    fetched = store.get(record["player_id"])
    assert fetched is not None
    assert fetched["name"] == "Amaka"


def test_unknown_id_returns_none(store):
    assert store.get("no-such-id") is None


def test_same_name_on_different_teams_is_two_players(store):
    girls_amaka = store.register("Amaka", "girls", "2026-01-05")
    boys_amaka = store.register("Amaka", "boys", "2026-01-05")
    assert girls_amaka["player_id"] != boys_amaka["player_id"]


def test_duplicate_name_on_same_team_is_rejected(store):
    store.register("Amaka", "girls", "2026-01-05")
    with pytest.raises(DuplicatePlayerError):
        store.register("Amaka", "girls", "2026-01-06")


def test_duplicate_name_is_case_insensitive(store):
    store.register("Amaka", "girls", "2026-01-05")
    with pytest.raises(DuplicatePlayerError):
        store.register("AMAKA", "girls", "2026-01-06")


def test_team_listing_is_scoped_and_name_sorted(store):
    store.register("Zainab", "girls", "2026-01-05")
    store.register("Amaka", "girls", "2026-01-05")
    store.register("Tunde", "boys", "2026-01-05")
    names = [p["name"] for p in store.list_for_team("girls")]
    assert names == ["Amaka", "Zainab"]
