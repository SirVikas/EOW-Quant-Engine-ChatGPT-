"""
EOW Quant Engine — Phase 5: Adaptive Scorer (Dynamic Intelligence)
Replaces static factor weights in trade_scorer with self-adjusting weights
that evolve from real trade outcomes.

Mechanism:
  After each closed trade the scorer updates factor weights using:
    weight_i += LR × outcome × factor_score_i   (outcome: +1=win, −1=loss)
  Weights are then clipped to [MIN_WEIGHT, MAX_WEIGHT] and re-normalised.

This ensures factors that correctly predict winning trades gain influence
while factors correlating with losses lose influence over time.

Bootstrap: starts with the same weights as Phase 4 trade_scorer.
The interface is a drop-in replacement for TradeScorer.score().
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Optional

from loguru import logger

from config import cfg


# ── Starting weights (Phase 4 baseline) ──────────────────────────────────────
_INITIAL_WEIGHTS: Dict[str, float] = {
    "regime_alignment": 0.25,
    "volume_strength":  0.20,
    "adx_trend":        0.20,
    "rsi_momentum":     0.15,
    "vol_expansion":    0.10,
    "cost_efficiency":  0.10,
}

_REGIME_SCORE: Dict[str, float] = {
    "TRENDING":             1.00,
    "VOLATILITY_EXPANSION": 0.90,
    "MEAN_REVERTING":       0.70,
    "UNKNOWN":              0.55,  # raised 0.40→0.55 — mirrors trade_scorer; UNKNOWN is now rare
}


@dataclass
class AdaptiveScoreResult:
    ok:        bool
    score:     float
    breakdown: dict
    weights:   dict   # current live weights
    reason:    str = ""


class AdaptiveScorer:
    """
    Drop-in replacement for TradeScorer with self-adjusting factor weights.
    Stores pending factor scores per symbol to enable post-trade weight updates.
    """

    def __init__(self):
        self._weights: Dict[str, float] = dict(_INITIAL_WEIGHTS)
        self._pending: Dict[str, dict]  = {}   # symbol → last factor breakdown
        self._n_updates: int = 0
        self.min_score = cfg.MIN_TRADE_SCORE
        self._lr       = cfg.ADAPTIVE_LR
        self._w_min    = cfg.ADAPTIVE_MIN_WEIGHT
        self._w_max    = cfg.ADAPTIVE_MAX_WEIGHT
        logger.info(
            f"[ADAPTIVE-SCORER] Phase 5 activated | "
            f"min_score={self.min_score} lr={self._lr} "
            f"w_range=[{self._w_min},{self._w_max}]"
        )

    # ── Scoring ───────────────────────────────────────────────────────────────

    def score(
        self,
        symbol:        str,
        regime:        str,
        adx:           float,
        rsi:           float,
        rsi_prev:      float,
        atr_pct:       float,
        avg_atr_pct:   float,
        vol_ratio:     float,
        cost_fraction: float,
        signal_side:   str,
    ) -> AdaptiveScoreResult:
        """
        Computes composite score using current adaptive weights.
        Stores factor breakdown per symbol for later weight update on trade close.
        """
        # ── Sub-scores (identical computation to TradeScorer) ─────────────────
        s_regime = _REGIME_SCORE.get(regime, 0.40)
        s_volume = min(vol_ratio / 3.0, 1.0) if vol_ratio > 0 else 0.0
        s_adx    = min(adx / 60.0, 1.0)

        rsi_slope = rsi - rsi_prev
        if signal_side == "LONG":
            s_rsi = min(max(rsi_slope / 10.0, 0.0), 1.0)
        else:
            s_rsi = min(max(-rsi_slope / 10.0, 0.0), 1.0)

        if avg_atr_pct > 0:
            s_vol_exp = min(max((atr_pct / avg_atr_pct - 0.8) / 1.2, 0.0), 1.0)
        else:
            s_vol_exp = 0.50

        s_cost = max(1.0 - (cost_fraction / cfg.MAX_COST_FRACTION), 0.0)

        breakdown = {
            "regime_alignment": round(s_regime, 3),
            "volume_strength":  round(s_volume, 3),
            "adx_trend":        round(s_adx, 3),
            "rsi_momentum":     round(s_rsi, 3),
            "vol_expansion":    round(s_vol_exp, 3),
            "cost_efficiency":  round(s_cost, 3),
        }

        w = self._weights
        composite = round(
            s_regime  * w["regime_alignment"]
            + s_volume  * w["volume_strength"]
            + s_adx     * w["adx_trend"]
            + s_rsi     * w["rsi_momentum"]
            + s_vol_exp * w["vol_expansion"]
            + s_cost    * w["cost_efficiency"],
            4,
        )

        # Store breakdown so record_outcome() can update weights on close
        self._pending[symbol] = breakdown

        if composite < self.min_score:
            return AdaptiveScoreResult(
                ok=False, score=composite, breakdown=breakdown,
                weights=dict(self._weights),
                reason=f"ADAPTIVE_LOW_SCORE({composite:.3f}<{self.min_score})",
            )

        return AdaptiveScoreResult(
            ok=True, score=composite, breakdown=breakdown,
            weights=dict(self._weights),
        )

    # ── Weight updates ────────────────────────────────────────────────────────

    def record_outcome(self, symbol: str, won: bool):
        """
        Update factor weights based on the trade outcome for this symbol.
        Call from the on_tick position-close handler.
        outcome: +1 = win, −1 = loss
        """
        breakdown = self._pending.pop(symbol, None)
        if breakdown is None:
            return  # no pending score (e.g. position opened before this scorer started)

        outcome = 1.0 if won else -1.0
        for factor, score in breakdown.items():
            if factor not in self._weights:
                continue
            self._weights[factor] += self._lr * outcome * score

        self._clip_and_normalise()
        self._n_updates += 1
        logger.debug(
            f"[ADAPTIVE-SCORER] weight update #{self._n_updates} "
            f"{'WIN' if won else 'LOSS'} {symbol} → "
            + " ".join(f"{k}={v:.3f}" for k, v in self._weights.items())
        )

    # ── Inspection ────────────────────────────────────────────────────────────

    def current_weights(self) -> dict:
        return dict(self._weights)

    def n_updates(self) -> int:
        return self._n_updates

    def summary(self) -> dict:
        return {
            "weights":    {k: round(v, 4) for k, v in self._weights.items()},
            "n_updates":  self._n_updates,
            "min_score":  self.min_score,
            "lr":         self._lr,
            "w_range":    [self._w_min, self._w_max],
            "module":     "ADAPTIVE_SCORER",
            "phase":      5,
        }

    # ── Internals ────────────────────────────────────────────────────────────

    def _clip_and_normalise(self):
        """
        Project weights onto the box-constrained simplex.
        Iterates clip→normalize until all weights satisfy [min, max] bounds.
        Converges because the feasible set is non-empty (n×min < 1 < n×max).
        """
        keys = list(self._weights.keys())
        vals = [self._weights[k] for k in keys]
        for _ in range(50):
            total = sum(vals)
            if total > 0:
                vals = [v / total for v in vals]
            vals = [max(self._w_min, min(self._w_max, v)) for v in vals]
            if all(self._w_min - 1e-9 <= v <= self._w_max + 1e-9 for v in vals):
                break
        for k, v in zip(keys, vals):
            self._weights[k] = round(v, 6)


# ── Module-level singleton ────────────────────────────────────────────────────
adaptive_scorer = AdaptiveScorer()
