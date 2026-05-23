"""
PRP-PHASED.E.5 — Confidence Realism Engine
DIAGNOSTIC ONLY — no trading decisions, no I/O, no side effects.
"""
from __future__ import annotations

import time as _time
import statistics
from typing import List


def compute_confidence_realism(trades: List[dict]) -> dict:
    try:
        return _compute(trades)
    except Exception as exc:
        return {
            "report": "CONFIDENCE_REALISM_REPORT",
            "error": str(exc),
            "diagnostic_only": True,
            "auto_authorized": False,
            "generated_ts": int(_time.time() * 1000),
        }


def _compute(trades: List[dict]) -> dict:
    ts = int(_time.time() * 1000)
    base = {
        "report": "CONFIDENCE_REALISM_REPORT",
        "diagnostic_only": True,
        "auto_authorized": False,
        "generated_ts": ts,
    }

    total_trades = len(trades)

    conf_trades = [
        t for t in trades
        if isinstance(t.get("decision_snapshot"), dict)
        and t["decision_snapshot"].get("confidence") is not None
        and isinstance(t["decision_snapshot"]["confidence"], (int, float))
    ]

    empty_result = {
        **base,
        "total_trades": total_trades,
        "trades_with_confidence": 0,
        "realism_score": 50,
        "conviction_reliability": "UNKNOWN",
        "hallucination_detected": False,
        "overconfidence_zones": [],
        "overconfidence_zone_count": 0,
        "expectancy_confirmed_confidence": None,
        "confidence_entropy": None,
        "confidence_buckets": {},
    }

    if not conf_trades:
        return empty_result

    def _conf(t: dict) -> float:
        return float(t["decision_snapshot"]["confidence"])

    def _net(t: dict) -> float:
        return float(t.get("net_pnl", 0.0))

    bucket_defs = [
        ("VERY_HIGH", lambda c: c >= 0.85),
        ("HIGH",      lambda c: 0.70 <= c < 0.85),
        ("MODERATE",  lambda c: 0.50 <= c < 0.70),
        ("LOW",       lambda c: c < 0.50),
    ]

    confidence_buckets: dict = {}
    overconfidence_zones: list[dict] = []

    for bucket_name, pred in bucket_defs:
        bucket_trades = [t for t in conf_trades if pred(_conf(t))]
        if len(bucket_trades) < 3:
            continue
        confs = [_conf(t) for t in bucket_trades]
        nets = [_net(t) for t in bucket_trades]
        avg_conf = round(statistics.mean(confs), 4)
        avg_net = round(statistics.mean(nets), 4)
        wins = sum(1 for n in nets if n > 0)
        win_rate = round(wins / len(nets) * 100, 1)
        alignment = "ALIGNED" if avg_net > 0 else "MISALIGNED"
        confidence_buckets[bucket_name] = {
            "trade_count": len(bucket_trades),
            "avg_confidence": avg_conf,
            "avg_net_pnl": avg_net,
            "win_rate": win_rate,
            "alignment": alignment,
        }
        if avg_conf >= 0.70 and avg_net < 0:
            overconfidence_zones.append({
                "bucket": bucket_name,
                "avg_confidence": avg_conf,
                "avg_net_pnl": avg_net,
                "win_rate": win_rate,
                "issue": "High confidence with negative expectancy",
            })

    all_confs = [_conf(t) for t in conf_trades]
    all_nets = [_net(t) for t in conf_trades]
    n = len(conf_trades)

    confidence_entropy: float | None = None
    if n >= 3:
        confidence_entropy = round(statistics.pstdev(all_confs), 6)

    conviction_reliability = "UNKNOWN"
    if n >= 5:
        mean_c = statistics.mean(all_confs)
        mean_n = statistics.mean(all_nets)
        cov = sum((c - mean_c) * (p - mean_n) for c, p in zip(all_confs, all_nets)) / n
        sd_c = statistics.pstdev(all_confs)
        sd_n = statistics.pstdev(all_nets)
        if sd_c > 0 and sd_n > 0:
            correlation = cov / (sd_c * sd_n)
            if correlation > 0.1:
                conviction_reliability = "RELIABLE"
            elif correlation < -0.1:
                conviction_reliability = "UNRELIABLE"
            else:
                conviction_reliability = "NEUTRAL"
        else:
            conviction_reliability = "NEUTRAL"

    high_conf_trades = [t for t in conf_trades if _conf(t) >= 0.70]
    expectancy_confirmed_confidence: float | None = None
    if high_conf_trades:
        wins_hc = sum(1 for t in high_conf_trades if _net(t) > 0)
        expectancy_confirmed_confidence = round(wins_hc / len(high_conf_trades) * 100, 1)

    score = 50
    if conviction_reliability == "RELIABLE":
        score += 25
    elif conviction_reliability == "UNRELIABLE":
        score -= 25
    if expectancy_confirmed_confidence is not None:
        if expectancy_confirmed_confidence >= 60:
            score += 15
        elif expectancy_confirmed_confidence < 40:
            score -= 15
    if not overconfidence_zones:
        score += 10
    if len(overconfidence_zones) >= 2:
        score -= 20
    realism_score = max(0, min(100, score))

    hallucination_detected = bool(overconfidence_zones and conviction_reliability == "UNRELIABLE")

    return {
        **base,
        "total_trades": total_trades,
        "trades_with_confidence": n,
        "realism_score": realism_score,
        "conviction_reliability": conviction_reliability,
        "hallucination_detected": hallucination_detected,
        "overconfidence_zones": overconfidence_zones,
        "overconfidence_zone_count": len(overconfidence_zones),
        "expectancy_confirmed_confidence": expectancy_confirmed_confidence,
        "confidence_entropy": confidence_entropy,
        "confidence_buckets": confidence_buckets,
    }
