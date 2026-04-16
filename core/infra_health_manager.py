"""Unified infrastructure health manager (Redis + WebSocket + API)."""
from __future__ import annotations

import asyncio
import time
from typing import Optional

from core.redis_health import RedisHealth, RedisStatus


class InfraHealthManager:
    def __init__(
        self,
        redis_health: Optional[RedisHealth] = None,
        redis_retries: int = 3,
    ):
        self._redis_health = redis_health or RedisHealth()
        self._redis_retries = max(1, redis_retries)
        self._last = {
            "redis": RedisStatus.NOT_AVAILABLE.value,
            "websocket": "UNKNOWN",
            "api": "NOT CONNECTED",
            "api_ok": False,
            "ts": int(time.time() * 1000),
        }

    async def refresh(
        self,
        ws_state: str = "UNKNOWN",
        api_mode: str = "NOT CONNECTED",
        api_ok: bool = False,
    ) -> dict:
        redis_state = await self._redis_health.check(timeout=2.0, retries=self._redis_retries)
        self._last = {
            "redis": redis_state.value,
            "websocket": ws_state,
            "api": api_mode,
            "api_ok": api_ok,
            "ts": int(time.time() * 1000),
        }
        return dict(self._last)

    async def monitor(
        self,
        interval_seconds: int,
        ws_state_fn,
        api_mode_fn,
        api_ok_fn,
        running_fn,
    ):
        while running_fn():
            await self.refresh(
                ws_state=str(ws_state_fn()),
                api_mode=str(api_mode_fn()),
                api_ok=bool(api_ok_fn()),
            )
            await asyncio.sleep(max(1, interval_seconds))

    def snapshot(self) -> dict:
        return dict(self._last)
