"""
EOW Quant Engine — WebSocket Stabilizer
Tick watchdog: triggers reconnect if no tick received within MAX_GAP_SECONDS.
Maintains connection state, consecutive-ok counter, and per-reconnect backoff
with ±30% jitter to prevent thundering-herd after mass disconnect.
"""
from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from loguru import logger


MAX_GAP_SECONDS = 10     # reconnect if no tick for this long
MAX_BACKOFF_SEC = 60     # ceiling on exponential backoff
JITTER_FRACTION = 0.30   # ±30% jitter applied to every backoff delay


class WsState(str, Enum):
    CONNECTED    = "CONNECTED"
    RECONNECTING = "RECONNECTING"
    DISCONNECTED = "DISCONNECTED"


@dataclass
class WsStats:
    state:           WsState = WsState.DISCONNECTED
    last_tick_ts:    float   = 0.0    # epoch seconds
    reconnect_count: int     = 0
    consecutive_ok:  int     = 0      # ticks since last reconnect
    last_error:      str     = ""
    gap_seconds:     float   = 0.0   # seconds since last tick (computed on read)


class WsStabilizer:
    """
    Wraps a MarketDataProvider and watches for tick staleness.
    When the gap exceeds MAX_GAP_SECONDS, calls mdp.reconnect() with
    exponential backoff + jitter.
    """

    def __init__(self, mdp: Any, max_gap: float = MAX_GAP_SECONDS):
        self._mdp     = mdp
        self._max_gap = max_gap
        self._stats   = WsStats()
        self._backoff = 1.0
        self._running = False

    # ── Public ────────────────────────────────────────────────────────────────

    def record_tick(self):
        """Call this whenever a live tick arrives from MDP."""
        now = time.time()
        self._stats.last_tick_ts   = now
        self._stats.consecutive_ok += 1
        self._stats.gap_seconds    = 0.0
        if self._stats.state != WsState.CONNECTED:
            self._stats.state = WsState.CONNECTED
            self._backoff     = 1.0
            logger.info("[WS-STAB] Stream healthy — backoff reset.")

    @property
    def stats(self) -> WsStats:
        if self._stats.last_tick_ts:
            self._stats.gap_seconds = time.time() - self._stats.last_tick_ts
        return self._stats

    async def start(self):
        """Launch background watchdog. Runs until stop() is called."""
        self._running            = True
        self._stats.last_tick_ts = time.time()   # grace period on first start
        logger.info("[WS-STAB] Watchdog started.")
        await self._watchdog_loop()

    async def stop(self):
        self._running = False
        logger.info("[WS-STAB] Watchdog stopped.")

    # ── Internals ────────────────────────────────────────────────────────────

    async def _watchdog_loop(self):
        while self._running:
            await asyncio.sleep(2)
            gap = time.time() - self._stats.last_tick_ts
            self._stats.gap_seconds = gap

            if gap <= self._max_gap:
                continue

            # Stale stream — trigger reconnect
            self._stats.state       = WsState.RECONNECTING
            self._stats.reconnect_count += 1
            self._stats.consecutive_ok  = 0
            self._stats.last_error  = f"Tick gap {gap:.1f}s > {self._max_gap}s"

            jitter = random.uniform(0, self._backoff * JITTER_FRACTION)
            delay  = self._backoff + jitter
            logger.warning(
                f"[WS-STAB] No tick for {gap:.1f}s — "
                f"reconnect #{self._stats.reconnect_count} in {delay:.1f}s "
                f"(backoff={self._backoff:.0f}s)"
            )

            try:
                await self._mdp.reconnect()
            except Exception as exc:
                logger.debug(f"[WS-STAB] reconnect() raised: {exc}")

            await asyncio.sleep(delay)
            # Reset last_tick_ts so we don't trigger again immediately
            self._stats.last_tick_ts = time.time()
            self._backoff = min(self._backoff * 2, MAX_BACKOFF_SEC)

    def summary(self) -> dict:
        s = self.stats
        return {
            "state":           s.state.value,
            "gap_seconds":     round(s.gap_seconds, 1),
            "reconnect_count": s.reconnect_count,
            "consecutive_ok":  s.consecutive_ok,
            "last_error":      s.last_error,
        }
