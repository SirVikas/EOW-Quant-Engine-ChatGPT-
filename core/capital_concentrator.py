"""
EOW Quant Engine — Phase 7: Capital Concentrator
Allocates more capital to top-ranked trades based on TradeRanker rank_score.

Rank bands → size multiplier:
  0.60–0.70  → 0.5× base risk  (LOW)
  0.70–0.80  → 1.0× base risk  (MID)
  0.80–0.90  → 1.5× base risk  (HIGH)
  > 0.90     → 2.0× base risk  (ELITE)

Safety constraints (always enforced, override any boost):
  • CC_MAX_POSITION_PCT — hard cap as % of equity per trade
  • DD + Loss Cluster multipliers are applied before this module
  • result multiplier is never > CC_MULT_ELITE (2.0×)

Decision chain position: after TradeRanker, before Execution.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from loguru import logger

from config import cfg


# Band definitions: (min_rank_inclusive, max_rank_exclusive, multiplier, label)
_BANDS = [
    (cfg.CC_BAND_ELITE_MIN, 1.01,                cfg.CC_MULT_ELITE, "ELITE"),
    (cfg.CC_BAND_HIGH_MIN,  cfg.CC_BAND_HIGH_MAX, cfg.CC_MULT_HIGH,  "HIGH"),
    (cfg.CC_BAND_MID_MIN,   cfg.CC_BAND_MID_MAX,  cfg.CC_MULT_MID,   "MID"),
    (cfg.CC_BAND_LOW_MIN,   cfg.CC_BAND_LOW_MAX,  cfg.CC_MULT_LOW,   "LOW"),
]


@dataclass
class ConcentrationResult:
    ok:             bool      # False → blocked (rank below minimum band)
    size_multiplier: float
    band:           str       # "ELITE" | "HIGH" | "MID" | "LOW" | "REJECT"
    capped:         bool      # True if equity cap was applied
    max_risk_usdt:  float
    reason:         str = ""


class CapitalConcentrator:
    """
    Concentrates capital on high-rank trades; starves low-rank trades.
    Must be called after TradeRanker and after DD/LossCluster adjustments.

    The upstream size_mult (from CapitalAllocator + DrawdownController +
    LossCluster) is passed in so this module applies a *further* concentration
    layer on top — it never bypasses upstream safety reductions.
    """

    def __init__(self):
        self._daily_risk_used: float = 0.0
        self._current_day: int = int(time.time()) // 86400
        logger.info(
            f"[CAPITAL-CONCENTRATOR] Phase 7 activated | "
            f"bands: LOW={cfg.CC_MULT_LOW}× MID={cfg.CC_MULT_MID}× "
            f"HIGH={cfg.CC_MULT_HIGH}× ELITE={cfg.CC_MULT_ELITE}× | "
            f"max_pos={cfg.CC_MAX_POSITION_PCT:.0%}"
        )

    def _reset_daily_if_needed(self):
        today = int(time.time()) // 86400
        if today != self._current_day:
            self._daily_risk_used = 0.0
            self._current_day = today

    def concentrate(
        self,
        rank_score:       float,
        equity:           float,
        base_risk_usdt:   float,
        upstream_mult:    float = 1.0,
        ev:               float = 0.0,   # Phase 7B: direct EV for secondary sizing
    ) -> ConcentrationResult:
        """
        Compute concentrated size multiplier based on rank_score.

        Args:
            rank_score:     from TradeRanker.rank() (0–1)
            equity:         current account equity (USDT)
            base_risk_usdt: raw risk USDT before any multiplier
            upstream_mult:  combined multiplier from DD+LossCluster+CapAllocator
                            (applied first; concentration multiplier is additive
                            on top within safety caps)
            ev:             Phase 7B — direct EV value; applies an additional
                            boost/penalty on proposed_risk after band selection

        Returns ConcentrationResult; ok=False → skip trade.
        """
        self._reset_daily_if_needed()

        # Find band
        band_mult = 0.0
        band_label = "REJECT"
        for lo, hi, mult, label in _BANDS:
            if lo <= rank_score < hi:
                band_mult = mult
                band_label = label
                break

        if band_mult == 0.0:
            reason = f"CC_REJECT(rank={rank_score:.3f} below all bands)"
            logger.debug(f"[CAPITAL-CONCENTRATOR] {reason}")
            return ConcentrationResult(
                ok=False, size_multiplier=0.0, band="REJECT",
                capped=False, max_risk_usdt=0.0, reason=reason,
            )

        # Proposed risk = base × upstream_mult × concentration_mult
        proposed_risk = base_risk_usdt * upstream_mult * band_mult

        # Phase 7B: direct EV boost/penalty applied after band selection
        ev_boost = 1.0
        if ev > cfg.P7B_EV_HIGH_THRESHOLD:
            ev_boost = cfg.P7B_EV_CC_BOOST
        elif ev < cfg.P7B_EV_LOW_THRESHOLD:
            ev_boost = cfg.P7B_EV_CC_PENALTY
        proposed_risk = proposed_risk * ev_boost

        # Hard cap: max % equity per trade
        max_trade_risk = equity * cfg.CC_MAX_POSITION_PCT
        capped = proposed_risk > max_trade_risk
        final_risk = min(proposed_risk, max_trade_risk)

        # Derived final multiplier (for informational reporting)
        if base_risk_usdt > 0:
            final_mult = final_risk / base_risk_usdt
        else:
            final_mult = band_mult * upstream_mult

        reason = (
            f"CC_{band_label}(rank={rank_score:.3f} → {band_mult}× "
            f"× upstream={upstream_mult:.2f}× × ev_boost={ev_boost:.2f}× = {final_mult:.2f}×"
            + (" [CAPPED]" if capped else "")
            + ")"
        )
        logger.debug(f"[CAPITAL-CONCENTRATOR] {reason}")

        return ConcentrationResult(
            ok=True,
            size_multiplier=round(final_mult, 4),
            band=band_label,
            capped=capped,
            max_risk_usdt=round(final_risk, 4),
            reason=reason,
        )

    def record_risk_used(self, risk_usdt: float):
        self._reset_daily_if_needed()
        self._daily_risk_used += risk_usdt

    def summary(self) -> dict:
        return {
            "bands": {
                "ELITE": f"≥{cfg.CC_BAND_ELITE_MIN} → {cfg.CC_MULT_ELITE}×",
                "HIGH":  f"{cfg.CC_BAND_HIGH_MIN}–{cfg.CC_BAND_HIGH_MAX} → {cfg.CC_MULT_HIGH}×",
                "MID":   f"{cfg.CC_BAND_MID_MIN}–{cfg.CC_BAND_MID_MAX} → {cfg.CC_MULT_MID}×",
                "LOW":   f"{cfg.CC_BAND_LOW_MIN}–{cfg.CC_BAND_LOW_MAX} → {cfg.CC_MULT_LOW}×",
            },
            "max_position_pct": cfg.CC_MAX_POSITION_PCT,
            "daily_risk_used":  round(self._daily_risk_used, 4),
            "module": "CAPITAL_CONCENTRATOR",
            "phase":  7,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
capital_concentrator = CapitalConcentrator()
