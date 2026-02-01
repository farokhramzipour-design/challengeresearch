from __future__ import annotations

from pathlib import Path

from app.core.config import settings
from app.utils.hashing import stable_hash


def run_dir(run_id: str) -> Path:
    root = settings.data_dir / run_id
    (root / "html").mkdir(parents=True, exist_ok=True)
    (root / "text").mkdir(parents=True, exist_ok=True)
    return root


def html_path(run_id: str, url: str) -> Path:
    key = stable_hash(url)
    return run_dir(run_id) / "html" / f"{key}.html"


def text_path(run_id: str, url: str) -> Path:
    key = stable_hash(url)
    return run_dir(run_id) / "text" / f"{key}.txt"
