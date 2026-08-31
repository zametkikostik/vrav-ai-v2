"""Rate limiter tests."""

import time

from core.ratelimit import RateLimiter


def test_allow_within_limit():
    rl = RateLimiter(max_calls=3, window_seconds=60)
    assert rl.allow("u1")
    assert rl.allow("u1")
    assert rl.allow("u1")
    assert not rl.allow("u1")
    assert rl.remaining("u1") == 0


def test_separate_keys():
    rl = RateLimiter(max_calls=1, window_seconds=60)
    assert rl.allow("a")
    assert not rl.allow("a")
    assert rl.allow("b")


def test_window_expiry():
    rl = RateLimiter(max_calls=1, window_seconds=0.2)
    assert rl.allow("x")
    assert not rl.allow("x")
    time.sleep(0.25)
    assert rl.allow("x")


def test_reset():
    rl = RateLimiter(max_calls=1, window_seconds=60)
    assert rl.allow("z")
    assert not rl.allow("z")
    rl.reset("z")
    assert rl.allow("z")
