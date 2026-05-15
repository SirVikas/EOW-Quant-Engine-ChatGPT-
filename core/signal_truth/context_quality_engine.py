"""
PRP-001 — Context Quality Engine

Scores market structure context at signal generation time.
Evaluates: volatility compatibility, trend alignment, regime coherence,
and RSI zone quality. Produces a 0.0–1.0 context quality score.

Also tracks whether high-quality contexts produce better outcomes than
low-quality contexts (context discrimination validation).

Forensic outputs:
  05_context_quality_analysis.json
"""
from __future__ import annotations

import time
import threading
from collections import defaultdict, deque
from typing import Dict, Any, Optional, List

from loguru import logger


# ── Score weights ──────────────────────────────────────────────────────────────
W_REGIME_COHERENCE  = 0.30   # does the signal type match the regime?
W_RSI_QUALITY       = 0.30   # is RSI in a high-quality zone for this setup?
W_VOLATILITY_COMPAT = 0.20   # is ATR reasonable for the trade structure?
W_TREND_ALIGNMENT   = 0.20   # does the SMA direction agree with the signal?

# Context quality tiers
HIGH_QUALITY_THRESH = 0.65
LOW_QUALITY_THRESH  = 0.40
MIN_SAMPLE          = 5

# ATR bounds (pct of price): if ATR is too high, context is volatile/dangerous
ATR_SAFE_MAX        = 3.0    # above 3% = risky context
ATR_OPTIMAL_MAX     = 1.5    # below 1.5% = ideal


class ContextQualityEngine:
    """
    PRP-001 context scorer. Thread-safe.
    Scores every signal at generation time and tracks whether
    higher-quality contexts produce better outcomes.
    """

    def __init__(self):
        self._lock = threading.RLock()

        # Pending signals awaiting outcome
        self._pending: Dict[str, Dict[str, Any]] = {}

        # Outcome tracking by context tier
        self._tier_stats: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {"count": 0, "wins": 0, "net_pnl": 0.0}
        )

        # Rolling quality log
        self._quality_log: deque = deque(maxlen=500)

        self._total_scored: int = 0

    # ── Scoring API ────────────────────────────────────────────────────────────

    def score_signal(
        self,
        signal_id:   str,
        regime:      str,
        strategy_id: str,
        side:        str,
        confidence:  float,
        rsi_val:     float,
        above_sma:   bool,
        atr_pct:     float,
    ) -> float:
        """
        Compute and store context quality score for this signal.
        Returns 0.0–1.0 (higher = better context quality).
        """
        with self._lock:
            score = self._compute_score(regime, strategy_id, side, rsi_val, above_sma, atr_pct)
            tier  = self._tier(score)

            self._pending[signal_id] = {
                "regime":      regime,
                "strategy_id": strategy_id,
                "side":        side,
                "score":       score,
                "tier":        tier,
                "rsi_val":     rsi_val,
                "above_sma":   above_sma,
                "atr_pct":     atr_pct,
                "gen_ts":      int(time.time() * 1000),
            }
            self._quality_log.append({
                "signal_id": signal_id, "score": round(score, 3),
                "tier": tier, "regime": regime,
                "rsi": round(rsi_val, 2), "atr_pct": round(atr_pct, 3),
            })
            self._total_scored += 1
            return score

    def record_outcome(
        self,
        signal_id: str,
        was_win:   bool,
        net_pnl:   float,
    ) -> None:
        """Record trade outcome for a previously scored signal."""
        with self._lock:
            ctx = self._pending.pop(signal_id, None)
            if ctx is None:
                return
            tier = ctx["tier"]
            self._tier_stats[tier]["count"] += 1
            self._tier_stats[tier]["net_pnl"] += net_pnl
            if was_win:
                self._tier_stats[tier]["wins"] += 1

    # ── Internal scoring logic ─────────────────────────────────────────────────

    def _compute_score(
        self,
        regime:      str,
        strategy_id: str,
        side:        str,
        rsi_val:     float,
        above_sma:   bool,
        atr_pct:     float,
    ) -> float:
        # Component 1: Regime coherence
        regime_score = self._regime_coherence(regime, strategy_id, side)

        # Component 2: RSI zone quality
        rsi_score = self._rsi_quality(regime, side, rsi_val)

        # Component 3: Volatility compatibility
        vol_score = self._volatility_compat(atr_pct)

        # Component 4: Trend alignment
        trend_score = self._trend_alignment(side, above_sma, regime)

        total = (
            W_REGIME_COHERENCE  * regime_score +
            W_RSI_QUALITY       * rsi_score    +
            W_VOLATILITY_COMPAT * vol_score    +
            W_TREND_ALIGNMENT   * trend_score
        )
        return min(max(round(total, 4), 0.0), 1.0)

    def _regime_coherence(self, regime: str, strategy_id: str, side: str) -> float:
        """Does the signal type match the regime?"""
        if "MEAN_REVERS" in strategy_id.upper() or "MR" in strategy_id.upper():
            # Mean reversion strategies belong in MEAN_REVERTING regime
            return 1.0 if regime == "MEAN_REVERTING" else 0.4
        elif "TREND" in strategy_id.upper() or "TF" in strategy_id.upper():
            # Trend strategies belong in TRENDING regime
            return 1.0 if regime == "TRENDING" else 0.4
        else:
            # Unknown strategy — neutral
            return 0.5

    def _rsi_quality(self, regime: str, side: str, rsi: float) -> float:
        """Is RSI in a quality zone for this setup?"""
        if regime == "MEAN_REVERTING":
            if side == "LONG":
                # Want RSI low and stable — below 30 is ideal
                if rsi < 25:   return 1.0
                elif rsi < 30: return 0.8
                elif rsi < 35: return 0.5
                else:          return 0.1
            else:  # SHORT
                if rsi > 75:   return 1.0
                elif rsi > 70: return 0.8
                elif rsi > 65: return 0.5
                else:          return 0.1
        else:  # TRENDING / UNKNOWN
            if side == "LONG":
                # Want RSI not overbought — below 48 pullback
                if 30 <= rsi <= 45: return 1.0
                elif rsi <= 48:     return 0.7
                elif rsi <= 55:     return 0.4
                else:               return 0.1
            else:  # SHORT
                if 55 <= rsi <= 70: return 1.0
                elif rsi >= 52:     return 0.7
                elif rsi >= 45:     return 0.4
                else:               return 0.1

    def _volatility_compat(self, atr_pct: float) -> float:
        """Is ATR in a range compatible with the trade structure?"""
        if atr_pct <= 0:
            return 0.5   # unknown
        if atr_pct <= ATR_OPTIMAL_MAX:
            return 1.0
        elif atr_pct <= ATR_SAFE_MAX:
            # Linear decline from 1.0 at 1.5% to 0.2 at 3.0%
            return max(0.2, 1.0 - (atr_pct - ATR_OPTIMAL_MAX) / (ATR_SAFE_MAX - ATR_OPTIMAL_MAX) * 0.8)
        else:
            return 0.1   # extremely volatile — poor context

    def _trend_alignment(self, side: str, above_sma: bool, regime: str) -> float:
        """Does SMA direction agree with the signal?"""
        if regime == "MEAN_REVERTING":
            # Counter-trend: we want price ABOVE SMA for SHORT, BELOW for LONG
            if (side == "SHORT" and above_sma) or (side == "LONG" and not above_sma):
                return 1.0
            return 0.3
        else:  # TRENDING
            # With-trend: LONG when above SMA, SHORT when below
            if (side == "LONG" and above_sma) or (side == "SHORT" and not above_sma):
                return 1.0
            return 0.2

    @staticmethod
    def _tier(score: float) -> str:
        if score >= HIGH_QUALITY_THRESH: return "HIGH"
        elif score >= LOW_QUALITY_THRESH: return "MEDIUM"
        else:                             return "LOW"

    # ── Forensic report ────────────────────────────────────────────────────────

    def context_quality_analysis(self) -> Dict[str, Any]:
        """Report 05: Context quality tiers vs outcome win rates."""
        with self._lock:
            tier_breakdown = {}
            for tier, s in self._tier_stats.items():
                count = s["count"]
                tier_breakdown[tier] = {
                    "count":    count,
                    "wins":     s["wins"],
                    "win_rate": round(s["wins"] / count, 4) if count > 0 else 0.0,
                    "avg_pnl":  round(s["net_pnl"] / count, 4) if count > 0 else 0.0,
                }

            discrimination = "INSUFFICIENT_DATA"
            if all(t in tier_breakdown for t in ("HIGH", "LOW")):
                high_wr = tier_breakdown["HIGH"]["win_rate"]
                low_wr  = tier_breakdown["LOW"]["win_rate"]
                if high_wr > low_wr + 0.05:
                    discrimination = "GOOD"
                elif high_wr > low_wr:
                    discrimination = "MARGINAL"
                else:
                    discrimination = "POOR"

            return {
                "report":            "05_context_quality_analysis",
                "prp":               "001",
                "total_scored":      self._total_scored,
                "tier_breakdown":    tier_breakdown,
                "discrimination":    discrimination,
                "recent_quality":    list(self._quality_log)[-20:],
                "ts":                int(time.time() * 1000),
            }

    def get_telemetry(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "module":        "ContextQualityEngine",
                "prp":           "001",
                "total_scored":  self._total_scored,
                "pending":       len(self._pending),
                "tier_stats":    {k: dict(v) for k, v in self._tier_stats.items()},
                "ts":            int(time.time() * 1000),
            }


# ── Singleton ──────────────────────────────────────────────────────────────────
context_quality_engine = ContextQualityEngine()
