"""
FTD-031 — Performance Guard (Fail-Safe)

Implements three-tier performance protection (Q11):

    NORMAL      → all modules active, full processing
    DEGRADED    → skip non-critical modules, reduce polling frequency
    SAFE_MODE   → minimal processing: real-time path only

State machine:
    NORMAL  ──(N consecutive latency breaches)──→  DEGRADED
    DEGRADED ──(M more breaches OR memory critical)──→ SAFE_MODE
    DEGRADED ──(latency recovers for K cycles)──→ NORMAL
    SAFE_MODE ──(operator reset only)──→ NORMAL

Safety constraint (Q16): risk engine logic, hard limits, and validation
correctness are NEVER affected regardless of guard state.

Usage:
    perf_guard.observe(cycle_ms=45.2)      # called after each cycle
    perf_guard.state                       # "NORMAL" | "DEGRADED" | "SAFE_MODE"
    perf_guard.should_skip("export_engine")  # True when in degraded/safe mode
    perf_guard.reset()                     # operator manual reset
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Dict, List, Optional, Set

from loguru import logger

from config import cfg

STATE_NORMAL    = "NORMAL"
STATE_DEGRADED  = "DEGRADED"
STATE_SAFE_MODE = "SAFE_MODE"

# Modules that are NEVER skipped regardless of guard state (Q16 safety boundary)
_PROTECTED_MODULES: Set[str] = {
    "risk_engine",
    "risk_controller",
    "guardian",
    "global_gate_controller",
    "pre_trade_gate",
    "hard_start",
    "data_health_monitor",
}

# Default modules to skip when DEGRADED (overridden by cfg.PERF_DEGRADED_SKIP_MODULES)
_DEFAULT_DEGRADED_SKIP = [
    "export_engine",
    "learning_engine",
    "auto_intelligence_engine",
    "genome_engine",
    "analytics",
]

# Default modules to skip when SAFE_MODE (subset of DEGRADED_SKIP + more)
_DEFAULT_SAFE_SKIP = _DEFAULT_DEGRADED_SKIP + [
    "deep_validation",
    "correction_engine",
    "scorecard",
    "regime_ai",
    "adaptive_filter",
]


@dataclass
class _GuardSnapshot:
    ts: int
    state: str
    consecutive_breaches: int
    consecutive_recoveries: int
    cycle_ms: float
    reason: str


class PerfGuard:
    """Singleton performance fail-safe state machine."""

    _BREACH_TO_DEGRADED   = 5    # consecutive latency breaches → DEGRADED
    _BREACH_TO_SAFE       = 10   # further breaches in DEGRADED → SAFE_MODE
    _RECOVERY_TO_NORMAL   = 20   # consecutive OK cycles in DEGRADED → NORMAL

    def __init__(self) -> None:
        self._state = STATE_NORMAL
        self._consecutive_breaches = 0
        self._consecutive_recoveries = 0
        self._breach_threshold = cfg.PERF_LATENCY_BREACH_MS
        self._state_changes: List[_GuardSnapshot] = []
        self._lock = Lock()

        # Build skip sets from config (with fallback to defaults)
        raw_degraded: list = cfg.PERF_DEGRADED_SKIP_MODULES or _DEFAULT_DEGRADED_SKIP
        raw_safe: list = cfg.PERF_SAFE_MODE_SKIP_MODULES or _DEFAULT_SAFE_SKIP
        self._degraded_skip: Set[str] = set(raw_degraded) - _PROTECTED_MODULES
        self._safe_skip: Set[str] = set(raw_safe) - _PROTECTED_MODULES

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    def observe(self, cycle_ms: float, memory_critical: bool = False) -> str:
        """
        Record one cycle observation and update state machine.
        Returns current state after update.
        """
        is_breach = cycle_ms > self._breach_threshold or memory_critical
        with self._lock:
            old_state = self._state

            if is_breach:
                self._consecutive_breaches += 1
                self._consecutive_recoveries = 0
            else:
                self._consecutive_recoveries += 1
                self._consecutive_breaches = 0

            new_state = self._next_state(old_state, memory_critical)
            if new_state != old_state:
                self._state = new_state
                reason = (
                    f"memory_critical" if memory_critical
                    else f"cycle_ms={cycle_ms:.1f} breach_threshold={self._breach_threshold}"
                )
                snap = _GuardSnapshot(
                    ts=int(time.time() * 1000),
                    state=new_state,
                    consecutive_breaches=self._consecutive_breaches,
                    consecutive_recoveries=self._consecutive_recoveries,
                    cycle_ms=cycle_ms,
                    reason=reason,
                )
                self._state_changes.append(snap)
                if len(self._state_changes) > 100:
                    self._state_changes = self._state_changes[-100:]

                if new_state == STATE_DEGRADED:
                    logger.warning(
                        f"[FTD-031] PerfGuard: NORMAL → DEGRADED | "
                        f"consecutive_breaches={self._consecutive_breaches} "
                        f"cycle_ms={cycle_ms:.1f}ms"
                    )
                elif new_state == STATE_SAFE_MODE:
                    logger.error(
                        f"[FTD-031] PerfGuard: {old_state} → SAFE_MODE | "
                        f"reason={reason}"
                    )
                elif new_state == STATE_NORMAL:
                    logger.info(
                        f"[FTD-031] PerfGuard: {old_state} → NORMAL | "
                        f"consecutive_recoveries={self._consecutive_recoveries}"
                    )

            return self._state

    def _next_state(self, current: str, memory_critical: bool) -> str:
        if memory_critical:
            return STATE_SAFE_MODE

        if current == STATE_NORMAL:
            if self._consecutive_breaches >= self._BREACH_TO_DEGRADED:
                return STATE_DEGRADED

        elif current == STATE_DEGRADED:
            if self._consecutive_breaches >= self._BREACH_TO_SAFE:
                return STATE_SAFE_MODE
            if self._consecutive_recoveries >= self._RECOVERY_TO_NORMAL:
                return STATE_NORMAL

        # SAFE_MODE: only manual reset can recover
        return current

    def should_skip(self, module: str) -> bool:
        """Returns True if module should be skipped in current guard state."""
        with self._lock:
            state = self._state
        if state == STATE_NORMAL:
            return False
        if state == STATE_DEGRADED:
            return module in self._degraded_skip
        if state == STATE_SAFE_MODE:
            return module in self._safe_skip
        return False

    def reset(self) -> None:
        """Operator manual reset → NORMAL."""
        with self._lock:
            old = self._state
            self._state = STATE_NORMAL
            self._consecutive_breaches = 0
            self._consecutive_recoveries = 0
        logger.info(f"[FTD-031] PerfGuard reset: {old} → NORMAL (operator)")

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "state":                   self._state,
                "consecutive_breaches":    self._consecutive_breaches,
                "consecutive_recoveries":  self._consecutive_recoveries,
                "state_changes":           len(self._state_changes),
                "breach_threshold_ms":     self._breach_threshold,
                "degraded_skip_modules":   sorted(self._degraded_skip),
                "safe_skip_modules":       sorted(self._safe_skip),
                "protected_modules":       sorted(_PROTECTED_MODULES),
            }

    def history(self, last_n: int = 10) -> List[Dict[str, Any]]:
        with self._lock:
            snaps = self._state_changes[-last_n:]
        return [
            {
                "ts":                    s.ts,
                "state":                 s.state,
                "consecutive_breaches":  s.consecutive_breaches,
                "cycle_ms":              s.cycle_ms,
                "reason":                s.reason,
            }
            for s in snaps
        ]


perf_guard = PerfGuard()
