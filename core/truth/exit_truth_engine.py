"""
Exit Truth Engine (XTE) — FTD-PHOENIX-ENTRY-EXIT-TRUTH-ENGINE-001
Phase 1: Advisory Mode — scores open position state, outputs advisory hints.
Does NOT force-close. XTE_FORCE_CLOSE_ENABLED=False by default.

Five sub-engines:
  XTE-01  trend_persistence_score  — continuation probability, momentum decay
  XTE-02  volatility_shift_score   — expansion/compression/exhaustion
  XTE-03  liquidity_exhaustion_score — participation decay, volume collapse
  XTE-04  profit_protection_score  — scale-out, dynamic trailing, BE transitions
  XTE-05  risk_escalation_score    — abnormal movement, shock, structural invalidation

Output: EXIT_TRUTH_SCORE (0-100) + advisory hints dict
High score = hold / let trade run
Low score = tighten / scale out
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from loguru import logger

XTE_WEIGHTS = {
    "trend_persistence":    0.25,
    "volatility_shift":     0.20,
    "liquidity_exhaustion": 0.20,
    "profit_protection":    0.20,
    "risk_escalation":      0.15,
}


@dataclass
class XTEAdvisory:
    """Advisory hints — never enforced, only passed as hints to exit manager."""
    tighten_tsl: bool = False       # suggest tightening trailing stop
    trigger_be:  bool = False       # suggest moving to break-even
    scale_out:   bool = False       # suggest partial exit
    hold:        bool = True        # high-conviction hold


@dataclass
class XTEResult:
    score:                      float
    trend_persistence_score:    float
    volatility_shift_score:     float
    liquidity_exhaustion_score: float
    profit_protection_score:    float
    risk_escalation_score:      float
    advisory:                   XTEAdvisory
    force_close:                bool = False   # always False in Phase 1
    reason:                     str  = ""


class ExitTruthEngine:
    def __init__(self):
        logger.info("[BOOT] EXIT_TRUTH_ENGINE=ACTIVE")
        self._eval_count = 0
        self._last_result: Optional[XTEResult] = None

    # ── XTE-01: Trend Persistence ────────────────────────────────────────────
    def _score_trend_persistence(self, closes: List[float], side: str) -> float:
        if len(closes) < 5:
            return 50.0

        def ema(prices: List[float], period: int) -> float:
            if len(prices) < period:
                return prices[-1] if prices else 0.0
            k = 2.0 / (period + 1)
            val = prices[0]
            for p in prices[1:]:
                val = p * k + val * (1 - k)
            return val

        fast = ema(closes, 5)
        slow = ema(closes, min(20, len(closes)))

        trend_intact = (fast > slow) if side == "LONG" else (fast < slow)

        # Momentum decay: rate of change last 3 vs prior 3
        if len(closes) >= 6:
            recent_roc = (closes[-1] - closes[-4]) / closes[-4] * 100 if closes[-4] != 0 else 0.0
            prior_roc  = (closes[-4] - closes[-7]) / closes[-7] * 100 if len(closes) >= 7 and closes[-7] != 0 else recent_roc
            decaying = abs(recent_roc) < abs(prior_roc) * 0.7
        else:
            decaying = False

        if len(closes) < 20:
            return 50.0

        if trend_intact and not decaying:
            return 80.0
        elif trend_intact and decaying:
            return 60.0
        else:
            return 30.0

    # ── XTE-02: Volatility Shift ─────────────────────────────────────────────
    def _score_volatility_shift(self, atr_pct: float, atr_ema: float) -> float:
        if atr_ema <= 0:
            return 70.0
        ratio = atr_pct / atr_ema
        if ratio > 1.5:
            return 35.0   # expansion — risky to hold
        elif ratio >= 0.8:
            return 70.0   # normal
        else:
            return 80.0   # compression — favorable

    # ── XTE-03: Liquidity Exhaustion ─────────────────────────────────────────
    def _score_liquidity_exhaustion(self, volumes: List[float]) -> float:
        if len(volumes) < 4:
            return 65.0
        recent_avg = sum(volumes[-3:]) / 3
        prior_avg  = sum(volumes[-13:-3]) / min(10, len(volumes) - 3) if len(volumes) >= 4 else recent_avg
        if prior_avg <= 0:
            return 65.0
        ratio = recent_avg / prior_avg
        if ratio < 0.70:
            return 25.0   # declining >30%
        elif ratio <= 1.10:
            return 65.0   # stable
        else:
            return 80.0   # increasing

    # ── XTE-04: Profit Protection ─────────────────────────────────────────────
    def _score_profit_protection(self, current_r: float) -> float:
        if current_r >= 2.0:
            return 85.0
        elif current_r >= 1.0:
            return 70.0
        elif current_r >= 0.5:
            return 55.0
        else:
            return 25.0

    # ── XTE-05: Risk Escalation ───────────────────────────────────────────────
    def _score_risk_escalation(
        self,
        current_r: float,
        peak_r: float,
        atr_pct: float,
        atr_ema: float,
    ) -> float:
        # ATR shock
        if atr_ema > 0 and atr_pct / atr_ema > 2.5:
            return 15.0

        # Drawdown from peak
        drawdown = (peak_r - current_r) / (peak_r + 0.001)
        if drawdown > 0.5 and peak_r > 1.0:
            return 20.0

        return 70.0

    # ── Composite + Advisory ──────────────────────────────────────────────────
    def evaluate(
        self,
        closes: List[float],
        volumes: List[float],
        atr_pct: float,
        atr_ema: float,
        current_r: float,
        peak_r: float,
        side: str,
    ) -> XTEResult:
        try:
            s_trend      = self._score_trend_persistence(closes, side)
            s_vol        = self._score_volatility_shift(atr_pct, atr_ema)
            s_liq        = self._score_liquidity_exhaustion(volumes)
            s_profit     = self._score_profit_protection(current_r)
            s_risk       = self._score_risk_escalation(current_r, peak_r, atr_pct, atr_ema)

            composite = round(
                s_trend  * XTE_WEIGHTS["trend_persistence"]    +
                s_vol    * XTE_WEIGHTS["volatility_shift"]     +
                s_liq    * XTE_WEIGHTS["liquidity_exhaustion"] +
                s_profit * XTE_WEIGHTS["profit_protection"]    +
                s_risk   * XTE_WEIGHTS["risk_escalation"],
                1,
            )

            # Advisory generation
            advisory = XTEAdvisory()
            if composite < 35:
                advisory.tighten_tsl = True
            if composite < 25:
                advisory.scale_out = True
            if s_profit > 80:
                advisory.scale_out = True
            if s_profit > 60:
                advisory.trigger_be = True
            if s_risk < 30:
                advisory.tighten_tsl = True
            if current_r < 0:
                advisory.tighten_tsl = True
            advisory.hold = composite >= 60

            result = XTEResult(
                score=composite,
                trend_persistence_score=s_trend,
                volatility_shift_score=s_vol,
                liquidity_exhaustion_score=s_liq,
                profit_protection_score=s_profit,
                risk_escalation_score=s_risk,
                advisory=advisory,
                force_close=False,  # never True in Phase 1
            )
            self._eval_count += 1
            self._last_result = result
            return result
        except Exception as e:
            logger.warning(f"[XTE] evaluate error: {e}")
            advisory = XTEAdvisory()
            return XTEResult(
                score=50.0,
                trend_persistence_score=50.0,
                volatility_shift_score=50.0,
                liquidity_exhaustion_score=50.0,
                profit_protection_score=50.0,
                risk_escalation_score=50.0,
                advisory=advisory,
                force_close=False,
                reason=f"XTE_ERROR:{e}",
            )

    def summary(self) -> dict:
        r = self._last_result
        return {
            "eval_count": self._eval_count,
            "last_score": r.score if r else None,
            "last_trend_persistence": r.trend_persistence_score if r else None,
            "last_volatility_shift": r.volatility_shift_score if r else None,
            "last_liquidity_exhaustion": r.liquidity_exhaustion_score if r else None,
            "last_profit_protection": r.profit_protection_score if r else None,
            "last_risk_escalation": r.risk_escalation_score if r else None,
            "last_advisory_tighten": r.advisory.tighten_tsl if r else False,
            "last_advisory_hold": r.advisory.hold if r else True,
        }


# Module-level singleton
exit_truth_engine = ExitTruthEngine()
