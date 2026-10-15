from backend.scoring.history import history_points


def log(day, minutes, rpe):
    return {"date": f"2026-01-{day:02d}", "duration_minutes": minutes, "rpe": rpe}


def test_every_session_date_appears_once_in_order():
    sessions = [log(8, 60, 5), log(1, 60, 5), log(15, 60, 5)]
    points = history_points(sessions)
    assert [p["date"] for p in points] == ["2026-01-01", "2026-01-08", "2026-01-15"]


def test_early_points_build_baseline():
    points = history_points([log(1, 60, 5), log(2, 60, 5)])
    assert points[0]["level"] == "building"
    assert points[0]["numbers"]["building_baseline"] is True


def test_late_point_reflects_load_jump():
    points = history_points([log(1, 60, 5), log(8, 60, 5), log(15, 60, 5), log(22, 120, 5)])
    assert points[-1]["level"] == "act"
    assert points[-2]["level"] == "building"


def test_session_load_recorded_per_point():
    points = history_points([log(1, 90, 4)])
    assert points[0]["session_load"] == 360.0


def test_two_players_histories_are_computed_from_their_own_lists():
    light = history_points([log(1, 20, 3), log(8, 20, 3), log(15, 20, 3), log(22, 20, 3)])
    heavy = history_points([log(1, 60, 5), log(8, 60, 5), log(15, 60, 5), log(22, 200, 8)])
    assert light[-1]["numbers"]["weekly_load"] == 60.0
    assert heavy[-1]["numbers"]["weekly_load"] == 1600.0
    assert light[-1]["numbers"]["baseline"] != heavy[-1]["numbers"]["baseline"]


def test_multiple_sessions_on_same_day_are_aggregated():
    points = history_points([log(1, 60, 5), log(1, 30, 4)])
    assert len(points) == 1
    assert points[0]["session_count"] == 2
    assert points[0]["session_load"] == 420.0


def test_checkin_only_day_is_in_history_and_pain_area_is_returned():
    points = history_points([log(1, 60, 5)], [{
        "date": "2026-01-02", "sleep": 4, "energy": 3, "soreness": 4,
        "stress": 4, "pain": True, "pain_area": "Knee", "pain_acknowledged": False,
    }])
    assert [p["date"] for p in points] == ["2026-01-01", "2026-01-02"]
    assert points[1]["session_count"] == 0
    assert points[1]["pain"] is True
    assert points[1]["pain_area"] == "Knee"
    assert points[1]["wellness_score"] == 3.75
