from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.api.generate_ad import generate_lyrics_for_song
from backend.api.generate_voice import generate_voice_clip
from backend.api.mix_audio import mix_song_with_insert
from backend.services.audio_service import ORIGINALS_DIR

ROOT_DIR = Path(__file__).resolve().parents[2]
SONGS_CONFIG_PATH = ROOT_DIR / "backend" / "config" / "songs.json"
PUBLIC_DIR = ROOT_DIR / "public"

router = APIRouter(prefix="/api", tags=["interlude"])


class InsertWindow(BaseModel):
    start_ms: int
    end_ms: int


class Song(BaseModel):
    song_id: str
    title: str
    file: str
    bpm: int
    mood: str
    insert_window: InsertWindow


class GenerateRequest(BaseModel):
    song_id: str = Field(..., description="Song identifier")
    ad_prompt: str = Field(..., min_length=3, description="What ad to generate")


class GenerateResponse(BaseModel):
    lyrics: str
    audio_url: str


@lru_cache(maxsize=1)
def load_songs() -> List[Dict[str, Any]]:
    with SONGS_CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def _song_index() -> Dict[str, Dict[str, Any]]:
    return {song["song_id"]: song for song in load_songs()}


@router.get("/songs", response_model=List[Song])
def get_songs() -> List[Dict[str, Any]]:
    return load_songs()


@router.post("/generate", response_model=GenerateResponse)
def generate_in_song_ad(payload: GenerateRequest) -> GenerateResponse:
    songs = _song_index()
    song = songs.get(payload.song_id)
    if not song:
        raise HTTPException(status_code=404, detail=f"Unknown song_id: {payload.song_id}")

    start_ms = song["insert_window"]["start_ms"]
    end_ms = song["insert_window"]["end_ms"]
    max_duration_seconds = (end_ms - start_ms) / 1000.0

    lyrics = generate_lyrics_for_song(
        mood=song["mood"],
        bpm=song["bpm"],
        ad_prompt=payload.ad_prompt,
        max_duration_seconds=max_duration_seconds,
    )

    voice_path = generate_voice_clip(lyrics)
    song_path = ORIGINALS_DIR / song["file"]
    mixed_path = mix_song_with_insert(
        song_id=song["song_id"],
        song_path=song_path,
        insert_path=voice_path,
        start_ms=start_ms,
        end_ms=end_ms,
    )

    audio_relative = mixed_path.relative_to(PUBLIC_DIR).as_posix()
    return GenerateResponse(lyrics=lyrics, audio_url=f"/{audio_relative}")

