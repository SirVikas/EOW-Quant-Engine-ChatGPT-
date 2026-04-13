"""
EOW Quant Engine — Regime AI  (FTD-REF-MASTER-001)
Multi-factor weighted regime classification engine.

Inputs: ADX, ATR%, BB Width, RSI slope
Output: Regime + confidence score (0–1)

This module is a higher-level layer on top of RegimeDetector.
It produces the same Regime enum but with richer confidence scoring
derived from combining all four factors with calibrated weights.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional

from loguru import logger

from core.regime_detector import Regime


# ── Weights (must sum to 1.0) ─────────────────────────────────────────────────
WEIGHTS: Dict[str, float] = {
    "adx":       0.35,
    "atr_pct":   0.25,
    "bb_width":  0.25,
    "rsi_slope": 0.15,
}

# ── Decision thresholds ───────────────────────────────────────────────────────
ADX_TRENDING_MIN      = 20.0   # ADX ≥ 20 → trending evidence
ADX_MEAN_REV_MAX      = 15.0   # ADX < 15 → mean-reversion evidence
ATR_EXPANSION_THRESH  =  0.40  # ATR% > 0.40% → elevated volatility
BB_WIDTH_EXPANSION    =  4.0   # BB Width > 4% → expansion evidence
RSI_SLOPE_BULLISH     =  0.5   # RSI increasing → bullish trend support
RSI_SLOPE_BEARISH     = -0.5   # RSI decreasing → bearish trend support
MIN_CONFIDENCE        =  0.30  # below this → regime is UNKNOWN


@dataclass
class RegimeAiResult:
    regime:     Regime
    confidence: float           # 0.0 – 1.0
    adx_score:  float           # individual factor contribution
    atr_score:  float
    bb_score:   float
    rsi_score:  float
    notes:      str = ""


class RegimeAI:
    """
    Stateless multi-factor regime classifier.
    Call classify() with pre-computed indicator values.
    """

    def classify(
        self,
        adx:      float,
        atr_pct:  float,
        bb_width: float,
        closes:   List[float],   # used to compute RSI slope
        rsi_period: int = 14,
    ) -> RegimeAiResult:
        """
        Compute weighted regime + confidence from four factors.
        Returns RegimeAiResult with regime and per-factor scores.
        """
        rsi_slope = self._rsi_slope(closes, rsi_period)

        # ── Per-factor normalised scores (0–1) ───────────────────────────────
        adx_s   = self._score_adx(adx)
        atr_s   = self._score_atr(atr_pct)
        bb_s    = self._score_bb(bb_width)
        rsi_s   = self._score_rsi(rsi_slope)

        # ── Decision logic (priority order) ──────────────────────────────────
        notes = ""

        # Priority 1: Volatility Expansion
        if atr_pct > ATR_EXPANSION_THRESH and bb_width > BB_WIDTH_EXPANSION:
            regime     = Regime.VOLATILITY_EXPANSION
            confidence = min(0.95, (
                WEIGHTS["atr_pct"]  * atr_s +
                WEIGHTS["bb_width"] * bb_s  +
                WEIGHTS["adx"]      * (1 - adx_s) +   # low ADX supports breakout
                WEIGHTS["rsi_slope"] * 0.5
            ))
            notes = f"ATR%={atr_pct:.2f}>0.40 + BB={bb_width:.2f}>4.0"

        # Priority 2: Trending
        elif adx >= ADX_TRENDING_MIN and abs(rsi_slope) >= abs(RSI_SLOPE_BULLISH):
            regime     = Regime.TRENDING
            confidence = min(0.95, (
                WEIGHTS["adx"]       * adx_s +
                WEIGHTS["rsi_slope"] * abs(rsi_s) +
                WEIGHTS["atr_pct"]   * atr_s +
                WEIGHTS["bb_width"]  * bb_s * 0.5
            ))
            notes = f"ADX={adx:.1f}≥20 + RSI_slope={rsi_slope:.2f}"

        # Priority 3: Mean Reverting
        elif adx < ADX_MEAN_REV_MAX:
            regime     = Regime.MEAN_REVERTING
            confidence = min(0.95, (
                WEIGHTS["adx"]       * (1 - adx_s) +   # low ADX supports MR
                WEIGHTS["bb_width"]  * (1 - bb_s)  +   # narrow bands support MR
                WEIGHTS["atr_pct"]   * (1 - atr_s) +
                WEIGHTS["rsi_slope"] * (1 - abs(rsi_s))
            ))
            notes = f"ADX={adx:.1f}<15 → mean-reversion"

        # Fallback: insufficient evidence
        else:
            regime     = Regime.UNKNOWN
            confidence = 0.0
            notes      = f"ADX={adx:.1f} in ambiguous range"

        # If confidence is too low, demote to UNKNOWN
        if confidence < MIN_CONFIDENCE and regime != Regime.UNKNOWN:
            notes  += f" → demoted (conf={confidence:.2f}<{MIN_CONFIDENCE})"
            regime  = Regime.UNKNOWN

        result = RegimeAiResult(
            regime=regime, confidence=round(confidence, 3),
            adx_score=round(adx_s, 3), atr_score=round(atr_s, 3),
            bb_score=round(bb_s, 3), rsi_score=round(rsi_s, 3),
            notes=notes,
        )
        logger.debug(
            f"[REGIME-AI] → {regime.value} conf={confidence:.2f} | {notes}"
        )
        return result

    # ── Per-factor score functions (0 = low evidence, 1 = high evidence) ─────

    @staticmethod
    def _score_adx(adx: float) -> float:
        """Normalise ADX to 0–1. Peak at ADX=50."""
        return min(1.0, adx / 50.0)

    @staticmethod
    def _score_atr(atr_pct: float) -> float:
        """Normalise ATR%. High ATR → high score → supports volatile/trending."""
        return min(1.0, atr_pct / 1.0)   # 1.0% ATR = max score

    @staticmethod
    def _score_bb(bb_width: float) -> float:
        """Normalise BB width. Wide bands → expansion signal."""
        return min(1.0, bb_width / 8.0)  # 8% width = max score

    @staticmethod
    def _score_rsi(rsi_slope: float) -> float:
        """Normalise RSI slope. Returns signed score (positive = uptrend)."""
        return max(-1.0, min(1.0, rsi_slope / 2.0))

    @staticmethod
    def _rsi_slope(closes: List[float], period: int = 14) -> float:
        """
        Compute RSI slope as (RSI_now - RSI_prev) / period.
        Returns 0.0 if not enough data.
        """
        if len(closes) < period + 2:
            return 0.0

        def _rsi(c: List[float]) -> float:
            gains = [max(c[i] - c[i-1], 0) for i in range(1, len(c))]
            losses = [max(c[i-1] - c[i], 0) for i in range(1, len(c))]
            n = min(period, len(gains))
            avg_gain = sum(gains[-n:]) / n
            avg_loss = sum(losses[-n:]) / n
            if avg_loss == 0:
                return 100.0
            rs = avg_gain / avg_loss
            return 100 - (100 / (1 + rs))

        rsi_now  = _rsi(closes)
        rsi_prev = _rsi(closes[:-1])
        return rsi_now - rsi_prev


# ── Module-level singleton ────────────────────────────────────────────────────
regime_ai = RegimeAI()
