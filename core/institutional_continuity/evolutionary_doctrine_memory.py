"""
PRP-PHASED.H.2 — Evolutionary Doctrine Memory Engine.

Tracks how PHOENIX behavioural doctrine evolves across long timelines by
segmenting trade history into quartiles and measuring doctrine dimensions
(survivability, restraint, equilibrium, adaptation) in each.

Detects: doctrine drift, survivability regression, hidden architectural
erosion, historical doctrine contradictions, unsafe adaptation trends.

DIAGNOSTIC ONLY — no execution authority, no deployment authority.

Pure module — accepts trades: List[dict], no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from statistics import mean
from typing import Any, Dict, List, Optional


def _net(t: dict) -> float:
    return t.get("net_pnl", 0.0)


def _hold_sec(t: dict) -> float:
    return max(0.0, ((t.get("exit_ts") or 0) - (t.get("entry_ts") or 0)) / 1000.0)


def _conf(t: dict) -> Optional[float]:
    ds = t.get("decision_snapshot") or {}
    v  = ds.get("confidence")
    return float(v) if v is not None else None


def _quartile_doctrine(segment: List[dict]) -> Dict[str, Any]:
    if not segment:
        return {"net_exp": None, "win_rate": None, "fast_ratio": None, "avg_conf": None}
    nets  = [_net(t) for t in segment]
    wins  = sum(1 for n in nets if n > 0)
    fast  = sum(1 for t in segment if _hold_sec(t) < 60)
    confs = [c for t in segment for c in [_conf(t)] if c is not None]
    return {
        "net_exp":   round(mean(nets), 4),
        "win_rate":  round(wins / len(segment) * 100, 1),
        "fast_ratio": round(fast / len(segment), 4),
        "avg_conf":  round(mean(confs), 4) if confs else None,
        "count":     len(segment),
    }


def compute_evolutionary_doctrine_memory(trades: List[dict]) -> dict:
    """
    PRP-PHASED.H.2 — Analyse doctrine evolution across trade-history quartiles.

    Args:
        trades: Combined session + historical trade dicts.

    Returns EVOLUTIONARY_DOCTRINE_REPORT; never raises.
    """
    ts_ms = int(_time.time() * 1000)

    try:
        if len(trades) < 8:
            return {
                "report":                      "EVOLUTIONARY_DOCTRINE_REPORT",
                "total_trades":                len(trades),
                "note":                        "Insufficient history for doctrine analysis.",
                "quartile_doctrines":          {},
                "drift_signals":               [],
                "drift_count":                 0,
                "contradictions":              [],
                "doctrine_state":              "INSUFFICIENT_DATA",
                "diagnostic_only":             True,
                "auto_authorized":             False,
                "generated_ts":                ts_ms,
            }

        sorted_t = sorted(trades, key=lambda t: t.get("entry_ts", 0))
        n = len(sorted_t)
        q = n // 4
        segments = {
            "Q1": sorted_t[:q],
            "Q2": sorted_t[q:2*q],
            "Q3": sorted_t[2*q:3*q],
            "Q4": sorted_t[3*q:],
        }
        quartile_doctrines = {k: _quartile_doctrine(v) for k, v in segments.items()}

        q1 = quartile_doctrines["Q1"]
        q4 = quartile_doctrines["Q4"]

        drift_signals: List[str] = []
        contradictions: List[str] = []

        # Restraint drift: fast_ratio worsening
        if q1["fast_ratio"] is not None and q4["fast_ratio"] is not None:
            if q4["fast_ratio"] > q1["fast_ratio"] + 0.15:
                drift_signals.append("RESTRAINT_DOCTRINE_DRIFT")

        # Survivability regression: win_rate declining
        if q1["win_rate"] is not None and q4["win_rate"] is not None:
            if q4["win_rate"] < q1["win_rate"] - 10:
                drift_signals.append("SURVIVABILITY_DOCTRINE_REGRESSION")

        # Confidence hallucination drift
        if (q1["avg_conf"] is not None and q4["avg_conf"] is not None
                and q1["net_exp"] is not None and q4["net_exp"] is not None):
            if q4["avg_conf"] > q1["avg_conf"] + 0.05 and q4["net_exp"] < q1["net_exp"]:
                drift_signals.append("CONFIDENCE_HALLUCINATION_DRIFT")

        # Unsafe adaptation: net_exp declining and fast_ratio rising together
        if (q1["net_exp"] is not None and q4["net_exp"] is not None
                and q1["fast_ratio"] is not None and q4["fast_ratio"] is not None):
            if q4["net_exp"] < 0 and q4["fast_ratio"] > q1["fast_ratio"]:
                drift_signals.append("UNSAFE_ADAPTATION_TREND")

        # Architectural erosion: all quartiles show declining net_exp
        exps = [quartile_doctrines[k]["net_exp"] for k in ("Q1","Q2","Q3","Q4")
                if quartile_doctrines[k]["net_exp"] is not None]
        if len(exps) == 4 and all(exps[i] > exps[i+1] for i in range(3)):
            drift_signals.append("HIDDEN_ARCHITECTURAL_EROSION")

        # Contradiction: high confidence in Q1 with negative expectancy
        if q1["avg_conf"] is not None and q1["net_exp"] is not None:
            if q1["avg_conf"] >= 0.75 and q1["net_exp"] < 0:
                contradictions.append("High confidence from earliest era with negative expectancy — confidence unreliable from start")

        # Positive evolution
        positive_evolution = (
            q4["net_exp"] is not None and q1["net_exp"] is not None
            and q4["net_exp"] > q1["net_exp"]
            and not drift_signals
        )

        if not drift_signals and not contradictions:
            state = "DOCTRINE_STABLE"
        elif positive_evolution:
            state = "DOCTRINE_EVOLVING_POSITIVELY"
        elif "SURVIVABILITY_DOCTRINE_REGRESSION" in drift_signals:
            state = "DOCTRINE_REGRESSED"
        elif drift_signals:
            state = "DOCTRINE_DRIFTING"
        else:
            state = "DOCTRINE_STABLE"

        return {
            "report":             "EVOLUTIONARY_DOCTRINE_REPORT",
            "total_trades":       len(trades),
            "quartile_doctrines": quartile_doctrines,
            "drift_signals":      drift_signals,
            "drift_count":        len(drift_signals),
            "contradictions":     contradictions,
            "doctrine_state":     state,
            "positive_evolution": positive_evolution,
            "diagnostic_only":    True,
            "auto_authorized":    False,
            "generated_ts":       ts_ms,
        }

    except Exception as exc:
        return {
            "report":             "EVOLUTIONARY_DOCTRINE_REPORT",
            "error":              str(exc),
            "total_trades":       len(trades) if trades else 0,
            "quartile_doctrines": {},
            "drift_signals":      [],
            "drift_count":        0,
            "contradictions":     [],
            "doctrine_state":     "INSUFFICIENT_DATA",
            "diagnostic_only":    True,
            "auto_authorized":    False,
            "generated_ts":       ts_ms,
        }
