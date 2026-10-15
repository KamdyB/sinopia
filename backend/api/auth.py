"""Google ID-token sign-in and server-side coach sessions."""
import os
import base64
import hashlib
import hmac
import html
import json
import time
from urllib.request import Request as UrlRequest, urlopen
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


class EmailSignupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=3, max_length=320)
    turnstile_token: str | None = Field(default=None, max_length=2048)
    age_18_or_older: bool
    authorised_and_parental_consent_obtained: bool
    accept_terms_and_privacy: bool


class EmailVerificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=20, max_length=4096)


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


def _email_token_secret() -> bytes:
    secret = os.environ.get("SINOPIA_EMAIL_TOKEN_SECRET", "").strip()
    if len(secret) < 32:
        raise HTTPException(status_code=503, detail="Email registration is not configured.")
    return secret.encode("utf-8")


def _sign_email_token(payload: dict[str, Any]) -> str:
    raw = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).rstrip(b"=").decode()
    signature = hmac.new(_email_token_secret(), raw.encode(), hashlib.sha256).digest()
    return raw + "." + base64.urlsafe_b64encode(signature).rstrip(b"=").decode()


def _verify_email_token(token: str) -> dict[str, Any]:
    try:
        raw, supplied = token.split(".", 1)
        expected = hmac.new(_email_token_secret(), raw.encode(), hashlib.sha256).digest()
        actual = base64.urlsafe_b64decode(supplied + "=" * (-len(supplied) % 4))
        if not hmac.compare_digest(expected, actual):
            raise ValueError("signature")
        payload = json.loads(base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)))
        if payload.get("purpose") != "coach-signup" or int(payload.get("exp", 0)) < int(time.time()):
            raise ValueError("expired")
        return payload
    except Exception:
        raise HTTPException(status_code=400, detail="This verification link is invalid or has expired. Request a new one.")


@router.post("/email/request")
def request_email_signup(payload: EmailSignupRequest) -> dict[str, bool]:
    require_turnstile(payload.turnstile_token, "login")
    email = payload.email.strip().lower()
    if "@" not in email or "." not in email.rsplit("@", 1)[-1] or any(ch.isspace() for ch in email):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")
    if not payload.age_18_or_older or not payload.authorised_and_parental_consent_obtained or not payload.accept_terms_and_privacy:
        raise HTTPException(status_code=422, detail="Confirm both declarations and accept the Terms and Privacy notice.")
    if auth_store.coach_exists(email):
        raise HTTPException(status_code=409, detail="An account already exists for this email. Use Sign in instead.")
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    sender = os.environ.get("SINOPIA_EMAIL_FROM", "").strip()
    app_url = os.environ.get("SINOPIA_EMAIL_APP_URL", "").strip().rstrip("/")
    if not api_key or not sender or not app_url:
        raise HTTPException(status_code=503, detail="Email registration is not configured yet.")
    token = _sign_email_token({
        "purpose": "coach-signup", "email": email,
        "name": " ".join(payload.full_name.split())[:120],
        "exp": int(time.time()) + 900,
        "terms_version": TERMS_VERSION, "privacy_version": PRIVACY_VERSION,
    })
    link = app_url + "/verify-email?token=" + token
    body = {
        "from": sender, "to": [email], "subject": "Verify your email for Sinopia",
        "html": "<p>Confirm this email address to create your Sinopia coach account.</p>"
        + '<p><a href="' + html.escape(link, quote=True) + '">Verify email and create account</a></p>'
        + "<p>This link expires in 15 minutes. If you did not request it, ignore this message.</p>",
    }
    request = UrlRequest(
        "https://api.resend.com/emails", data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=8) as response:
            if response.status < 200 or response.status >= 300:
                raise ValueError("email provider rejected request")
    except Exception:
        raise HTTPException(status_code=503, detail="We could not send the verification email. Try again shortly.")
    return {"sent": True}


@router.post("/email/verify", response_model=CoachPublicResponse)
def verify_email_signup(payload: EmailVerificationRequest, response: Response) -> dict[str, Any]:
    claims = _verify_email_token(payload.token)
    email = str(claims.get("email", "")).strip().lower()
    name = str(claims.get("name", "")).strip()
    if not email or not name:
        raise HTTPException(status_code=400, detail="This verification link is invalid. Request a new one.")
    coach = auth_store.register_coach(email, name)
    if coach is None:
        raise HTTPException(status_code=409, detail="An account already exists for this email. Sign in instead.")
    auth_store.accept_policies(email, str(claims["terms_version"]), str(claims["privacy_version"]))
    auth_store.log_event("policies_accepted", coach["team_id"])
    auth_store.delete_sessions_for_coach(email)
    session_token = auth_store.create_session(email)
    auth_store.log_event("coach_signed_in", coach["team_id"])
    response.set_cookie(
        key=SESSION_COOKIE, value=session_token, max_age=SESSION_HOURS * 60 * 60,
        httponly=True, secure=_secure_cookie(), samesite="lax", path="/",
    )
    coach = auth_store.get_session(session_token)
    if coach is None:
        raise HTTPException(status_code=500, detail="Account was created but the session could not be loaded. Sign in.")
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
