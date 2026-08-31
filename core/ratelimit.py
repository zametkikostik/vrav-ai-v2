"""Simple in-memory rate limiter (per key)."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field


@dataclass
class RateLimiter:
    """Token-bucket style: max_calls within window_seconds per key."""

    max_calls: int = 20
    window_seconds: float = 60.0
    _hits: dict[str, deque[float]] = field(default_factory=lambda: defaultdict(deque))

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        q = self._hits[key]
        cutoff = now - self.window_seconds
        while q and q[0] < cutoff:
            q.popleft()
        if len(q) >= self.max_calls:
            return False
        q.append(now)
        return True

    def remaining(self, key: str) -> int:
        now = time.monotonic()
        q = self._hits[key]
        cutoff = now - self.window_seconds
        while q and q[0] < cutoff:
            q.popleft()
        return max(0, self.max_calls - len(q))

    def reset(self, key: str | None = None) -> None:
        if key is None:
            self._hits.clear()
        else:
            self._hits.pop(key, None)
