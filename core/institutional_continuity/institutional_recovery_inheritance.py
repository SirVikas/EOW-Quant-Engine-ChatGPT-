"""
PRP-PHASED.H.4 — Institutional Recovery Inheritance Engine.

Preserves recovery intelligence from historical degradation periods so that
future restoration can inherit from past successes. Identifies repeatable
recovery pathways and conditions historically associated with stabilisation.

DIAGNOSTIC ONLY — no execution authority, no deployment authority.

Pure module — accepts trades: List[dict], no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from collections import Counter
from statistics import mean
from typing import Any, Dict, List, Optional


def _net(t: dict) -> float:
    return t.get("net_pnl", 0.0)


def _rolling_means(nets: List[float], window: int = 10) -> List[float]:
    if len(nets) < window:
        return [round(mean(nets), 4)] if nets else []
    return [round(mean(nets[i - window + 1: i + 1]), 4) for i in range(window - 1, len(nets))]


def compute_institutional_recovery_inheritance(trades: List[dict]) -> dict:
    """
    PRP-PHASED.H.4 — Extract and preserve historical recovery intelligence.

    Args:
        trades: Combined session + historical trade dicts.

    Returns RECOVERY_INHERITANCE_REPORT; never raises.
    """
    ts_ms = int(_time.time() * 1000)

    try:
        if len(trades) < 10:
            return {
                "report":                     "RECOVERY_INHERITANCE_REPORT",
                "total_trades":               len(trades),
                "note":                       "Insufficient history for recovery analysis.",
                "recovery_pathways":          [],
                "pathway_count":              0,
                "repeatability":              "NO_INHERITANCE",
                "repeatable_conditions":      [],
                "recovery_regime_frequency":  {},
                "recovery_session_frequency": {},
                "behaviors_restored":         [],
                "inheritance_state":          "NO_INHERITANCE",
                "diagnostic_only":            True,
                "auto_authorized":            False,
                "generated_ts":               ts_ms,
            }

        sorted_t = sorted(trades, key=lambda t: t.get("entry_ts", 0))
        nets     = [_net(t) for t in sorted_t]
        rolling  = _rolling_means(nets, window=min(10, len(nets)))

        # Find recovery crossovers (negative → positive rolling mean)
        recovery_pathways: List[dict] = []
        for i in range(1, len(rolling)):
            if rolling[i - 1] < 0 and rolling[i] >= 0:
                # Trades in surrounding window (5 before / after crossover in sorted_t)
                trade_idx  = i + (min(10, len(nets)) - 1)  # approx trade index at crossover
                local_start = max(0, trade_idx - 5)
                local_end   = min(len(sorted_t), trade_idx + 5)
                local_trades = sorted_t[local_start:local_end]

                if not local_trades:
                    continue

                regimes  = [t.get("regime", "UNKNOWN") or "UNKNOWN" for t in local_trades]
                sessions = [t.get("origin_session", "UNKNOWN") or "UNKNOWN" for t in local_trades]
                dom_regime  = Counter(regimes).most_common(1)[0][0]
                dom_session = Counter(sessions).most_common(1)[0][0]

                pre_mean  = round(mean(rolling[max(0, i-5):i]), 4) if i >= 1 else rolling[i-1]
                post_mean = round(mean(rolling[i:min(len(rolling), i+5)]), 4)

                recovery_pathways.append({
                    "crossover_idx":    i,
                    "pre_recovery_exp": pre_mean,
                    "post_recovery_exp": post_mean,
                    "recovery_strength": round(post_mean - pre_mean, 4),
                    "dominant_regime":  dom_regime,
                    "dominant_session": dom_session,
                    "trade_count":      len(local_trades),
                })

        # Regime / session frequency in recoveries
        recovery_regimes  = [p["dominant_regime"]  for p in recovery_pathways]
        recovery_sessions = [p["dominant_session"] for p in recovery_pathways]
        regime_freq  = dict(Counter(recovery_regimes))
        session_freq = dict(Counter(recovery_sessions))

        # Repeatability: same regime in >= 2 pathways
        repeatable_conditions: List[str] = []
        for regime, cnt in regime_freq.items():
            if cnt >= 2:
                repeatable_conditions.append(
                    f"Regime {regime}: historically associated with {cnt} recovery events"
                )
        for session, cnt in session_freq.items():
            if cnt >= 2:
                repeatable_conditions.append(
                    f"Session {session}: historically associated with {cnt} recovery events"
                )

        # Behaviors that restored survivability
        behaviors: List[str] = []
        if recovery_pathways:
            strongest = max(recovery_pathways, key=lambda p: p["recovery_strength"])
            behaviors.append(
                f"Strongest recovery: regime={strongest['dominant_regime']} "
                f"session={strongest['dominant_session']} strength={strongest['recovery_strength']:.4f}"
            )
        for regime, cnt in regime_freq.items():
            if cnt >= 1:
                behaviors.append(f"{regime} regime historically associated with recovery restoration")

        pc = len(recovery_pathways)
        if repeatable_conditions:
            repeatability = "REPEATABLE"
        elif pc >= 1:
            repeatability = "SINGLE_EVENT"
        else:
            repeatability = "NO_INHERITANCE"

        if pc >= 3:
            state = "RICH_INHERITANCE"
        elif pc >= 2:
            state = "MODERATE_INHERITANCE"
        elif pc == 1:
            state = "SPARSE_INHERITANCE"
        else:
            state = "NO_INHERITANCE"

        return {
            "report":                     "RECOVERY_INHERITANCE_REPORT",
            "total_trades":               len(trades),
            "recovery_pathways":          recovery_pathways,
            "pathway_count":              pc,
            "repeatability":              repeatability,
            "repeatable_conditions":      repeatable_conditions,
            "recovery_regime_frequency":  regime_freq,
            "recovery_session_frequency": session_freq,
            "behaviors_restored":         behaviors,
            "inheritance_state":          state,
            "diagnostic_only":            True,
            "auto_authorized":            False,
            "generated_ts":               ts_ms,
        }

    except Exception as exc:
        return {
            "report":                     "RECOVERY_INHERITANCE_REPORT",
            "error":                      str(exc),
            "total_trades":               len(trades) if trades else 0,
            "recovery_pathways":          [],
            "pathway_count":              0,
            "repeatability":              "NO_INHERITANCE",
            "repeatable_conditions":      [],
            "recovery_regime_frequency":  {},
            "recovery_session_frequency": {},
            "behaviors_restored":         [],
            "inheritance_state":          "NO_INHERITANCE",
            "diagnostic_only":            True,
            "auto_authorized":            False,
            "generated_ts":               ts_ms,
        }
