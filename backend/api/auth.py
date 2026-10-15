"""Google sign-in and coach/team session endpoints."""
import os
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from pydantic import BaseModel, Field, model_validator
from backend.data.account_store import account_store

router = APIRouter()
SESSION_COOKIE = "sinopia_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7

def _serializer():
    secret = os.getenv("SESSION_SECRET")
    if not secret:
        if os.getenv("VERCEL") == "1":
            raise RuntimeError("SESSION_SECRET must be configured in production.")
        secret = "local-development-only-change-me"
    return URLSafeTimedSerializer(secret, salt="sinopia-session-v1")

class GoogleLoginRequest(BaseModel):
    credential: str = Field(min_length=20)
    intent: Literal["sign-in", "sign-up"]
    adult_confirmed: bool = False
    authorized: bool = False

    @model_validator(mode="after")
    def _declarations_for_signup(self):
        if self.intent == "sign-up" and not (self.adult_confirmed and self.authorized):
            raise ValueError("Confirm that you are at least 18 and authorized to manage this team's data.")
        return self

class TeamRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    team_type: Literal["girls", "boys", "mixed"]
    accepted_terms: bool = False

    @model_validator(mode="after")
    def _terms_required(self):
        if not self.accepted_terms:
            raise ValueError("Accept the terms before creating a team.")
        return self

def get_current_coach(request: Request) -> dict:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Your session has expired. Sign in again.")
    try:
        payload = _serializer().loads(token, max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        raise HTTPException(status_code=401, detail="Your session has expired. Sign in again.")
    coach = account_store.get_coach(str(payload.get("sub", "")))
    if not coach:
        raise HTTPException(status_code=401, detail="Your session has expired. Sign in again.")
    return coach

def get_current_team(coach: dict = Depends(get_current_coach)) -> dict:
    team = account_store.get_team(coach["google_sub"])
    if not team:
        raise HTTPException(status_code=409, detail="Complete team setup to continue.")
    return team

@router.post("/auth/google")
def google_sign_in(req: GoogleLoginRequest, response: Response):
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=503, detail="Google sign-in is not configured yet.")
    try:
        claims = id_token.verify_oauth2_token(req.credential, GoogleRequest(), audience=client_id)
    except Exception:
        raise HTTPException(status_code=401, detail="Google could not verify this sign-in. Try again.")
    if not claims.get("email_verified") or not claims.get("sub") or not claims.get("email"):
        raise HTTPException(status_code=401, detail="Use a verified Google account to continue.")
    coach_id = str(claims["sub"])
    existing = account_store.get_coach(coach_id)
    if req.intent == "sign-in" and not existing:
        raise HTTPException(status_code=404, detail="No Sinopia account exists for this Google account. Choose Get started.")
    if req.intent == "sign-up":
        account_store.upsert_coach(coach_id, str(claims["email"]), str(claims.get("name") or claims["email"]))
    elif existing:
        account_store.upsert_coach(coach_id, str(claims["email"]), str(claims.get("name") or claims["email"]))
    signed = _serializer().dumps({"sub": coach_id})
    response.set_cookie(
        key=SESSION_COOKIE, value=signed, max_age=SESSION_MAX_AGE, httponly=True,
        secure=os.getenv("SESSION_COOKIE_SECURE", "true" if os.getenv("VERCEL") == "1" else "false").lower() == "true",
        samesite="lax", path="/",
    )
    return {"coach": account_store.get_coach(coach_id), "team": account_store.get_team(coach_id)}

@router.get("/auth/me")
def who_am_i(coach: dict = Depends(get_current_coach)):
    return {"coach": coach, "team": account_store.get_team(coach["google_sub"])}

@router.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, samesite="lax",
                           secure=os.getenv("SESSION_COOKIE_SECURE", "true" if os.getenv("VERCEL") == "1" else "false").lower() == "true")
    return {"ok": True}

@router.get("/teams/current")
def current_team(team: dict = Depends(get_current_team)):
    return team

@router.post("/teams", status_code=201)
def create_team(req: TeamRequest, coach: dict = Depends(get_current_coach)):
    try:
        team = account_store.create_team(coach["google_sub"], " ".join(req.name.split()), req.team_type)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return team
