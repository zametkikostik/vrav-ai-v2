"""Persistent SQLite rate limiter tests."""

from core.ratelimit import RateLimiter


def test_sqlite_persist(tmp_path):
    db = tmp_path / "rate.db"
    rl = RateLimiter(max_calls=2, window_seconds=60, db_path=db)
    assert rl.allow("u1")
    assert rl.allow("u1")
    assert not rl.allow("u1")
    rl2 = RateLimiter(max_calls=2, window_seconds=60, db_path=db)
    assert not rl2.allow("u1")


def test_sqlite_reset(tmp_path):
    db = tmp_path / "rate2.db"
    rl = RateLimiter(max_calls=1, window_seconds=60, db_path=db)
    assert rl.allow("x")
    assert not rl.allow("x")
    rl.reset("x")
    assert rl.allow("x")


def test_memory_mode_unchanged():
    rl = RateLimiter(max_calls=2, window_seconds=60, db_path=None)
    assert rl.allow("a")
    assert rl.allow("a")
    assert not rl.allow("a")
