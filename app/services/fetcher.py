from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import httpx
import trafilatura
from bs4 import BeautifulSoup
from readability import Document
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.services.cache import html_path, text_path
from app.utils.rate_limit import DomainRateLimiter
from app.utils.robots import can_fetch


@dataclass
class FetchResult:
    url: str
    html: Optional[str]
    text: Optional[str]


class PageFetcher:
    def __init__(self) -> None:
        self.rate_limiter = DomainRateLimiter(settings.rate_limit_per_domain_s)

    def _extract_text(self, html: str) -> Optional[str]:
        text = trafilatura.extract(html)
        if text:
            return text
        try:
            doc = Document(html)
            cleaned = doc.summary()
            soup = BeautifulSoup(cleaned, "html.parser")
            return soup.get_text("\n", strip=True)
        except Exception:
            soup = BeautifulSoup(html, "html.parser")
            return soup.get_text("\n", strip=True)

    @retry(stop=stop_after_attempt(settings.max_retries), wait=wait_exponential(min=1, max=10))
    def fetch(self, url: str) -> FetchResult:
        domain = urlparse(url).netloc
        self.rate_limiter.wait(domain)

        if not can_fetch(url, settings.user_agent):
            return FetchResult(url=url, html=None, text=None)

        headers = {"User-Agent": settings.user_agent}
        with httpx.Client(timeout=settings.request_timeout_s, headers=headers, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            html = resp.text

        text = self._extract_text(html)
        return FetchResult(url=url, html=html, text=text)

    def fetch_with_cache(self, run_id: str, url: str, dry_run: bool = False) -> FetchResult:
        h_path = html_path(run_id, url)
        t_path = text_path(run_id, url)

        if dry_run:
            if t_path.exists() and h_path.exists():
                return FetchResult(
                    url=url,
                    html=h_path.read_text(encoding="utf-8"),
                    text=t_path.read_text(encoding="utf-8"),
                )
            return FetchResult(url=url, html=None, text=None)

        result = self.fetch(url)
        if result.html:
            h_path.write_text(result.html, encoding="utf-8")
        if result.text:
            t_path.write_text(result.text, encoding="utf-8")
        return result
