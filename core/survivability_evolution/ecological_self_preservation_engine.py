"""
PRP-PHASED.E.2 — Ecological Self-Preservation Engine
DIAGNOSTIC ONLY — no trading decisions, no I/O, no side effects.
"""
from __future__ import annotations

import time as _time
import statistics
from typing import List


def compute_ecological_self_preservation(trades: List[dict]) -> dict:
    try:
        return _compute(trades)
    except Exception as exc:
        return {
            "report": "ECOLOGICAL_SELF_PRESERVATION_REPORT",
            "error": str(exc),
            "diagnostic_only": True,
            "auto_authorized": False,
            "generated_ts": int(_time.time() * 1000),
        }


def _compute(trades: List[dict]) -> dict:
    ts = int(_time.time() * 1000)
    base = {
        "report": "ECOLOGICAL_SELF_PRESERVATION_REPORT",
        "diagnostic_only": True,
        "auto_authorized": False,
        "generated_ts": ts,
    }

    if not trades:
        return {
            **base,
            "total_trades": 0,
            "preservation_score": 100,
            "preservation_tier": "SAFE",
            "threat_count": 0,
            "threats": [],
            "high_threat_count": 0,
            "recommendations": [],
        }

    nets = [float(t.get("net_pnl", 0.0)) for t in trades]
    n = len(nets)
    threats: list[dict] = []

    # OVERTRADING_ESCALATION
    if n >= 40:
        first20 = nets[:20]
        last20 = nets[-20:]
        count_first = len(first20)
        count_last = len(last20)
        if count_last > 1.5 * count_first and statistics.mean(last20) < 0:
            threats.append({
                "threat": "OVERTRADING_ESCALATION",
                "severity": "HIGH",
                "detail": (
                    f"Last-20 trade count ({count_last}) > 1.5× first-20 ({count_first}) "
                    f"with avg net {statistics.mean(last20):.4f}"
                ),
            })

    # ALPHA_EXHAUSTION
    if n >= 20:
        first10_nets = nets[:10]
        last10_nets = nets[-10:]
        if statistics.mean(last10_nets) < 0 and statistics.mean(first10_nets) > 0:
            threats.append({
                "threat": "ALPHA_EXHAUSTION",
                "severity": "HIGH",
                "detail": (
                    f"First-10 avg net={statistics.mean(first10_nets):.4f} → "
                    f"Last-10 avg net={statistics.mean(last10_nets):.4f}"
                ),
            })

    # ECOLOGICAL_SATURATION
    fast_trades = [
        t for t in trades
        if (float(t.get("exit_ts", 0)) - float(t.get("entry_ts", 0))) / 1000.0 < 60
    ]
    fast_nets = [float(t.get("net_pnl", 0.0)) for t in fast_trades]
    if len(fast_trades) >= 5 and len(fast_trades) / max(1, n) > 0.60 and statistics.mean(fast_nets) < 0:
        threats.append({
            "threat": "ECOLOGICAL_SATURATION",
            "severity": "HIGH",
            "detail": (
                f"{len(fast_trades)}/{n} trades held <60s ({len(fast_trades)/n*100:.1f}%), "
                f"avg net={statistics.mean(fast_nets):.4f}"
            ),
        })

    # VOLATILITY_POISONING
    vol_trades = [t for t in trades if t.get("regime") == "VOLATILITY_EXPANSION"]
    vol_nets = [float(t.get("net_pnl", 0.0)) for t in vol_trades]
    if len(vol_trades) >= 3 and len(vol_trades) / max(1, n) > 0.30 and statistics.mean(vol_nets) < 0:
        threats.append({
            "threat": "VOLATILITY_POISONING",
            "severity": "MEDIUM",
            "detail": (
                f"VOLATILITY_EXPANSION={len(vol_trades)}/{n} trades "
                f"({len(vol_trades)/n*100:.1f}%), avg net={statistics.mean(vol_nets):.4f}"
            ),
        })

    # CONFIDENCE_OVERHEATING
    if n >= 10:
        last10 = trades[-10:]
        conf_vals = [
            float(t["decision_snapshot"]["confidence"])
            for t in last10
            if isinstance(t.get("decision_snapshot"), dict)
            and "confidence" in t["decision_snapshot"]
        ]
        last10_nets = [float(t.get("net_pnl", 0.0)) for t in last10]
        if conf_vals and statistics.mean(conf_vals) > 0.80 and statistics.mean(last10_nets) < 0:
            threats.append({
                "threat": "CONFIDENCE_OVERHEATING",
                "severity": "HIGH",
                "detail": (
                    f"Last-10 avg confidence={statistics.mean(conf_vals):.3f} "
                    f"with avg net={statistics.mean(last10_nets):.4f}"
                ),
            })

    # REGIME_TOXICITY
    unknown_trades = [t for t in trades if t.get("regime") == "UNKNOWN"]
    unknown_nets = [float(t.get("net_pnl", 0.0)) for t in unknown_trades]
    if (
        len(unknown_trades) >= 5
        and len(unknown_trades) / max(1, n) > 0.40
        and statistics.mean(unknown_nets) < 0
    ):
        threats.append({
            "threat": "REGIME_TOXICITY",
            "severity": "MEDIUM",
            "detail": (
                f"UNKNOWN regime={len(unknown_trades)}/{n} trades "
                f"({len(unknown_trades)/n*100:.1f}%), avg net={statistics.mean(unknown_nets):.4f}"
            ),
        })

    # INSTABILITY_ACCELERATION
    if n >= 20:
        first_half = nets[:n // 2]
        last_half = nets[-(n // 2):]
        if len(first_half) >= 3 and len(last_half) >= 3:
            sd_first = statistics.pstdev(first_half)
            sd_last = statistics.pstdev(last_half)
            if sd_last > 1.5 * sd_first:
                threats.append({
                    "threat": "INSTABILITY_ACCELERATION",
                    "severity": "HIGH",
                    "detail": (
                        f"Last-half stdev={sd_last:.4f} > 1.5× first-half stdev={sd_first:.4f}"
                    ),
                })

    high_threats = [t for t in threats if t["severity"] == "HIGH"]

    score = 100
    for t in threats:
        score -= 20 if t["severity"] == "HIGH" else 10
    score = max(0, min(100, score))

    if score >= 80:
        tier = "SAFE"
    elif score >= 60:
        tier = "GUARDED"
    elif score >= 30:
        tier = "STRESSED"
    else:
        tier = "CRITICAL"

    _rec_map = {
        "OVERTRADING_ESCALATION": "Implement defensive throttle — reduce trade frequency by 50%",
        "ALPHA_EXHAUSTION": "Enter ecological cooldown — pause new entries for recovery window",
        "ECOLOGICAL_SATURATION": "Contract to longer-hold trades only — exit fast-trade strategy",
        "VOLATILITY_POISONING": "Avoid VOLATILITY_EXPANSION regime — risk contraction indicated",
        "CONFIDENCE_OVERHEATING": "Reduce confidence-driven sizing — calibrate conviction thresholds",
        "REGIME_TOXICITY": "Pause UNKNOWN-regime trades — regime classification required",
        "INSTABILITY_ACCELERATION": "Enter survivability preservation state — high variance detected",
    }
    recommendations = [
        _rec_map[t["threat"]]
        for t in high_threats
        if t["threat"] in _rec_map
    ]

    return {
        **base,
        "total_trades": n,
        "preservation_score": score,
        "preservation_tier": tier,
        "threat_count": len(threats),
        "threats": threats,
        "high_threat_count": len(high_threats),
        "recommendations": recommendations,
    }
