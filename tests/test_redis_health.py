"""
Tests for core/redis_health.py

Run with:  python -m pytest tests/test_redis_health.py -v
"""
import asyncio
import pytest

from core.redis_health import RedisHealth, RedisStatus


# ── Helpers ───────────────────────────────────────────────────────────────────

def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestRedisHealth:

    def test_initial_status_is_not_available(self):
        rh = RedisHealth()
        assert rh.status == RedisStatus.NOT_AVAILABLE
        assert rh.is_connected is False

    def test_check_unreachable_returns_not_available(self):
        """Probe a port that is guaranteed to refuse connections."""
        rh = RedisHealth(url="redis://127.0.0.1:19999/0")
        status = run(rh.check(timeout=1.0))
        assert status == RedisStatus.NOT_AVAILABLE
        assert rh.is_connected is False

    def test_summary_structure(self):
        rh = RedisHealth(url="redis://127.0.0.1:19999/0")
        s = rh.summary()
        assert "status" in s
        assert "url" in s
        assert s["status"] == RedisStatus.NOT_AVAILABLE.value

    def test_check_local_redis_if_available(self):
        """
        Attempts to connect to the real local Redis.
        Passes in either direction — this is an integration smoke test.
        """
        rh = RedisHealth()
        status = run(rh.check(timeout=2.0))
        # Valid in both connected and not-connected environments
        assert status in (RedisStatus.CONNECTED, RedisStatus.NOT_AVAILABLE)

    def test_status_enum_values(self):
        assert RedisStatus.CONNECTED.value     == "CONNECTED"
        assert RedisStatus.NOT_AVAILABLE.value == "NOT_AVAILABLE"
