"""
EOW Quant Engine — Redis Health Checker
Returns CONNECTED / NOT_AVAILABLE status asynchronously.
Used at boot time and by the stabilizer for live health reporting.
"""
from __future__ import annotations

import asyncio
from enum import Enum
from typing import Optional

import redis.asyncio as aioredis
from loguru import logger

from config import cfg


class RedisStatus(str, Enum):
    CONNECTED = "CONNECTED"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class RedisHealth:
    """
    Lightweight async Redis health probe with retry-aware state updates.
    """

    def __init__(self, url: Optional[str] = None):
        self._url = url or cfg.REDIS_URL
        self._status = RedisStatus.NOT_AVAILABLE

    @property
    def status(self) -> RedisStatus:
        return self._status

    @property
    def is_connected(self) -> bool:
        return self._status == RedisStatus.CONNECTED

    async def check_redis(self, timeout: float = 2.0) -> bool:
        """Hard validation probe: True only when Redis ping succeeds."""
        client = None
        try:
            client = await aioredis.from_url(
                self._url,
                decode_responses=True,
                socket_connect_timeout=timeout,
                socket_timeout=timeout,
                retry_on_timeout=True,
            )
            await asyncio.wait_for(client.ping(), timeout=timeout)
            return True
        except Exception as exc:
            logger.debug(f"[REDIS-HEALTH] Probe failed: {type(exc).__name__}")
            return False
        finally:
            if client is not None:
                try:
                    await client.aclose()
                except Exception:
                    pass

    async def check(self, timeout: float = 2.0, retries: int = 1) -> RedisStatus:
        """Probe Redis and update cached status. Retries before declaring unavailable."""
        attempts = max(1, retries)
        for attempt in range(1, attempts + 1):
            if await self.check_redis(timeout=timeout):
                self._status = RedisStatus.CONNECTED
                return self._status
            if attempt < attempts:
                await asyncio.sleep(0.15 * attempt)

        self._status = RedisStatus.NOT_AVAILABLE
        return self._status

    def summary(self) -> dict:
        return {"status": self._status.value, "url": self._url}


redis_health = RedisHealth()
