from __future__ import annotations

import os
from pathlib import Path

from backend.services.audio_service import GENERATED_DIR, generate_silence_wav

GRADIUM_API_KEY = os.getenv("GRADIUM_API_KEY", "TEMP_GRADIUM_API_KEY")
VOICE_ID = os.getenv("VOICE_ID", "TEMP_VOICE_ID")


def generate_voice(text: str, energy: str = "high", pace: str = "medium") -> str:
    """
    Calls Gradium TTS API with custom voice_id.
    TEMP IMPLEMENTATION: creates placeholder ad voice WAV and returns its path.
    """
    _ = (GRADIUM_API_KEY, VOICE_ID, energy, pace)
    duration_seconds = min(10, max(6, len(text.split()) // 2))
    output_path = Path(GENERATED_DIR) / "ad_voice.wav"
    generate_silence_wav(output_path, duration_seconds=duration_seconds)
    return str(output_path)

