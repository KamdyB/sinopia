from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.checkins import router as checkins_router
from backend.api.explain import router as explain_router
from backend.api.players import router as players_router
from backend.api.sessions import router as sessions_router
from backend.api.statuses import router as statuses_router

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(sessions_router)
app.include_router(checkins_router)
app.include_router(statuses_router)
app.include_router(explain_router)
app.include_router(players_router)
