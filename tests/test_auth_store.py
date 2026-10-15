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
