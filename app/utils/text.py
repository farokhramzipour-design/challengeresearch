from __future__ import annotations

import re
from typing import Iterable


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def key_phrase(text: str, max_words: int = 12) -> str:
    tokens = normalize_text(text).split()
    return " ".join(tokens[:max_words])


def clamp_quotes(quotes: Iterable[str], max_words: int = 25) -> list[str]:
    clamped = []
    for q in quotes:
        words = q.split()
        clamped.append(" ".join(words[:max_words]))
    return clamped
