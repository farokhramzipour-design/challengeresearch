from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import numpy as np

from app.utils.hashing import dedupe_key
from app.utils.text import normalize_text


@dataclass
class DedupeResult:
    items: List[Dict[str, Any]]
    duplicates_removed: int


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def dedupe_items(
    items: List[Dict[str, Any]],
    embeddings: List[List[float]],
    threshold: float = 0.86,
) -> DedupeResult:
    kept: List[Dict[str, Any]] = []
    kept_embeddings: List[np.ndarray] = []
    seen_titles = set()
    seen_keys = set()
    duplicates = 0

    for item, emb in zip(items, embeddings):
        title_key = normalize_text(item.get("title", ""))
        key = dedupe_key(item.get("title", ""), item.get("summary", ""))
        item["dedupe_key"] = key

        if title_key in seen_titles or key in seen_keys:
            duplicates += 1
            continue

        emb_vec = np.array(emb, dtype=np.float32)
        is_dup = False
        for kept_vec in kept_embeddings:
            if cosine_similarity(emb_vec, kept_vec) >= threshold:
                is_dup = True
                break

        if is_dup:
            duplicates += 1
            continue

        kept.append(item)
        kept_embeddings.append(emb_vec)
        seen_titles.add(title_key)
        seen_keys.add(key)

    return DedupeResult(items=kept, duplicates_removed=duplicates)
