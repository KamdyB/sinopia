from backend.data.auth_store import AuthStore


def test_sessions_are_opaque_expiring_and_revocable(tmp_path):
    store = AuthStore(str(tmp_path / "auth.db"))
    store.ensure_coach("coach@example.com", "Coach")
    token = store.create_session("coach@example.com")
    assert store.get_session(token)["email"] == "coach@example.com"
    store.delete_session(token)
    assert store.get_session(token) is None


def test_login_rotation_invalidates_prior_sessions(tmp_path):
    store = AuthStore(str(tmp_path / "auth.db"))
    store.ensure_coach("coach@example.com", "Coach")
    old_token = store.create_session("coach@example.com")
    new_token = store.create_session("coach@example.com")
    store.delete_sessions_for_coach("coach@example.com")
    assert store.get_session(old_token) is None
    assert store.get_session(new_token) is None


def test_team_composition_is_saved_once(tmp_path):
    store = AuthStore(str(tmp_path / "team.db"))
    created = store.ensure_coach("team@example.com", "Coach")
    assert created["team_type"] is None
    team = store.update_team("team@example.com", "  U17   Football ", "mixed")
    assert team["team_name"] == "U17 Football"
    assert team["team_type"] == "mixed"
    session = store.get_session(store.create_session("team@example.com"))
    assert session["team_type"] == "mixed"
    import pytest
    with pytest.raises(ValueError):
        store.update_team("team@example.com", "Changed", "girls")


def test_register_coach_creates_one_account_and_initial_team(tmp_path):
    store = AuthStore(str(tmp_path / "registration.db"))

    created = store.register_coach("New.Coach@example.com", "New Coach")

    assert created is not None
    assert created["email"] == "new.coach@example.com"
    assert created["team_id"]
    assert created["team_name"] == "My team"
    assert store.coach_exists("NEW.COACH@example.com")


def test_register_coach_rejects_duplicate_email_case_insensitively(tmp_path):
    store = AuthStore(str(tmp_path / "duplicate-registration.db"))

    first = store.register_coach("Coach@example.com", "Coach")
    duplicate = store.register_coach(" coach@EXAMPLE.com ", "Second Coach")

    assert first is not None
    assert duplicate is None
    assert store.coach_exists("coach@example.com")
    with __import__("backend.data.db", fromlist=["connect"]).connect(str(tmp_path / "duplicate-registration.db")) as conn:
        assert conn.execute("SELECT COUNT(*) AS count FROM coaches WHERE email = ?", ("coach@example.com",)).fetchone()["count"] == 1
        assert conn.execute("SELECT COUNT(*) AS count FROM teams WHERE coach_email = ?", ("coach@example.com",)).fetchone()["count"] == 1
