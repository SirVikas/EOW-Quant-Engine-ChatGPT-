"""
I.2 Out-of-Sample Validation Engine.

Splits trades chronologically: first 60% = in-sample, last 40% = out-of-sample.
OOS performance must not degrade catastrophically relative to IS performance.

Degradation ratio < 0.7 = significant degradation (strategy overfit to IS data).
Requires 50 trades minimum for a meaningful IS/OOS split.

Pure function — no I/O, no side effects, fail-open, import-safe.
"""
from __future__ import annotations
import hashlib, time
from typing import List

_MIN_TRADES = 50
_IS_RATIO   = 0.60


def compute_oos_validation(trades: List[dict]) -> dict:
    ts_ms = int(time.time() * 1000)
    try:
        n = len(trades)
        if n < _MIN_TRADES:
            return _insufficient(ts_ms, n)

        split   = int(n * _IS_RATIO)
        is_set  = trades[:split]
        oos_set = trades[split:]

        def _stats(subset):
            pnls     = [float(t.get("gross_pnl", t.get("pnl", 0))) for t in subset]
            wins     = sum(1 for p in pnls if p > 0)
            win_rate = wins / len(pnls) if pnls else 0.0
            mean_pnl = sum(pnls) / len(pnls) if pnls else 0.0
            return {"win_rate": win_rate, "mean_pnl": mean_pnl, "n": len(pnls)}

        is_stats  = _stats(is_set)
        oos_stats = _stats(oos_set)

        # Win-rate degradation ratio: OOS / IS  (1.0 = no degradation)
        wr_ratio = (oos_stats["win_rate"] / is_stats["win_rate"]
                    if is_stats["win_rate"] > 0 else 0.0)

        # PnL degradation ratio
        pnl_ratio = (oos_stats["mean_pnl"] / is_stats["mean_pnl"]
                     if is_stats["mean_pnl"] > 0 else (-1.0 if oos_stats["mean_pnl"] <= 0 else 0.0))

        # OOS must also be independently positive
        oos_positive = oos_stats["win_rate"] > 0.5 and oos_stats["mean_pnl"] > 0

        state = (
            "OOS_CONSISTENT"         if oos_positive and wr_ratio >= 0.85 else
            "MINOR_DEGRADATION"      if oos_positive and wr_ratio >= 0.70 else
            "SIGNIFICANT_DEGRADATION"if oos_positive and wr_ratio >= 0.50 else
            "OOS_FAILURE"
        )

        payload    = f"I2|{ts_ms}|{round(wr_ratio,4)}|{state}"
        lineage_id = "ALPHA-I2-" + hashlib.sha256(payload.encode()).hexdigest()[:12]

        return {
            "engine":              "I.2_OOS_VALIDATION",
            "lineage_id":          lineage_id,
            "trade_count":         n,
            "is_trades":           is_stats["n"],
            "oos_trades":          oos_stats["n"],
            "is_win_rate":         round(is_stats["win_rate"], 4),
            "oos_win_rate":        round(oos_stats["win_rate"], 4),
            "is_mean_pnl":         round(is_stats["mean_pnl"], 4),
            "oos_mean_pnl":        round(oos_stats["mean_pnl"], 4),
            "wr_degradation_ratio":round(wr_ratio, 4),
            "pnl_degradation_ratio":round(pnl_ratio, 4),
            "oos_independently_positive": oos_positive,
            "state":               state,
            "diagnostic_only":     True,
            "auto_authorized":     False,
            "live_deployment_authorized": False,
            "lineage_preserved":   True,
        }
    except Exception as exc:
        return {
            "engine": "I.2_OOS_VALIDATION", "state": "OOS_FAILURE",
            "error": str(exc), "diagnostic_only": True,
            "auto_authorized": False, "live_deployment_authorized": False, "lineage_preserved": True,
        }


def _insufficient(ts_ms: int, n: int) -> dict:
    return {
        "engine": "I.2_OOS_VALIDATION", "state": "OOS_FAILURE",
        "trade_count": n, "min_required": _MIN_TRADES,
        "diagnostic_only": True, "auto_authorized": False,
        "live_deployment_authorized": False, "lineage_preserved": True,
    }
