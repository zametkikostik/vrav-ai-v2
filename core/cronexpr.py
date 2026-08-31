"""Minimal 5-field cron expression matcher (min hour dom month dow)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


def _parse_field(field: str, min_v: int, max_v: int) -> set[int]:
    values: set[int] = set()
    for part in field.split(","):
        part = part.strip()
        if not part:
            continue
        step = 1
        if "/" in part:
            base, step_s = part.split("/", 1)
            step = int(step_s)
            part = base
        if part == "*":
            start, end = min_v, max_v
        elif "-" in part:
            a, b = part.split("-", 1)
            start, end = int(a), int(b)
        else:
            start = end = int(part)
        if start < min_v or end > max_v or start > end or step < 1:
            raise ValueError(f"invalid cron field segment: {field!r}")
        values.update(range(start, end + 1, step))
    if not values:
        raise ValueError(f"empty cron field: {field!r}")
    return values


@dataclass(frozen=True)
class CronExpr:
    minute: set[int]
    hour: set[int]
    day: set[int]
    month: set[int]
    dow: set[int]
    raw: str

    @classmethod
    def parse(cls, expr: str) -> CronExpr:
        parts = expr.strip().split()
        if len(parts) != 5:
            raise ValueError(
                f"cron must have 5 fields (min hour dom month dow), got: {expr!r}"
            )
        dow = _parse_field(parts[4], 0, 7)
        if 7 in dow:
            dow = (dow - {7}) | {0}
        return cls(
            minute=_parse_field(parts[0], 0, 59),
            hour=_parse_field(parts[1], 0, 23),
            day=_parse_field(parts[2], 1, 31),
            month=_parse_field(parts[3], 1, 12),
            dow=dow,
            raw=expr.strip(),
        )

    def matches(self, dt: datetime) -> bool:
        cron_dow = (dt.weekday() + 1) % 7
        return (
            dt.minute in self.minute
            and dt.hour in self.hour
            and dt.day in self.day
            and dt.month in self.month
            and cron_dow in self.dow
        )
