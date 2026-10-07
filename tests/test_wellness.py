from backend.scoring.wellness import wellness_drift


def test_too_few_entries_never_drifts():
    assert wellness_drift([1.0, 1.0, 1.0, 1.0, 1.0]) is False


def test_stable_scores_do_not_drift():
    scores = [4.0, 4.0, 4.0, 4.0, 4.0, 4.0]
    assert wellness_drift(scores) is False


def test_recent_drop_beyond_margin_drifts():
    scores = [4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 2.0, 2.0, 2.0]
    assert wellness_drift(scores) is True


def test_small_recent_drop_within_margin_does_not_drift():
    scores = [4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 3.5, 3.5, 3.5]
    assert wellness_drift(scores) is False


def test_improving_scores_do_not_drift():
    scores = [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 4.0, 4.0, 4.0]
    assert wellness_drift(scores) is False
