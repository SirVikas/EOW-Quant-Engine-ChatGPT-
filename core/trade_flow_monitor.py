"""
EOW Quant Engine — Phase 5.1: Trade Flow Monitor
Ensures healthy trading frequency by tracking activity and rejection patterns.

Metrics (rolling TFM_WINDOW_MIN window):
  - trades_per_hour:    completed trades in window, scaled to 1 hour
  - signals_per_hour:   signals evaluated (before any gate)
  - rejection_rate:     skips / (skips + trades), fraction 0–1
  - minutes_since_last_trade: global time since last successful trade
  - top_rejection_reasons: top-5 block causes (for diagnostics)

Integration: passive observer — never blocks trades. Call record_signal(),
record_trade(), record_skip() at the appropriate points. Use summary() for
/api/status to expose trading health in real time.
"""
from __future__ import annotations

import time
from collections import deque, defaultdict
from dataclasses import dataclass
from typing import Deque, Dict

from loguru import logger

from config import cfg


@dataclass
class FlowStats:
    trades_per_hour:          float
    signals_per_hour:         float
    rejection_rate:           float   # 0–1 fraction
    minutes_since_last_trade: float
    top_reasons:              dict    # reason_key → count, top 5


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
        logger.info(
            f"[FLOW-MONITOR] Phase 5.1 activated | "
            f"window={cfg.TFM_WINDOW_MIN}min"
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

    def summary(self) -> dict:
        stats = self.get_stats()
        return {
            "trades_per_hour":          stats.trades_per_hour,
            "signals_per_hour":         stats.signals_per_hour,
            "rejection_rate_pct":       round(stats.rejection_rate * 100, 1),
            "minutes_since_last_trade": stats.minutes_since_last_trade,
            "top_rejection_reasons":    stats.top_reasons,
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
