from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv

from backend.utils.paths import env_path


PLACEHOLDER = "PASTE_YOUR_KEY_HERE"
ALT_PLACEHOLDER = "PASTE_NEW_KEY_HERE"


def ensure_local_env_file() -> None:
    path = env_path()
    if path.exists():
        return
    content = "\n".join(
        [
            f"GRADIUM_API_KEY={PLACEHOLDER}",
            "GRADIUM_VOICE_ID=zVI-68f2GRJbOGTT",
            "GRADIUM_REGION=us",
            "",
        ]
    )
    path.write_text(content, encoding="utf-8")
    print("Created .env with placeholders. Paste your real key into .env.")


def load_env() -> None:
    ensure_local_env_file()
    load_dotenv(dotenv_path=str(env_path()), override=False)


def get_env(name: str, default: str | None = None, required: bool = False) -> Optional[str]:
    value = os.getenv(name)
    if value is None and default is not None:
        value = default
    if value is not None:
        value = value.strip()
    if required and (not value or value in {PLACEHOLDER, ALT_PLACEHOLDER}):
        raise RuntimeError(
            f"Missing {name}. Set it in .env at {env_path().resolve()} "
            "or in your deployment environment."
        )
    if value in {PLACEHOLDER, ALT_PLACEHOLDER}:
        return None
    return value
