"""Team export and confirmed hard deletion endpoints."""
import csv
import io
import os
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from pydantic import BaseModel, ConfigDict, Field

from backend.api.auth import SESSION_COOKIE, current_coach, require_accepted_coach
from backend.data.checkin_store import checkin_store
from backend.data.db import DB_PATH, connect
from backend.data.player_store import player_store
from backend.data.session_store import session_store

router = APIRouter(prefix="/privacy")


class DeleteAccountRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    credential: str = Field(min_length=20, max_length=8192)
    confirm: bool


def _team_export(team_id: str) -> dict:
    players = []
    for team_type in ("girls", "boys", "mixed"):
        for player in player_store.list_for_team(team_type, team_id):
            players.append({
                "label": player["name"],
                "team_type": player["team_type"],
                "registered_date": player["registered_date"],
                "sessions": session_store.get_sessions(player["player_id"], team_id),
                "checkins": checkin_store.get_checkins(player["player_id"], team_id),
            })
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "players": players,
    }


@router.get("/export")
def export_team(format: str = "json", coach: dict = Depends(require_accepted_coach)):
    if format not in {"json", "csv"}:
        raise HTTPException(status_code=422, detail="Format must be json or csv.")
    data = _team_export(coach["team_id"])
    if format == "json":
        return data

    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow([
        "record_type", "athlete_label", "team_type", "date", "duration_minutes",
        "rpe", "sleep", "energy", "soreness", "stress", "pain", "pain_area",
        "pain_acknowledged",
    ])
    for player in data["players"]:
        for session in player["sessions"]:
            writer.writerow([
                "session", player["label"], player["team_type"], session["date"],
                session["duration_minutes"], session["rpe"], "", "", "", "", "", "", "",
            ])
        for checkin in player["checkins"]:
            writer.writerow([
                "check-in", player["label"], player["team_type"], checkin["date"],
                "", "", checkin["sleep"], checkin["energy"], checkin["soreness"],
                checkin["stress"], checkin["pain"], checkin["pain_area"] or "",
                checkin["pain_acknowledged"],
            ])
    return Response(
        output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="sinopia-team-export.csv"'},
    )


@router.post("/delete-account")
def delete_account(
    payload: DeleteAccountRequest,
    request: Request,
    response: Response,
    coach: dict = Depends(current_coach),
) -> dict[str, bool]:
    if not payload.confirm:
        raise HTTPException(status_code=422, detail="Confirm permanent deletion to continue.")
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=503, detail="Google sign-in is not configured.")
    try:
        claims = id_token.verify_oauth2_token(
            payload.credential, GoogleRequest(), audience=client_id
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Fresh Google sign-in could not be verified.")
    issued_at = claims.get("iat")
    if (
        claims.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}
        or claims.get("aud") != client_id
        or claims.get("email_verified") is not True
        or str(claims.get("email", "")).lower() != coach["email"].lower()
        or not isinstance(issued_at, (int, float))
        or time.time() - issued_at > 300
        or issued_at > time.time() + 30
    ):
        raise HTTPException(status_code=401, detail="Fresh Google sign-in could not be verified.")

    team_id = coach["team_id"]
    email = coach["email"].lower()
    with connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            "DELETE FROM sessions WHERE team_id = ? OR player_id IN "
            "(SELECT player_id FROM players WHERE team_id = ?)",
            (team_id, team_id),
        )
        conn.execute(
            "DELETE FROM checkins WHERE team_id = ? OR player_id IN "
            "(SELECT player_id FROM players WHERE team_id = ?)",
            (team_id, team_id),
        )
        conn.execute("DELETE FROM players WHERE team_id = ?", (team_id,))
        conn.execute("DELETE FROM coach_sessions WHERE coach_email = ?", (email,))
        conn.execute("DELETE FROM teams WHERE team_id = ?", (team_id,))
        conn.execute("DELETE FROM coaches WHERE email = ?", (email,))
    response.delete_cookie(
        key=SESSION_COOKIE,
        path="/",
        httponly=True,
        secure=os.environ.get("SINOPIA_ENV", "development").lower() == "production",
        samesite="lax",
    )
    return {"deleted": True}
