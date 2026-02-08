from __future__ import annotations

import json
import logging
import traceback
import uuid
import os
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.api.generate_ad import generate_lyrics_for_song
from backend.api.generate_voice import generate_voice_clip
from backend.api.mix_audio import mix_song_with_insert
from backend.services.audio_service import GENERATED_DIR, ORIGINALS_DIR
from backend.services.gradium_service import generate_voice
from backend.services.songify_service import songify_tts_to_singing
from backend.utils.doctor import run_doctor
from backend.utils.env import get_env, load_env
from backend.utils.ffmpeg import assert_ffmpeg_available
from backend.utils.paths import env_path

ROOT_DIR = Path(__file__).resolve().parents[2]
SONGS_CONFIG_PATH = ROOT_DIR / "backend" / "config" / "songs.json"
PUBLIC_DIR = ROOT_DIR / "public"

router = APIRouter(prefix="/api", tags=["interlude"])
logger = logging.getLogger("interlude.api")


class DoctorError(RuntimeError):
    def __init__(self, message: str, report: dict):
        super().__init__(message)
        self.report = report


class InsertWindow(BaseModel):
    start_ms: int
    end_ms: int


class AdContext(BaseModel):
    before_lyrics: str
    after_lyrics: str


class Song(BaseModel):
    song_id: str
    title: str
    artist: str | None = None
    cover_image: str | None = None
    file: str
    bpm: int
    mood: str
    insert_window: InsertWindow
    ad_context: AdContext


class GenerateRequest(BaseModel):
    song_id: str = Field(..., description="Song identifier")
    ad_prompt: str = Field(..., min_length=3, description="What ad to generate")


class GenerateResponse(BaseModel):
    lyrics: str
    audio_url: str | None = None
    audio_error: str | None = None


class SongifyRequest(BaseModel):
    lyrics: str = Field(..., min_length=3)
    bpm: int = Field(120, ge=40, le=240)
    key: str = Field("C_minor")
    style: str = Field("talk_sing")


class SongifyResponse(BaseModel):
    raw_tts_url: str
    songified_url: str
    meta: Dict[str, Any]


def _next_steps_from_report(report: dict) -> List[str]:
    steps: List[str] = []
    load_env()
    python_deps = report.get("python_deps", {})
    if isinstance(python_deps, dict) and not all(python_deps.values()):
        steps.append("Install Python deps: python -m pip install -r backend/requirements.txt")
    if report.get("ffmpeg") is False:
        steps.append("Install ffmpeg: brew install ffmpeg (macOS)")
        steps.append("Install ffmpeg: sudo apt-get update && sudo apt-get install -y ffmpeg (Ubuntu/Debian)")
    try:
        get_env("GRADIUM_API_KEY", required=True)
    except RuntimeError:
        steps.append(
            f"Set GRADIUM_API_KEY in {env_path().resolve()} or in your deployment environment."
        )
    return steps


def _panic_safe(handler):
    def wrapper(*args, **kwargs):
        try:
            return handler(*args, **kwargs)
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        except DoctorError as exc:
            logger.exception("DoctorError during request")
            report = exc.report
            return JSONResponse(
                status_code=500,
                content={
                    "error": str(exc),
                    "detail": repr(exc),
                    "traceback": traceback.format_exc(),
                    "doctor": report,
                    "next_steps": _next_steps_from_report(report),
                },
            )
        except Exception as exc:
            logger.exception("Unhandled error during request")
            report = run_doctor(auto_fix=False)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal error while processing /api/songify",
                    "detail": repr(exc),
                    "traceback": traceback.format_exc(),
                    "doctor": report,
                    "next_steps": _next_steps_from_report(report),
                },
            )

    return wrapper


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
        title=song["title"],
        artist=song.get("artist"),
        mood=song["mood"],
        bpm=song["bpm"],
        ad_prompt=payload.ad_prompt,
        max_duration_seconds=max_duration_seconds,
        lyrics_before=song["ad_context"]["before_lyrics"],
        lyrics_after=song["ad_context"]["after_lyrics"],
    )

    audio_enabled = os.getenv("ENABLE_AUDIO_GENERATION", "true").strip().lower() == "true"
    if not audio_enabled:
        return GenerateResponse(
            lyrics=lyrics,
            audio_url=None,
            audio_error="Audio generation is disabled. Set ENABLE_AUDIO_GENERATION=true.",
        )

    try:
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
        return GenerateResponse(lyrics=lyrics, audio_url=f"/{audio_relative}", audio_error=None)
    except Exception as exc:
        logger.exception("Audio generation failed for song_id=%s", song["song_id"])
        return GenerateResponse(
            lyrics=lyrics,
            audio_url=None,
            audio_error=f"Unable to generate audio. {exc}",
        )


@router.post("/songify", response_model=SongifyResponse)
@_panic_safe
def songify(payload: SongifyRequest) -> SongifyResponse:
    load_env()
    if payload.style not in {"talk_sing", "chant", "rap"}:
        raise HTTPException(status_code=400, detail="style must be talk_sing, chant, or rap")

    logger.info("songify: doctor start")
    doctor_report = run_doctor(auto_fix=True)
    if not doctor_report.get("ok"):
        raise DoctorError("Dependency check failed. See doctor report.", doctor_report)
    logger.info("songify: doctor ok")

    assert_ffmpeg_available()
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    lines = [line.strip() for line in payload.lyrics.splitlines() if line.strip()]
    if not lines:
        raise HTTPException(status_code=400, detail="lyrics must contain at least one line")

    try:
        from pydub import AudioSegment
    except Exception as exc:
        raise RuntimeError(f"pydub import failed: {exc}") from exc

    silence_gap = AudioSegment.silent(duration=120)
    combined = AudioSegment.silent(duration=0)

    for line in lines:
        logger.info("songify: TTS line length=%s", len(line))
        wav_path = Path(generate_voice(text=line))
        clip = AudioSegment.from_wav(wav_path)
        combined = combined + clip + silence_gap

    job_id = uuid.uuid4().hex
    raw_wav_path = GENERATED_DIR / f"{job_id}_raw.wav"
    logger.info("songify: export raw wav=%s", raw_wav_path)
    combined.export(raw_wav_path, format="wav")

    songified_path = GENERATED_DIR / f"{job_id}_songified.wav"
    logger.info("songify: songify start")
    songify_tts_to_singing(
        input_wav=raw_wav_path,
        lyrics=payload.lyrics,
        bpm=payload.bpm,
        key=payload.key,
        style=payload.style,
        output_wav=songified_path,
    )
    logger.info("songify: songify done -> %s", songified_path)

    raw_relative = raw_wav_path.relative_to(PUBLIC_DIR).as_posix()
    songified_relative = songified_path.relative_to(PUBLIC_DIR).as_posix()
    return SongifyResponse(
        raw_tts_url=f"/{raw_relative}",
        songified_url=f"/{songified_relative}",
        meta={"bpm": payload.bpm, "key": payload.key, "style": payload.style},
    )


@router.get("/health/doctor")
def health_doctor() -> Dict[str, Any]:
    load_env()
    report = run_doctor(auto_fix=False)
    env_report = {
        "GRADIUM_API_KEY": bool(get_env("GRADIUM_API_KEY")),
        "GRADIUM_VOICE_ID": bool(get_env("GRADIUM_VOICE_ID") or get_env("VOICE_ID")),
        "GRADIUM_REGION": bool(get_env("GRADIUM_REGION")),
    }
    return {"python_deps": report.get("python_deps"), "ffmpeg": report.get("ffmpeg"), "env": env_report}
    audio_enabled = os.getenv("ENABLE_AUDIO_GENERATION", "false").lower() == "true"
    if not audio_enabled:
        return GenerateResponse(
            lyrics=lyrics,
            audio_url=None,
            audio_error="Unable to generate audio.",
        )

    try:
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
        return GenerateResponse(lyrics=lyrics, audio_url=f"/{audio_relative}", audio_error=None)
    except Exception:
        return GenerateResponse(
            lyrics=lyrics,
            audio_url=None,
            audio_error="Unable to generate audio.",
        )
