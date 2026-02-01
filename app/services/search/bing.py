from __future__ import annotations

from typing import List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.services.search.base import SearchResult


class BingSearchClient:
    def __init__(self) -> None:
        if not settings.azure_bing_key:
            raise ValueError("AZURE_BING_KEY is required for Bing search")
        self.endpoint = settings.azure_bing_endpoint
        self.headers = {"Ocp-Apim-Subscription-Key": settings.azure_bing_key}

    @retry(stop=stop_after_attempt(settings.max_retries), wait=wait_exponential(min=1, max=10))
    def search(self, query: str, top_n: int, recency_days: int) -> List[SearchResult]:
        params = {
            "q": query,
            "count": top_n,
            "mkt": "en-GB",
            "safeSearch": "Moderate",
        }
        # Bing API doesn't directly accept recency_days; use freshness where possible
        if recency_days <= 1:
            params["freshness"] = "Day"
        elif recency_days <= 7:
            params["freshness"] = "Week"
        elif recency_days <= 30:
            params["freshness"] = "Month"

        with httpx.Client(timeout=settings.request_timeout_s) as client:
            resp = client.get(self.endpoint, headers=self.headers, params=params)
            resp.raise_for_status()
            data = resp.json()

        results = []
        for item in data.get("webPages", {}).get("value", [])[:top_n]:
            results.append(
                SearchResult(
                    title=item.get("name", ""),
                    url=item.get("url", ""),
                    snippet=item.get("snippet"),
                    source="bing",
                )
            )
        return results
