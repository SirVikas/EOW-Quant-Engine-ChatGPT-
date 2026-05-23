"""
PRP-PHASED.H.1 — Multi-Cycle Survivability Memory Engine.

Preserves survivability intelligence across multiple market cycles by
detecting collapse eras, recovery eras, alpha-persistence eras, and
regime-transition eras from the full trade history.

Distinguishes temporary adaptation from long-term survivability continuity.

DIAGNOSTIC ONLY — no execution authority, no deployment authority.

Pure module — accepts trades: List[dict], no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from collections import Counter
from statistics import mean, stdev
from typing import Any, Dict, List, Optional


def _net(t: dict) -> float:
    return t.get("net_pnl", 0.0)


def _rolling_means(nets: List[float], window: int = 10) -> List[float]:
    if len(nets) < window:
        return [round(mean(nets), 4)] if nets else []
    return [round(mean(nets[i - window + 1: i + 1]), 4) for i in range(window - 1, len(nets))]


def _detect_eras(rolling: List[float]) -> List[dict]:
    """Segment rolling means into positive/negative runs of >= 3 consecutive points."""
    if not rolling:
        return []
    eras: List[dict] = []
    start = 0
    polarity = "POSITIVE" if rolling[0] >= 0 else "NEGATIVE"
    for i in range(1, len(rolling)):
        new_pol = "POSITIVE" if rolling[i] >= 0 else "NEGATIVE"
        if new_pol != polarity:
            run = rolling[start:i]
            if len(run) >= 3:
                eras.append({"polarity": polarity, "start_idx": start, "end_idx": i - 1,
                              "length": len(run), "mean_exp": round(mean(run), 4)})
            start = i
            polarity = new_pol
    run = rolling[start:]
    if len(run) >= 3:
        eras.append({"polarity": polarity, "start_idx": start, "end_idx": len(rolling) - 1,
                     "length": len(run), "mean_exp": round(mean(run), 4)})
    return eras


def compute_multi_cycle_survivability_memory(trades: List[dict]) -> dict:
    """
    PRP-PHASED.H.1 — Detect multi-cycle survivability patterns.

    Args:
        trades: Combined session + historical trade dicts.

    Returns MULTI_CYCLE_SURVIVABILITY_REPORT; never raises.
    """
    ts_ms = int(_time.time() * 1000)

    try:
        if not trades:
            return {
                "report":                   "MULTI_CYCLE_SURVIVABILITY_REPORT",
                "total_trades":             0,
                "note":                     "No trades available.",
                "cycles":                   [],
                "cycle_count":              0,
                "collapse_cycle_count":     0,
                "recovery_cycle_count":     0,
                "longest_positive_era":     0,
                "longest_negative_era":     0,
                "survivability_continuity": "INSUFFICIENT_DATA",
                "multi_cycle_verdict":      "NO_DATA",
                "diagnostic_only":          True,
                "auto_authorized":          False,
                "generated_ts":             ts_ms,
            }

        sorted_t = sorted(trades, key=lambda t: t.get("entry_ts", 0))
        nets     = [_net(t) for t in sorted_t]
        rolling  = _rolling_means(nets, window=min(10, len(nets)))

        # ── Era detection ─────────────────────────────────────────────────────
        eras = _detect_eras(rolling)

        # ── Classify each era as a cycle type ─────────────────────────────────
        cycles: List[dict] = []
        prev_polarity: Optional[str] = None
        for era in eras:
            if era["polarity"] == "NEGATIVE":
                ctype = "COLLAPSE"
            elif prev_polarity == "NEGATIVE":
                ctype = "RECOVERY"
            else:
                ctype = "ALPHA_PERSISTENCE"
            cycles.append({**era, "cycle_type": ctype})
            prev_polarity = era["polarity"]

        collapse_count  = sum(1 for c in cycles if c["cycle_type"] == "COLLAPSE")
        recovery_count  = sum(1 for c in cycles if c["cycle_type"] == "RECOVERY")
        alpha_count     = sum(1 for c in cycles if c["cycle_type"] == "ALPHA_PERSISTENCE")

        pos_lengths = [c["length"] for c in cycles if c["polarity"] == "POSITIVE"]
        neg_lengths = [c["length"] for c in cycles if c["polarity"] == "NEGATIVE"]
        longest_pos = max(pos_lengths) if pos_lengths else 0
        longest_neg = max(neg_lengths) if neg_lengths else 0

        # Temporary vs persistent distinction
        if longest_pos >= 10:
            continuity = "PERSISTENT_SURVIVABILITY"
        elif pos_lengths:
            continuity = "TEMPORARY_ADAPTATION"
        else:
            continuity = "INSUFFICIENT_DATA"

        # Overall verdict
        if not cycles:
            verdict = "NO_DATA"
        elif collapse_count == 0 and longest_pos >= 5:
            verdict = "DURABLE"
        elif recovery_count >= collapse_count:
            verdict = "CYCLICAL"
        elif collapse_count > recovery_count:
            verdict = "DETERIORATING"
        else:
            verdict = "CYCLICAL"

        return {
            "report":                   "MULTI_CYCLE_SURVIVABILITY_REPORT",
            "total_trades":             len(trades),
            "cycles":                   cycles,
            "cycle_count":              len(cycles),
            "collapse_cycle_count":     collapse_count,
            "recovery_cycle_count":     recovery_count,
            "alpha_persistence_count":  alpha_count,
            "longest_positive_era":     longest_pos,
            "longest_negative_era":     longest_neg,
            "survivability_continuity": continuity,
            "multi_cycle_verdict":      verdict,
            "diagnostic_only":          True,
            "auto_authorized":          False,
            "generated_ts":             ts_ms,
        }

    except Exception as exc:
        return {
            "report":                   "MULTI_CYCLE_SURVIVABILITY_REPORT",
            "error":                    str(exc),
            "total_trades":             len(trades) if trades else 0,
            "cycles":                   [],
            "cycle_count":              0,
            "collapse_cycle_count":     0,
            "recovery_cycle_count":     0,
            "longest_positive_era":     0,
            "longest_negative_era":     0,
            "survivability_continuity": "INSUFFICIENT_DATA",
            "multi_cycle_verdict":      "NO_DATA",
            "diagnostic_only":          True,
            "auto_authorized":          False,
            "generated_ts":             ts_ms,
        }
