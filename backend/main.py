import os
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

from backend.api.auth import router as auth_router
from backend.api.checkins import router as checkins_router
from backend.api.explain import router as explain_router
from backend.api.players import router as players_router
from backend.api.privacy import router as privacy_router
from backend.api.sessions import router as sessions_router
from backend.api.statuses import router as statuses_router

# Process-local emergency throttle. Production deployments with multiple workers
# should also enforce limits at the edge/shared store.
_RATE_EVENTS: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_RATE_LOCK = Lock()


def _client_ip(request: Request) -> str:
    if os.environ.get("SINOPIA_TRUST_PROXY", "").lower() == "true":
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded.strip():
            # Only enable this when the app is reachable exclusively through
            # a trusted reverse proxy that overwrites this header.
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _rate_limit(request: Request) -> tuple[int, int] | None:
    path = request.url.path
    if path == "/auth/google" and request.method == "POST":
        return (5, 60)
    if path == "/checkins" and request.method == "POST":
        return (10, 60)
    if path.startswith("/checkin/") and request.method == "GET":
        return (10, 60)
    if path == "/explain" and request.method == "POST":
        return (20, 3600)
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        return (60, 60)
    return None


PRODUCTION = os.environ.get("SINOPIA_ENV", "development").lower() == "production"
app = FastAPI(
    docs_url=None if PRODUCTION else "/docs",
    redoc_url=None if PRODUCTION else "/redoc",
    openapi_url=None if PRODUCTION else "/openapi.json",
)

allowed_origins = [
    origin.strip().rstrip("/")
    for origin in os.environ.get(
        "SINOPIA_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:5174"
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Sinopia-Request"],
    allow_credentials=True,
)


@app.middleware("http")
async def apply_rate_limits(request: Request, call_next):
    rule = _rate_limit(request)
    if rule:
        maximum, window = rule
        now = time.monotonic()
        key = (request.url.path, _client_ip(request))
        with _RATE_LOCK:
            events = _RATE_EVENTS[key]
            while events and events[0] <= now - window:
                events.popleft()
            if len(events) >= maximum:
                retry_after = max(1, int(window - (now - events[0])))
                return Response(
                    "Too many requests.", status_code=429,
                    headers={"Retry-After": str(retry_after)},
                )
            events.append(now)
    return await call_next(request)


@app.middleware("http")
async def protect_state_changes(request: Request, call_next):
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        if request.headers.get("x-sinopia-request") != "1":
            return Response("Request rejected.", status_code=403)
        origin = request.headers.get("origin")
        if PRODUCTION and not origin:
            return Response("Request rejected.", status_code=403)
        if origin and origin.rstrip("/") not in allowed_origins:
            return Response("Request rejected.", status_code=403)
    return await call_next(request)


@app.middleware("http")
async def security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; base-uri 'self'; form-action 'self'; "
        "frame-ancestors 'none'; object-src 'none'; connect-src 'self'; "
        "img-src 'self' data:; script-src 'self'; style-src 'self' 'unsafe-inline'",
    )
    if PRODUCTION:
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
    return response


app.include_router(auth_router)
app.include_router(sessions_router)
app.include_router(checkins_router)
app.include_router(statuses_router)
app.include_router(explain_router)
app.include_router(players_router)
app.include_router(privacy_router)
