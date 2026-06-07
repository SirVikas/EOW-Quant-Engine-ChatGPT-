"""
EOW Quant Engine — Phase 5.1: Trade Flow Monitor
Ensures healthy trading frequency by tracking activity and rejection patterns.

Metrics (rolling TFM_WINDOW_MIN window):
  - trades_per_hour:    completed trades in window, scaled to 1 hour
  - signals_per_hour:   signals evaluated (before any gate)
  - rejection_rate:     skips / (skips + trades), fraction 0–1
  - minutes_since_last_trade: global time since last successful trade
  - top_rejection_reasons: top-5 block causes (for diagnostics)

Stage-2 Visibility (qFTD-STAGE2-VISIBILITY-001):
  Instruments the silent drop between Ecology approval and LeanGate.
  Call record_ecology_approved() when ecology says approved=True.
  Call record_stage2_none() when strategy.generate_signal() returns NONE.
  The gap between these two counters is the previously invisible drop zone.

Integration: passive observer — never blocks trades. Call record_signal(),
record_trade(), record_skip() at the appropriate points. Use summary() for
/api/status to expose trading health in real time.
"""
from __future__ import annotations

import time
from collections import deque, defaultdict
from dataclasses import dataclass, field
from typing import Deque, Dict, List

from loguru import logger

from config import cfg


@dataclass
class FlowStats:
    trades_per_hour:          float
    signals_per_hour:         float
    rejection_rate:           float   # 0–1 fraction
    minutes_since_last_trade: float
    top_reasons:              dict    # reason_key → count, top 5


@dataclass
class Stage2NoneEvent:
    """One Signal.NONE event from strategy.generate_signal() after ecology approval."""
    ts:            float
    symbol:        str
    strategy:      str
    regime:        str
    reason:        str    # which condition failed (EMA_CROSS, TREND_FILTER, RSI_ZONE, etc.)
    rsi:           float
    above_sma:     bool


class TradeFlowMonitor:
    """
    Rolling-window trade activity and rejection tracker.
    All methods are O(1) amortised — safe to call on every tick.
    """

    def __init__(self):
        self._window_sec = cfg.TFM_WINDOW_MIN * 60
        self._trade_ts:  Deque[float] = deque()
        self._signal_ts: Deque[float] = deque()
        self._skip_ts:   Deque[float] = deque()
        self._skip_reasons: Dict[str, int] = defaultdict(int)
        self._boot_ts: float = time.time()   # qFTD-032: track session start for anti-idle
        self._last_trade_ts: float = 0.0

        # ── Stage-2 Visibility counters (qFTD-STAGE2-VISIBILITY-001) ──────────
        # Session-total counters (never pruned — full session history)
        self._s2_ecology_approved:  int = 0   # ecology said approved=True
        self._s2_strategy_none:     int = 0   # strategy returned Signal.NONE after approval
        self._s2_alpha_none:        int = 0   # alpha engine also produced nothing
        self._s2_reached_leangate:  int = 0   # signal survived Stage-2 and entered LeanGate
        self._s2_none_reasons:  Dict[str, int] = defaultdict(int)   # why strategy returned NONE
        self._s2_none_by_sym:   Dict[str, int] = defaultdict(int)   # per-symbol NONE count
        self._s2_none_by_strat: Dict[str, int] = defaultdict(int)   # per-strategy NONE count
        self._s2_none_by_regime:Dict[str, int] = defaultdict(int)   # per-regime NONE count
        self._s2_recent_nones:  deque = deque(maxlen=50)            # last 50 Stage-2 NONE events

        logger.info(
            f"[FLOW-MONITOR] Phase 5.1 activated | "
            f"window={cfg.TFM_WINDOW_MIN}min | "
            f"stage2_visibility=ON (qFTD-STAGE2-VISIBILITY-001)"
        )

    # ── Recording ─────────────────────────────────────────────────────────────

    def record_signal(self, symbol: str):
        """Call when a signal candidate enters the pipeline."""
        self._signal_ts.append(time.time())

    def record_trade(self, symbol: str):
        """Call when a trade is successfully placed."""
        now = time.time()
        self._trade_ts.append(now)
        self._last_trade_ts = now
        logger.debug(f"[FLOW-MONITOR] trade recorded: {symbol}")

    def record_skip(self, symbol: str, reason: str):
        """Call when a signal is blocked by any gate."""
        now = time.time()
        self._skip_ts.append(now)
        # Aggregate by first token of reason for clean bucketing
        key = reason.split("(")[0].strip()
        self._skip_reasons[key] += 1

    # ── Stage-2 Visibility (qFTD-STAGE2-VISIBILITY-001) ──────────────────────

    def record_ecology_approved(self, symbol: str, strategy: str, regime: str):
        """Call immediately after ecology returns approved=True — before strategy.generate_signal()."""
        self._s2_ecology_approved += 1

    def record_stage2_none(
        self,
        symbol:   str,
        strategy: str,
        regime:   str,
        reason:   str,
        rsi:      float = 0.0,
        above_sma: bool = False,
    ):
        """
        Call when strategy.generate_signal() returns Signal.NONE after ecology approved.
        reason must be one of: EMA_CROSS_MISSING, TREND_FILTER_FAIL, RSI_ZONE_FAIL,
        RSI_DIRECTION_FAIL, BB_ZONE_FAIL, VOL_EXPANSION_FAIL, UNKNOWN.
        """
        self._s2_strategy_none += 1
        key = reason.split("(")[0].strip()
        self._s2_none_reasons[key]        += 1
        self._s2_none_by_sym[symbol]      += 1
        self._s2_none_by_strat[strategy]  += 1
        self._s2_none_by_regime[regime]   += 1
        self._s2_recent_nones.append(Stage2NoneEvent(
            ts=time.time(), symbol=symbol, strategy=strategy,
            regime=regime, reason=reason, rsi=rsi, above_sma=above_sma,
        ))

    def record_alpha_none(self, symbol: str, strategy: str, regime: str):
        """Call when alpha engine also produces nothing after strategy was NONE."""
        self._s2_alpha_none += 1

    def record_reached_leangate(self, symbol: str, strategy: str):
        """Call when a signal survives Stage-2 and enters LeanGate evaluation."""
        self._s2_reached_leangate += 1

    # ── Querying ──────────────────────────────────────────────────────────────

    def minutes_since_last_trade(self) -> float:
        """Minutes elapsed since the last trade.
        Uses session boot time when no trade has occurred yet so the Trade
        Activator can relax volume/score filters even before the first trade.
        """
        if self._last_trade_ts == 0.0:
            # qFTD-032: returning 0 here caused a permanent NORMAL-tier deadlock —
            # Trade Activator never relaxed because it always saw 0 minutes idle.
            return (time.time() - self._boot_ts) / 60.0
        return (time.time() - self._last_trade_ts) / 60.0

    def get_stats(self) -> FlowStats:
        """Compute rolling-window statistics."""
        cutoff = time.time() - self._window_sec
        self._prune(cutoff)

        trades  = len(self._trade_ts)
        signals = len(self._signal_ts)
        skips   = len(self._skip_ts)

        window_hours     = cfg.TFM_WINDOW_MIN / 60.0
        trades_per_hour  = trades  / window_hours
        signals_per_hour = signals / window_hours
        rejection_rate   = skips / (skips + trades) if (skips + trades) > 0 else 0.0

        top_reasons = dict(
            sorted(self._skip_reasons.items(), key=lambda x: -x[1])[:5]
        )

        return FlowStats(
            trades_per_hour=round(trades_per_hour, 2),
            signals_per_hour=round(signals_per_hour, 2),
            rejection_rate=round(rejection_rate, 4),
            minutes_since_last_trade=round(self.minutes_since_last_trade(), 1),
            top_reasons=top_reasons,
        )

    def stage2_summary(self) -> dict:
        """Stage-2 visibility report — the previously invisible drop zone."""
        approved  = self._s2_ecology_approved
        s2_none   = self._s2_strategy_none
        alpha_none= self._s2_alpha_none
        reached   = self._s2_reached_leangate

        # Conversion rates
        none_rate = s2_none / approved if approved > 0 else 0.0
        pass_rate = reached / approved if approved > 0 else 0.0

        recent = [
            {
                "symbol":   e.symbol,
                "strategy": e.strategy,
                "regime":   e.regime,
                "reason":   e.reason,
                "rsi":      round(e.rsi, 1),
                "above_sma":e.above_sma,
            }
            for e in list(self._s2_recent_nones)[-20:]
        ]

        return {
            "stage":                    2,
            "description":              "Strategy signal generation — between ecology and LeanGate",
            "ecology_approved_total":   approved,
            "strategy_none_total":      s2_none,
            "alpha_none_total":         alpha_none,
            "reached_leangate_total":   reached,
            "stage2_none_rate_pct":     round(none_rate * 100, 1),
            "stage2_pass_rate_pct":     round(pass_rate * 100, 1),
            "none_by_reason":           dict(sorted(self._s2_none_reasons.items(), key=lambda x: -x[1])),
            "none_by_symbol":           dict(sorted(self._s2_none_by_sym.items(),   key=lambda x: -x[1])[:10]),
            "none_by_strategy":         dict(sorted(self._s2_none_by_strat.items(), key=lambda x: -x[1])),
            "none_by_regime":           dict(self._s2_none_by_regime),
            "recent_none_events":       recent,
            "note":                     "stage2_none_rate_pct is the previously invisible drop zone",
        }

    def summary(self) -> dict:
        stats = self.get_stats()
        # Window totals (after pruning): counts within rolling window
        cutoff = time.time() - self._window_sec
        self._prune(cutoff)
        return {
            "trades_per_hour":          stats.trades_per_hour,
            "signals_per_hour":         stats.signals_per_hour,
            "rejection_rate_pct":       round(stats.rejection_rate * 100, 1),
            "minutes_since_last_trade": stats.minutes_since_last_trade,
            "top_rejection_reasons":    stats.top_reasons,
            "total_signals":            len(self._signal_ts),
            "total_trades":             len(self._trade_ts),
            "total_skips":              len(self._skip_ts),
            "window_min":               cfg.TFM_WINDOW_MIN,
            "module": "TRADE_FLOW_MONITOR",
            "phase":  5.1,
        }

    # ── Internals ─────────────────────────────────────────────────────────────

    def _prune(self, cutoff: float):
        for q in (self._trade_ts, self._signal_ts, self._skip_ts):
            while q and q[0] < cutoff:
                q.popleft()


# ── Module-level singleton ────────────────────────────────────────────────────
trade_flow_monitor = TradeFlowMonitor()
