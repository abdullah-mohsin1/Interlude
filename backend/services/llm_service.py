from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT_DIR = Path(__file__).resolve().parents[2]
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
# Primary default is intentionally non-Gemini/Gemma now.
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
MODEL_FALLBACKS = (
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
    "qwen-qwq-32b",
)
LOGGER = logging.getLogger(__name__)
LAST_GROQ_ERROR: str | None = None

TACKY_TERMS = (
    "buy now",
    "limited time",
    "discount",
    "sale",
    "promo code",
    "sponsored",
    "advertisement",
    "act now",
)


def _load_env_value(key: str) -> str | None:
    value = os.getenv(key)
    if value:
        return value

    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        return None

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, raw_value = line.split("=", 1)
        normalized_name = name.strip()
        if normalized_name.startswith("export "):
            normalized_name = normalized_name[len("export ") :].strip()
        if normalized_name != key:
            continue
        parsed = raw_value.strip().strip('"').strip("'")
        return parsed or None
    return None


def _sanitize_prompt(prompt: str) -> str:
    blocked = {"damn", "hell", "shit", "fuck"}
    words: List[str] = []
    for token in prompt.split():
        clean = token.lower().strip(".,!?")
        words.append("[redacted]" if clean in blocked else token)
    return re.sub(r"\s+", " ", " ".join(words)).strip()


def _is_section_header(line: str) -> bool:
    return line.startswith("[") and line.endswith("]")


def _normalize_lyrics_blob(text: str) -> str:
    return text.replace("\\r\\n", "\n").replace("\\n", "\n")


def _context_block(text: str, *, take_last: bool, max_lines: int = 5) -> str:
    lines: List[str] = []
    for raw in _normalize_lyrics_blob(text).splitlines():
        line = raw.strip()
        if not line:
            continue
        if _is_section_header(line):
            continue
        if line.lower().startswith("[context pending]"):
            continue
        lines.append(re.sub(r"\s+", " ", line))

    if not lines:
        return "- (none)"
    sliced = lines[-max_lines:] if take_last else lines[:max_lines]
    return "\n".join(f"- {line}" for line in sliced)


def _target_line_count(max_duration_seconds: float) -> int:
    if max_duration_seconds <= 8:
        return 4
    if max_duration_seconds <= 12:
        return 5
    return 6


def _build_prompt(
    *,
    title: str,
    artist: str | None,
    mood: str,
    bpm: int,
    ad_prompt: str,
    before_lyrics: str,
    after_lyrics: str,
    line_count: int,
) -> str:
    artist_name = artist or "Unknown Artist"
    before_block = _context_block(before_lyrics, take_last=True)
    after_block = _context_block(after_lyrics, take_last=False)
    return (
        f'Write a verse that flows naturally inside "{title}" by {artist_name}.\n'
        f"Style: {mood}. Tempo feel around {bpm} BPM.\n"
        f'Ad idea that must be included clearly: "{ad_prompt}".\n\n'
        "Lyrics right before insertion:\n"
        f"{before_block}\n\n"
        "Lyrics right after insertion:\n"
        f"{after_block}\n\n"
        "Guidance:\n"
        f"- Give me {line_count} lines (4-6 is acceptable if musical).\n"
        "- Prioritize natural flow and emotional continuity.\n"
        "- Keep it creative and human, avoid tacky sales language.\n"
        "- Do not copy exact opening words from the previous line.\n"
        "- Output only lyric lines, nothing else."
    )


def _strip_fences(text: str) -> str:
    output = text.strip()
    if output.startswith("```"):
        output = re.sub(r"^```[a-zA-Z]*\s*", "", output)
        output = re.sub(r"\s*```$", "", output)
    return output.strip()


def _extract_lines(raw_text: str, target_lines: int) -> List[str]:
    text = _strip_fences(raw_text)
    lines: List[str] = []

    # If model returned JSON, try reading "lines"
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict) and isinstance(parsed.get("lines"), list):
            for item in parsed["lines"]:
                line = str(item).strip()
                if line:
                    lines.append(line)
    except json.JSONDecodeError:
        pass

    if not lines:
        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                continue
            line = re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", line)
            line = re.sub(r"\[[^\]]+\]", "", line).strip()
            if line:
                lines.append(line)

    if len(lines) == 1 and ". " in lines[0]:
        split_lines = [part.strip() for part in re.split(r"[.!?]\s+", lines[0]) if part.strip()]
        if len(split_lines) > 1:
            lines = split_lines

    cleaned: List[str] = []
    for line in lines:
        line = re.sub(r"\s+", " ", line).strip()
        if not line:
            continue
        if any(term in line.lower() for term in TACKY_TERMS):
            continue
        if len(re.findall(r"[A-Za-z']+", line)) < 2:
            continue
        cleaned.append(line)

    if len(cleaned) < 2:
        return []
    return cleaned[: max(target_lines, len(cleaned))]


def _call_groq(prompt: str, *, temperature: float, max_tokens: int = 320) -> str | None:
    global LAST_GROQ_ERROR
    api_key = _load_env_value("GROQ_API_KEY") or _load_env_value("API_KEY")
    if not api_key:
        LAST_GROQ_ERROR = "Missing GROQ_API_KEY/API_KEY."
        LOGGER.warning("Groq call skipped: %s", LAST_GROQ_ERROR)
        return None

    preferred = _load_env_value("GROQ_LLM_MODEL")
    candidates = [preferred] if preferred else []
    for model in MODEL_FALLBACKS:
        if model and model not in candidates:
            candidates.append(model)
    if DEFAULT_GROQ_MODEL not in candidates:
        candidates.insert(0, DEFAULT_GROQ_MODEL)

    last_error = "No model candidates available."
    for model in candidates:
        payload = {
            "model": model,
            "temperature": temperature,
            "top_p": 0.95,
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a songwriter. Return only lyrics lines. "
                        "No commentary."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }

        request = Request(
            GROQ_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Interlude/0.1",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=30) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8")
            except Exception:
                detail = str(exc)
            last_error = f"HTTP {exc.code}: {detail}"
            LOGGER.warning("Groq model %s failed: %s", model, last_error)
            # Continue to next model for model-related failures.
            continue
        except URLError as exc:
            last_error = f"Network error: {exc}"
            LOGGER.warning("Groq network error on model %s: %s", model, exc)
            # Network error won't improve by model change; stop loop.
            break
        except TimeoutError:
            last_error = "Request timed out."
            LOGGER.warning("Groq request timed out on model %s.", model)
            continue
        except json.JSONDecodeError:
            last_error = "Could not decode JSON response."
            LOGGER.warning("Groq JSON decode failed on model %s.", model)
            continue

        choices = body.get("choices", [])
        if not choices:
            last_error = "No choices returned by Groq."
            LOGGER.warning("Groq response had no choices on model %s.", model)
            continue

        content = choices[0].get("message", {}).get("content")
        if not isinstance(content, str):
            last_error = "No message content returned by Groq."
            LOGGER.warning("Groq response missing content on model %s.", model)
            continue

        LAST_GROQ_ERROR = None
        LOGGER.info("Groq lyric generation succeeded with model %s.", model)
        return content.strip()

    LAST_GROQ_ERROR = last_error
    return None


def _best_effort_lines(raw_text: str, target_lines: int) -> List[str]:
    text = _strip_fences(raw_text)
    text = re.sub(r"\[[^\]]+\]", "", text)
    chunks: List[str] = []
    for line in text.splitlines():
        candidate = re.sub(r"\s+", " ", line).strip()
        if candidate:
            chunks.append(candidate)

    if len(chunks) <= 1:
        basis = chunks[0] if chunks else text
        # Split long single-paragraph outputs into lyric-like lines.
        parts = [
            part.strip()
            for part in re.split(r"[.!?;]\s+|\s+-\s+|,\s+(?=[A-Z])", basis)
            if part.strip()
        ]
        chunks = parts if parts else ([basis.strip()] if basis.strip() else [])

    cleaned: List[str] = []
    for chunk in chunks:
        item = re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", chunk).strip()
        if len(re.findall(r"[A-Za-z']+", item)) >= 2:
            cleaned.append(item)

    if not cleaned:
        return []
    return cleaned[: max(2, target_lines)]


def generate_ad_lyrics(
    title: str,
    artist: str | None,
    mood: str,
    bpm: int,
    ad_prompt: str,
    max_duration_seconds: float,
    syllable_limit: int,
    lyrics_before: str,
    lyrics_after: str,
) -> str:
    """
    Loosened generation path with no templated fallback:
    - Uses only live LLM outputs
    - If no usable output arrives, returns an explicit failure message
    """
    del syllable_limit  # compatibility with existing caller signature

    safe_prompt = _sanitize_prompt(ad_prompt) or "support your community"
    line_count = _target_line_count(max_duration_seconds)
    prompt = _build_prompt(
        title=title,
        artist=artist,
        mood=mood,
        bpm=bpm,
        ad_prompt=safe_prompt,
        before_lyrics=lyrics_before,
        after_lyrics=lyrics_after,
        line_count=line_count,
    )

    candidates: List[List[str]] = []
    raw_responses: List[str] = []
    for temperature in (1.25, 1.05, 0.85, 0.65):
        raw = _call_groq(prompt, temperature=temperature)
        if not raw:
            continue
        raw_responses.append(raw)
        lines = _extract_lines(raw, target_lines=line_count)
        if lines:
            candidates.append(lines)

    if candidates:
        # Prefer richer candidates with more distinct words and enough lines.
        def score(lines: List[str]) -> float:
            joined = " ".join(lines).lower()
            words = re.findall(r"[A-Za-z']+", joined)
            diversity = (len(set(words)) / len(words)) if words else 0
            return len(lines) * 4 + diversity * 20

        best = max(candidates, key=score)
        return "\n".join(best)

    if raw_responses:
        salvage = _best_effort_lines(max(raw_responses, key=len), line_count)
        if salvage:
            return "\n".join(salvage)

    if LAST_GROQ_ERROR:
        return f"Unable to generate lyrics right now. {LAST_GROQ_ERROR}"
    return "Unable to generate lyrics right now. Please try again."
