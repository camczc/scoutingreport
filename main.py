"""main.py"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.players import router as players_router
from app.api.games import router as games_router
from app.db.session import init_db

app = FastAPI(title="ScoutingReport API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

app.include_router(players_router, prefix="/players", tags=["players"])
app.include_router(games_router, prefix="/games", tags=["games"])

@app.get("/health")
def health():
    return {"status": "ok"}
