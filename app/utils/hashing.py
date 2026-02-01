from __future__ import annotations

import hashlib

from app.utils.text import key_phrase, normalize_text


def stable_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def dedupe_key(title: str, summary: str) -> str:
    normalized_title = normalize_text(title)
    claim = key_phrase(summary)
    return stable_hash(f"{normalized_title}|{claim}")
