"""
Entry Truth Engine (ETE) — FTD-PHOENIX-ENTRY-EXIT-TRUTH-ENGINE-001
Phase 1: Observation Mode — scores every trade entry, does NOT block.
Gate enforcement controlled by config.ETE_GATE_ENABLED (default False).

Six sub-engines:
  ETE-01  structure_score    — swing high/low, BOS, CHOCH, range vs trend
  ETE-02  regime_score       — regime type quality (TRENDING/MR/COMPRESSION/EXPANSION)
  ETE-03  momentum_score     — trend strength, velocity, acceleration, persistence
  ETE-04  volatility_score   — ATR state, compression/expansion, shock detection
  ETE-05  liquidity_score    — relative volume, participation quality
  ETE-06  cost_score         — fee burden, RR efficiency, spread cost

Final: ENTRY_TRUTH_SCORE = weighted sum (see weights below)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import math

from loguru import logger

# Component weights (sum = 1.0)
WEIGHTS = {
    "structure":  0.20,
    "regime":     0.20,
    "momentum":   0.15,
    "volatility": 0.15,
    "liquidity":  0.15,
    "cost":       0.15,
}


@dataclass
class ETEResult:
    score:            float          # 0-100 composite
    structure_score:  float          # 0-100
    regime_score:     float          # 0-100
    momentum_score:   float          # 0-100
    volatility_score: float          # 0-100
    liquidity_score:  float          # 0-100
    cost_score:       float          # 0-100
    gate_enabled:     bool           # True when ETE is in gate mode
    blocked:          bool           # True only if gate_enabled AND score < threshold
    reason:           str = ""
    component_detail: dict = field(default_factory=dict)


class EntryTruthEngine:
    def __init__(self):
        logger.info("[BOOT] ENTRY_TRUTH_ENGINE=ACTIVE")
        self._eval_count = 0
        self._last_result: Optional[ETEResult] = None

    # ── ETE-01: Structure Score ──────────────────────────────────────────────
    def _score_structure(
        self,
        closes: List[float],
        highs: List[float],
        lows: List[float],
    ) -> float:
        if len(closes) < 4 or len(highs) < 4 or len(lows) < 4:
            return 50.0

        score = 0.0
        window = min(20, len(closes))
        recent_c = closes[-window:]
        recent_h = highs[-window:]
        recent_l = lows[-window:]

        # Find swing highs/lows over ±3 bars in last 20 bars
        swing_highs = []
        swing_lows = []
        for i in range(3, len(recent_h) - 3):
            if all(recent_h[i] >= recent_h[j] for j in range(i - 3, i + 4) if j != i):
                swing_highs.append(recent_h[i])
            if all(recent_l[i] <= recent_l[j] for j in range(i - 3, i + 4) if j != i):
                swing_lows.append(recent_l[i])

        last_price = closes[-1]

        # BOS / CHOCH
        if swing_highs and last_price > swing_highs[-1]:
            score += 30  # BOS confirmed
        elif swing_lows and last_price < swing_lows[-1]:
            score += 10  # CHOCH (mean reversion setup)

        # Range analysis
        range_pct = (max(recent_h) - min(recent_l)) / last_price * 100 if last_price > 0 else 0.0
        if range_pct < 1.5:
            score += 20   # compression
        elif range_pct <= 4.0:
            score += 15   # normal
        else:
            score += 5    # wide

        # Trend state
        if len(recent_c) >= 20:
            ma10 = sum(recent_c[-10:]) / 10
            ma10_prev = sum(recent_c[-20:-10]) / 10
            if last_price > ma10 and ma10 > ma10_prev:
                score += 20  # uptrend

        return max(0.0, min(100.0, score))

    # ── ETE-02: Regime Score ─────────────────────────────────────────────────
    def _score_regime(self, regime: str) -> float:
        mapping = {
            "TRENDING":          85.0,
            "EXPANSION":         75.0,
            "MEAN_REVERTING":    60.0,
            "LOW_VOLATILITY":    40.0,
            "HIGH_VOLATILITY":   30.0,
            "COMPRESSION":       50.0,
            "UNKNOWN":           35.0,
        }
        return mapping.get(regime, 35.0)

    # ── ETE-03: Momentum Score ───────────────────────────────────────────────
    def _score_momentum(self, closes: List[float]) -> float:
        if len(closes) < 6:
            return 50.0

        score = 0.0
        c = closes

        # Velocity: 5-bar price change
        velocity = (c[-1] - c[-5]) / c[-5] * 100 if c[-5] != 0 else 0.0

        if abs(velocity) > 1.5:
            score += 40
        elif abs(velocity) >= 0.5:
            score += 25
        else:
            score += 10

        # Acceleration (need 10 bars)
        if len(c) >= 10:
            prev_velocity = (c[-5] - c[-10]) / c[-10] * 100 if c[-10] != 0 else 0.0
            acceleration = velocity - prev_velocity
            score += 30 if acceleration > 0 else 10
        else:
            score += 20  # neutral if insufficient data

        # Persistence: how many of last 5 bars moved in same direction as c[-1] vs c[-6]
        if len(c) >= 6:
            direction = 1 if c[-1] > c[-6] else -1
            persistent_bars = sum(
                1 for i in range(-5, 0)
                if (c[i] - c[i - 1]) * direction > 0
            )
            if persistent_bars >= 4:
                score += 30
            elif persistent_bars >= 3:
                score += 20
            else:
                score += 10
        else:
            score += 20

        return max(0.0, min(100.0, score))

    # ── ETE-04: Volatility Score ─────────────────────────────────────────────
    def _score_volatility(self, atr_pct: float, atr_ema: float) -> float:
        if atr_ema <= 0:
            return 50.0
        ratio = atr_pct / atr_ema
        if ratio > 2.5:
            return 10.0
        elif ratio > 2.0:
            return 25.0
        elif ratio >= 1.5:
            return 45.0
        elif ratio >= 1.0:
            return 70.0
        else:
            return 85.0  # compression

    # ── ETE-05: Liquidity Score ──────────────────────────────────────────────
    def _score_liquidity(self, volumes: List[float]) -> float:
        if not volumes:
            return 50.0

        avg_vol = sum(volumes[-20:]) / min(20, len(volumes))
        if avg_vol <= 0:
            return 50.0

        rv = volumes[-1] / avg_vol
        if rv > 3.0:
            score = 90.0
        elif rv >= 2.0:
            score = 80.0
        elif rv >= 1.5:
            score = 70.0
        elif rv >= 1.0:
            score = 55.0
        elif rv >= 0.5:
            score = 40.0
        else:
            score = 20.0

        # Volume trend: last 3 vs prev 3
        if len(volumes) >= 6:
            recent_avg = sum(volumes[-3:]) / 3
            prev_avg = sum(volumes[-6:-3]) / 3
            if prev_avg > 0 and recent_avg > prev_avg:
                score += 10

        return max(0.0, min(100.0, score))

    # ── ETE-06: Cost Score ───────────────────────────────────────────────────
    def _score_cost(self, fee_cost: float, gross_tp: float, rr: float) -> float:
        if gross_tp <= 0:
            return 60.0

        fee_ratio = fee_cost / gross_tp
        if fee_ratio < 0.05:
            score = 95.0
        elif fee_ratio < 0.10:
            score = 85.0
        elif fee_ratio < 0.15:
            score = 75.0
        elif fee_ratio < 0.20:
            score = 60.0
        elif fee_ratio < 0.25:
            score = 45.0
        elif fee_ratio <= 0.35:
            score = 30.0
        else:
            score = 15.0

        # RR bonus
        if rr >= 3.0:
            score += 10
        elif rr >= 2.0:
            score += 5

        return max(0.0, min(100.0, score))

    # ── Composite Evaluation ─────────────────────────────────────────────────
    def evaluate(
        self,
        closes: List[float],
        highs: List[float],
        lows: List[float],
        volumes: List[float],
        atr_pct: float,
        atr_ema: float,
        regime: str,
        fee_cost: float,
        gross_tp: float,
        rr: float,
        signal_side: str,
        gate_enabled: bool = False,
        min_score: float = 45.0,
    ) -> ETEResult:
        try:
            s_structure  = self._score_structure(closes, highs, lows)
            s_regime     = self._score_regime(regime)
            s_momentum   = self._score_momentum(closes)
            s_volatility = self._score_volatility(atr_pct, atr_ema)
            s_liquidity  = self._score_liquidity(volumes)
            s_cost       = self._score_cost(fee_cost, gross_tp, rr)

            composite = round(
                s_structure  * WEIGHTS["structure"]  +
                s_regime     * WEIGHTS["regime"]     +
                s_momentum   * WEIGHTS["momentum"]   +
                s_volatility * WEIGHTS["volatility"] +
                s_liquidity  * WEIGHTS["liquidity"]  +
                s_cost       * WEIGHTS["cost"],
                1,
            )

            # Gate enforcement is always False in Phase 1 (ETE_GATE_ENABLED=False)
            blocked = gate_enabled and composite < min_score

            self._eval_count += 1
            result = ETEResult(
                score=composite,
                structure_score=s_structure,
                regime_score=s_regime,
                momentum_score=s_momentum,
                volatility_score=s_volatility,
                liquidity_score=s_liquidity,
                cost_score=s_cost,
                gate_enabled=gate_enabled,
                blocked=blocked,
                reason="ETE_GATE_BLOCKED" if blocked else "",
                component_detail={
                    "structure":  s_structure,
                    "regime":     s_regime,
                    "momentum":   s_momentum,
                    "volatility": s_volatility,
                    "liquidity":  s_liquidity,
                    "cost":       s_cost,
                },
            )
            self._last_result = result
            return result
        except Exception as e:
            logger.warning(f"[ETE] evaluate error: {e}")
            return ETEResult(
                score=50.0,
                structure_score=50.0,
                regime_score=50.0,
                momentum_score=50.0,
                volatility_score=50.0,
                liquidity_score=50.0,
                cost_score=50.0,
                gate_enabled=gate_enabled,
                blocked=False,
                reason=f"ETE_ERROR:{e}",
            )

    def summary(self) -> dict:
        r = self._last_result
        return {
            "eval_count": self._eval_count,
            # diagnose.py reads "total_evaluated" — keep both keys in sync
            "total_evaluated": self._eval_count,
            "last_score": r.score if r else None,
            "last_structure": r.structure_score if r else None,
            "last_regime": r.regime_score if r else None,
            "last_momentum": r.momentum_score if r else None,
            "last_volatility": r.volatility_score if r else None,
            "last_liquidity": r.liquidity_score if r else None,
            "last_cost": r.cost_score if r else None,
            "last_blocked": r.blocked if r else False,
        }


# Module-level singleton
entry_truth_engine = EntryTruthEngine()
