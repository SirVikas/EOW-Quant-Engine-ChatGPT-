"""
EOW Quant Engine — Phase 5.2: Dynamic Threshold Provider
Single source of truth for ALL runtime filter thresholds.

Aggregates three Phase 5.x engines into one unified output:
  1. TradeActivator   — freeze-prevention relaxation (volume + score)
  2. AdaptiveFilter   — loss-streak tightening / no-trade relaxation (score)
  3. DrawdownController — DD-adjusted fee tolerance

Output schema:
  score_min         : float  — effective minimum confidence score (0–1)
  volume_multiplier : float  — multiplier on VOLUME_THRESHOLD_PCT (0.20–1.0)
  fee_tolerance     : float  — effective normal-RR max fee/TP fraction
  dd_allowed        : bool   — False when DD STOP is engaged
  dd_size_mult      : float  — 0.0–1.0 position-size multiplier from DD tier
  tier              : str    — activator tier ("NORMAL"|"TIER_1"|…)
  af_state          : str    — adaptive filter state ("NORMAL"|"RELAX"|"TIGHTEN")

Priority rules:
  • TIGHTEN always wins over RELAX for score_min
  • Volume multiplier comes exclusively from TradeActivator
  • Fee tolerance tightens proportionally with DD severity
  • All values logged every call at DEBUG level

Integration: call get() ONCE at the top of signal processing, pass the
returned DynamicThresholds to all downstream gates.
"""
from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

from config import cfg
from core.trade_activator    import trade_activator
from core.adaptive_filter    import adaptive_filter
from core.drawdown_controller import drawdown_controller


@dataclass
class DynamicThresholds:
    score_min:         float   # effective min score for this evaluation
    volume_multiplier: float   # applied to VOLUME_THRESHOLD_PCT
    fee_tolerance:     float   # normal-RR max fee/TP fraction
    dd_allowed:        bool    # False → DD STOP, no new trades
    dd_size_mult:      float   # 0.0–1.0 from DrawdownController
    tier:              str     # TradeActivator tier
    af_state:          str     # AdaptiveFilter state


class DynamicThresholdProvider:
    """
    Aggregates TradeActivator, AdaptiveFilter, and DrawdownController
    into a single DynamicThresholds snapshot per evaluation cycle.

    Stateless: all state is held by the individual engines.
    """

    def __init__(self):
        logger.info("[DTP] Phase 5.2 Dynamic Threshold Provider activated")

    def get(
        self,
        minutes_no_trade:   float = 0.0,
        consecutive_losses: int   = 0,
    ) -> DynamicThresholds:
        """
        Compute the current effective thresholds.

        Args:
            minutes_no_trade:   global minutes since last completed trade
            consecutive_losses: back-to-back losing trades (for adaptive filter)

        Returns a DynamicThresholds snapshot — cheap to call every tick.
        """
        # ── 1. Trade Activator ────────────────────────────────────────────────
        act = trade_activator.check(minutes_no_trade)

        # ── 2. Adaptive Filter ────────────────────────────────────────────────
        af = adaptive_filter.check(
            consecutive_losses=consecutive_losses,
            minutes_no_trade=minutes_no_trade,
        )

        # ── 3. Drawdown Controller (current equity state) ─────────────────────
        dd = drawdown_controller.check()

        # ── Combine: score_min ────────────────────────────────────────────────
        # TIGHTEN always overrides relaxation — loss streak > no-trade urgency
        if af.state == "TIGHTEN":
            score_min = af.effective_score_min
        else:
            # Take the most permissive score between activator and filter
            score_min = min(act.effective_score_min, af.effective_score_min)

        # ── Combine: volume_multiplier ────────────────────────────────────────
        # Exclusively from TradeActivator; AF doesn't touch volume
        volume_multiplier = act.effective_vol_mult

        # ── Combine: fee_tolerance ────────────────────────────────────────────
        # Base is SFG_NORMAL_FEE_MAX; tighten when DD is elevated to protect capital
        if dd.tier == "HARD_CUT":
            fee_tolerance = round(cfg.SFG_NORMAL_FEE_MAX * 0.85, 4)
        elif dd.tier == "SOFT_CUT":
            fee_tolerance = round(cfg.SFG_NORMAL_FEE_MAX * 0.90, 4)
        else:
            fee_tolerance = cfg.SFG_NORMAL_FEE_MAX

        result = DynamicThresholds(
            score_min=round(score_min, 4),
            volume_multiplier=round(volume_multiplier, 4),
            fee_tolerance=round(fee_tolerance, 4),
            dd_allowed=dd.allowed,
            dd_size_mult=dd.multiplier,
            tier=act.tier,
            af_state=af.state,
        )

        logger.debug(
            f"[DTP] score_min={result.score_min:.3f} "
            f"vol_mult={result.volume_multiplier:.2f} "
            f"fee_tol={result.fee_tolerance:.2f} "
            f"dd={dd.tier}({result.dd_size_mult:.2f}×) "
            f"tier={result.tier} af={result.af_state}"
        )
        return result

    def summary(self, minutes_no_trade: float = 0.0,
                consecutive_losses: int = 0) -> dict:
        t = self.get(minutes_no_trade, consecutive_losses)
        return {
            "score_min":         t.score_min,
            "volume_multiplier": t.volume_multiplier,
            "fee_tolerance":     t.fee_tolerance,
            "dd_allowed":        t.dd_allowed,
            "dd_size_mult":      t.dd_size_mult,
            "tier":              t.tier,
            "af_state":          t.af_state,
            "module": "DYNAMIC_THRESHOLD_PROVIDER",
            "phase":  5.2,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
dynamic_threshold_provider = DynamicThresholdProvider()
