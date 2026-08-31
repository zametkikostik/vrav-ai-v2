"""Scheduler: interval jobs + 5-field cron expressions."""

from __future__ import annotations

import signal
import threading
import time
from datetime import datetime, timezone
from typing import Callable

from core.cronexpr import CronExpr
from core.logging_setup import log


class CronScheduler:
    def __init__(self) -> None:
        self._interval_jobs: list[tuple[str, float, Callable[[], None]]] = []
        self._cron_jobs: list[tuple[str, CronExpr, Callable[[], None]]] = []
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_cron_minute: str | None = None

    def every(self, name: str, interval_seconds: float, fn: Callable[[], None]) -> None:
        if interval_seconds < 10:
            raise ValueError("interval must be >= 10 seconds")
        self._interval_jobs.append((name, float(interval_seconds), fn))

    def cron(self, name: str, expression: str, fn: Callable[[], None]) -> None:
        expr = CronExpr.parse(expression)
        self._cron_jobs.append((name, expr, fn))

    def start(self, block: bool = True) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="cron-scheduler", daemon=True)
        self._thread.start()
        log.info(
            "scheduler started interval=%s cron=%s",
            [j[0] for j in self._interval_jobs],
            [j[0] for j in self._cron_jobs],
        )
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

    def _run(self, name: str, fn: Callable[[], None]) -> None:
        try:
            log.info("cron job start name=%s at=%s", name, datetime.now(timezone.utc).isoformat())
            fn()
            log.info("cron job done name=%s", name)
        except Exception:
            log.exception("cron job failed name=%s", name)

    def _loop(self) -> None:
        last_run: dict[str, float] = {name: 0.0 for name, _, _ in self._interval_jobs}
        while not self._stop.is_set():
            now_m = time.monotonic()
            for name, interval, fn in self._interval_jobs:
                if now_m - last_run[name] >= interval:
                    last_run[name] = now_m
                    self._run(name, fn)

            now = datetime.now().replace(second=0, microsecond=0)
            minute_key = now.strftime("%Y-%m-%d %H:%M")
            if minute_key != self._last_cron_minute:
                self._last_cron_minute = minute_key
                for name, expr, fn in self._cron_jobs:
                    if expr.matches(now):
                        self._run(name, fn)

            self._stop.wait(1.0)


def run_dream_cron(
    interval_hours: float | None = 6.0,
    cron_expr: str | None = None,
) -> None:
    from memory.dream import dream

    sched = CronScheduler()

    def _job() -> None:
        print(dream())

    if cron_expr:
        sched.cron("dream", cron_expr, _job)
        print(f"Dream cron expression: {cron_expr!r}. Ctrl+C to stop.")
    else:
        hours = max(0.1, float(interval_hours or 6.0))
        sched.every("dream", hours * 3600, _job)
        print(f"Dream every {hours}h. Ctrl+C to stop.")

    signal.signal(signal.SIGINT, lambda *_: sched.stop())
    sched.start(block=True)
