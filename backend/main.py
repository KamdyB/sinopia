"""FastAPI application, request protections, and router registration."""
import os
import hmac
import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response
from fastapi.responses import JSONResponse

from backend.api.auth import router as auth_router
from backend.api.checkins import router as checkins_router
from backend.api.explain import router as explain_router
from backend.api.players import router as players_router
from backend.api.privacy import router as privacy_router
from backend.api.retention import router as retention_router
from backend.api.sessions import router as sessions_router
from backend.api.statuses import router as statuses_router
from backend.api.team_sessions import router as team_sessions_router
from backend.data.auth_store import auth_store
from backend.data.db import connect
from backend.security.rate_limit import client_ip, enforce_rate_limit
from backend.security.encryption import validate_encryption_config

# Fail closed: deployments must explicitly opt into development mode.
PRODUCTION = os.environ.get("SINOPIA_ENV", "production").lower() == "production"
origins_setting = os.environ.get("SINOPIA_ALLOWED_ORIGINS", "")
if PRODUCTION and not origins_setting.strip():
    raise RuntimeError(
        "SINOPIA_ALLOWED_ORIGINS must contain exact trusted HTTPS origins in production."
    )
allowed_origins = [
    origin.strip().rstrip("/")
    for origin in (
        origins_setting
        if origins_setting.strip()
        else "http://localhost:5173,http://localhost:5174"
    ).split(",")
    if origin.strip()
]
if PRODUCTION and any(not origin.startswith("https://") for origin in allowed_origins):
    raise RuntimeError("Production allowed origins must use HTTPS.")
if PRODUCTION:
    if not os.environ.get("DATABASE_URL", "").strip():
        raise RuntimeError("DATABASE_URL is required in production; SQLite is local-development only.")
    if not os.environ.get("GOOGLE_CLIENT_ID", "").strip():
        raise RuntimeError("GOOGLE_CLIENT_ID is required in production.")
    if len(os.environ.get("SINOPIA_PROXY_SECRET", "")) < 32:
        raise RuntimeError("SINOPIA_PROXY_SECRET must be at least 32 characters in production.")
    validate_encryption_config()

app = FastAPI(
    docs_url=None if PRODUCTION else "/docs",
    redoc_url=None if PRODUCTION else "/redoc",
    openapi_url=None if PRODUCTION else "/openapi.json",
)
@app.get("/health", include_in_schema=False)
def health_check() -> dict[str, str]:
    """Public process liveness endpoint; contains no deployment details."""
    return {"status": "ok"}


@app.get("/ready", include_in_schema=False)
def readiness_check():
    """Public readiness endpoint: confirms the configured database accepts a query."""
    try:
        with connect() as conn:
            conn.execute("SELECT 1").fetchone()
    except Exception:
        logging.getLogger("sinopia.api").warning("Readiness check failed: database unavailable")
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return {"status": "ready"}


logger = logging.getLogger("sinopia.api")

@app.exception_handler(Exception)
async def safe_unhandled_exception(request: Request, exc: Exception):
    # Never log request bodies, athlete labels, or exception text that may contain them.
    stack = "".join(traceback.format_tb(exc.__traceback__))
    logger.error("Unhandled API exception method=%s path=%s type=%s stack=%s",
                 request.method, request.url.path, type(exc).__name__, stack)
    headers = {"Vary": "Origin", "Access-Control-Allow-Credentials": "true"}
    origin = request.headers.get("origin", "")
    if origin and origin.rstrip("/") in allowed_origins:
        headers["Access-Control-Allow-Origin"] = origin
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again."},
        headers=headers,
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Sinopia-Request"],
    allow_credentials=True,
)


def _rate_limit(request: Request) -> tuple[int, int] | None:
    path = request.url.path
    if path in {"/auth/google", "/auth/email/request"} and request.method == "POST":
        return (5, 60)
    if path == "/auth/email/verify" and request.method == "POST":
        return (10, 60)
    if path == "/checkins" and request.method == "POST":
        return (10, 60)
    if path == "/checkin/validate" and request.method == "POST":
        return (10, 60)
    if path == "/privacy/delete-account" and request.method == "POST":
        return (3, 900)
    if path == "/explain" and request.method == "POST":
        return (20, 3600)
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        return (60, 60)
    return None


@app.middleware("http")
async def apply_rate_limits(request: Request, call_next):
    rule = _rate_limit(request)
    if rule:
        maximum, window = rule
        identity = client_ip(request)
        if request.url.path == "/explain":
            token = request.cookies.get("sinopia_session")
            coach = auth_store.get_session(token) if token else None
            if coach is not None:
                identity = "coach:" + coach["email"].lower()
            elif os.environ.get("SINOPIA_ENV", "production").lower() != "production":
                identity = "coach:dev@localhost"
        retry_after = enforce_rate_limit((request.url.path, identity), maximum, window)
        if retry_after is not None:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests."},
                headers={"Retry-After": str(retry_after)},
            )
    return await call_next(request)


@app.middleware("http")
async def require_trusted_proxy(request: Request, call_next):
    # Liveness/readiness probes are intentionally public and disclose no secrets.
    if request.url.path in {"/health", "/ready", "/internal/retention/purge"}:
        return await call_next(request)
    if PRODUCTION:
        configured = os.environ.get("SINOPIA_PROXY_SECRET", "")
        supplied = request.headers.get("x-sinopia-proxy-secret", "")
        if not configured or not supplied or not hmac.compare_digest(configured, supplied):
            return JSONResponse({"detail": "Request rejected."}, status_code=403)
    return await call_next(request)


@app.middleware("http")
async def protect_state_changes(request: Request, call_next):
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        if request.headers.get("x-sinopia-request") != "1":
            return JSONResponse({"detail": "Request rejected."}, status_code=403)
        origin = request.headers.get("origin")
        if PRODUCTION and not origin:
            return JSONResponse({"detail": "Request rejected."}, status_code=403)
        if origin and origin.rstrip("/") not in allowed_origins:
            return JSONResponse({"detail": "Request rejected."}, status_code=403)
    return await call_next(request)


@app.middleware("http")
async def security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault(
        "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
    )
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; "
        "form-action 'none'; object-src 'none'",
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
app.include_router(team_sessions_router)
app.include_router(explain_router)
app.include_router(players_router)
app.include_router(privacy_router)
app.include_router(retention_router)
