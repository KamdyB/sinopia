import logging
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.data.db import create_tables
from backend.api.auth import router as auth_router
from backend.api.checkins import router as checkins_router
from backend.api.explain import router as explain_router
from backend.api.players import router as players_router
from backend.api.sessions import router as sessions_router
from backend.api.statuses import router as statuses_router
from backend.api.team_sessions import router as team_sessions_router

logger = logging.getLogger("sinopia.api")

def configured_cors_origins():
    raw = os.getenv("CORS_ORIGINS")
    if raw:
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return [] if os.getenv("VERCEL") == "1" else ["*"]

CORS_ORIGINS = configured_cors_origins()
app = FastAPI()

@app.on_event("startup")
def startup():
    create_tables()

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled API exception on %s %s (%s)", request.method, request.url.path, type(exc).__name__)
    origin = request.headers.get("origin", "")
    headers = {"Vary": "Origin", "Access-Control-Allow-Credentials": "true"}
    if origin and ("*" in CORS_ORIGINS or origin in CORS_ORIGINS):
        headers["Access-Control-Allow-Origin"] = origin
    elif not origin and "*" in CORS_ORIGINS:
        headers["Access-Control-Allow-Origin"] = "*"
    return JSONResponse(status_code=500, content={"detail":"Something went wrong. Please try again. If the problem continues, contact your coach."}, headers=headers)

app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth_router)
app.include_router(sessions_router)
app.include_router(checkins_router)
app.include_router(statuses_router)
app.include_router(team_sessions_router)
app.include_router(explain_router)
app.include_router(players_router)
