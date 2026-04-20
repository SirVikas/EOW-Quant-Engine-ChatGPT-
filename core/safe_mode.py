"""
EOW Quant Engine — Phase 6.5: Safe Mode Controller
Protects the system during data instability by halting new trade entry
while allowing management of existing open positions.

Activation triggers (any):
  • WsStabilityEngine detects > WSS_MAX_RECONNECTS_SAFE_MODE reconnects
  • BootDeployabilityEngine score < BDE_MIN_SCORE
  • DataHealthMonitor signals block_trading = True
  • Manual activation via activate()

While in safe mode:
  ✅ Manage existing positions (SL/TP adjustments, partial closes)
  ❌ No new trade entries
  ❌ No exploration trades
  ❌ No size increases

Auto-resume check:
  Every SMC_RESUME_AFTER_MIN minutes the engine re-checks if score ≥
  SMC_MIN_SCORE_RESUME. If so, safe mode is lifted automatically.
  Manual deactivate() bypasses the score gate (used by operators).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from loguru import logger

from config import cfg


class SafeModeState(str, Enum):
    ACTIVE   = "ACTIVE"
    INACTIVE = "INACTIVE"


@dataclass
class SafeModeEvent:
    ts:      float
    action:  str    # "ACTIVATED" | "DEACTIVATED" | "CHECKED_STILL_ACTIVE" | "AUTO_RESUME_DENIED"
    reason:  str


@dataclass
class SafeModeStatus:
    state:          SafeModeState
    active:         bool
    reason:         str
    activated_at:   Optional[float]
    can_open_trade: bool    # always False when active
    can_manage:     bool    # always True
    duration_min:   float   # minutes since activation (0 when inactive)


class SafeModeController:
    """
    System-wide safe mode gate.

    Single instance (safe_mode_controller) is imported by all trade-entry
    paths. All new trade entry checks must call can_open_new_trade() before
    proceeding.

    Usage:
        # At signal entry point:
        if not safe_mode_controller.can_open_new_trade():
            return  # skip new trade, do not exit existing

        # From WsStability / DataHealth:
        safe_mode_controller.activate("WS_STABILITY: 4 reconnects")

        # Check for auto-resume (call on each cycle):
        safe_mode_controller.check_auto_resume(current_score=82.0)
    """

    def __init__(self):
        self._state: SafeModeState = SafeModeState.INACTIVE
        self._reason: str = ""
        self._activated_at: Optional[float] = None
        self._last_resume_check: float = 0.0
        self._history: List[SafeModeEvent] = []
        logger.info(
            f"[SAFE-MODE] Phase 6.5 activated | "
            f"auto_resume_interval={cfg.SMC_RESUME_AFTER_MIN}min "
            f"resume_score≥{cfg.SMC_MIN_SCORE_RESUME}"
        )

    # ── Activation / Deactivation ─────────────────────────────────────────────

    def activate(self, reason: str) -> None:
        """Enter safe mode. Idempotent — calling again with a new reason updates reason."""
        was_inactive = self._state == SafeModeState.INACTIVE
        self._state = SafeModeState.ACTIVE
        self._reason = reason
        if was_inactive:
            self._activated_at = time.time()
            logger.error(f"[SAFE-MODE] *** ACTIVATED *** reason={reason}")
        else:
            logger.warning(f"[SAFE-MODE] Already active; reason updated: {reason}")
        self._log_event("ACTIVATED", reason)

    def deactivate(self, reason: str = "MANUAL_OVERRIDE") -> None:
        """Exit safe mode immediately (operator override)."""
        if self._state == SafeModeState.INACTIVE:
            return
        self._state = SafeModeState.INACTIVE
        self._activated_at = None
        self._reason = ""
        logger.info(f"[SAFE-MODE] DEACTIVATED: {reason}")
        self._log_event("DEACTIVATED", reason)

    def check_auto_resume(self, current_score: float) -> bool:
        """
        Evaluate whether safe mode can be automatically lifted.
        Call this on every decision cycle or at regular intervals.

        Args:
            current_score: current BootDeployabilityEngine score (0–100)

        Returns True if safe mode was lifted, False if still active.
        """
        if self._state == SafeModeState.INACTIVE:
            return True

        now = time.time()
        interval_sec = cfg.SMC_RESUME_AFTER_MIN * 60.0
        if now - self._last_resume_check < interval_sec:
            return False  # not time yet

        self._last_resume_check = now

        if current_score >= cfg.SMC_MIN_SCORE_RESUME:
            logger.info(
                f"[SAFE-MODE] AUTO-RESUME: score={current_score:.1f}"
                f"≥{cfg.SMC_MIN_SCORE_RESUME} — safe mode lifted"
            )
            self._log_event("DEACTIVATED", f"AUTO_RESUME(score={current_score:.1f})")
            self._state = SafeModeState.INACTIVE
            self._activated_at = None
            self._reason = ""
            return True

        logger.debug(
            f"[SAFE-MODE] Auto-resume check DENIED: "
            f"score={current_score:.1f}<{cfg.SMC_MIN_SCORE_RESUME}"
        )
        self._log_event(
            "AUTO_RESUME_DENIED",
            f"score={current_score:.1f}<{cfg.SMC_MIN_SCORE_RESUME}",
        )
        return False

    # ── Trade gates ──────────────────────────────────────────────────────────

    def can_open_new_trade(self) -> bool:
        """False when safe mode is active — no new entries allowed."""
        return self._state == SafeModeState.INACTIVE

    def can_manage_existing(self) -> bool:
        """Always True — existing positions must always be manageable."""
        return True

    # ── Introspection ─────────────────────────────────────────────────────────

    @property
    def is_active(self) -> bool:
        return self._state == SafeModeState.ACTIVE

    def status(self) -> SafeModeStatus:
        now = time.time()
        duration = (now - self._activated_at) / 60.0 if self._activated_at else 0.0
        return SafeModeStatus(
            state=self._state,
            active=self.is_active,
            reason=self._reason,
            activated_at=self._activated_at,
            can_open_trade=self.can_open_new_trade(),
            can_manage=True,
            duration_min=round(duration, 2),
        )

    def recent_events(self, n: int = 10) -> List[SafeModeEvent]:
        return self._history[-n:]

    def summary(self) -> dict:
        s = self.status()
        return {
            "active":           s.active,
            "state":            s.state.value,
            "reason":           s.reason,
            "duration_min":     s.duration_min,
            "can_open_trade":   s.can_open_trade,
            "can_manage":       s.can_manage,
            "total_activations": sum(1 for e in self._history if e.action == "ACTIVATED"),
            "thresholds": {
                "resume_after_min":  cfg.SMC_RESUME_AFTER_MIN,
                "min_score_resume":  cfg.SMC_MIN_SCORE_RESUME,
            },
            "module": "SAFE_MODE_CONTROLLER",
            "phase":  "6.5",
        }

    def _log_event(self, action: str, reason: str) -> None:
        self._history.append(SafeModeEvent(ts=time.time(), action=action, reason=reason))
        if len(self._history) > 200:
            self._history = self._history[-200:]


# ── Module-level singleton ────────────────────────────────────────────────────
safe_mode_controller = SafeModeController()
