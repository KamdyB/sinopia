"""Google sign-in, backend side.

The frontend obtains the Google ID token (Google Identity Services)
and sends it on every request. This module verifies it
cryptographically against GOOGLE_CLIENT_ID, and an expired or forged
token can never reach any route. Verification results are cached in
memory for a bounded time because the request volume is small and the
token itself is the session.

No user rows are stored from Google: the verified email resolves the
coach to their one team through the teams table.
"""
import os
import time
from dataclasses import dataclass

from fastapi import Header, HTTPException

from backend.data.team_store import team_store

_cache: dict[str, tuple[float, "CoachContext"]] = {}
_CACHE_TTL_SECONDS = 25 * 60


@dataclass(frozen=True)
class CoachContext:
    email: str


def _verify(raw_token: str) -> "CoachContext":
    # Imported lazily so the whole app still boots (and the dev/test
    # suite still runs) on machines without google-auth installed as
    # long as no authenticated route is actually hit.
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token as google_id_token

    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    if not client_id:
        raise HTTPException(
            status_code=503,
            detail="Google sign-in is not configured on the server. "
            "Set GOOGLE_CLIENT_ID.",
        )
    try:
        info = google_id_token.verify_oauth2_token(raw_token, google_requests.Request(), client_id)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired Google sign-in.") from exc

    email = info.get("email")
    if not email or not info.get("email_verified"):
        raise HTTPException(status_code=401, detail="Google account has no verified email.")

    return CoachContext(email=email)


def verify_token(raw_token: str) -> "CoachContext":
    cached = _cache.get(raw_token)
    if cached and (time.monotonic() - cached[0]) < _CACHE_TTL_SECONDS:
        return cached[1]
    context = _verify(raw_token)
    # Bounded cache: drop stale entries when it grows.
    if len(_cache) > 4096:
        now = time.monotonic()
        for key in [k for k, (ts, _) in _cache.items() if now - ts >= _CACHE_TTL_SECONDS]:
            del _cache[key]
    _cache[raw_token] = (time.monotonic(), context)
    return context


def get_coach(authorization: str = Header(default="")) -> CoachContext:
    """FastAPI dependency. Route modules through it before anything else."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Sign in with Google first; every query needs a verified coach.",
        )
    return verify_token(authorization[len("Bearer "):])


def require_team(coach: CoachContext) -> dict:
    """Resolves the authenticated coach to their one team.

    The team id always comes from the verified email on the server side,
    never from anything the client sends, so one coach can never reach
    another team's athletes, sessions or check-ins.
    """
    team = team_store.get_by_coach(coach.email)
    if team is None:
        raise HTTPException(
            status_code=404,
            detail="No team yet. Create your team first.",
        )
    return team
