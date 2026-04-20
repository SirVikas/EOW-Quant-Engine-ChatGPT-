"""
EOW Quant Engine — Phase 6: Capital Recovery Engine
Intelligent size restoration during and after drawdown cycles.

Problem: DrawdownController already reduces size during drawdown tiers.
But when equity starts recovering from a trough, jumping straight back
to full size risks another loss spike. This engine tracks the recovery
trajectory and gradually restores size as equity approaches the peak.

States:
  NORMAL     — no drawdown active, size_mult = 1.0
  DEFENSIVE  — in drawdown, still falling or at trough, size_mult = CRE_RECOVERY_SIZE_MIN
  RECOVERING — equity rising from trough, size_mult scales linearly
               from CRE_RECOVERY_SIZE_MIN → 1.0 as equity approaches peak
  FULLY_RECOVERED — back to peak, transitions to NORMAL

Non-negotiable: size_mult never exceeds 1.0 — this engine only controls
the restoration rate, not a boost above normal.

Usage: call update_equity() every tick (alongside drawdown_controller),
       call check() before the capital allocator.
"""
from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

from config import cfg


@dataclass
class RecoveryResult:
    state:        str    # "NORMAL" | "DEFENSIVE" | "RECOVERING" | "FULLY_RECOVERED"
    size_mult:    float  # 0.70–1.0
    recovery_pct: float  # 0–1: fraction of drawdown recovered
    drawdown_pct: float  # current DD fraction relative to peak
    reason:       str = ""


class CapitalRecoveryEngine:
    """
    Tracks equity peak and trough to control size during and after drawdown.
    Works alongside DrawdownController — DD controller handles hard tiers;
    this engine handles the smooth ramp-up after the trough is confirmed.
    """

    def __init__(self):
        self._peak:         float = 0.0
        self._trough:       float = 0.0   # 0 = no active drawdown cycle
        self._in_recovery:  bool  = False
        self._current:      float = 0.0
        logger.info(
            f"[CAPITAL-RECOVERY] Phase 6 activated | "
            f"defensive_dd>{cfg.CRE_DEFENSIVE_DD:.0%} "
            f"min_size={cfg.CRE_RECOVERY_SIZE_MIN:.0%}"
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def update_equity(self, equity: float):
        """
        Update equity and track peak/trough/recovery trajectory.
        Call every tick alongside drawdown_controller.update_equity().
        """
        self._current = equity

        if equity > self._peak:
            # New equity high — reset drawdown cycle
            self._peak        = equity
            self._trough      = 0.0
            self._in_recovery = False
            return

        if equity < self._peak:
            if self._trough == 0.0:
                self._trough      = equity   # first drop below peak
                self._in_recovery = False
            elif equity < self._trough:
                self._trough      = equity   # drawdown deepening
                self._in_recovery = False
            elif equity > self._trough:
                self._in_recovery = True     # equity rising from confirmed trough

    def check(self) -> RecoveryResult:
        """
        Return sizing guidance based on current equity vs peak/trough.
        Call once per signal evaluation in the common path.
        """
        if self._peak <= 0:
            return RecoveryResult(
                state="NORMAL", size_mult=1.0,
                recovery_pct=0.0, drawdown_pct=0.0,
                reason="NO_PEAK_YET",
            )

        # No active drawdown cycle
        if self._trough == 0.0:
            return RecoveryResult(
                state="NORMAL", size_mult=1.0,
                recovery_pct=0.0, drawdown_pct=0.0,
            )

        current_dd = max(0.0, (self._peak - self._current) / self._peak)

        # Below defensive threshold — no intervention needed
        if current_dd < cfg.CRE_DEFENSIVE_DD:
            return RecoveryResult(
                state="NORMAL", size_mult=1.0,
                recovery_pct=1.0, drawdown_pct=round(current_dd, 4),
            )

        # Still falling or at trough — full defensive posture
        if not self._in_recovery:
            reason = f"CRE_DEFENSIVE(dd={current_dd:.1%})"
            logger.debug(f"[CAPITAL-RECOVERY] {reason}")
            return RecoveryResult(
                state="DEFENSIVE",
                size_mult=cfg.CRE_RECOVERY_SIZE_MIN,
                recovery_pct=0.0,
                drawdown_pct=round(current_dd, 4),
                reason=reason,
            )

        # Recovering — linear interpolation from min_size → 1.0
        total_gap = self._peak - self._trough
        recovered = self._current - self._trough
        recovery_pct = max(0.0, min(1.0, recovered / total_gap)) if total_gap > 0 else 1.0

        if recovery_pct >= 1.0 or self._current >= self._peak:
            self._trough      = 0.0
            self._in_recovery = False
            return RecoveryResult(
                state="FULLY_RECOVERED", size_mult=1.0,
                recovery_pct=1.0, drawdown_pct=0.0,
                reason="CRE_FULLY_RECOVERED",
            )

        size_mult = cfg.CRE_RECOVERY_SIZE_MIN + (1.0 - cfg.CRE_RECOVERY_SIZE_MIN) * recovery_pct
        reason = (
            f"CRE_RECOVERING({recovery_pct:.0%} → "
            f"{size_mult:.2f}×)"
        )
        logger.debug(f"[CAPITAL-RECOVERY] {reason}")
        return RecoveryResult(
            state="RECOVERING",
            size_mult=round(size_mult, 4),
            recovery_pct=round(recovery_pct, 4),
            drawdown_pct=round(current_dd, 4),
            reason=reason,
        )

    def summary(self) -> dict:
        return {
            "peak_equity":         round(self._peak, 4),
            "trough_equity":       round(self._trough, 4),
            "current_equity":      round(self._current, 4),
            "in_recovery":         self._in_recovery,
            "defensive_dd_thresh": cfg.CRE_DEFENSIVE_DD,
            "recovery_size_min":   cfg.CRE_RECOVERY_SIZE_MIN,
            "module": "CAPITAL_RECOVERY_ENGINE",
            "phase":  6,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
capital_recovery_engine = CapitalRecoveryEngine()
