"""Shared Redis client helpers (sync + async) with environment-based URL."""
from __future__ import annotations

import os

import redis
import redis.asyncio as aioredis

from config import cfg


def get_redis_url() -> str:
    """Resolve Redis URL from env first, then config fallback."""
    return os.getenv("REDIS_URL") or cfg.REDIS_URL or "redis://127.0.0.1:6379/0"


def get_redis(timeout: float = 5.0) -> redis.Redis:
    """Create a sync Redis client with safe defaults."""
    return redis.from_url(
        get_redis_url(),
        socket_connect_timeout=timeout,
        socket_timeout=timeout,
        decode_responses=True,
    )


def get_async_redis(timeout: float = 5.0, url: str | None = None) -> aioredis.Redis:
    """Create an async Redis client with safe defaults."""
    return aioredis.from_url(
        url or get_redis_url(),
        socket_connect_timeout=timeout,
        socket_timeout=timeout,
        decode_responses=True,
        retry_on_timeout=True,
    )
