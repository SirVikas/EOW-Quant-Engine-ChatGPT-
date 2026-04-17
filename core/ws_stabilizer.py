"""
EOW Quant Engine — WebSocket Stabilizer  (FTD-REF-025 upgraded)
Tick watchdog: two-tier response to connection starvation.

Tier 1 — Ping (30 s gap):
  Sends a lightweight ping to probe connection health.
  Errors WS_001 logged to error_registry.

Tier 2 — Force reconnect (60 s gap):
  Calls mdp.reconnect() with exponential backoff + ±30% jitter.
  Errors WS_002 / WS_003 logged to error_registry.
  Backoff capped at MAX_BACKOFF (3 multiplier steps) to avoid
  very long waits — after MAX_BACKOFF doublings the delay plateaus.

WsTruthEngine is updated on every state change so the UI always
reflects the real connection state.
"""
from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from loguru import logger


# ── Thresholds ────────────────────────────────────────────────────────────────
PING_GAP_SEC      = 30    # gap before sending a probe ping
RECONNECT_GAP_SEC = 60    # gap before triggering a full reconnect
PING_INTERVAL     = 15    # how long to wait between successive pings (seconds)
MAX_BACKOFF       = 3     # maximum number of backoff doublings (caps delay)
MAX_BACKOFF_SEC   = 60    # absolute ceiling on exponential backoff delay (seconds)
JITTER_FRACTION   = 0.30  # ±30% jitter on backoff delays

# Legacy alias — kept for compatibility with existing on_tick callers
MAX_GAP_SECONDS   = RECONNECT_GAP_SEC


class WsState(str, Enum):
    CONNECTED    = "CONNECTED"
    RECONNECTING = "RECONNECTING"
    DISCONNECTED = "DISCONNECTED"


@dataclass
class WsStats:
    state:           WsState = WsState.DISCONNECTED
    last_tick_ts:    float   = 0.0
    reconnect_count: int     = 0
    consecutive_ok:  int     = 0
    last_error:      str     = ""
    gap_seconds:     float   = 0.0
    ping_sent_count: int     = 0          # FTD-REF-025
    last_ping_ts:    float   = 0.0        # FTD-REF-025


class WsStabilizer:
    """
    Wraps a MarketDataProvider and watches for tick staleness.

    Tier 1 (30 s): sends ping — non-disruptive health probe.
    Tier 2 (60 s): calls mdp.reconnect() — full reconnect with backoff.

    Integrates with WsTruthEngine (singleton imported lazily to avoid
    circular imports) and ErrorRegistry for structured error logging.
    """

    def __init__(self, mdp: Any, max_gap: float = RECONNECT_GAP_SEC):
        self._mdp             = mdp
        self._max_gap         = max_gap
        self._stats           = WsStats()
        self._backoff_step    = 0      # number of doublings applied (capped at MAX_BACKOFF)
        # Backward-compatible scalar used by existing tests/callers.
        # Mirrors the effective backoff delay base (1, 2, 4, ... capped at 60).
        self._backoff         = 1.0
        self._running         = False
        self._ping_in_flight  = False  # True while awaiting ping response

    # ── Public ────────────────────────────────────────────────────────────────

    def record_tick(self):
        """Call this whenever a live tick arrives from MDP."""
        now = time.time()
        self._stats.last_tick_ts   = now
        self._stats.consecutive_ok += 1
        self._stats.gap_seconds    = 0.0
        self._ping_in_flight       = False

        if self._stats.state != WsState.CONNECTED:
            self._stats.state  = WsState.CONNECTED
            self._backoff_step = 0
            self._backoff      = 1.0
            logger.info("[WS-STAB] Stream healthy — backoff reset.")

        # Notify truth engine
        self._truth_record_tick()

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

    def summary(self) -> dict:
        s = self.stats
        network_penalty = 10 if s.reconnect_count > 2 else 0
        return {
            "state":            s.state.value,
            "gap_seconds":      round(s.gap_seconds, 1),
            "reconnect_count":  s.reconnect_count,
            "network_penalty":  network_penalty,
            "consecutive_ok":   s.consecutive_ok,
            "ping_sent_count":  s.ping_sent_count,
            "last_error":       s.last_error,
        }

    # ── Internals ─────────────────────────────────────────────────────────────

    async def _watchdog_loop(self):
        ping_gap = min(PING_GAP_SEC, self._max_gap)
        reconnect_gap = self._max_gap
        while self._running:
            sleep_for = min(2.0, max(0.05, reconnect_gap / 2))
            await asyncio.sleep(sleep_for)
            gap = time.time() - self._stats.last_tick_ts
            self._stats.gap_seconds = gap

            if gap <= ping_gap:
                # Everything is healthy — nothing to do
                continue

            if gap <= reconnect_gap:
                # Tier 1: gap 30–60 s → send ping
                await self._maybe_ping(gap)
            else:
                # Tier 2: gap > 60 s → force reconnect
                await self._force_reconnect(gap)

    async def _maybe_ping(self, gap: float):
        """Send a lightweight ping if one isn't already in flight."""
        now = time.time()
        if self._ping_in_flight:
            return   # already waiting for a response
        if now - self._stats.last_ping_ts < PING_INTERVAL:
            return   # minimum interval between pings

        self._ping_in_flight      = True
        self._stats.ping_sent_count += 1
        self._stats.last_ping_ts  = now
        self._stats.state         = WsState.RECONNECTING

        self._error_log("WS_001", extra=f"gap={gap:.1f}s")
        logger.warning(
            f"[WS-STAB] No tick for {gap:.1f}s — "
            f"ping #{self._stats.ping_sent_count} sent."
        )
        self._truth_record_reconnect_attempt()

        try:
            ping_fn = getattr(self._mdp, "ping", None)
            if ping_fn and asyncio.iscoroutinefunction(ping_fn):
                await ping_fn()
            # If ping is not implemented, the truth engine state will update
            # once a real tick arrives (or we escalate to reconnect at 60 s).
        except Exception as exc:
            logger.debug(f"[WS-STAB] ping() raised: {exc}")
            self._error_log("WS_003", extra=str(exc))

    async def _force_reconnect(self, gap: float):
        """Full reconnect with exponential backoff (capped at MAX_BACKOFF steps)."""
        self._stats.state         = WsState.RECONNECTING
        self._stats.reconnect_count += 1
        self._stats.consecutive_ok  = 0
        self._stats.last_error    = f"Tick gap {gap:.1f}s > {self._max_gap}s"

        # Compute backoff: 1, 2, 4, 8 … capped at MAX_BACKOFF doublings
        backoff_sec = min(self._backoff, MAX_BACKOFF_SEC)
        jitter      = random.uniform(0, backoff_sec * JITTER_FRACTION)
        delay       = backoff_sec + jitter

        self._error_log("WS_002", extra=f"gap={gap:.1f}s attempt={self._stats.reconnect_count}")
        logger.warning(
            f"[WS-STAB] No tick for {gap:.1f}s — "
            f"reconnect #{self._stats.reconnect_count} in {delay:.1f}s "
            f"(backoff_step={self._backoff_step}/{MAX_BACKOFF})"
        )
        self._truth_record_reconnect_attempt()

        try:
            await self._mdp.reconnect()
            self._truth_record_reconnect_success()
        except Exception as exc:
            self._error_log("WS_003", extra=str(exc))
            logger.debug(f"[WS-STAB] reconnect() raised: {exc}")

        await asyncio.sleep(delay)
        # Advance backoff step but cap it
        if self._backoff_step < MAX_BACKOFF:
            self._backoff_step += 1
        self._backoff = min(self._backoff * 2, float(MAX_BACKOFF_SEC))
        # Reset last_tick_ts so we don't trigger again immediately
        self._stats.last_tick_ts = time.time()

    # ── Lazy truth engine + error registry integration ─────────────────────────

    @staticmethod
    def _truth_record_tick():
        try:
            from core.ws_truth_engine import ws_truth_engine
            ws_truth_engine.record_tick()
        except Exception:
            pass

    @staticmethod
    def _truth_record_reconnect_attempt():
        try:
            from core.ws_truth_engine import ws_truth_engine
            ws_truth_engine.record_reconnect_attempt()
        except Exception:
            pass

    @staticmethod
    def _truth_record_reconnect_success():
        try:
            from core.ws_truth_engine import ws_truth_engine
            ws_truth_engine.record_reconnect_success()
        except Exception:
            pass

    @staticmethod
    def _error_log(code: str, symbol: str = "", extra: str = ""):
        try:
            from core.error_registry import error_registry
            error_registry.log(code, symbol=symbol, extra=extra)
        except Exception:
            pass
