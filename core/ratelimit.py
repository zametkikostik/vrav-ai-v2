"""Rate limiter: in-memory + optional SQLite persistence."""

from __future__ import annotations

import sqlite3
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RateLimiter:
    max_calls: int = 20
    window_seconds: float = 60.0
    db_path: Path | str | None = None
    _hits: dict[str, deque[float]] = field(default_factory=lambda: defaultdict(deque))

    def __post_init__(self) -> None:
        if self.db_path is not None:
            self.db_path = Path(self.db_path)
            self._init_db()

    def _init_db(self) -> None:
        assert self.db_path is not None
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS rate_hits (key TEXT NOT NULL, ts REAL NOT NULL)"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_rate_key_ts ON rate_hits(key, ts)")
        conn.commit()
        conn.close()

    def _purge_and_count_db(self, key: str, now: float) -> int:
        assert self.db_path is not None
        cutoff = now - self.window_seconds
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM rate_hits WHERE ts < ?", (cutoff,))
        row = conn.execute(
            "SELECT COUNT(*) FROM rate_hits WHERE key = ? AND ts >= ?",
            (key, cutoff),
        ).fetchone()
        conn.commit()
        conn.close()
        return int(row[0]) if row else 0

    def _add_db(self, key: str, now: float) -> None:
        assert self.db_path is not None
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO rate_hits(key, ts) VALUES (?, ?)", (key, now))
        conn.commit()
        conn.close()

    def allow(self, key: str) -> bool:
        now = time.time() if self.db_path else time.monotonic()
        if self.db_path is not None:
            count = self._purge_and_count_db(key, now)
            if count >= self.max_calls:
                return False
            self._add_db(key, now)
            return True
        q = self._hits[key]
        cutoff = now - self.window_seconds
        while q and q[0] < cutoff:
            q.popleft()
        if len(q) >= self.max_calls:
            return False
        q.append(now)
        return True

    def remaining(self, key: str) -> int:
        now = time.time() if self.db_path else time.monotonic()
        if self.db_path is not None:
            count = self._purge_and_count_db(key, now)
            return max(0, self.max_calls - count)
        q = self._hits[key]
        cutoff = now - self.window_seconds
        while q and q[0] < cutoff:
            q.popleft()
        return max(0, self.max_calls - len(q))

    def reset(self, key: str | None = None) -> None:
        if self.db_path is not None:
            conn = sqlite3.connect(self.db_path)
            if key is None:
                conn.execute("DELETE FROM rate_hits")
            else:
                conn.execute("DELETE FROM rate_hits WHERE key = ?", (key,))
            conn.commit()
            conn.close()
            return
        if key is None:
            self._hits.clear()
        else:
            self._hits.pop(key, None)
