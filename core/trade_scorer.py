"""
EOW Quant Engine — Phase 4: Trade Scorer (Alpha Quality Engine)
Assigns a composite confidence score (0–1) to every trade candidate.

Scoring factors and weights:
  Regime alignment     25%  — TRENDING/VE scores higher than MR/UNKNOWN
  Volume strength      20%  — current volume vs avg (capped at 3x)
  Trend strength ADX   20%  — ADX normalised 0–60
  Momentum RSI slope   15%  — rate of RSI change in signal direction
  Volatility expansion 10%  — current ATR vs average ATR
  Cost efficiency      10%  — 1 − (cost / MAX_COST_FRACTION)

Rule: IF score < MIN_TRADE_SCORE (0.60) → REJECT TRADE
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from loguru import logger

from config import cfg


# ── Factor weights (must sum to 1.0) ─────────────────────────────────────────
WEIGHTS: Dict[str, float] = {
    "regime_alignment": 0.25,
    "volume_strength":  0.20,
    "adx_trend":        0.20,
    "rsi_momentum":     0.15,
    "vol_expansion":    0.10,
    "cost_efficiency":  0.10,
}

# Regime → alignment sub-score
_REGIME_SCORE: Dict[str, float] = {
    "TRENDING":             1.00,
    "VOLATILITY_EXPANSION": 0.90,
    "MEAN_REVERTING":       0.70,
    "UNKNOWN":              0.40,
}


@dataclass
class ScoreResult:
    ok:        bool
    score:     float
    breakdown: dict
    reason:    str = ""


class TradeScorer:
    """
    Scores every trade candidate on 6 alpha factors before execution.
    Trades scoring below MIN_TRADE_SCORE are rejected.
    """

    def __init__(self):
        self.min_score = cfg.MIN_TRADE_SCORE
        logger.info(f"[TRADE-SCORER] Phase 4 activated | min_score={self.min_score}")

    def score(
        self,
        regime:       str,
        adx:          float,
        rsi:          float,
        rsi_prev:     float,
        atr_pct:      float,
        avg_atr_pct:  float,   # baseline ATR% (pass atr_pct itself when unknown)
        vol_ratio:    float,   # current_volume / avg_volume
        cost_fraction: float,  # round-trip cost / gross TP
        signal_side:  str,     # "LONG" or "SHORT"
    ) -> ScoreResult:
        """
        Returns ScoreResult(ok=True, score=…) when trade meets quality threshold.
        All sub-scores are clamped to [0, 1].
        """
        # 1. Regime alignment (25%)
        s_regime = _REGIME_SCORE.get(regime, 0.40)

        # 2. Volume strength (20%) — ratio capped at 3x for normalisation
        s_volume = min(vol_ratio / 3.0, 1.0) if vol_ratio > 0 else 0.0

        # 3. Trend strength ADX (20%) — normalised over 0–60 range
        s_adx = min(adx / 60.0, 1.0)

        # 4. RSI momentum slope (15%) — directional RSI acceleration
        rsi_slope = rsi - rsi_prev
        if signal_side == "LONG":
            s_rsi = min(max(rsi_slope / 10.0, 0.0), 1.0)
        else:
            s_rsi = min(max(-rsi_slope / 10.0, 0.0), 1.0)

        # 5. Volatility expansion (10%) — ATR above its baseline
        if avg_atr_pct > 0:
            expansion = atr_pct / avg_atr_pct
            # Score ramps 0→1 as expansion goes from 0.8x to 2.0x baseline
            s_vol_exp = min(max((expansion - 0.8) / 1.2, 0.0), 1.0)
        else:
            s_vol_exp = 0.50  # neutral when no baseline available

        # 6. Cost efficiency (10%) — lower cost relative to cap = better
        s_cost = max(1.0 - (cost_fraction / cfg.MAX_COST_FRACTION), 0.0)

        breakdown = {
            "regime_alignment": round(s_regime, 3),
            "volume_strength":  round(s_volume, 3),
            "adx_trend":        round(s_adx, 3),
            "rsi_momentum":     round(s_rsi, 3),
            "vol_expansion":    round(s_vol_exp, 3),
            "cost_efficiency":  round(s_cost, 3),
        }

        composite = round(
            s_regime  * WEIGHTS["regime_alignment"]
            + s_volume  * WEIGHTS["volume_strength"]
            + s_adx     * WEIGHTS["adx_trend"]
            + s_rsi     * WEIGHTS["rsi_momentum"]
            + s_vol_exp * WEIGHTS["vol_expansion"]
            + s_cost    * WEIGHTS["cost_efficiency"],
            4,
        )

        if composite < self.min_score:
            return ScoreResult(
                ok=False, score=composite, breakdown=breakdown,
                reason=f"LOW_SCORE({composite:.3f}<{self.min_score})",
            )

        return ScoreResult(ok=True, score=composite, breakdown=breakdown)

    def summary(self) -> dict:
        return {
            "min_score": self.min_score,
            "weights":   WEIGHTS,
            "module":    "TRADE_SCORER",
            "phase":     4,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
trade_scorer = TradeScorer()
