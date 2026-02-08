from __future__ import annotations

from pathlib import Path

from backend.services.audio_service import GENERATED_DIR, mix_audio


def mix_song_with_insert(
    song_id: str,
    song_path: Path,
    insert_path: Path,
    start_ms: int,
    end_ms: int,
) -> Path:
    output_path = Path(GENERATED_DIR) / f"{song_id}_with_ad.wav"
    return mix_audio(
        song_path=song_path,
        insert_path=insert_path,
        start_ms=start_ms,
        end_ms=end_ms,
        output_path=output_path,
    )

