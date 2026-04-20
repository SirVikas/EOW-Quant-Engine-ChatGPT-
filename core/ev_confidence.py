"""
EOW Quant Engine — Phase 6: EV Confidence Engine
Classifies trades by EV strength and applies a size multiplier accordingly.

Tiers (based on expected value of the trade):
  EV ≥ EVC_HIGH_THRESHOLD (0.15) → HIGH_CONF  — full size (1.0×)
  EV ≥ EVC_MID_THRESHOLD  (0.05) → MEDIUM_CONF — normal size (1.0×)
  EV ≥ 0                         → LOW_CONF    — reduced size (0.70×)
  EV < 0                         → REJECT      — blocked (EV engine should catch first)

Purpose: Trade size should reflect EV strength. A barely-positive EV trade
earns reduced capital; a strong EV trade gets full allocation. This smooths
the equity curve by scaling confidence proportional to alpha quality.

Non-negotiable: No size boost above 1.0× — system must not chase profit.
"""
from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

from config import cfg


@dataclass
class EVConfResult:
    tier:      str    # "HIGH_CONF" | "MEDIUM_CONF" | "LOW_CONF" | "REJECT"
    ev:        float
    size_mult: float
    ok:        bool
    reason:    str = ""


class EVConfidenceEngine:
    """
    Classifies an EV value into a confidence tier and emits a size multiplier.
    Integrates after EV Engine in the quality chain.
    """

    def __init__(self):
        logger.info(
            f"[EV-CONF] Phase 6 activated | "
            f"HIGH≥{cfg.EVC_HIGH_THRESHOLD}({cfg.EVC_HIGH_SIZE_MULT:.0%}) "
            f"MID≥{cfg.EVC_MID_THRESHOLD}({cfg.EVC_MID_SIZE_MULT:.0%}) "
            f"LOW≥0({cfg.EVC_LOW_SIZE_MULT:.0%})"
        )

    def classify(self, ev: float) -> EVConfResult:
        """
        Classify the EV value and return a size multiplier.

        Args:
            ev: expected value from EVEngine.evaluate() (USDT per unit risk)

        Returns EVConfResult; ok=False → reject trade (negative EV).
        """
        if ev < 0:
            reason = f"EVC_REJECT(ev={ev:.4f}<0)"
            logger.debug(f"[EV-CONF] {reason}")
            return EVConfResult(tier="REJECT", ev=ev, size_mult=0.0,
                                ok=False, reason=reason)

        if ev >= cfg.EVC_HIGH_THRESHOLD:
            return EVConfResult(
                tier="HIGH_CONF", ev=ev,
                size_mult=cfg.EVC_HIGH_SIZE_MULT, ok=True,
                reason=f"EVC_HIGH({ev:.4f}≥{cfg.EVC_HIGH_THRESHOLD})",
            )

        if ev >= cfg.EVC_MID_THRESHOLD:
            return EVConfResult(
                tier="MEDIUM_CONF", ev=ev,
                size_mult=cfg.EVC_MID_SIZE_MULT, ok=True,
                reason=f"EVC_MID({ev:.4f}≥{cfg.EVC_MID_THRESHOLD})",
            )

        # LOW_CONF: EV ≥ 0 but below mid threshold
        reason = f"EVC_LOW({ev:.4f}<{cfg.EVC_MID_THRESHOLD} → {cfg.EVC_LOW_SIZE_MULT:.0%}×)"
        logger.debug(f"[EV-CONF] {reason}")
        return EVConfResult(
            tier="LOW_CONF", ev=ev,
            size_mult=cfg.EVC_LOW_SIZE_MULT, ok=True,
            reason=reason,
        )

    def summary(self) -> dict:
        return {
            "high_threshold": cfg.EVC_HIGH_THRESHOLD,
            "mid_threshold":  cfg.EVC_MID_THRESHOLD,
            "high_size_mult": cfg.EVC_HIGH_SIZE_MULT,
            "mid_size_mult":  cfg.EVC_MID_SIZE_MULT,
            "low_size_mult":  cfg.EVC_LOW_SIZE_MULT,
            "module": "EV_CONFIDENCE_ENGINE",
            "phase":  6,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
ev_confidence_engine = EVConfidenceEngine()
