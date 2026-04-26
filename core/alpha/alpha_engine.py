"""
EOW Quant Engine — FTD-033 Part 5: Alpha Engine (Cost-Adjusted)

Responsibilities:
  ✔ Cost-adjusted RR calculation
  ✔ Signal ranking by net edge (not just raw score)
  ✔ Strategy filtering based on cost efficiency
  ✔ Per-symbol high-slippage tracking

Formula:
  Alpha Score = (Expected Move – Cost) × Confidence × Regime Weight

This layer sits after the signal scorer and before the execution gate.
It does NOT replace strategies/alpha_engine.py (which generates raw signals)
— it post-processes them with cost awareness.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Optional

from core.alpha.net_edge_engine import net_edge_engine, NetEdgeDecision

try:
    from config import cfg
    _EXPLORATION_MODE = getattr(cfg, "EXPLORATION_MODE", True)
    _MAX_COST_PCT     = getattr(cfg, "MAX_COST_PCT", 0.005)
except Exception:
    _EXPLORATION_MODE = True
    _MAX_COST_PCT     = 0.005


@dataclass
class AlphaSignalEval:
    """Result of cost-adjusted alpha evaluation for one signal."""
    symbol:           str
    side:             str
    signal_type:      str
    raw_score:        float
    confidence:       float
    regime_weight:    float
    net_edge_decision: NetEdgeDecision
    alpha_score:      float        # (net_edge_pct - cost_pct) × confidence × regime_weight
    approved:         bool
    exploration:      bool
    size_factor:      float
    rejection_reason: str = ""
    timestamp:        float = field(default_factory=time.time)


@dataclass
class SymbolCostStats:
    """Per-symbol cost efficiency tracking."""
    symbol:          str
    trades:          int   = 0
    total_cost_pct:  float = 0.0
    total_slippage:  float = 0.0
    high_cost_count: int   = 0

    @property
    def avg_cost_pct(self) -> float:
        return (self.total_cost_pct / self.trades) if self.trades else 0.0

    @property
    def is_high_cost(self) -> bool:
        return self.avg_cost_pct > _MAX_COST_PCT * 100


class AlphaEngine:
    """
    Cost-adjusted alpha evaluator.

    Accepts raw signal parameters, applies the net edge filter, then
    computes an alpha_score that incorporates cost, confidence, and regime.

    Usage:
        eval = alpha_engine.evaluate(
            symbol="ETHUSDT", side="LONG", signal_type="TCB",
            entry_price=2500.0, take_profit=2750.0, stop_loss=2400.0,
            qty=0.04, atr_pct=0.012,
            raw_score=0.72, confidence=0.85, regime_weight=1.0,
        )
        if eval.approved:
            place_order(size=base_qty * eval.size_factor)
    """

    HISTORY_WINDOW = 50

    def __init__(self):
        self._symbol_stats: dict[str, SymbolCostStats] = defaultdict(
            lambda: SymbolCostStats(symbol="")
        )
        self._recent_evals: deque[AlphaSignalEval] = deque(maxlen=500)

    # ── Core evaluation ───────────────────────────────────────────────────────

    def evaluate(
        self,
        symbol:        str,
        side:          str,
        signal_type:   str,
        entry_price:   float,
        take_profit:   float,
        stop_loss:     float,
        qty:           float,
        atr_pct:       float,
        raw_score:     float       = 0.60,
        confidence:    float       = 0.70,
        regime_weight: float       = 1.0,
    ) -> AlphaSignalEval:
        """Evaluate a signal with full cost adjustment."""
        decision: NetEdgeDecision = net_edge_engine.evaluate(
            entry_price=entry_price,
            take_profit=take_profit,
            stop_loss=stop_loss,
            qty=qty,
            atr_pct=atr_pct,
            side=side,
        )

        # Alpha Score = (net_edge_pct) × confidence × regime_weight
        # Negative net_edge → negative alpha_score (penalizes bad setups)
        alpha_score = decision.net_edge_pct * confidence * regime_weight

        approved   = decision.approved
        exploration = decision.exploration and _EXPLORATION_MODE

        # Track per-symbol cost stats
        cb = decision.raw_result.cost_breakdown
        stats = self._symbol_stats[symbol]
        stats.symbol = symbol
        stats.trades += 1
        stats.total_cost_pct  += cb.cost_pct_of_notional
        stats.total_slippage  += (cb.slippage_entry + cb.slippage_exit)
        if cb.cost_pct_of_notional > _MAX_COST_PCT * 100:
            stats.high_cost_count += 1

        result = AlphaSignalEval(
            symbol=symbol,
            side=side,
            signal_type=signal_type,
            raw_score=raw_score,
            confidence=confidence,
            regime_weight=regime_weight,
            net_edge_decision=decision,
            alpha_score=round(alpha_score, 4),
            approved=approved,
            exploration=exploration,
            size_factor=decision.size_factor if (approved or exploration) else 0.0,
            rejection_reason=decision.rejection_reason,
        )
        self._recent_evals.append(result)
        return result

    def rank_signals(self, evals: list[AlphaSignalEval]) -> list[AlphaSignalEval]:
        """Sort signals by alpha_score descending (best first)."""
        return sorted(evals, key=lambda e: -e.alpha_score)

    # ── Analytics ─────────────────────────────────────────────────────────────

    def high_cost_symbols(self) -> list[str]:
        """Return symbols with above-threshold average cost."""
        return [sym for sym, s in self._symbol_stats.items() if s.is_high_cost]

    def strategy_cost_summary(self) -> dict:
        """Aggregate cost stats by strategy type from recent evals."""
        strategy_stats: dict[str, dict] = defaultdict(lambda: {"count": 0, "total_alpha": 0.0, "approved": 0})
        for e in self._recent_evals:
            s = strategy_stats[e.signal_type]
            s["count"]       += 1
            s["total_alpha"] += e.alpha_score
            s["approved"]    += 1 if e.approved else 0
        return {
            k: {
                "count":    v["count"],
                "avg_alpha": round(v["total_alpha"] / v["count"], 4) if v["count"] else 0.0,
                "approval_rate_pct": round(v["approved"] / v["count"] * 100, 1) if v["count"] else 0.0,
            }
            for k, v in strategy_stats.items()
        }

    def net_edge_summary(self) -> dict:
        """Summary for the reporting section."""
        evals = list(self._recent_evals)
        if not evals:
            return {
                "total_evaluated":        0,
                "positive_net_edge_pct":  0.0,
                "rejected_due_to_cost_pct": 0.0,
                "avg_alpha_score":        0.0,
                "high_cost_symbols":      [],
            }

        total    = len(evals)
        positive = sum(1 for e in evals if e.net_edge_decision.raw_result.net_edge > 0)
        rejected_cost = sum(
            1 for e in evals
            if not e.approved and not e.exploration
            and "EDGE" in e.net_edge_decision.verdict
        )
        avg_alpha = sum(e.alpha_score for e in evals) / total

        return {
            "total_evaluated":          total,
            "positive_net_edge_pct":    round(positive / total * 100, 1),
            "rejected_due_to_cost_pct": round(rejected_cost / total * 100, 1),
            "avg_alpha_score":          round(avg_alpha, 4),
            "high_cost_symbols":        self.high_cost_symbols(),
            "strategy_summary":         self.strategy_cost_summary(),
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
alpha_engine = AlphaEngine()
