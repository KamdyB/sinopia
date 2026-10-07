from datetime import date

from backend.scoring.load_calculator import (
    daily_loads,
    rolling_baseline,
    session_load,
    weeks_tracked,
    weekly_load,
)


def s(day, minutes, rpe):
    return {"date": f"2026-01-{day:02d}", "duration_minutes": minutes, "rpe": rpe}


def test_session_load_is_minutes_times_rpe():
    assert session_load(60, 5) == 300.0


def test_same_day_sessions_merge_in_daily_loads():
    daily = daily_loads([s(1, 30, 4), s(1, 30, 6), s(2, 60, 5)])
    assert daily[date(2026, 1, 1)] == 300.0
    assert daily[date(2026, 1, 2)] == 300.0


def test_weekly_load_treats_missing_days_as_zero():
    daily = daily_loads([s(1, 60, 5)])  # only Jan 1 has load
    as_of = date(2026, 1, 7)
    assert weekly_load(daily, as_of) == 300.0


def test_weekly_load_counts_only_trailing_seven_days():
    daily = daily_loads([s(1, 60, 5), s(8, 60, 5)])
    assert weekly_load(daily, date(2026, 1, 8)) == 300.0


def test_weeks_tracked_counts_complete_windows_only():
    daily = daily_loads([s(1, 30, 5)])
    assert weeks_tracked(daily, date(2026, 1, 14)) == 1
    assert weeks_tracked(daily, date(2026, 1, 21)) == 2
    assert weeks_tracked(daily, date(2026, 1, 7)) == 0


def test_rolling_baseline_averages_only_tracked_weeks():
    # One week of history at 300 per week: baseline over one tracked week is 300.
    daily = daily_loads([s(1, 60, 5)])
    baseline = rolling_baseline(daily, date(2026, 1, 21), 4)
    assert baseline == 300.0


def test_rolling_baseline_is_zero_without_history():
    assert rolling_baseline({}, date(2026, 1, 21), 4) == 0.0
