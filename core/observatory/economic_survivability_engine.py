"""
PHOENIX OBSERVATORY-X — Economic Survivability Engine  [GAP-R2]

Answers: "Is the recommendation profitable AFTER costs?"

Adjusts raw PnL performance for:
  - Trading fees (maker/taker)
  - Bid-ask spread impact
  - Estimated slippage (position size × market impact coefficient)
  - Liquidity penalty (illiquid instruments cost more)

A recommendation that looks profitable in backtest may fail after cost adjustment.
This engine forces that reality check.

Survivability tiers:
  SURVIVES         — positive net PnL after all costs
  MARGINAL         — positive but < cost_floor threshold
  EATEN_BY_COSTS   — positive gross, negative net
  LOSS             — negative gross (costs make it worse)
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


DEFAULT_FEE_RATE       = 0.00075   # 0.075% per side (maker/taker average)
DEFAULT_SPREAD_PCT     = 0.0005    # 0.05% typical spread impact
DEFAULT_SLIPPAGE_COEFF = 0.0002    # 0.02% base slippage
COST_FLOOR_THRESHOLD   = 0.001     # minimum net PnL to be "SURVIVES" not "MARGINAL"

SURVIVABILITY_TIERS = {
    "SURVIVES":       "#22c55e",
    "MARGINAL":       "#fbbf24",
    "EATEN_BY_COSTS": "#f97316",
    "LOSS":           "#f87171",
}


@dataclass
class SurvivabilityRecord:
    rec_id: str
    rec_type: str
    gross_pnl: float
    fee_cost: float
    spread_cost: float
    slippage_cost: float
    liquidity_penalty: float
    net_pnl: float
    survivability: str
    position_size_usd: float
    recorded_at: float = field(default_factory=time.time)


class EconomicSurvivabilityEngine:
    """
    Cost-adjusted profitability analysis per recommendation class.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: List[SurvivabilityRecord] = []

    def compute(
        self,
        rec_id: str,
        rec_type: str,
        gross_pnl: float,
        position_size_usd: float = 1000.0,
        fee_rate: float = DEFAULT_FEE_RATE,
        spread_pct: float = DEFAULT_SPREAD_PCT,
        slippage_coeff: float = DEFAULT_SLIPPAGE_COEFF,
        liquidity_penalty_pct: float = 0.0,
    ) -> SurvivabilityRecord:
        fee_cost       = 2 * fee_rate * position_size_usd          # both sides
        spread_cost    = spread_pct * position_size_usd
        slippage_cost  = slippage_coeff * position_size_usd
        liq_penalty    = liquidity_penalty_pct * position_size_usd
        total_cost     = fee_cost + spread_cost + slippage_cost + liq_penalty
        net_pnl        = gross_pnl - total_cost

        if net_pnl > COST_FLOOR_THRESHOLD:
            survivability = "SURVIVES"
        elif net_pnl > 0:
            survivability = "MARGINAL"
        elif gross_pnl > 0:
            survivability = "EATEN_BY_COSTS"
        else:
            survivability = "LOSS"

        r = SurvivabilityRecord(
            rec_id=rec_id,
            rec_type=rec_type,
            gross_pnl=round(gross_pnl, 6),
            fee_cost=round(fee_cost, 6),
            spread_cost=round(spread_cost, 6),
            slippage_cost=round(slippage_cost, 6),
            liquidity_penalty=round(liq_penalty, 6),
            net_pnl=round(net_pnl, 6),
            survivability=survivability,
            position_size_usd=position_size_usd,
        )
        with self._lock:
            self._records.append(r)
            if len(self._records) > 50_000:
                self._records = self._records[-50_000:]
        return r

    def aggregate_for_type(self, rec_type: str) -> dict:
        with self._lock:
            items = [r for r in self._records if r.rec_type == rec_type]
        if not items:
            return {"rec_type": rec_type, "count": 0, "note": "No data"}
        by_tier: Dict[str, int] = {}
        for r in items:
            by_tier[r.survivability] = by_tier.get(r.survivability, 0) + 1
        net_total = sum(r.net_pnl for r in items)
        gross_total = sum(r.gross_pnl for r in items)
        return {
            "rec_type":          rec_type,
            "count":             len(items),
            "gross_pnl":         round(gross_total, 4),
            "net_pnl":           round(net_total, 4),
            "cost_drag":         round(gross_total - net_total, 4),
            "survival_rate":     round(by_tier.get("SURVIVES", 0) / len(items), 3),
            "by_survivability":  by_tier,
            "verdict":           "VIABLE" if net_total > 0 else "NOT_VIABLE",
        }

    def all_types_summary(self) -> List[dict]:
        with self._lock:
            rec_types = list(set(r.rec_type for r in self._records))
        return sorted(
            [self.aggregate_for_type(rt) for rt in rec_types],
            key=lambda x: x.get("net_pnl", 0),
            reverse=True,
        )

    def cost_breakdown_analysis(self) -> dict:
        with self._lock:
            items = list(self._records)
        if not items:
            return {"note": "No records yet"}
        avg_fee     = sum(r.fee_cost for r in items) / len(items)
        avg_spread  = sum(r.spread_cost for r in items) / len(items)
        avg_slip    = sum(r.slippage_cost for r in items) / len(items)
        avg_liq     = sum(r.liquidity_penalty for r in items) / len(items)
        total_cost  = avg_fee + avg_spread + avg_slip + avg_liq
        return {
            "sample_count":          len(items),
            "avg_fee_cost":          round(avg_fee, 6),
            "avg_spread_cost":       round(avg_spread, 6),
            "avg_slippage_cost":     round(avg_slip, 6),
            "avg_liquidity_penalty": round(avg_liq, 6),
            "avg_total_cost":        round(total_cost, 6),
            "fee_pct_of_total":      round(avg_fee / total_cost * 100, 1) if total_cost else 0,
            "spread_pct_of_total":   round(avg_spread / total_cost * 100, 1) if total_cost else 0,
            "slippage_pct_of_total": round(avg_slip / total_cost * 100, 1) if total_cost else 0,
        }

    def viable_rec_types(self) -> List[str]:
        return [s["rec_type"] for s in self.all_types_summary() if s.get("verdict") == "VIABLE"]


# Singleton
economic_survivability_engine = EconomicSurvivabilityEngine()
