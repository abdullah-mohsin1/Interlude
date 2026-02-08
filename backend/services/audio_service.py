from __future__ import annotations

import wave
from pathlib import Path
from typing import Iterable

from backend.utils.ffmpeg import assert_ffmpeg_available

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
    Mixes ad audio into a song:
    - duck original song in insert window
    - apply soft fades + simple room tail on insert
    - overlay insert at fixed start
    """
    if not song_path.exists():
        if song_path.suffix.lower() != ".wav":
            raise FileNotFoundError(f"Missing source audio file: {song_path}")
        duration_seconds = max(20, int(end_ms / 1000) + 5)
        generate_silence_wav(song_path, duration_seconds)

    if not insert_path.exists():
        generate_silence_wav(insert_path, duration_seconds=max(6, int((end_ms - start_ms) / 1000)))

    try:
        from pydub import AudioSegment
    except Exception as exc:
        raise RuntimeError(
            "pydub is required for audio mixing. Install backend dependencies first."
        ) from exc

    assert_ffmpeg_available()

    song = AudioSegment.from_file(song_path)
    insert = AudioSegment.from_file(insert_path)

    safe_start = max(0, min(start_ms, len(song)))
    safe_end = max(safe_start + 1, min(end_ms, len(song)))
    window_ms = max(1, safe_end - safe_start)

    clipped_insert = insert[:window_ms]
    fade_ms = max(120, min(400, window_ms // 5, len(clipped_insert) // 4))
    if len(clipped_insert) > fade_ms * 2:
        clipped_insert = clipped_insert.fade_in(fade_ms).fade_out(fade_ms)

    # Simple faux reverb tail: two low-level delayed overlays.
    reverb_layer = AudioSegment.silent(duration=len(clipped_insert) + 180)
    reverb_layer = reverb_layer.overlay(clipped_insert - 11, position=70)
    reverb_layer = reverb_layer.overlay(clipped_insert - 15, position=140)
    processed_insert = reverb_layer.overlay(clipped_insert, position=0)[:window_ms]

    ducked_window = song[safe_start:safe_end].apply_gain(-8)
    ducked_song = song[:safe_start] + ducked_window + song[safe_end:]
    mixed = ducked_song.overlay(processed_insert, position=safe_start)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ext = output_path.suffix.lower().lstrip(".") or "wav"
    export_args = {"format": ext}
    if ext == "mp3":
        export_args["bitrate"] = "192k"
    mixed.export(output_path, **export_args)
    return output_path
