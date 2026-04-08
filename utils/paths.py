from __future__ import annotations

import os
import sys
from pathlib import Path


def app_root() -> Path:
    """
    Root for bundled read-only resources (assets/, default config/, etc).

    - Dev: repo root (folder containing `main.py`)
    - PyInstaller: sys._MEIPASS temp extraction dir
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS")).resolve()
    return Path(__file__).resolve().parents[1]


def app_data_root() -> Path:
    """
    Writable per-user storage root (database, logs, user config).
    """
    # Prefer Windows roaming profile; fall back to home dir.
    base = os.environ.get("APPDATA") or str(Path.home())
    d = Path(base) / "AftabSaharERP"
    d.mkdir(parents=True, exist_ok=True)
    return d


def config_dir() -> Path:
    d = app_data_root() / "config"
    d.mkdir(parents=True, exist_ok=True)
    return d


def data_dir() -> Path:
    d = app_data_root() / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def logs_dir() -> Path:
    d = app_data_root() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def assets_dir() -> Path:
    d = app_root() / "assets"
    d.mkdir(parents=True, exist_ok=True)
    return d

