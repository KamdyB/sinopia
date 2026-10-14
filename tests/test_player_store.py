import base64
import sqlite3
import pytest

from backend.data.checkin_store import CheckinStore
from backend.data.player_store import DuplicatePlayerError, PlayerStore


@pytest.fixture()
def store(tmp_path):
    return PlayerStore(str(tmp_path / "players.db"))


def test_register_returns_a_complete_record(store):
    record = store.register("Amaka", "girls", "2026-01-05")
    assert set(record.keys()) == {"player_id", "name", "team_type", "registered_date", "team_id"}
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



def test_athlete_label_and_pain_area_are_encrypted_and_rotatable(tmp_path, monkeypatch):
    db_path = str(tmp_path / "encrypted.db")
    old_key = base64.urlsafe_b64encode(b"o" * 32).decode().rstrip("=")
    new_key = base64.urlsafe_b64encode(b"n" * 32).decode().rstrip("=")
    monkeypatch.setenv("SINOPIA_ENV", "development")
    monkeypatch.setenv("SINOPIA_ENCRYPTION_KEYS", "old:" + old_key)

    players = PlayerStore(db_path)
    player = players.register("Private Label", "girls", "2026-01-05", "team-a")
    checkins = CheckinStore(db_path)
    checkins.log_checkin(
        player["player_id"],
        {"date": "2026-01-05", "sleep": 3, "energy": 3, "soreness": 3,
         "stress": 3, "pain": True, "pain_area": "Knee"},
        "team-a",
    )

    with sqlite3.connect(db_path) as conn:
        stored_name = conn.execute(
            "SELECT name FROM players WHERE player_id = ?", (player["player_id"],)
        ).fetchone()[0]
        stored_area = conn.execute(
            "SELECT pain_area FROM checkins WHERE player_id = ?", (player["player_id"],)
        ).fetchone()[0]
    assert stored_name.startswith("enc:v1:old:")
    assert stored_area.startswith("enc:v1:old:")
    assert "Private Label" not in stored_name
    assert "Knee" not in stored_area

    monkeypatch.setenv("SINOPIA_ENCRYPTION_KEYS", "new:" + new_key + ",old:" + old_key)
    players_after_rotation = PlayerStore(db_path)
    checkins_after_rotation = CheckinStore(db_path)
    assert players_after_rotation.get(player["player_id"])["name"] == "Private Label"
    assert checkins_after_rotation.get_checkins(player["player_id"])[0]["pain_area"] == "Knee"
    with sqlite3.connect(db_path) as conn:
        rotated_name = conn.execute(
            "SELECT name FROM players WHERE player_id = ?", (player["player_id"],)
        ).fetchone()[0]
        rotated_area = conn.execute(
            "SELECT pain_area FROM checkins WHERE player_id = ?", (player["player_id"],)
        ).fetchone()[0]
    assert rotated_name.startswith("enc:v1:new:")
    assert rotated_area.startswith("enc:v1:new:")
