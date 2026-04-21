"""
EOW Quant Engine — core/gating/safe_mode_engine.py
Phase 6.6: Safe Mode Engine

Controls the system's operational mode with three distinct states:

    NORMAL  → Full trading allowed (new entries + position management)
    SAFE    → No new trades; existing positions managed normally
    BLOCKED → Full stop; no new trades, no modifications to positions
              (reserved for catastrophic failure conditions)

Activation:
    safe_mode_engine.activate(reason)          → SAFE mode
    safe_mode_engine.activate_blocked(reason)  → BLOCKED mode
    safe_mode_engine.deactivate()              → NORMAL mode (manual only)

Auto-resume:
    check_recovery(deploy_score, can_trade) is called by GlobalGateController
    every evaluation cycle. When can_trade=True OR deploy_score ≥
    SMC_MIN_SCORE_RESUME the engine transitions SAFE → NORMAL automatically.
    BLOCKED never auto-recovers.

Non-negotiable:
    BLOCKED state can only be cleared by explicit operator call to
    force_reset(). No automatic recovery from BLOCKED.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from loguru import logger

from config import cfg
from core.gating.gate_logger import gate_logger


class SafeMode(str, Enum):
    NORMAL  = "NORMAL"    # full trading
    SAFE    = "SAFE"      # no new trades
    BLOCKED = "BLOCKED"   # full stop


@dataclass
class SafeModeEvent:
    ts:     float
    mode:   SafeMode
    reason: str


@dataclass
class SafeModeStatus:
    mode:           SafeMode
    can_trade:      bool      # True only in NORMAL
    can_manage:     bool      # True in NORMAL + SAFE
    reason:         str
    activated_at:   Optional[float]
    duration_min:   float


class SafeModeEngine:
    """
    Three-state protection system.

    State transitions:
        NORMAL → SAFE    : activate(reason)
        NORMAL → BLOCKED : activate_blocked(reason)
        SAFE   → NORMAL  : deactivate() or check_recovery()
        SAFE   → BLOCKED : activate_blocked(reason)
        BLOCKED → NORMAL : force_reset() ONLY (operator action)
    """

    def __init__(self):
        self._mode: SafeMode = SafeMode.NORMAL
        self._reason: str = ""
        self._activated_at: Optional[float] = None
        self._last_resume_check: float = 0.0
        self._history: List[SafeModeEvent] = []
        logger.info(
            f"[SAFE-MODE-ENGINE] Phase 6.6 activated | "
            f"auto_resume_score≥{cfg.SMC_MIN_SCORE_RESUME} "
            f"check_interval={cfg.SMC_RESUME_AFTER_MIN}min"
        )

    # ── Mode transitions ──────────────────────────────────────────────────────

    def activate(self, reason: str) -> None:
        """Enter SAFE mode (no new trades; existing managed normally)."""
        if self._mode == SafeMode.BLOCKED:
            logger.warning(f"[SAFE-MODE-ENGINE] Already BLOCKED — ignoring SAFE activate: {reason}")
            return
        prev = self._mode
        self._mode = SafeMode.SAFE
        if prev != SafeMode.SAFE:
            self._activated_at = time.time()
            gate_logger.safe_mode(reason=reason, detail=f"prev={prev.value}")
            logger.error(f"[SAFE-MODE-ENGINE] SAFE MODE ACTIVATED | reason={reason}")
        else:
            self._reason = reason
        self._reason = reason
        self._log(SafeMode.SAFE, reason)

    def activate_blocked(self, reason: str) -> None:
        """Enter BLOCKED mode (full stop — no trading, no management)."""
        prev = self._mode
        self._mode = SafeMode.BLOCKED
        self._reason = reason
        self._activated_at = time.time() if prev == SafeMode.NORMAL else self._activated_at
        gate_logger.safe_mode(reason=f"BLOCKED:{reason}", detail=f"prev={prev.value}")
        logger.critical(
            f"[SAFE-MODE-ENGINE] *** BLOCKED *** reason={reason} — full stop"
        )
        self._log(SafeMode.BLOCKED, reason)

    def deactivate(self, reason: str = "MANUAL") -> None:
        """Return to NORMAL mode. Does not clear BLOCKED — use force_reset()."""
        if self._mode == SafeMode.BLOCKED:
            logger.warning(
                "[SAFE-MODE-ENGINE] Cannot deactivate BLOCKED mode — use force_reset()"
            )
            return
        if self._mode == SafeMode.NORMAL:
            return
        self._mode = SafeMode.NORMAL
        self._reason = ""
        self._activated_at = None
        logger.info(f"[SAFE-MODE-ENGINE] NORMAL mode restored | reason={reason}")
        self._log(SafeMode.NORMAL, reason)

    def force_reset(self, reason: str = "OPERATOR_RESET") -> None:
        """Clear even BLOCKED state. Requires explicit operator action."""
        prev = self._mode
        self._mode = SafeMode.NORMAL
        self._reason = ""
        self._activated_at = None
        logger.warning(
            f"[SAFE-MODE-ENGINE] FORCE RESET from {prev.value} | reason={reason}"
        )
        self._log(SafeMode.NORMAL, f"FORCE_RESET:{reason}")

    def check_recovery(self, deploy_score: float, can_trade: bool = False) -> bool:
        """
        Auto-resume from SAFE to NORMAL.

        Exits SAFE when either condition holds:
          • can_trade=True  (GlobalGate just evaluated all-clear)
          • deploy_score ≥ SMC_MIN_SCORE_RESUME

        Throttle applies only after the first check since activation
        (_last_resume_check == 0.0 means never checked → always permitted).
        BLOCKED never recovers here.

        Returns True if mode was changed to NORMAL.
        """
        if self._mode != SafeMode.SAFE:
            return False

        now = time.time()
        interval = cfg.SMC_RESUME_AFTER_MIN * 60.0
        # qFTD-005: skip throttle on the very first check after activation
        if self._last_resume_check > 0 and (now - self._last_resume_check) < interval:
            return False
        self._last_resume_check = now

        if can_trade or deploy_score >= cfg.SMC_MIN_SCORE_RESUME:
            logger.info(
                f"[SAFE-MODE-ENGINE] Auto-resume: score={deploy_score:.1f} "
                f"can_trade={can_trade} threshold={cfg.SMC_MIN_SCORE_RESUME}"
            )
            self.deactivate(
                reason=f"AUTO_RESUME(score={deploy_score:.1f} can_trade={can_trade})"
            )
            return True

        logger.debug(
            f"[SAFE-MODE-ENGINE] Auto-resume denied: "
            f"score={deploy_score:.1f}<{cfg.SMC_MIN_SCORE_RESUME} can_trade={can_trade}"
        )
        return False

    # ── State queries ─────────────────────────────────────────────────────────

    @property
    def mode(self) -> SafeMode:
        return self._mode

    @property
    def can_trade(self) -> bool:
        """True only when in NORMAL mode."""
        return self._mode == SafeMode.NORMAL

    @property
    def can_manage(self) -> bool:
        """True in NORMAL and SAFE; False in BLOCKED."""
        return self._mode != SafeMode.BLOCKED

    def status(self) -> SafeModeStatus:
        now = time.time()
        dur = (now - self._activated_at) / 60.0 if self._activated_at else 0.0
        return SafeModeStatus(
            mode=self._mode,
            can_trade=self.can_trade,
            can_manage=self.can_manage,
            reason=self._reason,
            activated_at=self._activated_at,
            duration_min=round(dur, 2),
        )

    def summary(self) -> dict:
        s = self.status()
        return {
            "mode":         s.mode.value,
            "can_trade":    s.can_trade,
            "can_manage":   s.can_manage,
            "reason":       s.reason,
            "duration_min": s.duration_min,
            "total_events": len(self._history),
            "thresholds": {
                "resume_score": cfg.SMC_MIN_SCORE_RESUME,
                "check_min":    cfg.SMC_RESUME_AFTER_MIN,
            },
            "module": "SAFE_MODE_ENGINE",
            "phase":  "6.6",
        }

    def _log(self, mode: SafeMode, reason: str) -> None:
        self._history.append(SafeModeEvent(ts=time.time(), mode=mode, reason=reason))
        if len(self._history) > 200:
            self._history = self._history[-200:]


# ── Module-level singleton ────────────────────────────────────────────────────
safe_mode_engine = SafeModeEngine()
