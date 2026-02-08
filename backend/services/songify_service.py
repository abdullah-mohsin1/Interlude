from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import librosa
import numpy as np
import soundfile as sf


def _parse_key(key: str) -> Tuple[str, str]:
    if "_" in key:
        tonic, mode = key.split("_", 1)
    else:
        tonic, mode = key, "major"
    return tonic.capitalize(), mode.lower()


def _scale_semitones(tonic: str, mode: str) -> List[int]:
    major = [0, 2, 4, 5, 7, 9, 11]
    minor = [0, 2, 3, 5, 7, 8, 10]
    return major if mode == "major" else minor


def _note_to_midi(tonic: str) -> int:
    note_map = {
        "C": 60,
        "C#": 61,
        "Db": 61,
        "D": 62,
        "D#": 63,
        "Eb": 63,
        "E": 64,
        "F": 65,
        "F#": 66,
        "Gb": 66,
        "G": 67,
        "G#": 68,
        "Ab": 68,
        "A": 69,
        "A#": 70,
        "Bb": 70,
        "B": 71,
    }
    return note_map.get(tonic, 60)


def _build_melody(lyrics: str, key: str) -> List[int]:
    tonic, mode = _parse_key(key)
    scale = _scale_semitones(tonic, mode)
    base = _note_to_midi(tonic)

    lines = [line for line in lyrics.splitlines() if line.strip()]
    melody: List[int] = []
    motif = [0, 2, 4, 6]

    for idx, line in enumerate(lines):
        words = [w for w in line.split() if w.strip()]
        if not words:
            continue
        for w_idx, _ in enumerate(words):
            step = motif[(w_idx + idx) % len(motif)]
            degree = scale[step % len(scale)]
            melody.append(base + degree)
    return melody


def _segment_boundaries(lyrics: str, total_samples: int) -> List[Tuple[int, int]]:
    lines = [line for line in lyrics.splitlines() if line.strip()]
    words: List[str] = []
    for line in lines:
        words.extend([w for w in line.split() if w.strip()])

    if not words:
        return [(0, total_samples)]

    lengths = np.array([max(1, len(w)) for w in words], dtype=np.float32)
    lengths = lengths / lengths.sum()
    segments: List[Tuple[int, int]] = []
    cursor = 0
    for frac in lengths:
        seg_len = int(total_samples * float(frac))
        start = cursor
        end = min(total_samples, start + max(1, seg_len))
        segments.append((start, end))
        cursor = end
    if segments:
        segments[-1] = (segments[-1][0], total_samples)
    return segments


def _estimate_f0(segment: np.ndarray, sr: int) -> float | None:
    try:
        f0 = librosa.yin(segment, fmin=80, fmax=400, sr=sr)
        f0 = f0[np.isfinite(f0)]
        f0 = f0[f0 > 0]
        if f0.size == 0:
            return None
        return float(np.median(f0))
    except Exception:
        return None


def _pitch_shift_segment(segment: np.ndarray, sr: int, target_midi: int) -> np.ndarray:
    f0 = _estimate_f0(segment, sr)
    if not f0:
        return segment
    target_freq = librosa.midi_to_hz(target_midi)
    n_steps = 12 * np.log2(target_freq / f0)
    return librosa.effects.pitch_shift(segment, sr=sr, n_steps=n_steps)


def _crossfade(a: np.ndarray, b: np.ndarray, fade_samples: int) -> np.ndarray:
    if fade_samples <= 0:
        return np.concatenate([a, b])
    fade = np.linspace(0, 1, fade_samples)
    head = a[:-fade_samples]
    cross = a[-fade_samples:] * (1 - fade) + b[:fade_samples] * fade
    tail = b[fade_samples:]
    return np.concatenate([head, cross, tail])


def songify_tts_to_singing(
    input_wav: Path,
    lyrics: str,
    bpm: int,
    key: str,
    style: str,
    output_wav: Path,
) -> Path:
    _ = bpm
    audio, sr = librosa.load(str(input_wav), sr=44100, mono=True)
    if audio.size == 0:
        output_wav.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(output_wav), audio, 44100)
        return output_wav

    segments = _segment_boundaries(lyrics, len(audio))
    melody = _build_melody(lyrics, key)
    if len(melody) < len(segments):
        melody.extend([melody[-1]] * (len(segments) - len(melody)))

    processed: List[np.ndarray] = []
    for idx, (start, end) in enumerate(segments):
        seg = audio[start:end]
        if seg.size == 0:
            continue
        target_note = melody[idx % len(melody)] if melody else 60
        shifted = _pitch_shift_segment(seg, sr, target_note)
        processed.append(shifted)

    if not processed:
        output_wav.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(output_wav), audio, 44100)
        return output_wav

    fade_samples = int(0.01 * sr)
    combined = processed[0]
    for seg in processed[1:]:
        combined = _crossfade(combined, seg, fade_samples)

    peak = np.max(np.abs(combined)) if combined.size else 1.0
    if peak > 0:
        combined = combined / peak * 0.9

    if style in {"chant", "rap"}:
        delay = int(0.02 * sr)
        doubled = np.pad(combined, (delay, 0), mode="constant")[: combined.shape[0]]
        if style == "rap":
            doubled = librosa.effects.pitch_shift(doubled, sr=sr, n_steps=0.1)
        combined = combined * 0.9 + doubled * 0.2

    output_wav.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_wav), combined, sr)
    return output_wav

