from __future__ import annotations

from typing import List


def _sanitize_prompt(prompt: str) -> str:
    blocked = {"damn", "hell", "shit", "fuck"}
    words: List[str] = []
    for token in prompt.split():
        clean = token.lower().strip(".,!?")
        words.append("[redacted]" if clean in blocked else token)
    return " ".join(words).strip()


def generate_ad_lyrics(
    mood: str,
    bpm: int,
    ad_prompt: str,
    max_duration_seconds: float,
    syllable_limit: int,
) -> str:
    """
    Temporary LLM stub.
    Generates 2-4 short rhythmic lines constrained by rough syllable budget.
    """
    safe_prompt = _sanitize_prompt(ad_prompt) or "support your community event"

    lines = [
        f"Ride this {mood} wave, keep it moving,",
        f"{safe_prompt}, right on cue.",
        f"{bpm} on the pulse, step in and feel it,",
        "Interlude drops the message true.",
    ]

    approx_syllables = 0
    selected: List[str] = []
    for line in lines:
        line_syllables = max(1, len(line.split()))
        if approx_syllables + line_syllables > syllable_limit and len(selected) >= 2:
            break
        selected.append(line)
        approx_syllables += line_syllables

    if len(selected) < 2:
        selected = lines[:2]

    if max_duration_seconds <= 7 and len(selected) > 3:
        selected = selected[:3]

    return "\n".join(selected)

