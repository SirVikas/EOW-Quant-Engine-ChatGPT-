"""
EOW Quant Engine — FTD-033 Part 4: Gate Visibility Layer

Tracks per-signal gate verdicts across all four gate layers:
  GlobalGate → PreTradeGate → RiskGate → ExecutionGate

Purpose: Identify which gate dominates rejections so the developer
summary can state "Dominant Block: PRE_TRADE_GATE (LOW_SCORE)" and
the operator knows exactly where to intervene.
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional


PASS = "PASS"
FAIL = "FAIL"


@dataclass
class GateResult:
    """Verdict for a single gate evaluation."""
    gate:      str           # GLOBAL | PRE_TRADE | RISK | EXECUTION
    verdict:   str           # PASS | FAIL
    reason:    str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class SignalGateTrace:
    """All gate verdicts for one signal evaluation."""
    symbol:         str
    signal_type:    str
    score:          float
    global_gate:    Optional[GateResult] = None
    pre_trade_gate: Optional[GateResult] = None
    risk_gate:      Optional[GateResult] = None
    execution_gate: Optional[GateResult] = None
    timestamp:      float = field(default_factory=time.time)

    @property
    def first_failure(self) -> Optional[GateResult]:
        """Return the first gate that failed, in evaluation order."""
        for g in [self.global_gate, self.pre_trade_gate, self.risk_gate, self.execution_gate]:
            if g is not None and g.verdict == FAIL:
                return g
        return None

    @property
    def all_passed(self) -> bool:
        gates = [self.global_gate, self.pre_trade_gate, self.risk_gate, self.execution_gate]
        filled = [g for g in gates if g is not None]
        return bool(filled) and all(g.verdict == PASS for g in filled)


class GateTraceEngine:
    """
    Singleton that accumulates per-signal gate verdicts and produces
    aggregate statistics for the reporting layer.

    Usage:
        trace = gate_trace_engine.new_trace(symbol, signal_type, score)
        gate_trace_engine.record(trace, "GLOBAL", PASS)
        gate_trace_engine.record(trace, "PRE_TRADE", FAIL, reason="LOW_SCORE")
        gate_trace_engine.commit(trace)
    """

    MAX_RECORDS = 500
    GATE_NAMES  = ["GLOBAL", "PRE_TRADE", "RISK", "EXECUTION"]

    def __init__(self):
        self._traces: deque[SignalGateTrace] = deque(maxlen=self.MAX_RECORDS)

    # ── API ───────────────────────────────────────────────────────────────────

    def new_trace(self, symbol: str, signal_type: str, score: float) -> SignalGateTrace:
        return SignalGateTrace(symbol=symbol, signal_type=signal_type, score=score)

    def record(
        self,
        trace:   SignalGateTrace,
        gate:    str,
        verdict: str,
        reason:  str = "",
    ) -> None:
        result = GateResult(gate=gate, verdict=verdict, reason=reason)
        gate_upper = gate.upper()
        if gate_upper == "GLOBAL":
            trace.global_gate = result
        elif gate_upper in ("PRE_TRADE", "PRETRADE"):
            trace.pre_trade_gate = result
        elif gate_upper == "RISK":
            trace.risk_gate = result
        elif gate_upper == "EXECUTION":
            trace.execution_gate = result

    def commit(self, trace: SignalGateTrace) -> None:
        """Persist the completed trace."""
        self._traces.append(trace)

    # ── Analytics ─────────────────────────────────────────────────────────────

    def summary(self) -> dict:
        """Aggregate gate pass/fail stats for the report."""
        traces = list(self._traces)
        if not traces:
            return {
                "total":          0,
                "all_pass":       0,
                "dominant_block": "N/A",
                "gate_stats":     {},
            }

        total = len(traces)
        all_pass = sum(1 for t in traces if t.all_passed)

        # Count failures per gate
        gate_fail: dict[str, int] = {g: 0 for g in self.GATE_NAMES}
        gate_pass: dict[str, int] = {g: 0 for g in self.GATE_NAMES}

        for t in traces:
            for attr, name in [
                ("global_gate",    "GLOBAL"),
                ("pre_trade_gate", "PRE_TRADE"),
                ("risk_gate",      "RISK"),
                ("execution_gate", "EXECUTION"),
            ]:
                g: Optional[GateResult] = getattr(t, attr)
                if g is not None:
                    if g.verdict == PASS:
                        gate_pass[name] += 1
                    else:
                        gate_fail[name] += 1

        # Dominant blocker = gate with most FAILs
        dominant_block = max(gate_fail, key=gate_fail.get) if any(gate_fail.values()) else "N/A"
        dominant_reason = ""
        if dominant_block != "N/A":
            # Most common reason for dominant gate failures
            reasons: dict[str, int] = {}
            for t in traces:
                for attr, name in [
                    ("global_gate",    "GLOBAL"),
                    ("pre_trade_gate", "PRE_TRADE"),
                    ("risk_gate",      "RISK"),
                    ("execution_gate", "EXECUTION"),
                ]:
                    if name == dominant_block:
                        g = getattr(t, attr)
                        if g and g.verdict == FAIL and g.reason:
                            reasons[g.reason] = reasons.get(g.reason, 0) + 1
            if reasons:
                dominant_reason = max(reasons, key=reasons.get)

        gate_stats = {}
        for name in self.GATE_NAMES:
            evaluated = gate_pass[name] + gate_fail[name]
            gate_stats[name] = {
                "pass":       gate_pass[name],
                "fail":       gate_fail[name],
                "pass_pct":   round(gate_pass[name] / evaluated * 100, 1) if evaluated else 0.0,
            }

        return {
            "total":          total,
            "all_pass":       all_pass,
            "dominant_block": dominant_block,
            "dominant_reason": dominant_reason,
            "gate_stats":     gate_stats,
        }

    def recent_rows(self, n: int = 20) -> list[dict]:
        """Return recent traces formatted for the report table."""
        rows = []
        for t in list(self._traces)[-n:]:
            ff = t.first_failure
            rows.append({
                "time":     time.strftime("%H:%M:%S", time.localtime(t.timestamp)),
                "symbol":   t.symbol,
                "signal":   t.signal_type,
                "score":    f"{t.score:.3f}",
                "global":   _fmt(t.global_gate),
                "pre_trade": _fmt(t.pre_trade_gate),
                "risk":     _fmt(t.risk_gate),
                "execution": _fmt(t.execution_gate),
                "blocked_at": f"{ff.gate} ({ff.reason})" if ff else "—",
            })
        return rows


def _fmt(g: Optional[GateResult]) -> str:
    if g is None:
        return "—"
    return f"{'✔' if g.verdict == PASS else '✘'} {g.reason}" if g.reason else ("✔" if g.verdict == PASS else "✘")


# ── Singleton ─────────────────────────────────────────────────────────────────
gate_trace_engine = GateTraceEngine()
