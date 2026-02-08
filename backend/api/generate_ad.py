from __future__ import annotations

from backend.services.llm_service import generate_ad_lyrics


def generate_lyrics_for_song(
    title: str,
    artist: str | None,
    mood: str,
    bpm: int,
    ad_prompt: str,
    max_duration_seconds: float,
    lyrics_before: str,
    lyrics_after: str,
) -> str:
    syllable_limit = max(16, int(max_duration_seconds * 4))
    return generate_ad_lyrics(
        title=title,
        artist=artist,
        mood=mood,
        bpm=bpm,
        ad_prompt=ad_prompt,
        max_duration_seconds=max_duration_seconds,
        syllable_limit=syllable_limit,
        lyrics_before=lyrics_before,
        lyrics_after=lyrics_after,
    )
