from __future__ import annotations

import shutil


def assert_ffmpeg_available() -> None:
    if shutil.which("ffmpeg"):
        return
    raise RuntimeError(
        "ffmpeg is required but was not found on PATH.\n"
        "Install:\n"
        "  macOS: brew install ffmpeg\n"
        "  Ubuntu/Debian: sudo apt-get update && sudo apt-get install -y ffmpeg\n"
        "  Windows: install ffmpeg and add it to PATH."
    )

