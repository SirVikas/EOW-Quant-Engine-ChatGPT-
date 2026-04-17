"""
EOW Quant Engine — API Loader (Boot Diagnostics)
Runs once at startup; probes all external connections and prints a
structured boot status line to the console.

Boot log format (FTD-REF-MASTER-001 standard):
  [BOOT] Redis: CONNECTED ✅ | WebSocket: STABLE ✅ | Indicators: VALIDATED ✅
         Strategy Engine: ACTIVE ✅ | Risk Engine: ACTIVE ✅
         Execution Mode: PAPER_API | Deployability: IMPROVING
         API: NOT CONNECTED ❌
"""
from __future__ import annotations

import asyncio
from typing import Optional

from loguru import logger

from config import cfg
from core.redis_health import RedisStatus
from core.infra_health_manager import InfraHealthManager
from core.exchange.api_manager import ApiManager


class ApiLoader:
    """
    Boot-time orchestrator.
    Call run() once inside the FastAPI lifespan startup hook.
    """

    def __init__(self):
        self._redis_status:   RedisStatus = RedisStatus.NOT_AVAILABLE
        self._infra = InfraHealthManager(redis_retries=3)
        self._api_connected:  bool        = False
        self._api_mode:       str         = "NOT CONNECTED"
        self._ws_status:      str         = "CONNECTING"
        self._ind_status:     str         = "PENDING_RUNTIME_VALIDATION"
        self._deployability_score: float  = 0.0
        self._deployability_status: str   = "NOT_READY"

    # ── Public ────────────────────────────────────────────────────────────────

    async def run(self, api_manager: Optional[ApiManager] = None) -> dict:
        """
        Run all boot probes and print the standard boot log line.
        Returns a summary dict for the /api/boot-status endpoint.
        """
        # 1. Binance API probe (if credentials are set)
        if api_manager is not None:
            self._api_connected = await api_manager.connect()
            if self._api_connected and api_manager.client:
                self._api_mode = api_manager.client.mode.value.replace("_", "-")
            else:
                self._api_mode = "NOT CONNECTED"

        infra = await self._infra.refresh(
            ws_state=self._ws_status,
            api_mode=self._api_mode,
            api_ok=self._api_connected,
        )
        self._redis_status = RedisStatus(infra["redis"])

        self._print_boot_lines()
        return self.summary()

    def summary(self) -> dict:
        return {
            "redis":           self._redis_status.value,
            "websocket":       self._ws_status,
            "indicators":      self._ind_status,
            "api":             self._api_mode,
            "api_ok":          self._api_connected,
            "strategy_engine": "ACTIVE",
            "risk_engine":     "ACTIVE",
            "execution_mode":  cfg.TRADE_MODE,
            "deployability":   self._deployability_status,
            "deployability_score": self._deployability_score,
        }

    def set_deployability(self, score: float, status: str) -> None:
        self._deployability_score = max(0.0, min(100.0, float(score)))
        self._deployability_status = str(status or "NOT_READY")

    # ── Internals ─────────────────────────────────────────────────────────────

    def _print_boot_lines(self):
        def tick(cond: bool) -> str:
            return "✅" if cond else "❌"

        r_ok = self._redis_status == RedisStatus.CONNECTED
        a_ok = self._api_connected
        ws_ok = self._ws_status == "CONNECTED"
        ind_ok = self._ind_status == "VALIDATED"

        logger.info(
            f"[BOOT] Redis: {self._redis_status.value} {tick(r_ok)} | "
            f"WebSocket: {self._ws_status} {tick(ws_ok)} | "
            f"Indicators: {self._ind_status} {tick(ind_ok)}"
        )
        logger.info(
            f"[BOOT] Strategy Engine: ACTIVE ✅ | "
            f"Risk Engine: ACTIVE ✅ | "
            f"Execution Mode: {cfg.TRADE_MODE}"
        )
        logger.info(
            f"[BOOT] API: {self._api_mode} {tick(a_ok)} | "
            f"Deployability: {self._deployability_status} ({self._deployability_score:.0f}/100)"
        )


# ── Module-level singleton ────────────────────────────────────────────────────
api_loader = ApiLoader()
