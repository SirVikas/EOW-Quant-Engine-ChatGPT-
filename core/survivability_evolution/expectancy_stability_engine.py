"""
PRP-PHASED.E.1 — Expectancy Stability Engine
DIAGNOSTIC ONLY — no trading decisions, no I/O, no side effects.
"""
from __future__ import annotations

import time as _time
import statistics
from typing import List, Optional


def compute_expectancy_stability(trades: List[dict]) -> dict:
    try:
        return _compute(trades)
    except Exception as exc:
        return {
            "report": "EXPECTANCY_STABILITY_REPORT",
            "error": str(exc),
            "diagnostic_only": True,
            "auto_authorized": False,
            "generated_ts": int(_time.time() * 1000),
        }


def _compute(trades: List[dict]) -> dict:
    ts = int(_time.time() * 1000)
    base = {
        "report": "EXPECTANCY_STABILITY_REPORT",
        "diagnostic_only": True,
        "auto_authorized": False,
        "generated_ts": ts,
    }

    if not trades:
        return {
            **base,
            "total_trades": 0,
            "stability_state": "NO_DATA",
            "persistence_score": 0,
            "decay_velocity": None,
            "half_life_estimate": None,
            "confidence_interval": None,
            "instability_detected": False,
            "rolling_windows": {},
            "primary_window_size": 0,
        }

    nets = [float(t.get("net_pnl", 0.0)) for t in trades]
    n = len(nets)

    if n < 10:
        return {
            **base,
            "total_trades": n,
            "stability_state": "INSUFFICIENT_DATA",
            "persistence_score": 0,
            "decay_velocity": None,
            "half_life_estimate": None,
            "confidence_interval": None,
            "instability_detected": False,
            "rolling_windows": {},
            "primary_window_size": 0,
        }

    window_sizes = [10, 20, 50]
    rolling_windows = {}

    for w in window_sizes:
        if n < w:
            continue
        points = [
            statistics.mean(nets[i : i + w])
            for i in range(n - w + 1)
        ]
        pos = sum(1 for p in points if p > 0)
        dv = (points[-1] - points[0]) / max(1, len(points) - 1) if len(points) >= 2 else 0.0
        rolling_windows[f"w{w}"] = {
            "size": w,
            "points_computed": len(points),
            "positive_count": pos,
            "mean_exp": round(statistics.mean(points), 4),
            "decay_velocity": round(dv, 6),
        }

    primary_size = max((s for s in window_sizes if f"w{s}" in rolling_windows), default=0)
    primary_key = f"w{primary_size}" if primary_size else None

    if not primary_key:
        return {
            **base,
            "total_trades": n,
            "stability_state": "INSUFFICIENT_DATA",
            "persistence_score": 0,
            "decay_velocity": None,
            "half_life_estimate": None,
            "confidence_interval": None,
            "instability_detected": False,
            "rolling_windows": rolling_windows,
            "primary_window_size": 0,
        }

    pw = rolling_windows[primary_key]
    primary_points = [
        statistics.mean(nets[i : i + primary_size])
        for i in range(n - primary_size + 1)
    ]

    persistence_score = int(round(pw["positive_count"] / max(1, pw["points_computed"]) * 100))
    decay_velocity = pw["decay_velocity"]

    mean_p = statistics.mean(primary_points)
    stdev_p = statistics.pstdev(primary_points) if len(primary_points) >= 2 else 0.0

    confidence_interval = {
        "low": round(mean_p - 1.5 * stdev_p, 4),
        "high": round(mean_p + 1.5 * stdev_p, 4),
    }

    near_zero_mean = abs(mean_p) < 1e-9
    instability_detected = (
        len(primary_points) >= 5
        and not near_zero_mean
        and stdev_p > 2 * abs(mean_p)
    )

    half_life_estimate: Optional[int] = None
    for idx, val in enumerate(primary_points):
        if val < 0:
            half_life_estimate = idx
            break

    if decay_velocity < -0.05 and persistence_score < 30:
        stability_state = "COLLAPSING"
    elif decay_velocity < -0.01 and persistence_score < 50:
        stability_state = "DEGRADING"
    elif abs(decay_velocity) <= 0.01 and instability_detected:
        stability_state = "OSCILLATING"
    elif decay_velocity > 0.01 and persistence_score < 60:
        stability_state = "RECOVERING"
    elif persistence_score >= 60 and decay_velocity >= -0.01:
        stability_state = "STABILIZING"
    else:
        stability_state = "DEGRADING"

    return {
        **base,
        "total_trades": n,
        "stability_state": stability_state,
        "persistence_score": persistence_score,
        "decay_velocity": decay_velocity,
        "half_life_estimate": half_life_estimate,
        "confidence_interval": confidence_interval,
        "instability_detected": instability_detected,
        "rolling_windows": rolling_windows,
        "primary_window_size": primary_size,
    }
