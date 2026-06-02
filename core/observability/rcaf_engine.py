"""
FTD-RCAF-001 — Root Cause Attribution Framework Engine
=======================================================
Shadow-logs what every governance gate WOULD do for every trade signal.
Zero impact on trade execution — observation only.

Architecture:
  - Per-signal gate decisions buffered in-memory (ring buffer, 10k cap)
  - Aggregate stats accumulated per gate (never reset, session-persistent)
  - Fail-open: any logging failure is silently swallowed
  - Thread-safe: RLock guards all mutable state
"""
from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, Optional


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class GateDecision:
    gate_name:    str
    would_block:  bool
    reason:       str        = ""
    details:      dict       = field(default_factory=dict)


@dataclass
class ShadowRecord:
    """One complete shadow evaluation record per signal tick."""
    signal_id:   str          # "{symbol}_{timestamp_ms}"
    symbol:      str
    ts_ms:       int
    strategy:    str
    regime:      str
    gates:       Dict[str, GateDecision] = field(default_factory=dict)
    # Filled in once the trade is confirmed executed (or skipped)
    trade_executed: bool = False
    trade_id:       Optional[str] = None


@dataclass
class GateStats:
    """Running stats per gate — never reset within a session."""
    gate_name:         str
    would_block_count: int   = 0
    would_allow_count: int   = 0
    # Accumulated P&L of trades that WOULD have been blocked
    est_pnl_if_blocked:   float = 0.0
    # Accumulated P&L of trades that WOULD have been allowed
    est_pnl_if_allowed:   float = 0.0
    # Fee savings if trades were blocked
    est_fee_savings:      float = 0.0
    # Trades avoided (would_block_count subset that actually executed in bypass mode)
    trades_avoided_count: int   = 0


# ── Engine ────────────────────────────────────────────────────────────────────

class RCAFEngine:
    """
    Root Cause Attribution Framework Engine.

    Usage pattern (non-blocking):
        rcaf = RCAFEngine(enabled=True)

        # At signal evaluation time — before each gate:
        rcaf.log_gate("fee_viability", sym, ts, strat, regime,
                      would_block=not sfg_result.ok,
                      reason=sfg_result.reason)

        # When trade executes:
        rcaf.mark_executed(signal_id, trade_id)

        # When trade closes (for P&L attribution):
        rcaf.record_pnl(signal_id, net_pnl, fee)
    """

    _BUFFER_SIZE = 10_000   # ring buffer cap

    def __init__(self, enabled: bool = True) -> None:
        self.enabled     = enabled
        self._lock       = threading.RLock()
        # signal_id → ShadowRecord (recent window)
        self._buffer:    Deque[ShadowRecord]    = deque(maxlen=self._BUFFER_SIZE)
        self._index:     Dict[str, ShadowRecord] = {}   # fast lookup by signal_id
        # gate_name → GateStats
        self._gate_stats: Dict[str, GateStats]  = {}
        self._boot_ts    = int(time.time() * 1000)
        self._signals_seen  = 0
        self._trades_seen   = 0
        self._anomaly_log:  Deque[dict] = deque(maxlen=500)

    # ── Public API ────────────────────────────────────────────────────────────

    def open_signal(self, signal_id: str, symbol: str, ts_ms: int,
                    strategy: str, regime: str) -> None:
        """Called once per signal tick before any gate checks."""
        if not self.enabled:
            return
        try:
            with self._lock:
                rec = ShadowRecord(
                    signal_id=signal_id,
                    symbol=symbol,
                    ts_ms=ts_ms,
                    strategy=strategy,
                    regime=regime,
                )
                self._buffer.append(rec)
                self._index[signal_id] = rec
                self._signals_seen += 1
                # Evict oldest from index if buffer rolled over
                if len(self._index) > self._BUFFER_SIZE * 2:
                    oldest_keys = list(self._index.keys())[: self._BUFFER_SIZE]
                    for k in oldest_keys:
                        self._index.pop(k, None)
        except Exception:
            pass

    def log_gate(self, gate_name: str, signal_id: str,
                 would_block: bool, reason: str = "",
                 details: Optional[dict] = None) -> None:
        """Record one gate's shadow decision for this signal."""
        if not self.enabled:
            return
        try:
            with self._lock:
                # Update per-gate stats
                stats = self._gate_stats.setdefault(
                    gate_name, GateStats(gate_name=gate_name)
                )
                if would_block:
                    stats.would_block_count += 1
                else:
                    stats.would_allow_count += 1

                # Attach to signal record
                rec = self._index.get(signal_id)
                if rec is not None:
                    rec.gates[gate_name] = GateDecision(
                        gate_name=gate_name,
                        would_block=would_block,
                        reason=reason,
                        details=details or {},
                    )
        except Exception:
            pass

    def mark_executed(self, signal_id: str, trade_id: str) -> None:
        """Called when the trade from this signal is confirmed executed."""
        if not self.enabled:
            return
        try:
            with self._lock:
                rec = self._index.get(signal_id)
                if rec is not None:
                    rec.trade_executed = True
                    rec.trade_id = trade_id
                    self._trades_seen += 1
                    # A trade executed despite some gates saying would_block
                    # → record as "trades_avoided" miss
                    for gate_name, gd in rec.gates.items():
                        if gd.would_block:
                            s = self._gate_stats.get(gate_name)
                            if s:
                                s.trades_avoided_count += 1
        except Exception:
            pass

    def record_pnl(self, signal_id: str, net_pnl: float,
                   fee: float = 0.0) -> None:
        """
        Called when the associated trade closes.
        Attributes P&L back to gates for impact estimation.
        """
        if not self.enabled:
            return
        try:
            with self._lock:
                rec = self._index.get(signal_id)
                if rec is None:
                    return
                for gate_name, gd in rec.gates.items():
                    s = self._gate_stats.get(gate_name)
                    if s is None:
                        continue
                    if gd.would_block:
                        s.est_pnl_if_blocked  += net_pnl
                        s.est_fee_savings     += fee
                    else:
                        s.est_pnl_if_allowed  += net_pnl
        except Exception:
            pass

    # ── Anomaly detection ─────────────────────────────────────────────────────

    def check_anomaly(self, gate_name: str,
                      expected_block_rate_pct: Optional[float] = None) -> Optional[dict]:
        """
        Returns an anomaly dict if gate behaviour is outside expected range.
        Caller decides whether to alert.
        """
        if not self.enabled:
            return None
        try:
            with self._lock:
                s = self._gate_stats.get(gate_name)
                if s is None:
                    return None
                total = s.would_block_count + s.would_allow_count
                if total < 10:
                    return None   # too few samples
                block_rate = s.would_block_count / total * 100
                if expected_block_rate_pct is None:
                    return None
                deviation = abs(block_rate - expected_block_rate_pct)
                if deviation > 40:   # >40 pp off expected = anomaly
                    anomaly = {
                        "gate": gate_name,
                        "expected_block_rate_pct": expected_block_rate_pct,
                        "actual_block_rate_pct":   round(block_rate, 2),
                        "deviation_pp":            round(deviation, 2),
                        "total_evaluations":       total,
                        "ts": int(time.time() * 1000),
                    }
                    self._anomaly_log.append(anomaly)
                    return anomaly
        except Exception:
            pass
        return None

    # ── Report generation ─────────────────────────────────────────────────────

    def get_attribution_report(self) -> dict:
        """Full attribution report — called by /api/rcaf/attribution endpoint."""
        if not self.enabled:
            return {"status": "RCAF_DISABLED"}
        try:
            with self._lock:
                uptime_sec = (int(time.time() * 1000) - self._boot_ts) / 1000
                rows = []
                for gate_name, s in sorted(self._gate_stats.items()):
                    total = s.would_block_count + s.would_allow_count
                    block_rate = (
                        round(s.would_block_count / total * 100, 2)
                        if total > 0 else 0.0
                    )
                    # PnL impact: if gate had been enforced, what is the
                    # estimated improvement? (blocked trades' PnL they missed)
                    est_pnl_improvement = -s.est_pnl_if_blocked   # sign flip
                    est_fee_saving      = round(s.est_fee_savings, 4)

                    rows.append({
                        "component":               gate_name,
                        "would_block_count":       s.would_block_count,
                        "would_allow_count":       s.would_allow_count,
                        "total_evaluations":       total,
                        "block_rate_pct":          block_rate,
                        "trades_avoided_count":    s.trades_avoided_count,
                        "est_pnl_improvement":     round(est_pnl_improvement, 4),
                        "est_fee_savings":         est_fee_saving,
                        "est_pnl_if_blocked":      round(s.est_pnl_if_blocked, 4),
                        "est_pnl_if_allowed":      round(s.est_pnl_if_allowed, 4),
                        "confidence":              (
                            "HIGH" if total > 200 else
                            "MEDIUM" if total > 50 else
                            "LOW"
                        ),
                        "status": (
                            "ACTIVE_BYPASSED"   if s.would_block_count > 0 else
                            "ACTIVE_NO_BLOCKS"  if total > 0 else
                            "NO_DATA"
                        ),
                    })

                # Rank by estimated PnL improvement (highest impact first)
                rows.sort(key=lambda r: r["est_pnl_improvement"], reverse=True)

                return {
                    "status":            "ACTIVE",
                    "rcaf_boot_ts":      self._boot_ts,
                    "uptime_sec":        round(uptime_sec, 1),
                    "signals_seen":      self._signals_seen,
                    "trades_seen":       self._trades_seen,
                    "gates_monitored":   len(self._gate_stats),
                    "buffer_size":       len(self._buffer),
                    "anomalies_logged":  len(self._anomaly_log),
                    "components":        rows,
                    "anomalies":         list(self._anomaly_log)[-10:],
                    "generated_at":      time.strftime(
                        "%Y-%m-%d %H:%M:%S UTC", time.gmtime()
                    ),
                }
        except Exception as exc:
            return {"status": "ERROR", "error": str(exc)}

    def get_shadow_log(self, limit: int = 200) -> dict:
        """Recent per-signal shadow decisions — called by /api/rcaf/shadow-log."""
        if not self.enabled:
            return {"status": "RCAF_DISABLED"}
        try:
            with self._lock:
                records = list(self._buffer)[-limit:]
                out = []
                for rec in reversed(records):
                    gate_summary = {}
                    any_would_block = False
                    for gname, gd in rec.gates.items():
                        gate_summary[gname] = {
                            "would_block": gd.would_block,
                            "reason":      gd.reason,
                        }
                        if gd.would_block:
                            any_would_block = True
                    out.append({
                        "signal_id":        rec.signal_id,
                        "symbol":           rec.symbol,
                        "ts_ms":            rec.ts_ms,
                        "strategy":         rec.strategy,
                        "regime":           rec.regime,
                        "trade_executed":   rec.trade_executed,
                        "trade_id":         rec.trade_id,
                        "any_gate_blocked": any_would_block,
                        "gates":            gate_summary,
                    })
                return {
                    "status":  "ACTIVE",
                    "count":   len(out),
                    "records": out,
                }
        except Exception as exc:
            return {"status": "ERROR", "error": str(exc)}

    def get_health(self) -> dict:
        """Lightweight health check for boot visibility and /api/rcaf/health."""
        return {
            "status":          "ACTIVE" if self.enabled else "DISABLED",
            "signals_seen":    self._signals_seen,
            "trades_seen":     self._trades_seen,
            "gates_monitored": len(self._gate_stats),
            "buffer_used":     len(self._buffer),
            "buffer_cap":      self._BUFFER_SIZE,
            "anomalies":       len(self._anomaly_log),
            "uptime_ms":       int(time.time() * 1000) - self._boot_ts,
        }


# ── Module-level singleton ────────────────────────────────────────────────────

rcaf_engine = RCAFEngine(enabled=True)
