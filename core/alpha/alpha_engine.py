"""
EOW Quant Engine — FTD-033 / qFTD-033R Part 5: Alpha Engine (Cost-Adjusted)

Responsibilities:
  ✔ Cost-adjusted RR calculation
  ✔ Signal ranking by net edge (not just raw score)
  ✔ Strategy filtering based on cost efficiency
  ✔ Per-symbol high-slippage tracking

Formula (qFTD-033R Q7 upgrade):
  Alpha Score = net_edge_pct × confidence × regime_weight × rr_factor × dd_penalty

  rr_factor   = min(cost_adjusted_rr / ALPHA_RR_BASELINE, ALPHA_RR_FACTOR_CAP)
  dd_penalty  = max(1.0 − drawdown_pct × ALPHA_DD_PENALTY_MULT, 0.3)

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
    _EXPLORATION_MODE    = getattr(cfg, "EXPLORATION_MODE",      True)
    _MAX_COST_PCT        = getattr(cfg, "MAX_COST_PCT",          0.005)
    _ALPHA_RR_BASELINE   = getattr(cfg, "ALPHA_RR_BASELINE",     1.5)
    _ALPHA_RR_FACTOR_CAP = getattr(cfg, "ALPHA_RR_FACTOR_CAP",   2.0)
    _ALPHA_DD_PENALTY_MULT = getattr(cfg, "ALPHA_DD_PENALTY_MULT", 2.0)
except Exception:
    _EXPLORATION_MODE      = True
    _MAX_COST_PCT          = 0.005
    _ALPHA_RR_BASELINE     = 1.5
    _ALPHA_RR_FACTOR_CAP   = 2.0
    _ALPHA_DD_PENALTY_MULT = 2.0


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
    alpha_score:      float        # net_edge_pct × confidence × regime_weight × rr_factor × dd_penalty
    rr_factor:        float = 1.0  # qFTD-033R Q7: cost_adjusted_rr / rr_baseline (capped)
    dd_penalty:       float = 1.0  # qFTD-033R Q7: drawdown dampener [0.3, 1.0]
    approved:         bool  = False
    exploration:      bool  = False
    size_factor:      float = 0.0
    rejection_reason: str   = ""
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
        self._drawdown_pct: float = 0.0   # qFTD-033R Q7: current DD fraction (set by caller)

    def set_drawdown(self, drawdown_pct: float) -> None:
        """qFTD-033R Q7: inject current drawdown fraction (e.g. 0.08 for 8% DD)."""
        self._drawdown_pct = max(0.0, float(drawdown_pct))

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

        # qFTD-033R Q7: RR factor — rewards high-RR setups, penalises low-RR
        rr_baseline   = _ALPHA_RR_BASELINE
        rr_factor     = min(
            decision.cost_adjusted_rr / rr_baseline if rr_baseline > 0 else 1.0,
            _ALPHA_RR_FACTOR_CAP,
        )
        rr_factor = max(rr_factor, 0.1)   # floor: never zero-out a good net_edge

        # qFTD-033R Q7: drawdown penalty — dampen alpha when equity is in drawdown
        dd_penalty = max(1.0 - self._drawdown_pct * _ALPHA_DD_PENALTY_MULT, 0.3)

        # Upgraded formula: net_edge × confidence × regime × rr_factor × dd_penalty
        alpha_score = decision.net_edge_pct * confidence * regime_weight * rr_factor * dd_penalty

        approved    = decision.approved
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
            rr_factor=round(rr_factor, 3),
            dd_penalty=round(dd_penalty, 3),
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
        """Summary for the reporting section (qFTD-033R Q11/Q12 upgrades included)."""
        evals = list(self._recent_evals)
        if not evals:
            return {
                "total_evaluated":          0,
                "positive_net_edge_pct":    0.0,
                "rejected_due_to_cost_pct": 0.0,
                "avg_alpha_score":          0.0,
                "avg_rr_factor":            0.0,
                "avg_dd_penalty":           0.0,
                "high_cost_symbols":        [],
                "symbol_breakdown":         {},
            }

        total    = len(evals)
        positive = sum(1 for e in evals if e.net_edge_decision.raw_result.net_edge > 0)
        rejected_cost = sum(
            1 for e in evals
            if not e.approved and not e.exploration
            and "EDGE" in e.net_edge_decision.verdict
        )
        avg_alpha  = sum(e.alpha_score for e in evals) / total
        avg_rr     = sum(e.rr_factor   for e in evals) / total
        avg_dd_pen = sum(e.dd_penalty  for e in evals) / total

        # Symbol-level cost/rejection breakdown (qFTD-033R Q11)
        sym_stats: dict[str, dict] = {}
        for e in evals:
            s = sym_stats.setdefault(e.symbol, {"total": 0, "approved": 0, "rejected": 0, "total_cost_pct": 0.0})
            s["total"] += 1
            if e.approved or e.exploration:
                s["approved"] += 1
            else:
                s["rejected"] += 1
            s["total_cost_pct"] += e.net_edge_decision.raw_result.cost_breakdown.cost_pct_of_notional
        symbol_breakdown = {
            sym: {
                "total":           v["total"],
                "approved":        v["approved"],
                "rejected":        v["rejected"],
                "approval_pct":    round(v["approved"] / v["total"] * 100, 1),
                "avg_cost_pct":    round(v["total_cost_pct"] / v["total"], 4),
            }
            for sym, v in sorted(sym_stats.items(), key=lambda x: -x[1]["total"])
        }

        return {
            "total_evaluated":          total,
            "positive_net_edge_pct":    round(positive / total * 100, 1),
            "rejected_due_to_cost_pct": round(rejected_cost / total * 100, 1),
            "avg_alpha_score":          round(avg_alpha,  4),
            "avg_rr_factor":            round(avg_rr,     3),
            "avg_dd_penalty":           round(avg_dd_pen, 3),
            "high_cost_symbols":        self.high_cost_symbols(),
            "symbol_breakdown":         symbol_breakdown,
            "strategy_summary":         self.strategy_cost_summary(),
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
alpha_engine = AlphaEngine()
