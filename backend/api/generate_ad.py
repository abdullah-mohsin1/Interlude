from __future__ import annotations

from backend.services.llm_service import generate_ad_lyrics


def generate_lyrics_for_song(
    mood: str,
    bpm: int,
    ad_prompt: str,
    max_duration_seconds: float,
) -> str:
    syllable_limit = max(16, int(max_duration_seconds * 4))
    return generate_ad_lyrics(
        mood=mood,
        bpm=bpm,
        ad_prompt=ad_prompt,
        max_duration_seconds=max_duration_seconds,
        syllable_limit=syllable_limit,
    )

