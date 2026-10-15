"""Service-local calendar dates for records whose date is assigned by the server."""
import os
from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def service_date() -> date:
    timezone_name = os.environ.get("SINOPIA_TIMEZONE", "Africa/Lagos").strip()
    try:
        zone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise RuntimeError("SINOPIA_TIMEZONE must be a valid IANA time-zone name.") from exc
    return datetime.now(zone).date()
