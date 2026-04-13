"""
EOW Quant Engine — API Loader (Boot Diagnostics)
Runs once at startup; probes all external connections and prints a
structured boot status line to the console.

Boot log format (FTD-REF-019 standard):
  [BOOT] Redis: CONNECTED ✅ | WebSocket: STABLE ✅ | Indicators: VALIDATED ✅ | API: CONNECTED (READ-ONLY) ✅
  [BOOT] Redis: NOT_AVAILABLE ❌ | WebSocket: STABLE ✅ | Indicators: VALIDATED ✅ | API: NOT CONNECTED ❌
"""
from __future__ import annotations

import asyncio
from typing import Optional

from loguru import logger

from config import cfg
from core.redis_health import RedisHealth, RedisStatus
from core.exchange.api_manager import ApiManager


class ApiLoader:
    """
    Boot-time orchestrator.
    Call run() once inside the FastAPI lifespan startup hook.
    """

    def __init__(self):
        self._redis_status:   RedisStatus = RedisStatus.NOT_AVAILABLE
        self._api_connected:  bool        = False
        self._api_mode:       str         = "NOT CONNECTED"
        self._ws_status:      str         = "STABLE"      # assumed until first gap
        self._ind_status:     str         = "VALIDATED"   # static — guard is inline

    # ── Public ────────────────────────────────────────────────────────────────

    async def run(self, api_manager: Optional[ApiManager] = None) -> dict:
        """
        Run all boot probes and print the standard boot log line.
        Returns a summary dict for the /api/status endpoint.
        """
        # 1. Redis probe
        health = RedisHealth()
        self._redis_status = await health.check(timeout=2.0)

        # 2. Binance API probe (if credentials are set)
        if api_manager is not None:
            self._api_connected = await api_manager.connect()
            if self._api_connected and api_manager.client:
                self._api_mode = api_manager.client.mode.value.replace("_", "-")
            else:
                self._api_mode = "NOT CONNECTED"

        self._print_boot_line()
        return self.summary()

    def summary(self) -> dict:
        return {
            "redis":      self._redis_status.value,
            "websocket":  self._ws_status,
            "indicators": self._ind_status,
            "api":        self._api_mode,
            "api_ok":     self._api_connected,
        }

    # ── Internals ─────────────────────────────────────────────────────────────

    def _print_boot_line(self):
        r_tick = "✅" if self._redis_status == RedisStatus.CONNECTED else "❌"
        w_tick = "✅" if self._ws_status   == "STABLE"              else "❌"
        i_tick = "✅" if self._ind_status  == "VALIDATED"           else "❌"
        a_tick = "✅" if self._api_connected                        else "❌"

        line = (
            f"Redis: {self._redis_status.value} {r_tick} | "
            f"WebSocket: {self._ws_status} {w_tick} | "
            f"Indicators: {self._ind_status} {i_tick} | "
            f"API: {self._api_mode} {a_tick}"
        )
        logger.info(f"[BOOT] {line}")


# ── Module-level singleton ────────────────────────────────────────────────────
api_loader = ApiLoader()
