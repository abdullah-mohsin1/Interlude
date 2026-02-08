from __future__ import annotations

import sys

from backend.utils.env import get_env, load_env
from backend.utils.paths import env_path


def main() -> int:
    load_env()

    vars_to_check = ["GRADIUM_API_KEY", "GRADIUM_VOICE_ID", "GRADIUM_REGION"]
    for name in vars_to_check:
        value = get_env(name)
        print(f"{name}: {bool(value)}")

    try:
        get_env("GRADIUM_API_KEY", required=True)
    except RuntimeError:
        print(f"Set GRADIUM_API_KEY in {env_path().resolve()}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
