"""
EOW Quant Engine — FTD-033 Part 2: Net Edge Filter

Thin decision layer that sits between the signal scorer and the execution gate.
Wraps core/cost/cost_engine.evaluate_net_edge() and enforces:

  Signal → Net Edge Filter → APPROVE / EXPLORE / REJECT

Formula:
  net_edge = expected_move - total_cost
  if net_edge_pct < MIN_NET_EDGE → reject (unless exploration allowed)

Config (from config.py):
  COST_MIN_NET_EDGE_PCT   — minimum net edge % to approve (default 0.001 = 0.1%)
  COST_AWARE_TRADING      — master switch; False = skip cost check (testing only)
  EXPLORATION_MODE        — allow EXPLORE verdicts for marginal signals
"""
from __future__ import annotations

from dataclasses import dataclass

from core.cost.cost_engine import (
    NetEdgeResult,
    evaluate_net_edge,
    APPROVE,
    EXPLORE,
    REJECT_NEG_EDGE,
    REJECT_BELOW_THRESH,
)

try:
    from config import cfg
    _COST_AWARE  = getattr(cfg, "COST_AWARE_TRADING",  True)
    _EXPLORE_ON  = getattr(cfg, "EXPLORATION_MODE",    True)
    _MIN_EDGE    = getattr(cfg, "COST_MIN_NET_EDGE_PCT", 0.001)
except Exception:
    _COST_AWARE  = True
    _EXPLORE_ON  = True
    _MIN_EDGE    = 0.001


@dataclass
class NetEdgeDecision:
    """Enriched decision wrapping NetEdgeResult."""
    approved:        bool
    exploration:     bool
    rejected:        bool
    verdict:         str
    rejection_reason: str
    net_edge_pct:    float
    cost_adjusted_rr: float
    size_factor:     float
    raw_result:      NetEdgeResult


class NetEdgeEngine:
    """
    Evaluates whether a signal's expected move justifies its round-trip cost.

    Usage:
        decision = net_edge_engine.evaluate(
            entry_price=100.0,
            take_profit=110.0,
            stop_loss=97.0,
            qty=1.0,
            atr_pct=0.008,
            side="LONG",
        )
        if decision.approved:
            ...proceed to gate...
        elif decision.exploration:
            ...proceed with reduced size...
        else:
            ...log rejection reason...
    """

    def evaluate(
        self,
        entry_price: float,
        take_profit:  float,
        stop_loss:    float,
        qty:          float,
        atr_pct:      float,
        side:         str = "LONG",
    ) -> NetEdgeDecision:
        # Cost-aware trading disabled → always approve (pass-through for tests)
        if not _COST_AWARE:
            dummy = evaluate_net_edge(entry_price, take_profit, stop_loss, qty, atr_pct, side, False)
            return NetEdgeDecision(
                approved=True, exploration=False, rejected=False,
                verdict=APPROVE, rejection_reason="",
                net_edge_pct=dummy.net_edge_pct,
                cost_adjusted_rr=dummy.cost_adjusted_rr,
                size_factor=1.0,
                raw_result=dummy,
            )

        result = evaluate_net_edge(
            entry_price, take_profit, stop_loss, qty, atr_pct, side,
            exploration_mode=_EXPLORE_ON,
        )

        approved   = result.verdict == APPROVE
        exploration = result.verdict == EXPLORE
        rejected   = result.verdict in (REJECT_NEG_EDGE, REJECT_BELOW_THRESH)

        return NetEdgeDecision(
            approved=approved,
            exploration=exploration,
            rejected=rejected,
            verdict=result.verdict,
            rejection_reason=result.rejection_reason,
            net_edge_pct=result.net_edge_pct,
            cost_adjusted_rr=result.cost_adjusted_rr,
            size_factor=result.size_factor,
            raw_result=result,
        )

    def batch_evaluate(self, signals: list[dict]) -> list[NetEdgeDecision]:
        """
        Evaluate a list of signal dicts.
        Each dict must have: entry_price, take_profit, stop_loss, qty, atr_pct, side.
        Returns decisions in the same order, best net_edge first.
        """
        decisions = []
        for sig in signals:
            d = self.evaluate(
                entry_price=sig["entry_price"],
                take_profit=sig["take_profit"],
                stop_loss=sig["stop_loss"],
                qty=sig["qty"],
                atr_pct=sig.get("atr_pct", 0.005),
                side=sig.get("side", "LONG"),
            )
            decisions.append(d)
        # Rank: approved first, then exploration, then rejected; within group by net_edge desc
        decisions.sort(key=lambda d: (0 if d.approved else 1 if d.exploration else 2, -d.net_edge_pct))
        return decisions


# ── Singleton ─────────────────────────────────────────────────────────────────
net_edge_engine = NetEdgeEngine()
