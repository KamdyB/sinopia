"""Google ID-token sign-in and server-side coach sessions."""
import os
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from pydantic import BaseModel, ConfigDict, Field

from backend.data.auth_store import auth_store

router = APIRouter(prefix="/auth")
SESSION_COOKIE = "sinopia_session"
SESSION_HOURS = 8
TERMS_VERSION = os.environ.get("SINOPIA_TERMS_VERSION", "2026-10-14")
PRIVACY_VERSION = os.environ.get("SINOPIA_PRIVACY_VERSION", "2026-10-14")


class GoogleCredential(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    credential: str = Field(min_length=20, max_length=8192)


class PolicyAcceptance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    age_18_or_older: bool
    authorised_and_parental_consent_obtained: bool


def _secure_cookie() -> bool:
    return os.environ.get("SINOPIA_ENV", "development").lower() == "production"


def _public_coach(coach: dict[str, Any]) -> dict[str, Any]:
    return {
        "email": coach["email"],
        "display_name": coach["display_name"],
        "team_id": coach["team_id"],
        "team_name": coach["team_name"],
        "accepted_at": coach["accepted_at"],
        "terms_version": coach["terms_version"],
        "privacy_version": coach["privacy_version"],
        "needs_policy_acceptance": (
            coach["accepted_at"] is None
            or coach["terms_version"] != TERMS_VERSION
            or coach["privacy_version"] != PRIVACY_VERSION
        ),
    }


def current_coach(request: Request) -> dict[str, Any]:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Sign-in required.")
    coach = auth_store.get_session(token)
    if coach is None:
        raise HTTPException(status_code=401, detail="Session expired. Sign in again.")
    return coach


@router.post("/google")
def google_sign_in(payload: GoogleCredential, response: Response) -> dict[str, Any]:
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=503, detail="Google sign-in is not configured.")
    try:
        claims = id_token.verify_oauth2_token(
            payload.credential, GoogleRequest(), audience=client_id
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Google sign-in could not be verified.")
    if claims.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
        raise HTTPException(status_code=401, detail="Google sign-in could not be verified.")
    if claims.get("aud") != client_id or claims.get("email_verified") is not True:
        raise HTTPException(status_code=401, detail="Google sign-in could not be verified.")
    email = claims.get("email")
    if not isinstance(email, str) or not email.strip():
        raise HTTPException(status_code=401, detail="Google account email is unavailable.")
    coach = auth_store.ensure_coach(email, str(claims.get("name") or email))
    token = auth_store.create_session(email)
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=SESSION_HOURS * 60 * 60,
        httponly=True,
        secure=_secure_cookie(),
        samesite="lax",
        path="/",
    )
    return _public_coach(coach)


@router.get("/me")
def get_me(request: Request) -> dict[str, Any]:
    return _public_coach(current_coach(request))


@router.post("/accept-policies")
def accept_policies(payload: PolicyAcceptance, request: Request) -> dict[str, bool]:
    coach = current_coach(request)
    if not payload.age_18_or_older or not payload.authorised_and_parental_consent_obtained:
        raise HTTPException(status_code=422, detail="Both declarations must be accepted.")
    auth_store.accept_policies(coach["email"], TERMS_VERSION, PRIVACY_VERSION)
    return {"accepted": True}


@router.post("/logout")
def logout(request: Request, response: Response) -> dict[str, bool]:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        auth_store.delete_session(token)
    response.delete_cookie(
        key=SESSION_COOKIE, path="/", httponly=True, secure=_secure_cookie(), samesite="lax"
    )
    return {"logged_out": True}
