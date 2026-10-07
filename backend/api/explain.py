"""Turns an already-computed status into one plain-language sentence.

The LLM never calculates or changes a level and never receives an
athlete name. When no key is configured or the provider fails, a
deterministic template produces the wording instead.
"""
import os

from fastapi import APIRouter
from openai import OpenAI
from pydantic import BaseModel

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
    player_id: str
    level: str
    reasons: list[str]


class ExplainResponse(BaseModel):
    player_id: str
    summary: str


def template_summary(level: str, reasons: list[str]) -> str:
    """Deterministic wording, used whenever the LLM is unavailable."""
    first = reasons[0] if reasons else "No flags raised from the current rules."
    return f"Status is {level}. {first}"


@router.post("/explain", response_model=ExplainResponse)
def explain(req: ExplainRequest) -> ExplainResponse:
    # The athlete name is never sent to the provider; only the level and
    # the rule reasons leave this process.
    prompt = (
        "Rephrase the following athlete workload status as one short, "
        "plain-language sentence a youth sports coach can read at a glance. "
        "Do not change the level given, and do not add medical claims "
        "beyond what is stated.\n\n"
        f"Level: {req.level}\n"
        f"Reasons: {' '.join(req.reasons)}"
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
            summary = response.choices[0].message.content.strip()
        except Exception:
            summary = None
    return ExplainResponse(
        player_id=req.player_id,
        summary=summary if summary else template_summary(req.level, req.reasons),
    )
