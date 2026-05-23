"""
PRP-PHASED.E.4 — Alpha Persistence Tracker
DIAGNOSTIC ONLY — no trading decisions, no I/O, no side effects.
"""
from __future__ import annotations

import time as _time
import statistics
from collections import defaultdict
from typing import List, Optional


def track_alpha_persistence(trades: List[dict]) -> dict:
    try:
        return _compute(trades)
    except Exception as exc:
        return {
            "report": "ALPHA_PERSISTENCE_REPORT",
            "error": str(exc),
            "diagnostic_only": True,
            "auto_authorized": False,
            "generated_ts": int(_time.time() * 1000),
        }


def _compute(trades: List[dict]) -> dict:
    ts = int(_time.time() * 1000)
    base = {
        "report": "ALPHA_PERSISTENCE_REPORT",
        "diagnostic_only": True,
        "auto_authorized": False,
        "generated_ts": ts,
    }

    _insufficient = {
        **base,
        "total_trades": len(trades),
        "alpha_state": "STATISTICAL_NOISE",
        "persistence_score": 0,
        "decay_curve": [],
        "decay_velocity": None,
        "alpha_duration": None,
        "temporal_degradation": False,
        "evaporation_risk": "LOW",
        "concentration_migration": None,
        "regime_dependency": None,
    }

    if not trades:
        return _insufficient

    sorted_trades = sorted(trades, key=lambda t: float(t.get("entry_ts", 0)))
    nets = [float(t.get("net_pnl", 0.0)) for t in sorted_trades]
    n = len(nets)

    if n < 10:
        return {**_insufficient, "total_trades": n}

    decay_curve_full = [
        statistics.mean(nets[i : i + 10])
        for i in range(n - 10 + 1)
    ]

    decay_curve = decay_curve_full[-20:]

    alpha_duration: int = 0
    for val in decay_curve_full:
        if val > 0:
            alpha_duration += 1
        else:
            break

    decay_velocity: Optional[float] = None
    if len(decay_curve_full) >= 2:
        decay_velocity = (
            (decay_curve_full[-1] - decay_curve_full[0])
            / max(1, len(decay_curve_full) - 1)
        )

    last10_mean = statistics.mean(nets[-10:])
    temporal_degradation = (
        decay_velocity is not None
        and decay_velocity < -0.01
        and last10_mean < 0
    )

    if temporal_degradation and alpha_duration == 0:
        evaporation_risk = "CRITICAL"
    elif temporal_degradation:
        evaporation_risk = "HIGH"
    elif decay_velocity is not None and decay_velocity < -0.005:
        evaporation_risk = "MODERATE"
    else:
        evaporation_risk = "LOW"

    all_wins = sum(1 for v in nets if v > 0)
    all_win_rate = all_wins / n * 100

    concentration_migration: Optional[bool] = None
    if n >= 30:
        third = n // 3
        early_third = nets[:third]
        late_third = nets[-third:]
        early_wr = sum(1 for v in early_third if v > 0) / max(1, len(early_third)) * 100
        late_wr = sum(1 for v in late_third if v > 0) / max(1, len(late_third)) * 100
        concentration_migration = late_wr >= early_wr

    regime_nets: dict[str, list[float]] = defaultdict(list)
    for t in sorted_trades:
        regime_nets[t.get("regime", "UNKNOWN")].append(float(t.get("net_pnl", 0.0)))

    qualifying = {r: v for r, v in regime_nets.items() if len(v) >= 5}
    positive_regimes = [r for r, v in qualifying.items() if statistics.mean(v) > 0]

    regime_dependency: Optional[str] = None
    if len(qualifying) == 0:
        regime_dependency = "UNKNOWN"
    elif len(positive_regimes) == 1:
        regime_dependency = "REGIME_DEPENDENT"
    elif len(positive_regimes) >= 2:
        regime_dependency = "REGIME_INDEPENDENT"
    else:
        regime_dependency = "UNKNOWN"

    score = 0
    if decay_curve_full and statistics.mean(decay_curve_full) > 0:
        score += 30
    if alpha_duration >= 5:
        score += 20
    if all_win_rate >= 45.0:
        score += 20
    if not temporal_degradation:
        score += 15
    if n >= 30 and concentration_migration is True:
        score += 15

    if score >= 70:
        alpha_state = "PERSISTENT"
    elif score >= 40 and temporal_degradation:
        alpha_state = "DECAYING"
    elif evaporation_risk in ("HIGH", "CRITICAL"):
        alpha_state = "EVAPORATING"
    elif score < 20:
        alpha_state = "ABSENT"
    else:
        alpha_state = "LOCALIZED"

    return {
        **base,
        "total_trades": n,
        "alpha_state": alpha_state,
        "persistence_score": score,
        "decay_curve": [round(v, 6) for v in decay_curve],
        "decay_velocity": round(decay_velocity, 6) if decay_velocity is not None else None,
        "alpha_duration": alpha_duration,
        "temporal_degradation": temporal_degradation,
        "evaporation_risk": evaporation_risk,
        "concentration_migration": concentration_migration,
        "regime_dependency": regime_dependency,
    }
