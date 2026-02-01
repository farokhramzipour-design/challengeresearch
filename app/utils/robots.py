from __future__ import annotations

import urllib.robotparser
from urllib.parse import urlparse

import httpx

from app.core.config import settings


def can_fetch(url: str, user_agent: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    try:
        with httpx.Client(timeout=settings.request_timeout_s, headers={"User-Agent": user_agent}) as client:
            resp = client.get(robots_url)
            if resp.status_code >= 400:
                return True
            rp.parse(resp.text.splitlines())
        return rp.can_fetch(user_agent, url)
    except Exception:
        return True
