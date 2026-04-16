import asyncio

from core.redis_health import RedisHealth, RedisStatus


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_redis_retry_unavailable_sets_not_available():
    rh = RedisHealth(url="redis://127.0.0.1:19999/0")
    status = run(rh.check(timeout=0.2, retries=3))
    assert status == RedisStatus.NOT_AVAILABLE


def test_check_redis_returns_bool():
    rh = RedisHealth(url="redis://127.0.0.1:19999/0")
    ok = run(rh.check_redis(timeout=0.2))
    assert ok is False
