from __future__ import annotations

from pathlib import Path

from backend.services.gradium_service import generate_voice


def generate_voice_clip(lyrics: str) -> Path:
    return Path(generate_voice(text=lyrics, energy="high", pace="medium"))

