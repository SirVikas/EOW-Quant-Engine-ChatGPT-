"""
I.3 Fee-Survival Certification Engine.

Verifies that the edge survives full fee and slippage load across rolling windows.
A strategy that is gross-positive but net-negative is not certifiable.

Rolling 20-trade windows: net PnL must be positive in ≥80% of windows for CERTIFIED.
Requires 20 trades minimum.

Pure function — no I/O, no side effects, fail-open, import-safe.
"""
from __future__ import annotations
import hashlib, time
from typing import List

_MIN_TRADES   = 20
_WINDOW       = 20
_CERT_THRESHOLD = 0.80   # 80% of windows must be net-positive


def compute_fee_survival(trades: List[dict]) -> dict:
    ts_ms = int(time.time() * 1000)
    try:
        n = len(trades)
        if n < _MIN_TRADES:
            return _insufficient(ts_ms, n)

        # Prefer net_pnl if available; otherwise use pnl (assume inclusive of fees)
        pnls = [float(t.get("net_pnl", t.get("pnl", 0))) for t in trades]
        fees = [abs(float(t.get("fee_entry", 0)) + float(t.get("fee_exit", t.get("fee", t.get("commission", 0))))) for t in trades]

        total_fees    = sum(fees)
        total_gross   = sum(float(t.get("gross_pnl", t.get("pnl", 0))) for t in trades)
        total_net     = sum(pnls)
        fee_drag_pct  = total_fees / abs(total_gross) if total_gross != 0 else 1.0

        # Rolling window survival rate
        positive_windows = 0
        total_windows    = 0
        for i in range(0, n - _WINDOW + 1, max(1, _WINDOW // 4)):
            w = pnls[i: i + _WINDOW]
            if sum(w) > 0:
                positive_windows += 1
            total_windows += 1

        survival_rate = positive_windows / total_windows if total_windows else 0.0

        state = (
            "FEE_CERTIFIED" if total_net > 0 and survival_rate >= _CERT_THRESHOLD else
            "MARGINAL"      if total_net > 0 and survival_rate >= 0.60             else
            "FEE_ERODED"    if total_net > 0                                        else
            "FEE_DESTROYED"
        )

        payload    = f"I3|{ts_ms}|{round(survival_rate,4)}|{state}"
        lineage_id = "ALPHA-I3-" + hashlib.sha256(payload.encode()).hexdigest()[:12]

        return {
            "engine":              "I.3_FEE_SURVIVAL",
            "lineage_id":          lineage_id,
            "trade_count":         n,
            "total_gross_pnl":     round(total_gross, 4),
            "total_net_pnl":       round(total_net, 4),
            "total_fees":          round(total_fees, 4),
            "fee_drag_pct":        round(fee_drag_pct, 4),
            "window_survival_rate":round(survival_rate, 4),
            "positive_windows":    positive_windows,
            "total_windows":       total_windows,
            "state":               state,
            "diagnostic_only":     True,
            "auto_authorized":     False,
            "live_deployment_authorized": False,
            "lineage_preserved":   True,
        }
    except Exception as exc:
        return {
            "engine": "I.3_FEE_SURVIVAL", "state": "FEE_DESTROYED",
            "error": str(exc), "diagnostic_only": True,
            "auto_authorized": False, "live_deployment_authorized": False, "lineage_preserved": True,
        }


def _insufficient(ts_ms: int, n: int) -> dict:
    return {
        "engine": "I.3_FEE_SURVIVAL", "state": "FEE_DESTROYED",
        "trade_count": n, "min_required": _MIN_TRADES,
        "diagnostic_only": True, "auto_authorized": False,
        "live_deployment_authorized": False, "lineage_preserved": True,
    }
