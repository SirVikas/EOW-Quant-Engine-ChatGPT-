"""
PRP-PHASED.E.6 — Entropy Resistance Engine
DIAGNOSTIC ONLY — no trading decisions, no I/O, no side effects.
"""
from __future__ import annotations

import time as _time
import statistics
from collections import defaultdict
from typing import List


def compute_entropy_resistance(trades: List[dict]) -> dict:
    try:
        return _compute(trades)
    except Exception as exc:
        return {
            "report": "ENTROPY_RESISTANCE_REPORT",
            "error": str(exc),
            "diagnostic_only": True,
            "auto_authorized": False,
            "generated_ts": int(_time.time() * 1000),
        }


def _compute(trades: List[dict]) -> dict:
    ts = int(_time.time() * 1000)
    base = {
        "report": "ENTROPY_RESISTANCE_REPORT",
        "diagnostic_only": True,
        "auto_authorized": False,
        "generated_ts": ts,
    }

    _empty_domains = {
        "signal_entropy":                  {"score": 50, "stdev_net": None},
        "ecological_entropy":              {"score": 50, "fast_ratio": 0.0, "strategy_count": 0},
        "regime_instability_entropy":      {"score": 50, "transition_count": 0, "transition_rate": 0.0},
        "alpha_fragmentation":             {"score": 50, "positive_pockets": 0, "negative_pockets": 0},
        "survivability_erosion":           {"score": 50, "positive_ratio": None},
        "structural_degradation_velocity": {"score": 50, "decay_velocity": None},
    }

    if not trades:
        return {
            **base,
            "total_trades": 0,
            "entropy_state": "FRAGILE",
            "resistance_score": 50,
            "entropy_domains": _empty_domains,
            "degradation_velocity": None,
        }

    n = len(trades)
    nets = [float(t.get("net_pnl", 0.0)) for t in trades]

    # --- signal_entropy ---
    if n < 3:
        sig_score = 50
        sig_stdev = None
    else:
        sig_stdev = round(statistics.pstdev(nets), 6)
        if sig_stdev == 0:
            sig_score = 50
        else:
            sig_score = max(0, min(100, round(100 - sig_stdev * 10)))

    # --- ecological_entropy ---
    if n < 3:
        eco_score = 50
        fast_ratio = 0.0
        strategy_count = 0
    else:
        fast_trades = [
            t for t in trades
            if (float(t.get("exit_ts", 0)) - float(t.get("entry_ts", 0))) / 1000.0 < 60
        ]
        fast_ratio = len(fast_trades) / n
        strategy_ids = {t.get("strategy_id") for t in trades if t.get("strategy_id") is not None}
        strategy_count = len(strategy_ids)
        strategy_concentration = max(
            (
                sum(1 for t in trades if t.get("strategy_id") == sid)
                for sid in strategy_ids
            ),
            default=0,
        ) / n if strategy_ids else 0.0
        eco_score = max(0, min(100, round(100 - fast_ratio * 50 - strategy_concentration * 50)))

    # --- regime_instability_entropy ---
    if n < 3:
        reg_score = 50
        transition_count = 0
        transition_rate = 0.0
    else:
        sorted_trades = sorted(trades, key=lambda t: float(t.get("entry_ts", 0)))
        transition_count = sum(
            1 for i in range(1, len(sorted_trades))
            if sorted_trades[i].get("regime") != sorted_trades[i - 1].get("regime")
        )
        transition_rate = transition_count / max(1, n - 1)
        reg_score = max(0, min(100, round(100 - transition_rate * 100)))

    # --- alpha_fragmentation ---
    pocket_map: dict = defaultdict(list)
    for t in trades:
        key = (t.get("origin_session"), t.get("regime"))
        pocket_map[key].append(float(t.get("net_pnl", 0.0)))

    positive_pockets = sum(
        1 for nets_p in pocket_map.values()
        if len(nets_p) >= 3 and statistics.mean(nets_p) > 0
    )
    negative_pockets = sum(
        1 for nets_p in pocket_map.values()
        if len(nets_p) >= 3 and statistics.mean(nets_p) <= 0
    )
    if positive_pockets == 0:
        frag_score = 0
    elif negative_pockets == 0:
        frag_score = 100
    else:
        frag_score = max(0, min(100, round(positive_pockets / (positive_pockets + negative_pockets) * 100)))

    # --- survivability_erosion and structural_degradation_velocity ---
    if n < 10:
        erosion_score = 50
        positive_ratio = None
        vel_score = 50
        decay_velocity: float | None = None
        rolling_means: list[float] = []
    else:
        rolling_means = [
            statistics.mean(nets[i: i + 10])
            for i in range(n - 10 + 1)
        ]
        positive_ratio = round(sum(1 for m in rolling_means if m > 0) / len(rolling_means), 4)
        erosion_score = max(0, min(100, round(positive_ratio * 100)))

        decay_velocity = (rolling_means[-1] - rolling_means[0]) / max(1, len(rolling_means) - 1)
        vel_score = max(0, min(100, round(50 + decay_velocity * 200)))

    composite = round(
        sig_score * 0.20
        + eco_score * 0.15
        + reg_score * 0.15
        + frag_score * 0.20
        + erosion_score * 0.20
        + vel_score * 0.10
    )

    if composite >= 70:
        entropy_state = "STABLE"
    elif composite >= 50:
        entropy_state = "FRAGILE"
    elif composite >= 30:
        entropy_state = "CRITICAL"
    else:
        entropy_state = "DEGENERATIVE"

    return {
        **base,
        "total_trades": n,
        "entropy_state": entropy_state,
        "resistance_score": composite,
        "entropy_domains": {
            "signal_entropy": {
                "score": sig_score,
                "stdev_net": sig_stdev,
            },
            "ecological_entropy": {
                "score": eco_score,
                "fast_ratio": round(fast_ratio, 4) if n >= 3 else 0.0,
                "strategy_count": strategy_count,
            },
            "regime_instability_entropy": {
                "score": reg_score,
                "transition_count": transition_count,
                "transition_rate": round(transition_rate, 4),
            },
            "alpha_fragmentation": {
                "score": frag_score,
                "positive_pockets": positive_pockets,
                "negative_pockets": negative_pockets,
            },
            "survivability_erosion": {
                "score": erosion_score,
                "positive_ratio": positive_ratio,
            },
            "structural_degradation_velocity": {
                "score": vel_score,
                "decay_velocity": round(decay_velocity, 6) if decay_velocity is not None else None,
            },
        },
        "degradation_velocity": round(decay_velocity, 6) if decay_velocity is not None else None,
    }
