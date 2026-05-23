"""
F.4 Capital Utilization Engine.

Measures how efficiently deployed capital is working.
Low utilization = capital sitting idle or being over-diversified into noise.

Pure function — no I/O, no side effects, fail-open, import-safe.
"""
from __future__ import annotations
import hashlib, time
from typing import List


def compute_capital_utilization(trades: List[dict]) -> dict:
    ts_ms = int(time.time() * 1000)
    try:
        n = len(trades)
        if n < 5:
            return _no_data(ts_ms, n)

        pnls     = [float(t.get("pnl", 0)) for t in trades]
        sizes    = [abs(float(t.get("size", t.get("qty", 1)))) for t in trades]
        total_pnl = sum(pnls)

        # PnL per unit size — efficiency of each unit of capital deployed
        pnl_per_unit = [p / s for p, s in zip(pnls, sizes) if s > 0]
        avg_ppu = sum(pnl_per_unit) / len(pnl_per_unit) if pnl_per_unit else 0.0

        # Utilization score: ratio of positive-contribution trades
        positive_contribution = sum(1 for p, s in zip(pnl_per_unit, sizes) if p > 0)
        util_ratio = positive_contribution / len(pnl_per_unit) if pnl_per_unit else 0.0

        # Concentration: std of sizes — high std = uneven deployment
        mean_size = sum(sizes) / n if n else 1.0
        size_std  = (sum((s - mean_size) ** 2 for s in sizes) / n) ** 0.5
        cv        = size_std / mean_size if mean_size > 0 else 0.0  # coefficient of variation

        # Utilization score 0–100
        base_score = util_ratio * 70.0
        # Penalize high coefficient of variation (uneven sizing)
        cv_penalty = min(cv * 20.0, 30.0)
        utilization_score = round(max(0.0, base_score - cv_penalty + (30.0 if avg_ppu > 0 else 0.0)), 1)
        utilization_score = min(utilization_score, 100.0)

        state = (
            "EFFICIENT"      if utilization_score >= 70 else
            "ADEQUATE"       if utilization_score >= 50 else
            "UNDERUTILIZED"  if util_ratio >= 0.4       else
            "OVEREXTENDED"
        )

        payload = f"EQ-F4|{ts_ms}|{round(utilization_score, 1)}|{round(util_ratio, 4)}"
        lineage_id = "EQ-F4-" + hashlib.sha256(payload.encode()).hexdigest()[:12]

        return {
            "engine":              "F.4_CAPITAL_UTILIZATION",
            "lineage_id":          lineage_id,
            "trade_count":         n,
            "utilization_score":   utilization_score,
            "util_ratio":          round(util_ratio, 4),
            "avg_pnl_per_unit":    round(avg_ppu, 4),
            "size_cv":             round(cv, 4),
            "total_pnl":           round(total_pnl, 4),
            "state":               state,
            "diagnostic_only":     True,
            "auto_authorized":     False,
            "lineage_preserved":   True,
        }
    except Exception as exc:
        return {
            "engine": "F.4_CAPITAL_UTILIZATION", "state": "OVEREXTENDED",
            "error": str(exc), "diagnostic_only": True,
            "auto_authorized": False, "lineage_preserved": True,
        }


def _no_data(ts_ms: int, n: int) -> dict:
    return {
        "engine": "F.4_CAPITAL_UTILIZATION", "state": "UNDERUTILIZED",
        "trade_count": n, "insufficient_data": True,
        "diagnostic_only": True, "auto_authorized": False, "lineage_preserved": True,
    }
