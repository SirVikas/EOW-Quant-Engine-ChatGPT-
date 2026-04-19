"""
EOW Quant Engine — Phase 5.1: Smart Fee Guard
RR-aware fee tolerance to prevent rejection of genuinely high-value trades.

Problem: The static 20% fee/TP cap blocks high-RR trades (RR > 3×) that have
wide TP targets. A 3× RR trade with 0.25% fee drag is still deeply profitable,
but its fee/TP ratio can exceed 20% when TP is very far away.

Solution: Dynamic fee tolerance based on RR:
  RR ≥ SFG_HIGH_RR_THRESHOLD (3.0) → allow fee/TP up to 35%
  RR <  threshold               → allow fee/TP up to 20%

This replaces the static check from profit_guard.check_fee_ratio in the
Phase 5.1 decision flow. The existing execution_engine.should_reject_for_fees
check (absolute loss gate) still runs before this.
"""
from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

from config import cfg


@dataclass
class FeeGuardResult:
    ok:            bool
    effective_max: float   # fee/TP threshold actually used
    fee_ratio:     float   # actual fee/TP ratio
    high_rr:       bool    # True when high-RR tolerance was applied
    reason:        str = ""


class SmartFeeGuard:
    """
    RR-aware replacement for profit_guard.check_fee_ratio.
    High-RR trades earn a wider fee budget — their alpha justifies the cost.
    """

    def __init__(self):
        logger.info(
            f"[SMART-FEE-GUARD] Phase 5.1 activated | "
            f"high_rr≥{cfg.SFG_HIGH_RR_THRESHOLD}: "
            f"max={cfg.SFG_HIGH_RR_FEE_MAX:.0%}  "
            f"normal: max={cfg.SFG_NORMAL_FEE_MAX:.0%}"
        )

    def check(
        self,
        rr:       float,
        gross_tp: float,
        fee_cost: float,
    ) -> FeeGuardResult:
        """
        Evaluate fee acceptability with RR-aware tolerance.

        Args:
            rr:       risk-reward ratio for the signal
            gross_tp: gross TP profit in USDT (|tp − entry| × qty)
            fee_cost: total round-trip fee + slippage in USDT

        Returns FeeGuardResult; ok=False → reject trade.
        """
        if gross_tp <= 0:
            return FeeGuardResult(
                ok=True, effective_max=cfg.SFG_NORMAL_FEE_MAX,
                fee_ratio=0.0, high_rr=False, reason="NO_TP(pass)",
            )

        fee_ratio  = fee_cost / gross_tp
        high_rr    = rr >= cfg.SFG_HIGH_RR_THRESHOLD
        eff_max    = cfg.SFG_HIGH_RR_FEE_MAX if high_rr else cfg.SFG_NORMAL_FEE_MAX

        if fee_ratio > eff_max:
            reason = (
                f"FEE_BLOCKED(fee={fee_cost:.4f}"
                f"={fee_ratio*100:.1f}%_of_tp={gross_tp:.4f}"
                f" max={eff_max*100:.0f}%"
                f" rr={rr:.2f})"
            )
            logger.debug(f"[SMART-FEE-GUARD] {reason}")
            return FeeGuardResult(
                ok=False, effective_max=eff_max,
                fee_ratio=round(fee_ratio, 4),
                high_rr=high_rr, reason=reason,
            )

        return FeeGuardResult(
            ok=True, effective_max=eff_max,
            fee_ratio=round(fee_ratio, 4),
            high_rr=high_rr,
            reason=(
                f"FEE_OK({fee_ratio*100:.1f}%"
                f"≤{eff_max*100:.0f}% rr={rr:.2f})"
            ),
        )

    def summary(self) -> dict:
        return {
            "high_rr_threshold": cfg.SFG_HIGH_RR_THRESHOLD,
            "high_rr_fee_max":   cfg.SFG_HIGH_RR_FEE_MAX,
            "normal_fee_max":    cfg.SFG_NORMAL_FEE_MAX,
            "module": "SMART_FEE_GUARD",
            "phase":  5.1,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
smart_fee_guard = SmartFeeGuard()
