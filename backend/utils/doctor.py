from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

from backend.utils.paths import repo_root


REQUIRED_DEPS = ["requests", "dotenv", "pydub", "numpy", "librosa", "soundfile"]


def check_python_deps() -> Dict[str, bool]:
    results: Dict[str, bool] = {}
    for dep in REQUIRED_DEPS:
        try:
            __import__(dep)
            results[dep] = True
        except Exception:
            results[dep] = False
    return results


def check_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def auto_install_python_deps() -> Dict[str, bool]:
    requirements_path = repo_root() / "backend" / "requirements.txt"
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)]
    )
    return check_python_deps()


def auto_install_ffmpeg() -> bool:
    if check_ffmpeg():
        return True
    if platform.system().lower() != "darwin":
        raise RuntimeError(
            "ffmpeg is missing. Install:\n"
            "  macOS: brew install ffmpeg\n"
            "  Ubuntu/Debian: sudo apt-get update && sudo apt-get install -y ffmpeg\n"
            "  Windows: install ffmpeg and add it to PATH."
        )
    if shutil.which("brew") is None:
        raise RuntimeError(
            "ffmpeg is missing and Homebrew is not available. Install Homebrew or "
            "install ffmpeg manually and add it to PATH."
        )
    subprocess.check_call(["brew", "install", "ffmpeg"])
    return check_ffmpeg()


def _auto_install_allowed() -> bool:
    explicit = os.getenv("ALLOW_AUTO_INSTALL")
    if explicit is not None:
        return explicit.strip().lower() in {"1", "true", "yes"}
    env = os.getenv("ENV", "").lower()
    uvicorn_reload = os.getenv("UVICORN_RELOAD", "").lower() in {"1", "true", "yes"}
    return env == "development" or uvicorn_reload


def run_doctor(auto_fix: bool = True) -> dict:
    report: Dict[str, object] = {
        "python_deps": check_python_deps(),
        "ffmpeg": check_ffmpeg(),
        "auto_install_allowed": _auto_install_allowed(),
        "attempted_fixes": [],
    }

    if auto_fix and report["auto_install_allowed"]:
        attempted: List[str] = []
        if not all(report["python_deps"].values()):
            try:
                report["python_deps"] = auto_install_python_deps()
                attempted.append("python_deps")
            except Exception as exc:
                report["python_deps_error"] = str(exc)
        if not report["ffmpeg"]:
            try:
                report["ffmpeg"] = auto_install_ffmpeg()
                attempted.append("ffmpeg")
            except Exception as exc:
                report["ffmpeg_error"] = str(exc)
        report["attempted_fixes"] = attempted

    report["ok"] = bool(all(report["python_deps"].values()) and report["ffmpeg"])
    return report
