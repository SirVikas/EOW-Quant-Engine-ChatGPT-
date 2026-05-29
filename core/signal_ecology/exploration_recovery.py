"""
FTD-057-PHOENIX Phase 3 — Exploration Recovery Governor

Detects starvation / drought / rejection-loop conditions and issues
controlled curiosity trades with smaller allocation. Every recovery
cycle is fully auditable — no silent overrides.

Recovery modes:
  NONE       — healthy, no action
  CURIOSITY  — 1 trade with reduced allocation (CURIOSITY_SIZE_MULT)
  FORCED     — drought > FORCED_DROUGHT_SEC, allocation floor applied
"""
from __future__ import annotations

import time
import threading
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional

from loguru import logger


# ── Constants ──────────────────────────────────────────────────────────────────
CURIOSITY_SIZE_MULT   = 0.4    # size multiplier for curiosity trades
FORCED_SIZE_MULT      = 0.25   # size multiplier for forced-exploration trades
FORCED_DROUGHT_SEC    = 900    # 15 min drought → forced exploration
REJECTION_LOOP_N      = 50     # N consecutive blocks = rejection loop
COOLDOWN_SEC          = 180    # min seconds between recovery activations
MAX_RECOVERY_TRADES   = 3      # max curiosity trades per recovery episode
RECOVERY_WINDOW_SEC   = 600    # window to count recovery trades in


class RecoveryMode(Enum):
    NONE     = "NONE"
    CURIOSITY = "CURIOSITY"
    FORCED   = "FORCED"


@dataclass
class RecoveryDecision:
    mode:            RecoveryMode
    size_multiplier: float             # 1.0 = no change
    reason:          str
    cycle_id:        str
    recovery_active: bool
    consecutive_blocks: int
    drought_seconds: float
    ts:              int = field(default_factory=lambda: int(time.time() * 1000))


class ExplorationRecoveryGovernor:
    """
    Monitors signal ecology health and issues exploration recovery decisions.
    Integrates with SignalDensityEngine for drought/starvation state.
    Thread-safe.
    """

    def __init__(self):
        self._lock = threading.RLock()

        self._consecutive_blocks: int  = 0
        self._last_pass_ts:       float = time.time()
        self._last_recovery_ts:   float = 0.0
        self._active_cycle_id:    Optional[str] = None
        self._cycle_trade_count:  int  = 0
        self._total_recoveries:   int  = 0

        # Audit log
        self._cycle_log:    deque = deque(maxlen=100)
        self._decision_log: deque = deque(maxlen=500)

    # ── Primary API ────────────────────────────────────────────────────────────

    @property
    def is_active(self) -> bool:
        """True when a recovery cycle is currently open."""
        with self._lock:
            return self._active_cycle_id is not None

    def on_signal_blocked(self) -> None:
        """Call every time a signal is blocked (any reason)."""
        with self._lock:
            self._consecutive_blocks += 1

    def on_signal_passed(self) -> None:
        """Call every time a signal passes."""
        with self._lock:
            self._consecutive_blocks = 0
            self._last_pass_ts = time.time()
            # Close recovery cycle if open
            if self._active_cycle_id:
                self._close_recovery_cycle("SIGNAL_RECOVERED")

    def evaluate(
        self,
        drought_seconds: float,
        survival_rate: float,
        is_starvation: bool,
    ) -> RecoveryDecision:
        """
        Evaluate current ecology state and return a recovery decision.
        Call this before executing a trade to get the size multiplier.
        """
        with self._lock:
            now = time.time()
            cooldown_ok = (now - self._last_recovery_ts) >= COOLDOWN_SEC

            # Determine mode
            mode = RecoveryMode.NONE
            reason = ""

            if drought_seconds >= FORCED_DROUGHT_SEC and cooldown_ok:
                mode = RecoveryMode.FORCED
                reason = f"DROUGHT {drought_seconds:.0f}s ≥ {FORCED_DROUGHT_SEC}s"

            elif (is_starvation or self._consecutive_blocks >= REJECTION_LOOP_N) and cooldown_ok:
                mode = RecoveryMode.CURIOSITY
                if is_starvation:
                    reason = f"STARVATION sr={survival_rate:.3f}"
                else:
                    reason = f"REJECTION_LOOP consecutive_blocks={self._consecutive_blocks}"

            # Cap recovery trades per episode
            if mode != RecoveryMode.NONE:
                if self._cycle_trade_count >= MAX_RECOVERY_TRADES:
                    mode = RecoveryMode.NONE
                    reason = f"RECOVERY_CAP reached ({MAX_RECOVERY_TRADES} trades)"

            size_mult = 1.0
            if mode == RecoveryMode.CURIOSITY:
                size_mult = CURIOSITY_SIZE_MULT
                self._activate_recovery(mode, reason, now)
            elif mode == RecoveryMode.FORCED:
                size_mult = FORCED_SIZE_MULT
                self._activate_recovery(mode, reason, now)

            dec = RecoveryDecision(
                mode=mode,
                size_multiplier=size_mult,
                reason=reason,
                cycle_id=self._active_cycle_id or "",
                recovery_active=(mode != RecoveryMode.NONE),
                consecutive_blocks=self._consecutive_blocks,
                drought_seconds=drought_seconds,
            )
            self._decision_log.append({
                "ts":                dec.ts,
                "mode":              mode.value,
                "size_mult":         size_mult,
                "reason":            reason,
                "consecutive_blocks": self._consecutive_blocks,
                "drought_seconds":   round(drought_seconds, 1),
                "cycle_id":          dec.cycle_id,
            })
            return dec

    # ── Internals ──────────────────────────────────────────────────────────────

    def _activate_recovery(self, mode: RecoveryMode, reason: str, now: float) -> None:
        if self._active_cycle_id is None:
            import uuid
            self._active_cycle_id = f"REC-{int(now*1000)}"
            self._cycle_trade_count = 0
            self._total_recoveries += 1

        self._cycle_trade_count += 1
        self._last_recovery_ts = now

        self._cycle_log.append({
            "ts":         int(now * 1000),
            "cycle_id":   self._active_cycle_id,
            "mode":       mode.value,
            "reason":     reason,
            "trade_n":    self._cycle_trade_count,
            "total_cycles": self._total_recoveries,
        })
        logger.warning(
            f"[FTD-057][RECOVERY] {mode.value} activated | "
            f"cycle={self._active_cycle_id} trade_n={self._cycle_trade_count} | "
            f"{reason}"
        )

    def _close_recovery_cycle(self, close_reason: str) -> None:
        if self._active_cycle_id:
            self._cycle_log.append({
                "ts":       int(time.time() * 1000),
                "cycle_id": self._active_cycle_id,
                "event":    "CLOSED",
                "reason":   close_reason,
                "trades_in_cycle": self._cycle_trade_count,
            })
            logger.info(
                f"[FTD-057][RECOVERY] Cycle {self._active_cycle_id} closed: "
                f"{close_reason} ({self._cycle_trade_count} trades)"
            )
            self._active_cycle_id  = None
            self._cycle_trade_count = 0

    # ── Telemetry ──────────────────────────────────────────────────────────────

    def get_telemetry(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "module":               "ExplorationRecoveryGovernor",
                "ftd":                  "057",
                "total_recoveries":     self._total_recoveries,
                "active_cycle_id":      self._active_cycle_id,
                "cycle_trade_count":    self._cycle_trade_count,
                "consecutive_blocks":   self._consecutive_blocks,
                "drought_seconds":      round(time.time() - self._last_pass_ts, 1),
                "cooldown_remaining":   max(
                    0.0, COOLDOWN_SEC - (time.time() - self._last_recovery_ts)
                ),
                "recent_cycles":        list(self._cycle_log)[-20:],
                "recent_decisions":     list(self._decision_log)[-20:],
                "ts":                   int(time.time() * 1000),
            }

    def cycle_history(self, n: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._cycle_log)[-n:]


# ── Singleton ──────────────────────────────────────────────────────────────────
exploration_recovery_governor = ExplorationRecoveryGovernor()
