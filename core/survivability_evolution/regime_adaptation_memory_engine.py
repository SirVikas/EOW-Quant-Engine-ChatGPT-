"""
PRP-PHASED.E.3 — Regime Adaptation Memory Engine
DIAGNOSTIC ONLY — no trading decisions, no I/O, no side effects.
"""
from __future__ import annotations

import time as _time
import statistics
from collections import defaultdict
from typing import List, Optional


_REGIME_MAP = {
    "TRENDING": "TRENDING",
    "MEAN_REVERTING": "RANGING",
    "VOLATILITY_EXPANSION": "EXPANSION",
}


def _map_regime(raw: str) -> str:
    return _REGIME_MAP.get(raw, "UNCLASSIFIED")


def compute_regime_adaptation_memory(trades: List[dict]) -> dict:
    try:
        return _compute(trades)
    except Exception as exc:
        return {
            "report": "REGIME_ADAPTATION_MEMORY_REPORT",
            "error": str(exc),
            "diagnostic_only": True,
            "auto_authorized": False,
            "generated_ts": int(_time.time() * 1000),
        }


def _compute(trades: List[dict]) -> dict:
    ts = int(_time.time() * 1000)
    base = {
        "report": "REGIME_ADAPTATION_MEMORY_REPORT",
        "diagnostic_only": True,
        "auto_authorized": False,
        "generated_ts": ts,
    }

    if not trades:
        return {
            **base,
            "total_trades": 0,
            "regime_count": 0,
            "regime_memory": {},
            "transition_history": [],
            "transition_count": 0,
            "collapse_conditions": [],
            "survivability_conditions": [],
            "adaptive_fingerprints": {},
            "dominant_regime": None,
        }

    sorted_trades = sorted(trades, key=lambda t: float(t.get("entry_ts", 0)))

    by_regime: dict[str, list[dict]] = defaultdict(list)
    for t in sorted_trades:
        regime = _map_regime(t.get("regime", ""))
        by_regime[regime].append(t)

    transition_history: list[dict] = []
    prev_regime: Optional[str] = None
    for t in sorted_trades:
        curr_regime = _map_regime(t.get("regime", ""))
        if prev_regime is not None and curr_regime != prev_regime:
            transition_history.append({
                "from": prev_regime,
                "to": curr_regime,
                "net_at_transition": float(t.get("net_pnl", 0.0)),
            })
        prev_regime = curr_regime

    regime_memory: dict[str, dict] = {}

    for regime, r_trades in by_regime.items():
        if len(r_trades) < 3:
            continue

        r_nets = [float(t.get("net_pnl", 0.0)) for t in r_trades]
        tc = len(r_nets)
        net_exp = round(statistics.mean(r_nets), 4)
        wins = sum(1 for v in r_nets if v > 0)
        win_rate = round(wins / tc * 100, 1)

        if net_exp > 0 and win_rate >= 40.0:
            survivability = "SURVIVABLE"
        elif net_exp > 0:
            survivability = "MARGINAL"
        else:
            survivability = "NOT_SURVIVABLE"

        half = tc // 2
        early_nets = r_nets[:half] if half > 0 else r_nets
        late_nets = r_nets[half:] if half > 0 else r_nets
        early_exp = round(statistics.mean(early_nets), 4)
        late_exp = round(statistics.mean(late_nets), 4)

        if late_exp > early_exp:
            exp_trend = "IMPROVING"
        elif late_exp < early_exp:
            exp_trend = "DEGRADING"
        else:
            exp_trend = "STABLE"

        collapse_recurrence = 0
        recovery_count = 0
        prev_negative = False
        for i in range(tc - 9):
            window_mean = statistics.mean(r_nets[i : i + 10])
            curr_negative = window_mean < 0
            if curr_negative:
                collapse_recurrence += 1
            if prev_negative and not curr_negative:
                recovery_count += 1
            prev_negative = curr_negative

        regime_memory[regime] = {
            "trade_count": tc,
            "net_expectancy": net_exp,
            "survivability": survivability,
            "win_rate": win_rate,
            "early_expectancy": early_exp,
            "late_expectancy": late_exp,
            "expectancy_trend": exp_trend,
            "collapse_recurrence_count": collapse_recurrence,
            "recovery_count": recovery_count,
        }

    collapse_conditions: list[str] = []
    survivability_conditions: list[str] = []

    for regime, mem in regime_memory.items():
        if mem["survivability"] == "NOT_SURVIVABLE" and mem["trade_count"] >= 5:
            collapse_conditions.append(
                f"Regime {regime}: net_exp={mem['net_expectancy']:.4f}, "
                f"win_rate={mem['win_rate']:.1f}% — historically collapse-associated"
            )
        if mem["survivability"] == "SURVIVABLE" and mem["trade_count"] >= 5:
            survivability_conditions.append(
                f"Regime {regime}: persistent positive expectancy (win_rate={mem['win_rate']:.1f}%)"
            )

    surv_map = {r: m["survivability"] for r, m in regime_memory.items()}
    collapse_transitions = sum(
        1
        for tr in transition_history
        if surv_map.get(tr["from"]) == "SURVIVABLE"
        and surv_map.get(tr["to"]) == "NOT_SURVIVABLE"
    )
    if collapse_transitions >= 2:
        collapse_conditions.append("Repeated survivability collapse on regime transitions")

    adaptive_fingerprints: dict[str, str] = {}
    for regime, mem in regime_memory.items():
        ne = mem["net_expectancy"]
        early = mem["early_expectancy"]
        late = mem["late_expectancy"]
        if ne > 0 and late > early:
            fp = "POSITIVE_PERSISTENCE"
        elif ne > 0 and late <= early:
            fp = "POSITIVE_DEGRADING"
        elif ne < 0 and late > early and late > 0:
            fp = "RECOVERING"
        elif ne < 0 and late <= early:
            fp = "COLLAPSING"
        else:
            fp = "MARGINAL_STABLE"
        adaptive_fingerprints[regime] = fp

    dominant_regime: Optional[str] = None
    if regime_memory:
        dominant_regime = max(regime_memory, key=lambda r: regime_memory[r]["trade_count"])

    return {
        **base,
        "total_trades": len(trades),
        "regime_count": len(regime_memory),
        "regime_memory": regime_memory,
        "transition_history": transition_history,
        "transition_count": len(transition_history),
        "collapse_conditions": collapse_conditions,
        "survivability_conditions": survivability_conditions,
        "adaptive_fingerprints": adaptive_fingerprints,
        "dominant_regime": dominant_regime,
    }
