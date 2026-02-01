from __future__ import annotations

from dataclasses import dataclass
from typing import List, Protocol


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str | None = None
    source: str | None = None


class SearchClient(Protocol):
    def search(self, query: str, top_n: int, recency_days: int) -> List[SearchResult]:
        ...
