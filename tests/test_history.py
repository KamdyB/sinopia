from backend.scoring.history import history_points


def log(day, minutes, rpe):
    return {"date": f"2026-01-{day:02d}", "duration_minutes": minutes, "rpe": rpe}


def test_every_session_appears_once_in_order():
    sessions = [log(8, 60, 5), log(1, 60, 5), log(15, 60, 5)]
    points = history_points(sessions)
    assert [p["date"] for p in points] == ["2026-01-01", "2026-01-08", "2026-01-15"]


def test_early_points_build_baseline():
    sessions = [log(1, 60, 5), log(2, 60, 5)]
    points = history_points(sessions)
    assert points[0]["level"] == "ok"
    assert points[0]["numbers"]["building_baseline"] is True


def test_late_point_reflects_load_jump():
    sessions = [log(1, 60, 5), log(8, 60, 5), log(15, 60, 5), log(22, 120, 5)]
    points = history_points(sessions)
    assert points[-1]["level"] == "act"
    assert points[-2]["level"] == "ok"


def test_session_load_recorded_per_point():
    sessions = [log(1, 90, 4)]
    points = history_points(sessions)
    assert points[0]["session_load"] == 360.0


def test_two_players_histories_are_computed_from_their_own_lists():
    light = history_points([log(1, 20, 3), log(8, 20, 3), log(15, 20, 3), log(22, 20, 3)])
    heavy = history_points([log(1, 60, 5), log(8, 60, 5), log(15, 60, 5), log(22, 200, 8)])
    assert light[-1]["numbers"]["weekly_load"] == 60.0
    assert heavy[-1]["numbers"]["weekly_load"] == 1600.0
    assert light[-1]["numbers"]["baseline"] != heavy[-1]["numbers"]["baseline"]
