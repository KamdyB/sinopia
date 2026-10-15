import logging
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.data.db import create_tables
from backend.api.checkins import router as checkins_router
from backend.api.explain import router as explain_router
from backend.api.players import router as players_router
from backend.api.sessions import router as sessions_router
from backend.api.statuses import router as statuses_router

logger = logging.getLogger("sinopia.api")
app = FastAPI()

@app.on_event("startup")
def startup():
    create_tables()

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled API exception on %s %s (%s)", request.method, request.url.path, type(exc).__name__)
    origin = request.headers.get("origin", "")
    allowed = os.getenv("CORS_ORIGINS", "*").split(",")
    headers = {"Access-Control-Allow-Origin": origin if origin and ("*" in allowed or origin in allowed) else (allowed[0] if allowed else "*"), "Vary": "Origin", "Access-Control-Allow-Credentials": "true"}
    return JSONResponse(status_code=500, content={"detail":"Something went wrong. Please try again. If the problem continues, contact your coach."}, headers=headers)

app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS","*").split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(sessions_router)
app.include_router(checkins_router)
app.include_router(statuses_router)
app.include_router(explain_router)
app.include_router(players_router)
