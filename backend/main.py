from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import demo as demo_router
from backend.api.checkins import router as checkins_router
from backend.api.explain import router as explain_router
from backend.api.players import router as players_router
from backend.api.sessions import router as sessions_router
from backend.api.statuses import router as statuses_router
from backend.api.teams import router as teams_router
import os

app = FastAPI(title="Sinopia")

# Browsers on the Vercel frontend call this API cross-origin in
# deployment. Lock it down to the configured origins when set.
_origins = os.environ.get("SINOPIA_ALLOWED_ORIGINS", "*")
_origins = [origin.strip() for origin in _origins.split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=_origins or ["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(teams_router)
app.include_router(demo_router.router)
app.include_router(sessions_router)
app.include_router(checkins_router)
app.include_router(statuses_router)
app.include_router(explain_router)
app.include_router(players_router)
