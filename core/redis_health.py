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
    CONNECTED     = "CONNECTED"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class RedisHealth:
    """
    Lightweight async Redis health probe.
    check() probes the server and caches the result; call it as often as needed.
    """

    def __init__(self, url: Optional[str] = None):
        self._url    = url or cfg.REDIS_URL
        self._status = RedisStatus.NOT_AVAILABLE

    # ── Public ────────────────────────────────────────────────────────────────

    @property
    def status(self) -> RedisStatus:
        return self._status

    @property
    def is_connected(self) -> bool:
        return self._status == RedisStatus.CONNECTED

    async def check(self, timeout: float = 2.0) -> RedisStatus:
        """Probe Redis and update cached status. Returns the new status."""
        try:
            client = await aioredis.from_url(
                self._url,
                decode_responses=True,
                socket_connect_timeout=timeout,
            )
            await asyncio.wait_for(client.ping(), timeout=timeout)
            await client.aclose()
            self._status = RedisStatus.CONNECTED
        except Exception as exc:
            logger.debug(f"[REDIS-HEALTH] Probe failed: {type(exc).__name__}")
            self._status = RedisStatus.NOT_AVAILABLE
        return self._status

    def summary(self) -> dict:
        return {"status": self._status.value, "url": self._url}


# ── Module-level singleton ────────────────────────────────────────────────────
redis_health = RedisHealth()
