"""Cron expression parser tests."""

from datetime import datetime

import pytest

from core.cronexpr import CronExpr


def test_every_hour_at_0():
    e = CronExpr.parse("0 * * * *")
    assert e.matches(datetime(2026, 1, 1, 12, 0))
    assert not e.matches(datetime(2026, 1, 1, 12, 1))


def test_every_6_hours():
    e = CronExpr.parse("0 */6 * * *")
    assert e.matches(datetime(2026, 1, 1, 0, 0))
    assert e.matches(datetime(2026, 1, 1, 6, 0))
    assert not e.matches(datetime(2026, 1, 1, 7, 0))


def test_specific_weekday_monday():
    e = CronExpr.parse("30 9 * * 1")
    assert e.matches(datetime(2026, 1, 5, 9, 30))
    assert not e.matches(datetime(2026, 1, 6, 9, 30))


def test_range_and_list():
    e = CronExpr.parse("0 9-11 * * *")
    assert e.matches(datetime(2026, 3, 1, 9, 0))
    assert not e.matches(datetime(2026, 3, 1, 12, 0))


def test_invalid_raises():
    with pytest.raises(ValueError):
        CronExpr.parse("0 * *")
    with pytest.raises(ValueError):
        CronExpr.parse("60 * * * *")
