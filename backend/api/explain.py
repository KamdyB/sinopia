"""Produce a plain-language summary from a server-computed status."""
import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from openai import OpenAI

from backend.api.auth import require_accepted_coach
from backend.data.checkin_store import checkin_store
from backend.data.player_store import player_store
from backend.data.session_store import session_store
from backend.timeutil import service_date
from backend.scoring.athlete_status import status_from_records

router = APIRouter()
_client: OpenAI | None = None


def _get_client() -> OpenAI | None:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return None
        _client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)
    return _client


class ExplainRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    player_id: str = Field(min_length=1, max_length=80)


class ExplainResponse(BaseModel):
    player_id: str
    summary: str


def template_summary(level: str, reasons: list[str]) -> str:
    first = reasons[0] if reasons else "No flags raised from the current rules."
    return f"Status is {level}. {first}"


@router.post("/explain", response_model=ExplainResponse)
def explain(req: ExplainRequest, coach: dict = Depends(require_accepted_coach)) -> ExplainResponse:
    player = player_store.get(req.player_id, coach["team_id"])
    if player is None:
        raise HTTPException(status_code=404, detail="Athlete not found.")

    status = status_from_records(
        session_store.get_sessions(req.player_id, coach["team_id"]),
        checkin_store.get_checkins(req.player_id, coach["team_id"]),
        service_date(),
    )
    level = status["level"]
    reasons = status["reasons"]
    # Only server-computed generic status information is sent to the provider.
    prompt = (
        "Rephrase this youth sports workload status as one short, plain-language "
        "sentence for a coach. Do not change the level or add medical claims.\n"
        f"Level: {level}\nReasons: {' '.join(reasons)}"
    )
    summary: str | None = None
    client = _get_client()
    if client is not None:
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                max_tokens=120,
                messages=[{"role": "user", "content": prompt}],
            )
            summary = response.choices[0].message.content
            if summary:
                summary = summary.strip()
        except Exception:
            summary = None
    return ExplainResponse(
        player_id=req.player_id,
        summary=summary if summary else template_summary(level, reasons),
    )
