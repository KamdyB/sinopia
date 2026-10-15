"""Fail-closed server-side Cloudflare Turnstile verification."""
import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import HTTPException

VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def require_turnstile(token: str | None, expected_action: str) -> None:
    if os.environ.get("SINOPIA_ENV", "production").lower() != "production":
        return
    secret = os.environ.get("TURNSTILE_SECRET_KEY", "").strip()
    hostnames = {
        item.strip().lower()
        for item in os.environ.get("SINOPIA_TURNSTILE_HOSTNAMES", "").split(",")
        if item.strip()
    }
    if not secret or not hostnames:
        raise HTTPException(status_code=503, detail="Bot protection is not configured.")
    if not token or len(token) > 2048:
        raise HTTPException(status_code=403, detail="Complete the bot-protection check.")
    request = Request(
        VERIFY_URL,
        data=urlencode({"secret": secret, "response": token}).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=5) as response:
            result = json.loads(response.read(16384))
    except Exception:
        raise HTTPException(status_code=503, detail="Bot protection could not be verified. Try again.")
    if (
        result.get("success") is not True
        or str(result.get("hostname", "")).lower() not in hostnames
        or result.get("action") != expected_action
    ):
        raise HTTPException(status_code=403, detail="Bot-protection verification failed.")
