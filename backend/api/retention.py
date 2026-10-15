"""Scheduled, team-scoped retention for historical training and wellness records.

Configure CRON_SECRET and an explicitly approved SINOPIA_RETENTION_DAYS value.
Missing or invalid configuration fails closed and does not delete data.
"""
import hmac
import os
from datetime import timedelta

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from backend.data.auth_store import auth_store
from backend.data.checkin_store import checkin_store
from backend.data.session_store import session_store
from backend.timeutil import service_date

router = APIRouter(prefix="/internal/retention", tags=["internal"])


class RetentionResult(BaseModel):
    status: str
    cutoff_date: str
    deleted_sessions: int
    deleted_checkins: int


@router.get("/purge", response_model=RetentionResult, include_in_schema=False)
def purge_expired_records(request: Request) -> RetentionResult:
    expected = os.environ.get("CRON_SECRET", "").strip()
    if len(expected) < 32:
        raise HTTPException(status_code=503, detail="Retention job is not configured.")
    supplied = request.headers.get("authorization", "")
    if not hmac.compare_digest(supplied, f"Bearer {expected}"):
        raise HTTPException(status_code=403, detail="Forbidden.")

    raw_days = os.environ.get("SINOPIA_RETENTION_DAYS", "").strip()
    try:
        retention_days = int(raw_days)
    except (TypeError, ValueError):
        raise HTTPException(status_code=503, detail="Retention policy is not configured.")
    if not 1 <= retention_days <= 3650:
        raise HTTPException(status_code=503, detail="Retention policy is not configured.")

    cutoff = (service_date() - timedelta(days=retention_days)).isoformat()
    deleted_sessions = 0
    deleted_checkins = 0
    for team_id in auth_store.list_team_ids():
        deleted_sessions += session_store.purge_before(cutoff, team_id)
        deleted_checkins += checkin_store.purge_before(cutoff, team_id)

    return RetentionResult(
        status="completed",
        cutoff_date=cutoff,
        deleted_sessions=deleted_sessions,
        deleted_checkins=deleted_checkins,
    )
