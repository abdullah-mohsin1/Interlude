from __future__ import annotations

import uuid
from pathlib import Path
from typing import Tuple

import requests
import soundfile as sf
import librosa

from backend.services.audio_service import GENERATED_DIR
from backend.utils.ffmpeg import assert_ffmpeg_available
from backend.utils.env import get_env, load_env


DEFAULT_VOICE_ID = "zVI-68f2GRJbOGTT"
DEFAULT_REGION = "us"


def _gradium_endpoint(region: str) -> str:
    region = (region or DEFAULT_REGION).lower()
    if region == "eu":
        return "https://eu.api.gradium.ai/api/post/speech/tts"
    return "https://us.api.gradium.ai/api/post/speech/tts"


def _get_env() -> Tuple[str, str, str]:
    load_env()
    api_key = get_env("GRADIUM_API_KEY", required=True) or ""
    voice_id = (
        get_env("GRADIUM_VOICE_ID")
        or get_env("VOICE_ID", default=DEFAULT_VOICE_ID)
        or DEFAULT_VOICE_ID
    )
    region = get_env("GRADIUM_REGION", default=DEFAULT_REGION) or DEFAULT_REGION
    return api_key, voice_id, region


def _is_wav_bytes(data: bytes) -> bool:
    return len(data) > 12 and data[:4] == b"RIFF" and data[8:12] == b"WAVE"


def _ensure_wav_mono_44k(input_path: Path, output_path: Path) -> Path:
    audio, sr = librosa.load(str(input_path), sr=44100, mono=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), audio, 44100)
    return output_path


def generate_voice(text: str, energy: str = "high", pace: str = "medium") -> str:
    """
    Calls Gradium TTS API with custom voice_id and returns a WAV file path.
    """
    _ = (energy, pace)
    api_key, voice_id, region = _get_env()

    response = requests.post(
        _gradium_endpoint(region),
        headers={"x-api-key": api_key},
        json={"text": text, "voice_id": voice_id},
        timeout=60,
    )
    if response.status_code >= 400:
        raise RuntimeError(
            f"Gradium TTS failed: {response.status_code} - {response.text[:400]}"
        )

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    job_id = uuid.uuid4().hex
    raw_path = GENERATED_DIR / f"{job_id}_raw"
    wav_path = GENERATED_DIR / f"{job_id}.wav"

    data = response.content
    if _is_wav_bytes(data):
        raw_path = raw_path.with_suffix(".wav")
        raw_path.write_bytes(data)
        _ensure_wav_mono_44k(raw_path, wav_path)
        return str(wav_path)

    assert_ffmpeg_available()
    raw_path = raw_path.with_suffix(".bin")
    raw_path.write_bytes(data)
    try:
        from pydub import AudioSegment

        audio = AudioSegment.from_file(raw_path)
        audio = audio.set_channels(1).set_frame_rate(44100)
        audio.export(wav_path, format="wav")
    except Exception as exc:
        raise RuntimeError(f"Failed to convert Gradium audio to WAV: {exc}") from exc
    finally:
        try:
            raw_path.unlink(missing_ok=True)
        except Exception:
            pass

    return str(wav_path)
