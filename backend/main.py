from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.api.routes import load_songs, router
from backend.services.audio_service import ensure_song_assets
from backend.utils.env import load_env

load_env()

ROOT_DIR = Path(__file__).resolve().parents[1]
AUDIO_DIR = ROOT_DIR / "public" / "audio"

app = FastAPI(
    title="Interlude API",
    description="API for generating and inserting in-song ads (MVP stub)",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")


@app.on_event("startup")
def on_startup() -> None:
    ensure_song_assets(load_songs())


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "project": "Interlude"}
