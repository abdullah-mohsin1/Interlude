from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.api.generate_ad import generate_lyrics_for_song
from backend.api.generate_voice import generate_voice_clip
from backend.api.mix_audio import mix_song_with_insert
from backend.services.audio_service import GENERATED_DIR, ORIGINALS_DIR
from backend.services.gradium_service import generate_voice
from backend.services.songify_service import songify_tts_to_singing
from backend.utils.ffmpeg import assert_ffmpeg_available

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
    artist: str | None = None
    cover_image: str | None = None
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


class SongifyRequest(BaseModel):
    lyrics: str = Field(..., min_length=3)
    bpm: int = Field(120, ge=40, le=240)
    key: str = Field("C_minor")
    style: str = Field("talk_sing")


class SongifyResponse(BaseModel):
    raw_tts_url: str
    songified_url: str
    meta: Dict[str, Any]


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


@router.post("/songify", response_model=SongifyResponse)
def songify(payload: SongifyRequest) -> SongifyResponse:
    if payload.style not in {"talk_sing", "chant", "rap"}:
        raise HTTPException(status_code=400, detail="style must be talk_sing, chant, or rap")

    assert_ffmpeg_available()
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    lines = [line.strip() for line in payload.lyrics.splitlines() if line.strip()]
    if not lines:
        raise HTTPException(status_code=400, detail="lyrics must contain at least one line")

    try:
        from pydub import AudioSegment
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"pydub import failed: {exc}") from exc

    silence_gap = AudioSegment.silent(duration=120)
    combined = AudioSegment.silent(duration=0)

    for line in lines:
        try:
            wav_path = Path(generate_voice(text=line))
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        clip = AudioSegment.from_wav(wav_path)
        combined = combined + clip + silence_gap

    job_id = uuid.uuid4().hex
    raw_wav_path = GENERATED_DIR / f"{job_id}_raw.wav"
    combined.export(raw_wav_path, format="wav")

    songified_path = GENERATED_DIR / f"{job_id}_songified.wav"
    songify_tts_to_singing(
        input_wav=raw_wav_path,
        lyrics=payload.lyrics,
        bpm=payload.bpm,
        key=payload.key,
        style=payload.style,
        output_wav=songified_path,
    )

    raw_relative = raw_wav_path.relative_to(PUBLIC_DIR).as_posix()
    songified_relative = songified_path.relative_to(PUBLIC_DIR).as_posix()
    return SongifyResponse(
        raw_tts_url=f"/{raw_relative}",
        songified_url=f"/{songified_relative}",
        meta={"bpm": payload.bpm, "key": payload.key, "style": payload.style},
    )
