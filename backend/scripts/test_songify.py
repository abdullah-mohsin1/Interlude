from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

from backend.services.songify_service import songify_tts_to_singing
from backend.services.gradium_service import generate_voice
from backend.services.audio_service import GENERATED_DIR
from backend.utils.env import ensure_local_env_file


def main() -> None:
    ensure_local_env_file()
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--lyrics", type=Path, required=True, help="Path to lyrics text file")
    parser.add_argument("--bpm", type=int, default=120)
    parser.add_argument("--key", type=str, default="C_minor")
    parser.add_argument("--style", type=str, default="talk_sing")
    args = parser.parse_args()

    lyrics = args.lyrics.read_text(encoding="utf-8")
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    raw_path = Path(generate_voice(text=lyrics))
    songified_path = GENERATED_DIR / "test_songified.wav"
    songify_tts_to_singing(
        input_wav=raw_path,
        lyrics=lyrics,
        bpm=args.bpm,
        key=args.key,
        style=args.style,
        output_wav=songified_path,
    )

    print(f"Raw TTS WAV: {raw_path.resolve()}")
    print(f"Songified WAV: {songified_path.resolve()}")
    print(f"Serve raw: /audio/generated/{raw_path.name}")
    print(f"Serve songified: /audio/generated/{songified_path.name}")


if __name__ == "__main__":
    main()
