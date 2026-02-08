from __future__ import annotations

import shutil
import wave
from pathlib import Path
from typing import Iterable

ROOT_DIR = Path(__file__).resolve().parents[2]
PUBLIC_AUDIO_DIR = ROOT_DIR / "public" / "audio"
ORIGINALS_DIR = PUBLIC_AUDIO_DIR / "originals"
GENERATED_DIR = PUBLIC_AUDIO_DIR / "generated"


def generate_silence_wav(path: Path, duration_seconds: int, sample_rate: int = 16000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame_count = duration_seconds * sample_rate
    chunk_frames = sample_rate
    silence_chunk = (0).to_bytes(2, byteorder="little", signed=True) * chunk_frames

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        written = 0
        while written < frame_count:
            remaining = frame_count - written
            if remaining < chunk_frames:
                wav_file.writeframes(
                    (0).to_bytes(2, byteorder="little", signed=True) * remaining
                )
                written += remaining
            else:
                wav_file.writeframes(silence_chunk)
                written += chunk_frames


def ensure_song_assets(songs: Iterable[dict]) -> None:
    ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    for song in songs:
        original_path = ORIGINALS_DIR / song["file"]
        if original_path.exists():
            continue
        if original_path.suffix.lower() != ".wav":
            continue
        insert_end_seconds = int(song["insert_window"]["end_ms"] / 1000)
        generate_silence_wav(original_path, duration_seconds=max(20, insert_end_seconds + 5))


def mix_audio(
    song_path: Path,
    insert_path: Path,
    start_ms: int,
    end_ms: int,
    output_path: Path,
) -> Path:
    """
    TEMP IMPLEMENTATION:
    - Ensures source assets exist
    - Copies original song to output path as placeholder for final mix

    TODO:
    - Duck song volume during insert window
    - Overlay insert audio
    - Add crossfade and reverb matching
    """
    if not song_path.exists():
        if song_path.suffix.lower() != ".wav":
            raise FileNotFoundError(f"Missing source audio file: {song_path}")
        duration_seconds = max(20, int(end_ms / 1000) + 5)
        generate_silence_wav(song_path, duration_seconds)

    if not insert_path.exists():
        generate_silence_wav(insert_path, duration_seconds=max(6, int((end_ms - start_ms) / 1000)))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(song_path, output_path)
    return output_path
