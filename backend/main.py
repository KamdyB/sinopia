import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

from backend.api.checkins import router as checkins_router
from backend.api.explain import router as explain_router
from backend.api.players import router as players_router
from backend.api.sessions import router as sessions_router
from backend.api.statuses import router as statuses_router

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


app.include_router(sessions_router)
app.include_router(checkins_router)
app.include_router(statuses_router)
app.include_router(explain_router)
app.include_router(players_router)
