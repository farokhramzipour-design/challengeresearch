from __future__ import annotations

import time
from collections import defaultdict
from typing import DefaultDict


class DomainRateLimiter:
    def __init__(self, min_interval_s: float) -> None:
        self.min_interval_s = min_interval_s
        self._last_seen: DefaultDict[str, float] = defaultdict(lambda: 0.0)

    def wait(self, domain: str) -> None:
        now = time.time()
        elapsed = now - self._last_seen[domain]
        if elapsed < self.min_interval_s:
            time.sleep(self.min_interval_s - elapsed)
        self._last_seen[domain] = time.time()
