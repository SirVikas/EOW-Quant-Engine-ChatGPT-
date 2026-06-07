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

        # ── MR Funnel Telemetry (FTD-MR-FUNNEL-TELEMETRY-001) ────────────────
        # Hard counters — replaces estimates with measured stage-by-stage data
        self._mr_regime_events:      int = 0   # MR symbol entered scan pipeline
        self._mr_trend_lock_reject:  int = 0   # blocked by ADX > 25 early return
        self._mr_signal_generated:   int = 0   # MR strategy produced a non-NONE signal
        self._mr_signal_none:        int = 0   # MR strategy returned NONE
        self._mr_leangate_reject_rr: int = 0   # LeanGate blocked for RR_LOW
        self._mr_leangate_reject_sl: int = 0   # LeanGate blocked for SL_TOO_TIGHT
        self._mr_leangate_reject_fee:int = 0   # LeanGate blocked for FEE_HEAVY
        self._mr_leangate_reject_other:int = 0 # LeanGate blocked for other reason
        self._mr_leangate_pass:      int = 0   # signal survived LeanGate
        self._mr_fee_reject:         int = 0   # smart fee guard / fee-aware gate blocked
        self._mr_score_reject:       int = 0   # adaptive scorer blocked
        self._mr_executed:           int = 0   # trade reached execution

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

    # ── MR Funnel Telemetry (FTD-MR-FUNNEL-TELEMETRY-001) ────────────────────

    def record_mr_regime_event(self, symbol: str):
        """Call when a MEAN_REVERTING symbol enters the scan pipeline."""
        self._mr_regime_events += 1

    def record_mr_trend_lock(self, symbol: str, adx: float):
        """Call when MR_TREND_LOCK fires (ADX > 25 blocks MR pipeline)."""
        self._mr_trend_lock_reject += 1

    def record_mr_signal_generated(self, symbol: str):
        """Call when MeanReversionStrategy returns a non-NONE signal."""
        self._mr_signal_generated += 1

    def record_mr_signal_none(self, symbol: str):
        """Call when MeanReversionStrategy returns None/NONE."""
        self._mr_signal_none += 1

    def record_mr_leangate_result(self, symbol: str, passed: bool, reason: str = ""):
        """Call with LeanGate result for MR signals."""
        if passed:
            self._mr_leangate_pass += 1
        else:
            if "RR" in reason or "rr" in reason.lower():
                self._mr_leangate_reject_rr += 1
            elif "SL" in reason or "sl_dist" in reason.lower():
                self._mr_leangate_reject_sl += 1
            elif "FEE" in reason or "fee" in reason.lower():
                self._mr_leangate_reject_fee += 1
            else:
                self._mr_leangate_reject_other += 1

    def record_mr_fee_reject(self, symbol: str):
        """Call when fee gate (smart_fee_guard or fee-aware gate) blocks an MR signal."""
        self._mr_fee_reject += 1

    def record_mr_score_reject(self, symbol: str):
        """Call when adaptive scorer blocks an MR signal."""
        self._mr_score_reject += 1

    def record_mr_executed(self, symbol: str):
        """Call when an MR trade reaches execution."""
        self._mr_executed += 1

    def mr_funnel_summary(self) -> dict:
        """FTD-MR-FUNNEL-TELEMETRY-001 — measured MR execution funnel."""
        ev   = self._mr_regime_events
        tl   = self._mr_trend_lock_reject
        sg   = self._mr_signal_generated
        sn   = self._mr_signal_none
        lg_p = self._mr_leangate_pass
        lg_rr= self._mr_leangate_reject_rr
        lg_sl= self._mr_leangate_reject_sl
        lg_fe= self._mr_leangate_reject_fee
        lg_ot= self._mr_leangate_reject_other
        fr   = self._mr_fee_reject
        sr   = self._mr_score_reject
        ex   = self._mr_executed

        lg_total_reject = lg_rr + lg_sl + lg_fe + lg_ot

        def pct(n, d):
            return round(n / d * 100, 1) if d > 0 else 0.0

        return {
            "description": "MR execution funnel — FTD-MR-FUNNEL-TELEMETRY-001",
            "funnel": {
                "mr_regime_events":         {"count": ev,   "pct_of_events": 100.0},
                "mr_trend_lock_reject":     {"count": tl,   "pct_of_events": pct(tl, ev),
                                             "note": "ADX>25 early return — kills pipeline incl. alpha"},
                "mr_signal_generated":      {"count": sg,   "pct_of_events": pct(sg, ev)},
                "mr_signal_none":           {"count": sn,   "pct_of_events": pct(sn, ev)},
                "mr_leangate_reject_rr":    {"count": lg_rr,"pct_of_signals": pct(lg_rr, sg),
                                             "note": "RR < 2.5 — structural MR geometry issue"},
                "mr_leangate_reject_sl":    {"count": lg_sl,"pct_of_signals": pct(lg_sl, sg)},
                "mr_leangate_reject_fee":   {"count": lg_fe,"pct_of_signals": pct(lg_fe, sg)},
                "mr_leangate_reject_other": {"count": lg_ot,"pct_of_signals": pct(lg_ot, sg)},
                "mr_leangate_pass":         {"count": lg_p, "pct_of_signals": pct(lg_p, sg)},
                "mr_fee_reject":            {"count": fr,   "pct_of_leangate_pass": pct(fr, lg_p)},
                "mr_score_reject":          {"count": sr,   "pct_of_leangate_pass": pct(sr, lg_p)},
                "mr_executed":              {"count": ex,   "pct_of_events": pct(ex, ev)},
            },
            "dominant_suppressor": self._mr_dominant_suppressor(ev, tl, sg, lg_rr, lg_total_reject, fr, sr),
            "session_conversion_rate_pct": pct(ex, ev),
            "trend_lock_vs_signal_ratio": round(tl / max(sg + sn, 1), 2),
        }

    def _mr_dominant_suppressor(self, ev, tl, sg, lg_rr, lg_total, fr, sr) -> str:
        stages = {
            "MR_TREND_LOCK (ADX>25)":    tl,
            "SIGNAL_NONE (no BB touch)": max(0, ev - tl - sg),
            "LEANGATE_RR (<2.5)":        lg_rr,
            "LEANGATE_OTHER":            max(0, lg_total - lg_rr),
            "FEE_REJECT":                fr,
            "SCORE_REJECT":              sr,
        }
        return max(stages, key=stages.get) if any(stages.values()) else "INSUFFICIENT_DATA"

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
