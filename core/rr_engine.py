"""
EOW Quant Engine — Phase 4: RR Engine (Risk-Reward Enforcement)
Enforces minimum Risk-Reward ratio BEFORE trade execution.

Rule: IF (TP_distance / SL_distance) < MIN_RR_RATIO → REJECT TRADE

Volatility scaling:
  High volatility (atr_pct > 2.0%) → widen TP by 20%
  Low  volatility (atr_pct < 0.5%) → tighten SL by 20%
"""
from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

from config import cfg


@dataclass
class RRResult:
    ok:          bool
    rr:          float
    adjusted_tp: float
    adjusted_sl: float
    reason:      str = ""


class RREngine:
    """
    Enforces minimum Risk-Reward before trade execution.
    Returns adjusted TP/SL after volatility scaling.
    """

    def __init__(self):
        self.min_rr = cfg.MIN_RR_RATIO
        logger.info(f"[RR-ENGINE] Phase 4 activated | min_rr={self.min_rr}")

    def evaluate(
        self,
        side:       str,    # "LONG" or "SHORT"
        entry:      float,
        stop_loss:  float,
        take_profit: float,
        atr:        float,
        atr_pct:    float,  # ATR as % of price
    ) -> RRResult:
        """
        Validates and optionally adjusts TP/SL for volatility.
        Returns RRResult(ok=True) when adjusted RR meets minimum threshold.
        """
        sl_dist = abs(entry - stop_loss)
        tp_dist = abs(take_profit - entry)

        if sl_dist <= 0:
            return RRResult(
                ok=False, rr=0.0,
                adjusted_tp=take_profit, adjusted_sl=stop_loss,
                reason="ZERO_SL_DISTANCE",
            )

        adj_tp = take_profit
        adj_sl = stop_loss

        # High volatility: widen TP to capture larger moves
        if atr_pct > 2.0:
            if side == "LONG":
                adj_tp = entry + tp_dist * 1.20
            else:
                adj_tp = entry - tp_dist * 1.20

        # Low volatility: tighten SL to improve RR in quiet markets
        elif atr_pct < 0.5:
            if side == "LONG":
                adj_sl = entry - sl_dist * 0.80
            else:
                adj_sl = entry + sl_dist * 0.80

        adj_sl_dist = abs(entry - adj_sl)
        adj_tp_dist = abs(adj_tp - entry)
        rr = adj_tp_dist / adj_sl_dist if adj_sl_dist > 0 else 0.0

        if rr < self.min_rr:
            return RRResult(
                ok=False, rr=round(rr, 3),
                adjusted_tp=adj_tp, adjusted_sl=adj_sl,
                reason=f"RR_BELOW_MIN({rr:.2f}<{self.min_rr})",
            )

        return RRResult(
            ok=True, rr=round(rr, 3),
            adjusted_tp=adj_tp, adjusted_sl=adj_sl,
        )

    def summary(self) -> dict:
        return {"min_rr": self.min_rr, "module": "RR_ENGINE", "phase": 4}


# ── Module-level singleton ────────────────────────────────────────────────────
rr_engine = RREngine()
