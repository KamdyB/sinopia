"""Google ID-token sign-in and server-side coach sessions."""
import os
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request, Response
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from pydantic import BaseModel, ConfigDict, Field

from backend.data.auth_store import auth_store
from backend.security.turnstile import require_turnstile

router = APIRouter(prefix="/auth")
SESSION_COOKIE = "sinopia_session"
SESSION_HOURS = 8
TERMS_VERSION = os.environ.get("SINOPIA_TERMS_VERSION", "2026-10-14")
PRIVACY_VERSION = os.environ.get("SINOPIA_PRIVACY_VERSION", "2026-10-14")


class GoogleCredential(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    credential: str = Field(min_length=20, max_length=8192)
    turnstile_token: str | None = Field(default=None, max_length=2048)
    intent: Literal["signup", "signin"] = "signin"


class CoachPublicResponse(BaseModel):
    email: str
    display_name: str
    team_id: str
    team_name: str
    team_type: Literal["girls", "boys", "mixed"] | None
    needs_onboarding: bool
    accepted_at: str | None
    terms_version: str | None
    privacy_version: str | None
    needs_policy_acceptance: bool


class PolicyAcceptedResponse(BaseModel):
    accepted: bool


class LogoutResponse(BaseModel):
    logged_out: bool


class PolicyAcceptance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    age_18_or_older: bool
    authorised_and_parental_consent_obtained: bool
    accept_terms_and_privacy: bool


def _secure_cookie() -> bool:
    return os.environ.get("SINOPIA_ENV", "production").lower() == "production"


def _public_coach(coach: dict[str, Any]) -> dict[str, Any]:
    return {
        "email": coach["email"],
        "display_name": coach["display_name"],
        "team_id": coach["team_id"],
        "team_name": coach["team_name"],
        "team_type": coach.get("team_type"),
        "needs_onboarding": coach.get("team_type") not in {"girls", "boys", "mixed"},
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
    if os.environ.get("SINOPIA_ENV", "production").lower() != "production":
        return auth_store.ensure_coach("dev@localhost", "Local development coach")
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Sign-in required.")
    coach = auth_store.get_session(token)
    if coach is None:
        raise HTTPException(status_code=401, detail="Session expired. Sign in again.")
    return coach


def require_accepted_coach(request: Request) -> dict[str, Any]:
    coach = current_coach(request)
    if os.environ.get("SINOPIA_ENV", "production").lower() == "production":
        if (
            coach["accepted_at"] is None
            or coach["terms_version"] != TERMS_VERSION
            or coach["privacy_version"] != PRIVACY_VERSION
        ):
            raise HTTPException(status_code=403, detail="Accept the current declarations before continuing.")
    return coach


@router.post("/google", response_model=CoachPublicResponse)
def google_sign_in(payload: GoogleCredential, response: Response) -> dict[str, Any]:
    require_turnstile(payload.turnstile_token, "login")
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
    # Any verified Google account may register. Email uniqueness is enforced by the database.
    if payload.intent == "signup":
        coach = auth_store.register_coach(email, str(claims.get("name") or email))
        if coach is None:
            raise HTTPException(status_code=409, detail="An account already exists for this email. Sign in instead.")
    else:
        if not auth_store.coach_exists(email):
            raise HTTPException(status_code=404, detail="No account exists for this email. Choose Get started to create one.")
        coach = auth_store.ensure_coach(email, str(claims.get("name") or email))
    auth_store.delete_sessions_for_coach(email)
    token = auth_store.create_session(email)
    auth_store.log_event("coach_signed_in", coach["team_id"])
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


@router.get("/me", response_model=CoachPublicResponse)
def get_me(request: Request) -> dict[str, Any]:
    return _public_coach(current_coach(request))


@router.post("/accept-policies", response_model=PolicyAcceptedResponse)
def accept_policies(payload: PolicyAcceptance, request: Request) -> dict[str, bool]:
    coach = current_coach(request)
    if not payload.age_18_or_older or not payload.authorised_and_parental_consent_obtained or not payload.accept_terms_and_privacy:
        raise HTTPException(status_code=422, detail="Both declarations and the Terms/Privacy acceptance must be confirmed.")
    auth_store.accept_policies(coach["email"], TERMS_VERSION, PRIVACY_VERSION)
    auth_store.log_event("policies_accepted", coach["team_id"])
    return {"accepted": True}


@router.post("/logout", response_model=LogoutResponse)
def logout(request: Request, response: Response) -> dict[str, bool]:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        auth_store.delete_session(token)
    response.delete_cookie(
        key=SESSION_COOKIE, path="/", httponly=True, secure=_secure_cookie(), samesite="lax"
    )
    return {"logged_out": True}


class TeamSetupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    team_name: str = Field(min_length=1, max_length=120)
    team_type: Literal["girls", "boys", "mixed"]


@router.post("/setup-team", response_model=CoachPublicResponse)
def setup_team(payload: TeamSetupRequest, request: Request) -> dict[str, Any]:
    coach = require_accepted_coach(request)
    try:
        auth_store.update_team(coach["email"], payload.team_name, payload.team_type)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    updated = auth_store.get_session(request.cookies.get(SESSION_COOKIE, ""))
    if updated is None:
        raise HTTPException(status_code=401, detail="Session expired. Sign in again.")
    auth_store.log_event("team_created", updated["team_id"])
    return _public_coach(updated)


def require_onboarded_coach(request: Request) -> dict[str, Any]:
    coach = require_accepted_coach(request)
    if coach.get("team_type") not in {"girls", "boys", "mixed"}:
        raise HTTPException(status_code=409, detail="Complete team setup before managing athletes.")
    return coach
