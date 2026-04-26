"""
EOW Quant Engine — FTD-033 Part 7: Cost-Aware Learning Adapter

Learns from CostTradeRecords to identify:
  ✔ Which trades are cost-inefficient (fee drag > expected gain)
  ✔ Which symbols generate high slippage consistently
  ✔ Which patterns are net-negative after costs

Outputs:
  Pattern: "Low RR + High Fee" → confidence ↓
  Symbol: "BTCUSDT" → avg_slippage_pct HIGH (0.12%)

Integrates with:
  - core/learning_memory/negative_memory.py (failure blacklist)
  - core/cost/cost_engine.CostTradeRecord (input records)
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Optional


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class CostPattern:
    """Identified cost-inefficiency pattern."""
    pattern_key:   str      # e.g. "Low_RR+High_Fee", "High_Slippage:BTCUSDT"
    count:         int = 0
    net_pnl_sum:   float = 0.0
    confidence:    float = 1.0   # decays toward 0 as pattern persists
    last_seen:     float = field(default_factory=time.time)
    is_blacklisted: bool = False

    @property
    def avg_net_pnl(self) -> float:
        return (self.net_pnl_sum / self.count) if self.count else 0.0

    @property
    def is_negative(self) -> bool:
        return self.avg_net_pnl < 0 and self.count >= 5


@dataclass
class SymbolSlippageStats:
    """Per-symbol slippage accumulator."""
    symbol:            str
    observations:      int   = 0
    total_slippage_pct: float = 0.0
    max_slippage_pct:  float = 0.0
    flagged:           bool  = False

    @property
    def avg_slippage_pct(self) -> float:
        return (self.total_slippage_pct / self.observations) if self.observations else 0.0


# ── Adapter ───────────────────────────────────────────────────────────────────

class CostLearningAdapter:
    """
    Post-trade cost learning engine.

    Called after each trade closes with a completed CostTradeRecord.
    Maintains rolling pattern memory and symbol slippage stats.

    Usage:
        cost_learning_adapter.record(cost_trade_record)
        summary = cost_learning_adapter.summary()
        blacklist = cost_learning_adapter.get_blacklisted_patterns()
    """

    HIGH_SLIPPAGE_THRESHOLD_PCT = 0.08   # flag symbol if avg slippage > 0.08%
    BLACKLIST_MIN_COUNT         = 10     # pattern needs 10 trades to be blacklisted
    BLACKLIST_LOSS_THRESHOLD    = -0.50  # avg net PnL must be < -0.50 USDT

    def __init__(self):
        self._patterns:  dict[str, CostPattern]       = {}
        self._symbols:   dict[str, SymbolSlippageStats] = defaultdict(
            lambda: SymbolSlippageStats(symbol="")
        )
        self._recent_records: deque = deque(maxlen=200)

    # ── Public API ────────────────────────────────────────────────────────────

    def record(self, cost_record) -> None:
        """
        Process a completed CostTradeRecord.

        cost_record is a core.cost.cost_engine.CostTradeRecord instance.
        This adapter uses duck-typing to avoid circular imports.
        """
        self._recent_records.append(cost_record)

        # Skip records without outcomes yet
        if cost_record.outcome_net_pnl is None:
            return

        net_pnl = cost_record.outcome_net_pnl
        cb      = cost_record.cost_breakdown
        symbol  = cost_record.symbol
        rr      = cost_record.cost_adjusted_rr

        # ── Pattern detection ─────────────────────────────────────────────────
        patterns_for_record = []

        # Low RR + High Fee
        if rr < 1.0 and cb.cost_pct_of_notional > 0.04:
            patterns_for_record.append("Low_RR+High_Fee")

        # High slippage pattern
        slippage_pct = (cb.slippage_entry + cb.slippage_exit) / max(cb.total_cost, 1e-9) * cb.cost_pct_of_notional
        if slippage_pct > self.HIGH_SLIPPAGE_THRESHOLD_PCT:
            patterns_for_record.append(f"High_Slippage:{symbol}")

        # Net negative after costs
        if net_pnl < 0 and cost_record.cost_adjusted_rr < 0:
            patterns_for_record.append(f"Net_Negative:{cost_record.strategy_id}")

        # Exploration that was unprofitable
        if cost_record.exploration and net_pnl < 0:
            patterns_for_record.append("Exploration_Loss")

        for key in patterns_for_record:
            p = self._patterns.setdefault(key, CostPattern(pattern_key=key))
            p.count       += 1
            p.net_pnl_sum += net_pnl
            p.last_seen    = time.time()
            # Decay confidence as pattern repeats negatively
            if net_pnl < 0:
                p.confidence = max(0.1, p.confidence * 0.95)
            else:
                p.confidence = min(1.0, p.confidence * 1.02)
            # Auto-blacklist persistent losers
            if (p.count >= self.BLACKLIST_MIN_COUNT
                    and p.avg_net_pnl < self.BLACKLIST_LOSS_THRESHOLD):
                p.is_blacklisted = True

        # ── Symbol slippage tracking ──────────────────────────────────────────
        s_stats = self._symbols[symbol]
        s_stats.symbol = symbol
        s_stats.observations += 1
        slip_total = cb.slippage_entry + cb.slippage_exit
        slip_pct_of_notional = slip_total / max(
            1.0, (cb.total_cost / max(cb.cost_pct_of_notional / 100, 1e-6))
        ) * 100
        s_stats.total_slippage_pct += cb.cost_pct_of_notional
        s_stats.max_slippage_pct    = max(s_stats.max_slippage_pct, cb.cost_pct_of_notional)
        if s_stats.avg_slippage_pct > self.HIGH_SLIPPAGE_THRESHOLD_PCT:
            s_stats.flagged = True

    def get_blacklisted_patterns(self) -> list[str]:
        """Return patterns that are currently blacklisted."""
        return [k for k, p in self._patterns.items() if p.is_blacklisted]

    def get_confidence_adjustment(self, strategy_id: str, symbol: str) -> float:
        """
        Return a confidence multiplier (0.1–1.0) for a strategy+symbol pair.
        Lower means the pattern has been costly historically.
        """
        min_conf = 1.0
        for key, pattern in self._patterns.items():
            if strategy_id in key or symbol in key:
                min_conf = min(min_conf, pattern.confidence)
        return min_conf

    def high_slippage_symbols(self) -> list[str]:
        """Return symbols with above-threshold average cost."""
        return [sym for sym, s in self._symbols.items() if s.flagged]

    def summary(self) -> dict:
        """Aggregated learning summary for reporting."""
        total_records  = len(self._recent_records)
        neg_patterns   = [p for p in self._patterns.values() if p.is_negative]
        blacklisted    = [p for p in self._patterns.values() if p.is_blacklisted]
        high_slip_syms = self.high_slippage_symbols()

        pattern_rows = sorted(
            self._patterns.values(),
            key=lambda p: p.avg_net_pnl
        )[:10]

        return {
            "total_records":     total_records,
            "patterns_tracked":  len(self._patterns),
            "negative_patterns": len(neg_patterns),
            "blacklisted":       len(blacklisted),
            "blacklisted_keys":  [p.pattern_key for p in blacklisted],
            "high_slippage_symbols": high_slip_syms,
            "pattern_summary": [
                {
                    "key":         p.pattern_key,
                    "count":       p.count,
                    "avg_net_pnl": round(p.avg_net_pnl, 4),
                    "confidence":  round(p.confidence, 3),
                    "blacklisted": p.is_blacklisted,
                }
                for p in pattern_rows
            ],
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
cost_learning_adapter = CostLearningAdapter()
