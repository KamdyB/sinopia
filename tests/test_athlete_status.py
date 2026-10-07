from datetime import date

from backend.scoring.athlete_status import athlete_status, status_from_sessions


def log(day, minutes, rpe):
    return {"date": f"2026-01-{day:02d}", "duration_minutes": minutes, "rpe": rpe}


def test_brand_new_athlete_builds_baseline_without_load_flag():
    status = status_from_sessions([log(1, 60, 5)], date(2026, 1, 3))
    assert status["level"] == "ok"
    assert status["numbers"]["building_baseline"] is True


def test_one_huge_session_after_established_baseline_flags_act():
    # Three weeks at 300 per week, then a week at 600.
    sessions = [log(1, 60, 5), log(8, 60, 5), log(15, 60, 5), log(22, 120, 5)]
    status = status_from_sessions(sessions, date(2026, 1, 28))
    assert status["level"] == "act"
    assert status["numbers"]["weekly_load"] == 600.0
    assert status["numbers"]["baseline"] == 300.0


def test_steady_load_stays_ok():
    sessions = [log(1, 60, 5), log(8, 60, 5), log(15, 60, 5), log(22, 60, 5)]
    status = status_from_sessions(sessions, date(2026, 1, 28))
    assert status["level"] == "ok"


def test_zero_load_week_stays_ok_without_an_undertraining_rule():
    # The spec defines a load jump upward only; a quiet week is not a flag.
    sessions = [log(1, 60, 5), log(8, 60, 5), log(15, 60, 5)]
    status = status_from_sessions(sessions, date(2026, 1, 28))
    assert status["level"] == "ok"
    assert status["numbers"]["weekly_load"] == 0.0


def test_any_pain_refers_even_with_normal_load():
    status = athlete_status(
        weekly=300.0, baseline=300.0, weeks_available=6,
        wellness_scores=[], pain=True,
    )
    assert status["level"] == "refer"
    assert any("Pain" in reason for reason in status["reasons"])


def test_pain_refers_even_for_new_athlete():
    status = athlete_status(
        weekly=300.0, baseline=0.0, weeks_available=0,
        wellness_scores=[], pain=True,
    )
    assert status["level"] == "refer"
    assert status["numbers"]["building_baseline"] is True


def test_wellness_drift_alone_watches():
    status = athlete_status(
        weekly=300.0, baseline=300.0, weeks_available=6,
        wellness_scores=[4.0, 4.0, 4.0, 4.0, 4.0, 2.0, 2.0, 2.0], pain=False,
    )
    assert status["level"] == "watch"


def test_pain_outranks_load_jump():
    status = athlete_status(
        weekly=600.0, baseline=300.0, weeks_available=6,
        wellness_scores=[], pain=True,
    )
    assert status["level"] == "refer"
    assert len(status["reasons"]) == 2
