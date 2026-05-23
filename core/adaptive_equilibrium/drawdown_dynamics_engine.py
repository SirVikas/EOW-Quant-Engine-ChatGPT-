"""
F.2 Drawdown Dynamics Engine.

Multi-phase drawdown analysis: peak detection, severity scoring, recovery velocity.
Distinct from Phase-G gates — this is quantitative drawdown mathematics, not a gate.

Pure function — no I/O, no side effects, fail-open, import-safe.
"""
from __future__ import annotations
import hashlib, time
from typing import List


def compute_drawdown_dynamics(trades: List[dict]) -> dict:
    ts_ms = int(time.time() * 1000)
    try:
        n = len(trades)
        if n < 5:
            return _no_data(ts_ms, n)

        pnls = [float(t.get("pnl", 0)) for t in trades]
        # Running cumulative PnL
        cum = []
        running = 0.0
        for p in pnls:
            running += p
            cum.append(running)

        peak      = cum[0]
        max_dd    = 0.0
        drawdowns = []
        in_dd     = False
        dd_start  = 0.0

        for i, equity in enumerate(cum):
            if equity > peak:
                if in_dd:
                    # Recovery — record drawdown magnitude and length
                    drawdowns.append(abs(dd_start - min(cum[drawdowns_start_idx:i])) if drawdowns else abs(dd_start - equity))
                    in_dd = False
                peak = equity
            elif equity < peak:
                if not in_dd:
                    in_dd = True
                    dd_start = peak
                    drawdowns_start_idx = i
                dd_val = peak - equity
                if dd_val > max_dd:
                    max_dd = dd_val

        avg_drawdown = sum(drawdowns) / len(drawdowns) if drawdowns else 0.0

        # Recovery velocity: average PnL in the 5 trades after a new peak
        recovery_gains = []
        for i in range(1, n):
            if cum[i] > cum[i - 1]:
                window = pnls[i:i + 5]
                if window:
                    recovery_gains.append(sum(window) / len(window))
        recovery_velocity = sum(recovery_gains) / len(recovery_gains) if recovery_gains else 0.0

        total_pnl = cum[-1] if cum else 0.0
        drawdown_ratio = max_dd / abs(total_pnl) if total_pnl != 0 else (1.0 if max_dd > 0 else 0.0)

        state = (
            "RECOVERING"    if recovery_velocity > 0 and drawdown_ratio < 0.5 else
            "STABLE"        if max_dd == 0 or drawdown_ratio < 0.2             else
            "DETERIORATING" if drawdown_ratio < 0.8                             else
            "CRITICAL"
        )

        payload = f"EQ-F2|{ts_ms}|{round(max_dd, 4)}|{round(drawdown_ratio, 4)}"
        lineage_id = "EQ-F2-" + hashlib.sha256(payload.encode()).hexdigest()[:12]

        return {
            "engine":              "F.2_DRAWDOWN_DYNAMICS",
            "lineage_id":          lineage_id,
            "trade_count":         n,
            "max_drawdown":        round(max_dd, 4),
            "avg_drawdown":        round(avg_drawdown, 4),
            "drawdown_count":      len(drawdowns),
            "drawdown_ratio":      round(drawdown_ratio, 4),
            "recovery_velocity":   round(recovery_velocity, 4),
            "total_pnl":           round(total_pnl, 4),
            "state":               state,
            "diagnostic_only":     True,
            "auto_authorized":     False,
            "lineage_preserved":   True,
        }
    except Exception as exc:
        return {
            "engine": "F.2_DRAWDOWN_DYNAMICS", "state": "CRITICAL",
            "error": str(exc), "diagnostic_only": True,
            "auto_authorized": False, "lineage_preserved": True,
        }


def _no_data(ts_ms: int, n: int) -> dict:
    return {
        "engine": "F.2_DRAWDOWN_DYNAMICS", "state": "STABLE",
        "trade_count": n, "insufficient_data": True,
        "diagnostic_only": True, "auto_authorized": False, "lineage_preserved": True,
    }
