"""
I.5 Drawdown Tolerance Engine.

Assesses whether the observed drawdown profile is acceptable for any live
deployment consideration.  Conservative thresholds — live capital demands
tighter drawdown control than paper trading.

Metrics:
  - Maximum drawdown as fraction of peak equity
  - Recovery ratio: how completely did the strategy recover?
  - Calmar proxy: mean_pnl_per_trade / max_drawdown_per_trade

States: DEPLOYMENT_READY / BORDERLINE / EXCESSIVE_DRAWDOWN / DISQUALIFYING

Pure function — no I/O, no side effects, fail-open, import-safe.
"""
from __future__ import annotations
import hashlib, time
from typing import List

# Conservative live-deployment thresholds
_MAX_ACCEPTABLE_DD_RATIO = 0.25   # max drawdown ≤ 25% of peak
_MIN_CALMAR              = 0.50   # annualised return / max_dd proxy ≥ 0.5


def compute_drawdown_tolerance(trades: List[dict]) -> dict:
    ts_ms = int(time.time() * 1000)
    try:
        n = len(trades)
        if n < 10:
            return _insufficient(ts_ms, n)

        pnls = [float(t.get("gross_pnl", t.get("pnl", 0))) for t in trades]

        # Cumulative equity
        equity   = []
        running  = 0.0
        for p in pnls:
            running += p
            equity.append(running)

        peak     = equity[0]
        max_dd   = 0.0
        peak_val = equity[0]
        for e in equity:
            if e > peak_val:
                peak_val = e
            dd = peak_val - e
            if dd > max_dd:
                max_dd = dd
                peak   = peak_val

        final_equity = equity[-1]
        # Recovery: did we recover from max drawdown?
        recovery_ratio = min(final_equity / peak, 1.0) if peak > 0 else 0.0

        # Drawdown as fraction of peak
        dd_ratio = max_dd / peak if peak > 0 else 0.0

        # Calmar proxy: mean per-trade PnL / max per-trade equivalent drawdown
        mean_pnl = sum(pnls) / n
        calmar   = mean_pnl / (max_dd / n) if max_dd > 0 else (10.0 if mean_pnl > 0 else 0.0)

        state = (
            "DEPLOYMENT_READY"   if dd_ratio <= 0.15 and calmar >= 1.0 and recovery_ratio >= 0.90 else
            "BORDERLINE"         if dd_ratio <= _MAX_ACCEPTABLE_DD_RATIO and calmar >= _MIN_CALMAR   else
            "EXCESSIVE_DRAWDOWN" if dd_ratio <= 0.50                                                 else
            "DISQUALIFYING"
        )

        payload    = f"I5|{ts_ms}|{round(dd_ratio,4)}|{round(calmar,4)}|{state}"
        lineage_id = "ALPHA-I5-" + hashlib.sha256(payload.encode()).hexdigest()[:12]

        return {
            "engine":              "I.5_DRAWDOWN_TOLERANCE",
            "lineage_id":          lineage_id,
            "trade_count":         n,
            "max_drawdown":        round(max_dd, 4),
            "peak_equity":         round(peak, 4),
            "final_equity":        round(final_equity, 4),
            "dd_ratio":            round(dd_ratio, 4),
            "recovery_ratio":      round(recovery_ratio, 4),
            "calmar_proxy":        round(calmar, 4),
            "state":               state,
            "diagnostic_only":     True,
            "auto_authorized":     False,
            "live_deployment_authorized": False,
            "lineage_preserved":   True,
        }
    except Exception as exc:
        return {
            "engine": "I.5_DRAWDOWN_TOLERANCE", "state": "DISQUALIFYING",
            "error": str(exc), "diagnostic_only": True,
            "auto_authorized": False, "live_deployment_authorized": False, "lineage_preserved": True,
        }


def _insufficient(ts_ms: int, n: int) -> dict:
    return {
        "engine": "I.5_DRAWDOWN_TOLERANCE", "state": "DISQUALIFYING",
        "trade_count": n, "min_required": 10,
        "diagnostic_only": True, "auto_authorized": False,
        "live_deployment_authorized": False, "lineage_preserved": True,
    }
