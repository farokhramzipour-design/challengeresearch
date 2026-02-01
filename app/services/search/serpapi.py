from __future__ import annotations

from typing import List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.services.search.base import SearchResult


class SerpAPISearchClient:
    def __init__(self) -> None:
        if not settings.serpapi_key:
            raise ValueError("SERPAPI_KEY is required for SerpAPI search")
        self.api_key = settings.serpapi_key

    @retry(stop=stop_after_attempt(settings.max_retries), wait=wait_exponential(min=1, max=10))
    def search(self, query: str, top_n: int, recency_days: int) -> List[SearchResult]:
        params = {
            "engine": "google",
            "q": query,
            "num": top_n,
            "hl": "en",
            "gl": "gb",
            "api_key": self.api_key,
        }
        if recency_days:
            params["tbs"] = f"qdr:d{recency_days}"

        with httpx.Client(timeout=settings.request_timeout_s) as client:
            resp = client.get("https://serpapi.com/search.json", params=params)
            resp.raise_for_status()
            data = resp.json()

        results = []
        for item in data.get("organic_results", [])[:top_n]:
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet"),
                    source="serpapi",
                )
            )
        return results
