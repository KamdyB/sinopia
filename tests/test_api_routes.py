"""Route tests for the coach tool, signed in with a forged-but-server-side
trusted coach context and a throwaway database. The scoring engine has
its own dedicated tests elsewhere and is never modified here.
"""
import backend.auth as auth_module
from fastapi import HTTPException


def _fake_coach():
    return auth_module.CoachContext(email="coach@example.com")


def _signed_in(client, monkeypatch):
    # Override the auth dependency instead of forging HTTP bearer tokens.
    def fake_get_coach():
        return _fake_coach()
    import backend.main as main_module
    main_module.app.dependency_overrides[auth_module.get_coach] = fake_get_coach
    return client


def _teardown_auth_override():
    import backend.main as main_module
    main_module.app.dependency_overrides.pop(auth_module.get_coach, None)


def test_full_coach_flow(client, monkeypatch):
    _signed_in(client, monkeypatch)
    try:
        # Team creation: the coach owns exactly one team.
        created = client.post(
            "/teams",
            json={"team_name": "Squad One", "sport": "football", "age_band": "under-16", "composition": "full-squad"},
        )
        assert created.status_code == 201, created.json()
        team_id = created.json()["team_id"]
        again = client.post(
            "/teams",
            json={"team_name": "Squad Two", "sport": "netball", "age_band": "under-14", "composition": "other"},
        )
        assert again.status_code == 409

        # Profile update passes through.
        patched = client.patch(
            "/teams/me/profile",
            json={"sport": "netball"},
        )
        assert patched.status_code == 200
        assert patched.json()["sport"] == "netball"

        # Athlete: a code, never a name.
        reg = client.post("/players", json={"code": "ATH-01"})
        assert reg.status_code == 201, reg.json()
        player_id = reg.json()["player_id"]
        dup = client.post("/players", json={"code": "ath-01"})
        assert dup.status_code == 409

        roster = client.get("/players")
        assert roster.status_code == 200
        assert [p["code"] for p in roster.json()] == ["ATH-01"]

        # Sessions land and status comes back from the untouched engine.
        logged = client.post(
            "/sessions",
            json={"player_id": player_id, "date_str": "2026-01-01", "duration_minutes": 60, "rpe": 6},
        )
        assert logged.status_code == 200, logged.json()
        body = logged.json()
        assert body["code"] == "ATH-01"
        assert body["level"] in {"ok", "watch", "act", "refer"}

        # Roster, statuses and history are all team scoping-safe.
        statuses = client.get("/statuses")
        assert statuses.status_code == 200
        assert [s["code"] for s in statuses.json()] == ["ATH-01"]
        history = client.get(f"/players/{player_id}/history")
        assert history.status_code == 200

        # Player lookup from a shared check-in link: public, code only.
        looked_up = client.get(f"/players/{player_id}")
        assert looked_up.status_code == 200
        assert looked_up.json()["code"] == "ATH-01"
        assert "team_id" not in looked_up.json()
    finally:
        _teardown_auth_override()


def test_checkin_needs_no_signin_but_plays_by_team_rules(client, monkeypatch):
    _signed_in(client, monkeypatch)
    try:
        client.post("/teams", json={"team_name": "T", "sport": "other", "age_band": "other", "composition": "other"})
        reg = client.post("/players", json={"code": "ATH-02"}).json()
    finally:
        _teardown_auth_override()

    # Check-ins come from the shared link without any Google account.
    ok = client.post(
        "/checkins",
        json={"player_id": reg["player_id"], "sleep": 4, "energy": 4, "soreness": 4, "stress": 4, "pain": True, "pain_area": "Knee"},
    )
    assert ok.status_code == 201
    missing_player = client.post(
        "/checkins",
        json={"player_id": "does-not-exist", "sleep": 4, "energy": 4, "soreness": 4, "stress": 4, "pain": False},
    )
    assert missing_player.status_code == 404


def test_signed_out_coach_blocked_from_team_and_roster(client):
    for path, kwargs in [
        ("/players", {}),
        ("/statuses", {}),
        ("/teams/me", {}),
        (
            "/sessions",
            {
                "method": "post",
                "json": {"player_id": "x", "date_str": "2026-01-01", "duration_minutes": 30, "rpe": 4},
            },
        ),
    ]:
        method = kwargs.pop("method", "get")
        response = getattr(client, method)(path, **kwargs)
        assert response.status_code == 401, response.json()


def test_second_coach_cannot_see_first_coach_athletes(client, monkeypatch):
    def coach(email: str):
        return lambda: auth_module.CoachContext(email=email)

    import backend.main as main_module
    main_module.app.dependency_overrides[auth_module.get_coach] = coach("a@example.com")
    try:
        client.post("/teams", json={"team_name": "A", "sport": "other", "age_band": "other", "composition": "other"})
        client.post("/players", json={"code": "ATH-A"})
    finally:
        _teardown_auth_override()

    main_module.app.dependency_overrides[auth_module.get_coach] = coach("b@example.com")
    try:
        client.post("/teams", json={"team_name": "B", "sport": "other", "age_band": "other", "composition": "other"})
        roster = client.get("/players")
        assert [p["code"] for p in roster.json()] == []
        statuses = client.get("/statuses")
        assert statuses.json() == []
    finally:
        _teardown_auth_override()


def test_demo_needs_no_signin_and_never_touches_store(client):
    statuses = client.get("/demo/statuses")
    assert statuses.status_code == 200
    codes = [s["code"] for s in statuses.json()]
    assert codes and all(code.startswith("DEMO-") for code in codes)
    one = client.get("/demo/athletes/DEMO-A1/history")
    assert one.status_code == 200
    missing = client.get("/demo/athletes/NOPE/history")
    assert missing.status_code == 404
