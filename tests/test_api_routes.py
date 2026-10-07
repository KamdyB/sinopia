from backend.main import app  # imported so conftest patches apply to its routers


def register(client, name, team="girls"):
    response = client.post("/players", json={"name": name, "team_type": team})
    assert response.status_code == 201
    return response.json()["player_id"]


def test_register_and_log_returns_level_with_numbers(client):
    player_id = register(client, "Amaka")
    response = client.post(
        "/sessions",
        json={
            "player_id": player_id,
            "date_str": "2026-01-10",
            "duration_minutes": 60,
            "rpe": 5,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["level"] == "ok"
    assert body["previous_level"] is None
    assert body["numbers"]["building_baseline"] is True
    assert body["reasons"]


def test_log_again_reports_previous_level(client):
    player_id = register(client, "Bisi")
    client.post(
        "/sessions",
        json={"player_id": player_id, "date_str": "2026-01-01",
              "duration_minutes": 60, "rpe": 5},
    )
    response = client.post(
        "/sessions",
        json={"player_id": player_id, "date_str": "2026-01-02",
              "duration_minutes": 60, "rpe": 5},
    )
    assert response.json()["previous_level"] == "ok"


def test_unknown_player_404s(client):
    response = client.post(
        "/sessions",
        json={"player_id": "nope", "date_str": "2026-01-01",
              "duration_minutes": 60, "rpe": 5},
    )
    assert response.status_code == 404


def test_future_date_422s(client):
    player_id = register(client, "Chidi")
    response = client.post(
        "/sessions",
        json={"player_id": player_id, "date_str": "2099-01-01",
              "duration_minutes": 60, "rpe": 5},
    )
    assert response.status_code == 422


def test_duplicate_name_409s(client):
    register(client, "Amaka")
    response = client.post("/players", json={"name": "amaka", "team_type": "girls"})
    assert response.status_code == 409


def test_history_returns_walk_forward_levels(client):
    player_id = register(client, "Dami")
    for day, minutes in ((1, 60), (8, 60), (15, 60), (22, 120)):
        client.post(
            "/sessions",
            json={"player_id": player_id, "date_str": f"2026-01-{day:02d}",
                  "duration_minutes": minutes, "rpe": 5},
        )
    response = client.get(f"/players/{player_id}/history")
    assert response.status_code == 200
    points = response.json()
    assert len(points) == 4
    assert points[0]["level"] == "ok"
    assert points[-1]["level"] == "act"


def test_checkin_logged_then_pain_refers(client):
    player_id = register(client, "Efe")
    ok = client.post(
        "/checkins",
        json={"player_id": player_id, "sleep": 4, "energy": 3,
              "soreness": 2, "stress": 4, "pain": False},
    )
    assert ok.status_code == 201
    pain = client.post(
        "/checkins",
        json={"player_id": player_id, "sleep": 3, "energy": 2,
              "soreness": 3, "stress": 3, "pain": True, "pain_area": "Knee"},
    )
    assert pain.status_code == 201
    statuses = client.get("/statuses?team_type=girls").json()
    entry = next(s for s in statuses if s["player_id"] == player_id)
    assert entry["level"] == "refer"


def test_checkin_pain_without_area_422s(client):
    player_id = register(client, "Fola")
    response = client.post(
        "/checkins",
        json={"player_id": player_id, "sleep": 3, "energy": 3,
              "soreness": 3, "stress": 3, "pain": True},
    )
    assert response.status_code == 422


def test_statuses_orders_most_urgent_first(client):
    calm = register(client, "Gina")
    hurt = register(client, "Hauwa")
    client.post("/sessions", json={"player_id": calm, "date_str": "2026-01-01",
                                   "duration_minutes": 60, "rpe": 5})
    client.post("/checkins", json={"player_id": hurt, "sleep": 3, "energy": 3,
                                   "soreness": 3, "stress": 3, "pain": True,
                                   "pain_area": "Ankle or foot"})
    statuses = client.get("/statuses?team_type=girls").json()
    assert [s["player_id"] for s in statuses] == [hurt, calm]
