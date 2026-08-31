"""Lightweight cron-style scheduler for dream and other jobs."""

from __future__ import annotations

import signal
import threading
import time
from datetime import datetime, timezone
from typing import Callable

from core.logging_setup import log


class CronScheduler:
    def __init__(self) -> None:
        self._jobs: list[tuple[str, float, Callable[[], None]]] = []
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def every(self, name: str, interval_seconds: float, fn: Callable[[], None]) -> None:
        if interval_seconds < 10:
            raise ValueError("interval must be >= 10 seconds")
        self._jobs.append((name, float(interval_seconds), fn))

    def start(self, block: bool = True) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="cron-scheduler", daemon=True)
        self._thread.start()
        log.info("scheduler started jobs=%s", [j[0] for j in self._jobs])
        if block:
            try:
                while not self._stop.is_set():
                    time.sleep(0.5)
            except KeyboardInterrupt:
                self.stop()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
        log.info("scheduler stopped")

    def _loop(self) -> None:
        last_run: dict[str, float] = {name: 0.0 for name, _, _ in self._jobs}
        while not self._stop.is_set():
            now = time.monotonic()
            for name, interval, fn in self._jobs:
                if now - last_run[name] >= interval:
                    last_run[name] = now
                    try:
                        log.info("cron job start name=%s at=%s", name, datetime.now(timezone.utc).isoformat())
                        fn()
                        log.info("cron job done name=%s", name)
                    except Exception:
                        log.exception("cron job failed name=%s", name)
            self._stop.wait(1.0)


def run_dream_cron(interval_hours: float = 6.0) -> None:
    from memory.dream import dream

    hours = max(0.1, interval_hours)
    sched = CronScheduler()

    def _job() -> None:
        result = dream()
        print(result)

    sched.every("dream", hours * 3600, _job)
    print(f"Dream cron every {hours}h. Ctrl+C to stop.")
    signal.signal(signal.SIGINT, lambda *_: sched.stop())
    sched.start(block=True)
