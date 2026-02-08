from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def env_path() -> Path:
    return repo_root() / ".env"
