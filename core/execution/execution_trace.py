"""
EOW Quant Engine — FTD-033 Part 3: Execution Trace Engine

Records every signal's full journey from generation to outcome.
Purpose: Make execution pipeline fully transparent — zero silent rejections.

Every evaluated signal gets a TraceRecord. Callers append gate results
and the final verdict so the report engine can explain:
  - Why signal was rejected
  - Which gate blocked it
  - What the cost breakdown was
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

# ── Verdict constants ─────────────────────────────────────────────────────────
STATUS_EXECUTED = "EXECUTED"
STATUS_REJECTED = "REJECTED"
STATUS_PENDING  = "PENDING"


@dataclass
class TraceRecord:
    """Complete signal journey record."""
    symbol:          str
    side:            str          # LONG | SHORT
    signal_type:     str          # TCB | PBE | VSE | BB | EMA | etc.
    score:           float
    rr:              float

    # Cost / net edge
    net_edge:        float = 0.0
    net_edge_pct:    float = 0.0
    cost_verdict:    str   = "PENDING"   # APPROVE | EXPLORE | REJECT_*

    # Gate results
    global_gate:     Optional[str] = None   # PASS | FAIL | reason
    pre_trade_gate:  Optional[str] = None
    risk_gate:       Optional[str] = None
    execution_gate:  Optional[str] = None

    # Outcome
    passed_filters:  list = field(default_factory=list)
    failed_at:       Optional[str] = None
    rejection_reason: str = ""
    final_status:    str  = STATUS_PENDING

    # Metadata
    timestamp:       float = field(default_factory=time.time)
    trade_id:        Optional[str] = None
    exploration:     bool  = False


class ExecutionTrace:
    """
    Singleton recorder for signal journeys.

    Usage (from signal evaluation path):
        rec = execution_trace.start(symbol, side, signal_type, score, rr)
        rec.global_gate = "PASS"
        rec.pre_trade_gate = "FAIL"
        rec.failed_at = "PRE_TRADE_GATE"
        rec.rejection_reason = "LOW_SCORE"
        execution_trace.finalize(rec, status=STATUS_REJECTED)
    """

    MAX_RECORDS = 500

    def __init__(self):
        self._records: deque[TraceRecord] = deque(maxlen=self.MAX_RECORDS)

    # ── API ───────────────────────────────────────────────────────────────────

    def start(
        self,
        symbol:      str,
        side:        str,
        signal_type: str,
        score:       float,
        rr:          float,
    ) -> TraceRecord:
        """Create and register a new trace record."""
        rec = TraceRecord(
            symbol=symbol,
            side=side,
            signal_type=signal_type,
            score=score,
            rr=rr,
        )
        self._records.append(rec)
        return rec

    def finalize(self, rec: TraceRecord, status: str) -> None:
        """Mark the record with its final status."""
        rec.final_status = status

    def recent(self, n: int = 30) -> list[TraceRecord]:
        """Return the N most recent records (newest last)."""
        records = list(self._records)
        return records[-n:]

    def summary(self) -> dict:
        """Aggregate statistics for the reporting section."""
        records = list(self._records)
        if not records:
            return {
                "total_signals":      0,
                "executed":           0,
                "rejected":           0,
                "execution_rate_pct": 0.0,
                "rejection_reasons":  {},
                "dominant_block":     "N/A",
                "top_rejection":      "N/A",
            }

        total     = len(records)
        executed  = sum(1 for r in records if r.final_status == STATUS_EXECUTED)
        rejected  = sum(1 for r in records if r.final_status == STATUS_REJECTED)

        # Rejection reason frequency
        reasons: dict[str, int] = {}
        for r in records:
            if r.rejection_reason:
                reasons[r.rejection_reason] = reasons.get(r.rejection_reason, 0) + 1

        # Gate that blocks most
        gates: dict[str, int] = {}
        for r in records:
            if r.failed_at:
                gates[r.failed_at] = gates.get(r.failed_at, 0) + 1

        dominant_block = max(gates, key=gates.get) if gates else "N/A"
        top_rejection  = max(reasons, key=reasons.get) if reasons else "N/A"

        exec_rate = (executed / total * 100) if total else 0.0

        # Rejection reason percentages
        reason_pcts = {
            k: round(v / total * 100, 1)
            for k, v in sorted(reasons.items(), key=lambda x: -x[1])
        }

        return {
            "total_signals":      total,
            "executed":           executed,
            "rejected":           rejected,
            "execution_rate_pct": round(exec_rate, 1),
            "rejection_reasons":  reason_pcts,
            "dominant_block":     dominant_block,
            "top_rejection":      top_rejection,
            "gate_breakdown":     {
                k: round(v / total * 100, 1)
                for k, v in sorted(gates.items(), key=lambda x: -x[1])
            },
        }

    def gate_trace_rows(self, n: int = 20) -> list[dict]:
        """Return recent records formatted for the report table."""
        return [
            {
                "time":    time.strftime("%H:%M:%S", time.localtime(r.timestamp)),
                "symbol":  r.symbol,
                "signal":  r.signal_type,
                "score":   f"{r.score:.3f}",
                "net_edge": f"{r.net_edge_pct:.3f}%",
                "failed_at": r.failed_at or "—",
                "reason":  r.rejection_reason or "—",
                "status":  r.final_status,
            }
            for r in self.recent(n)
        ]


# ── Singleton ─────────────────────────────────────────────────────────────────
execution_trace = ExecutionTrace()
