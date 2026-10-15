from datetime import datetime
from zoneinfo import ZoneInfo

from backend.timeutil import service_date


def test_service_date_uses_configured_pilot_timezone(monkeypatch):
    monkeypatch.setenv("SINOPIA_TIMEZONE", "Africa/Lagos")
    expected = datetime.now(ZoneInfo("Africa/Lagos")).date()
    assert service_date() == expected
