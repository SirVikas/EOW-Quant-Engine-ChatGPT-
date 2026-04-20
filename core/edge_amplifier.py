"""
EOW Quant Engine — Phase 7: Edge Amplifier
Boosts high-confidence setups by widening TP targets and increasing trailing
stop aggressiveness.

Amplification fires only when ALL four conditions hold:
  1. EV ≥ EA_EV_THRESHOLD         (strong expected value)
  2. rank_score ≥ EA_RANK_THRESHOLD (trade ranked highly)
  3. regime is aligned             (TRENDING or VOLATILITY_EXPANSION)
  4. volume_ratio ≥ EA_VOL_RATIO_THRESHOLD (above-average volume)

When all conditions are met:
  • TP target ×  EA_TP_BOOST_MULT   (default 1.25×)
  • Trailing SL aggressiveness × EA_TRAIL_BOOST_MULT (default 1.20×)

Non-negotiable: amplification never bypasses DD limits or loss cluster
controls. It only affects TP and trailing parameters, not entry size.
"""
from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

from config import cfg


_AMPLIFY_REGIMES = {"TRENDING", "VOLATILITY_EXPANSION"}


@dataclass
class AmplifyResult:
    amplified:        bool
    tp_multiplier:    float   # 1.0 when not amplified
    trail_multiplier: float   # 1.0 when not amplified
    reason:           str = ""


class EdgeAmplifier:
    """
    Examines four qualitative conditions and returns TP/trail boost factors
    when all four are satisfied.

    Usage:
        result = edge_amplifier.evaluate(
            ev=0.18, rank_score=0.85,
            regime="TRENDING", volume_ratio=1.8
        )
        actual_tp = base_tp * result.tp_multiplier
        actual_trail_atr_mult = base_trail * result.trail_multiplier
    """

    def __init__(self):
        logger.info(
            f"[EDGE-AMPLIFIER] Phase 7 activated | "
            f"ev≥{cfg.EA_EV_THRESHOLD} rank≥{cfg.EA_RANK_THRESHOLD} "
            f"vol≥{cfg.EA_VOL_RATIO_THRESHOLD} → "
            f"TP×{cfg.EA_TP_BOOST_MULT} trail×{cfg.EA_TRAIL_BOOST_MULT}"
        )

    def evaluate(
        self,
        ev:           float,
        rank_score:   float,
        regime:       str,
        volume_ratio: float,
    ) -> AmplifyResult:
        """
        Evaluate whether this trade qualifies for edge amplification.

        Args:
            ev:           Expected value from EVEngine
            rank_score:   Composite rank from TradeRanker
            regime:       Current market regime string
            volume_ratio: current_volume / avg_volume

        Returns AmplifyResult with tp_multiplier and trail_multiplier.
        """
        checks = {
            "ev":     ev >= cfg.EA_EV_THRESHOLD,
            "rank":   rank_score >= cfg.EA_RANK_THRESHOLD,
            "regime": regime in _AMPLIFY_REGIMES,
            "volume": volume_ratio >= cfg.EA_VOL_RATIO_THRESHOLD,
        }
        all_pass = all(checks.values())

        if all_pass:
            reason = (
                f"AMPLIFY(ev={ev:.4f}≥{cfg.EA_EV_THRESHOLD} "
                f"rank={rank_score:.3f}≥{cfg.EA_RANK_THRESHOLD} "
                f"regime={regime} vol={volume_ratio:.2f}≥{cfg.EA_VOL_RATIO_THRESHOLD} "
                f"→ TP×{cfg.EA_TP_BOOST_MULT} trail×{cfg.EA_TRAIL_BOOST_MULT})"
            )
            logger.info(f"[EDGE-AMPLIFIER] {reason}")
            return AmplifyResult(
                amplified=True,
                tp_multiplier=cfg.EA_TP_BOOST_MULT,
                trail_multiplier=cfg.EA_TRAIL_BOOST_MULT,
                reason=reason,
            )

        failed = [k for k, v in checks.items() if not v]
        reason = f"NO_AMPLIFY(failed={failed})"
        logger.debug(f"[EDGE-AMPLIFIER] {reason}")
        return AmplifyResult(
            amplified=False,
            tp_multiplier=1.0,
            trail_multiplier=1.0,
            reason=reason,
        )

    def summary(self) -> dict:
        return {
            "ev_threshold":     cfg.EA_EV_THRESHOLD,
            "rank_threshold":   cfg.EA_RANK_THRESHOLD,
            "vol_threshold":    cfg.EA_VOL_RATIO_THRESHOLD,
            "tp_boost_mult":    cfg.EA_TP_BOOST_MULT,
            "trail_boost_mult": cfg.EA_TRAIL_BOOST_MULT,
            "amplify_regimes":  sorted(_AMPLIFY_REGIMES),
            "module": "EDGE_AMPLIFIER",
            "phase":  7,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
edge_amplifier = EdgeAmplifier()
