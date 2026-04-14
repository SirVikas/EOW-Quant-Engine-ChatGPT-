"""
EOW Quant Engine — Regime AI  (FTD-REF-023 upgraded)
Multi-factor weighted regime classification engine.

Upgrades over MASTER-001:
  1. UNKNOWN fallback — if classification is UNKNOWN, reuse last valid regime
     with a confidence penalty (×0.70) so the engine keeps trading.
  2. Market stability factor — scales confidence based on ATR% volatility:
       high ATR%  → stability is LOW  → confidence boosted  (more decisive)
       low ATR%   → stability is HIGH → confidence reduced  (be cautious)

Inputs: ADX, ATR%, BB Width, RSI slope
Output: RegimeAiResult (regime, confidence, factor scores, stability_factor)
"""
from __future__ import annotations

from dataclasses import dataclass, field
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
ADX_TRENDING_MIN      = 20.0
ADX_MEAN_REV_MAX      = 15.0
ATR_EXPANSION_THRESH  =  0.40
BB_WIDTH_EXPANSION    =  4.0
RSI_SLOPE_BULLISH     =  0.5
MIN_CONFIDENCE        =  0.30   # below this → demote to UNKNOWN

# ── Fallback & stability ──────────────────────────────────────────────────────
FALLBACK_CONF_PENALTY = 0.70   # multiply confidence by this on UNKNOWN fallback
ATR_HIGH_THRESH       =  0.50  # ATR% above this → high volatility regime
ATR_LOW_THRESH        =  0.10  # ATR% below this → low volatility (cautious)
STAB_BOOST            =  1.15  # confidence multiplier in high-vol environment
STAB_REDUCE           =  0.85  # confidence multiplier in low-vol environment


@dataclass
class RegimeAiResult:
    regime:           Regime
    confidence:       float           # 0.0 – 1.0 (after stability scaling)
    adx_score:        float
    atr_score:        float
    bb_score:         float
    rsi_score:        float
    stability_factor: float = 1.0    # applied multiplier
    fallback_used:    bool  = False   # True when last_valid_regime was used
    notes:            str   = ""


class RegimeAI:
    """
    Stateful multi-factor regime classifier.
    Maintains per-symbol last-valid-regime cache for UNKNOWN fallback.
    """

    def __init__(self):
        # symbol → last non-UNKNOWN RegimeAiResult
        self._last_valid: Dict[str, RegimeAiResult] = {}

    def classify(
        self,
        adx:        float,
        atr_pct:    float,
        bb_width:   float,
        closes:     List[float],
        rsi_period: int = 14,
        symbol:     str = "",   # used for per-symbol fallback cache
    ) -> RegimeAiResult:
        """
        Classify market regime with weighted confidence + stability scaling.
        Falls back to last valid regime when classification is UNKNOWN.
        """
        rsi_slope = self._rsi_slope(closes, rsi_period)

        # ── Per-factor scores ────────────────────────────────────────────────
        adx_s = self._score_adx(adx)
        atr_s = self._score_atr(atr_pct)
        bb_s  = self._score_bb(bb_width)
        rsi_s = self._score_rsi(rsi_slope)

        notes = ""

        # ── Decision logic ────────────────────────────────────────────────────
        # Priority 1: Volatility Expansion
        if atr_pct > ATR_EXPANSION_THRESH and bb_width > BB_WIDTH_EXPANSION:
            regime = Regime.VOLATILITY_EXPANSION
            confidence = min(0.95, (
                WEIGHTS["atr_pct"]   * atr_s +
                WEIGHTS["bb_width"]  * bb_s  +
                WEIGHTS["adx"]       * (1 - adx_s) +
                WEIGHTS["rsi_slope"] * 0.5
            ))
            notes = f"ATR%={atr_pct:.2f}>0.40 + BB={bb_width:.2f}>4.0"

        # Priority 2: Trending
        elif adx >= ADX_TRENDING_MIN and abs(rsi_slope) >= abs(RSI_SLOPE_BULLISH):
            regime = Regime.TRENDING
            confidence = min(0.95, (
                WEIGHTS["adx"]       * adx_s +
                WEIGHTS["rsi_slope"] * abs(rsi_s) +
                WEIGHTS["atr_pct"]   * atr_s +
                WEIGHTS["bb_width"]  * bb_s * 0.5
            ))
            notes = f"ADX={adx:.1f}≥20 + RSI_slope={rsi_slope:.2f}"

        # Priority 3: Mean Reverting
        elif adx < ADX_MEAN_REV_MAX:
            regime = Regime.MEAN_REVERTING
            confidence = min(0.95, (
                WEIGHTS["adx"]       * (1 - adx_s) +
                WEIGHTS["bb_width"]  * (1 - bb_s)  +
                WEIGHTS["atr_pct"]   * (1 - atr_s) +
                WEIGHTS["rsi_slope"] * (1 - abs(rsi_s))
            ))
            notes = f"ADX={adx:.1f}<15 → mean-reversion"

        else:
            regime     = Regime.UNKNOWN
            confidence = 0.0
            notes      = f"ADX={adx:.1f} in ambiguous range"

        # Demote low-confidence results
        if confidence < MIN_CONFIDENCE and regime != Regime.UNKNOWN:
            notes  += f" → demoted (conf={confidence:.2f}<{MIN_CONFIDENCE})"
            regime  = Regime.UNKNOWN

        # ── D. Dynamic market stability factor ────────────────────────────────
        # High volatility → more decisive → boost confidence
        # Low volatility  → less reliable → reduce confidence
        if atr_pct >= ATR_HIGH_THRESH:
            stability_factor = STAB_BOOST
        elif atr_pct <= ATR_LOW_THRESH:
            stability_factor = STAB_REDUCE
        else:
            stability_factor = 1.0

        confidence = min(0.95, confidence * stability_factor)

        # ── C. UNKNOWN fallback — reuse last valid regime ─────────────────────
        fallback_used = False
        if regime == Regime.UNKNOWN and symbol in self._last_valid:
            prev = self._last_valid[symbol]
            regime        = prev.regime
            confidence    = round(prev.confidence * FALLBACK_CONF_PENALTY, 3)
            fallback_used = True
            notes        += f" | FALLBACK→{regime.value} conf×{FALLBACK_CONF_PENALTY}"
            logger.debug(
                f"[REGIME-AI] {symbol} UNKNOWN → fallback {regime.value} "
                f"conf={confidence:.2f}"
            )

        result = RegimeAiResult(
            regime=regime,
            confidence=round(confidence, 3),
            adx_score=round(adx_s, 3),
            atr_score=round(atr_s, 3),
            bb_score=round(bb_s, 3),
            rsi_score=round(rsi_s, 3),
            stability_factor=round(stability_factor, 3),
            fallback_used=fallback_used,
            notes=notes,
        )

        # Cache last valid (non-fallback) result
        if regime != Regime.UNKNOWN and not fallback_used:
            self._last_valid[symbol] = result

        logger.debug(
            f"[REGIME-AI] {symbol or '?'} → {regime.value} "
            f"conf={result.confidence:.2f} stab={stability_factor:.2f} | {notes}"
        )
        return result

    # ── Factor scoring ────────────────────────────────────────────────────────

    @staticmethod
    def _score_adx(adx: float) -> float:
        return min(1.0, adx / 50.0)

    @staticmethod
    def _score_atr(atr_pct: float) -> float:
        return min(1.0, atr_pct / 1.0)

    @staticmethod
    def _score_bb(bb_width: float) -> float:
        return min(1.0, bb_width / 8.0)

    @staticmethod
    def _score_rsi(rsi_slope: float) -> float:
        return max(-1.0, min(1.0, rsi_slope / 2.0))

    @staticmethod
    def _rsi_slope(closes: List[float], period: int = 14) -> float:
        if len(closes) < period + 2:
            return 0.0

        def _rsi(c: List[float]) -> float:
            gains  = [max(c[i] - c[i-1], 0) for i in range(1, len(c))]
            losses = [max(c[i-1] - c[i], 0) for i in range(1, len(c))]
            n = min(period, len(gains))
            avg_gain = sum(gains[-n:]) / n
            avg_loss = sum(losses[-n:]) / n
            if avg_loss == 0:
                return 100.0
            return 100 - (100 / (1 + avg_gain / avg_loss))

        return _rsi(closes) - _rsi(closes[:-1])


# ── Module-level singleton ────────────────────────────────────────────────────
regime_ai = RegimeAI()
