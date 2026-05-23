"""
PRP-PHASED.H.3 — Long-Horizon Entropy Engine.

Detects slow-moving structural degradation that short-window entropy engines
miss: survivability erosion across quarters, adaptive instability accumulation,
long-cycle entropy growth, and structural exhaustion.

States: DURABLE / AGING / FRAGILE / EXHAUSTED

DIAGNOSTIC ONLY — no execution authority, no deployment authority.

Pure module — accepts trades: List[dict], no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from statistics import mean, stdev
from typing import Any, Dict, List, Optional


def _net(t: dict) -> float:
    return t.get("net_pnl", 0.0)


def _rolling_means(nets: List[float], window: int = 20) -> List[float]:
    if len(nets) < window:
        return [round(mean(nets), 4)] if nets else []
    return [round(mean(nets[i - window + 1: i + 1]), 4) for i in range(window - 1, len(nets))]


def compute_long_horizon_entropy(trades: List[dict]) -> dict:
    """
    PRP-PHASED.H.3 — Detect slow long-horizon structural degradation.

    Args:
        trades: Combined session + historical trade dicts.

    Returns LONG_HORIZON_ENTROPY_REPORT; never raises.
    """
    ts_ms = int(_time.time() * 1000)

    try:
        if len(trades) < 8:
            return {
                "report":                            "LONG_HORIZON_ENTROPY_REPORT",
                "total_trades":                      len(trades),
                "note":                              "Insufficient history for long-horizon analysis.",
                "entropy_state":                     "DURABLE",
                "degradation_signal_count":          0,
                "degradation_signals":               [],
                "slow_survivability_erosion":        False,
                "adaptive_instability_accumulation": False,
                "long_cycle_entropy_growth":         False,
                "hidden_degradation_momentum":       False,
                "persistence_weakening":             False,
                "structural_exhaustion":             False,
                "segment_analysis":                  {},
                "diagnostic_only":                   True,
                "auto_authorized":                   False,
                "generated_ts":                      ts_ms,
            }

        sorted_t = sorted(trades, key=lambda t: t.get("entry_ts", 0))
        nets     = [_net(t) for t in sorted_t]
        n        = len(nets)
        q        = max(1, n // 4)

        segs = {
            "Q1": nets[:q],
            "Q2": nets[q:2*q],
            "Q3": nets[2*q:3*q],
            "Q4": nets[3*q:],
        }
        seg_stats: Dict[str, Any] = {}
        for k, seg in segs.items():
            if not seg:
                seg_stats[k] = {"net_exp": None, "vol": None}
                continue
            net_exp = round(mean(seg), 4)
            try:
                vol = round(stdev(seg), 4) if len(seg) >= 2 else 0.0
            except Exception:
                vol = 0.0
            seg_stats[k] = {"net_exp": net_exp, "vol": vol, "count": len(seg)}

        exps  = [seg_stats[k]["net_exp"] for k in ("Q1","Q2","Q3","Q4") if seg_stats[k]["net_exp"] is not None]
        vols  = [seg_stats[k]["vol"]     for k in ("Q1","Q2","Q3","Q4") if seg_stats[k]["vol"]     is not None]

        signals: List[str] = []

        # 1. Slow survivability erosion: monotonically declining net_exp
        if len(exps) >= 3 and all(exps[i] > exps[i+1] for i in range(len(exps)-1)):
            signals.append("SLOW_SURVIVABILITY_EROSION")
        slow_erosion = "SLOW_SURVIVABILITY_EROSION" in signals

        # 2. Adaptive instability accumulation: monotonically rising vol
        if len(vols) >= 3 and all(vols[i] < vols[i+1] for i in range(len(vols)-1)):
            signals.append("ADAPTIVE_INSTABILITY_ACCUMULATION")
        instability = "ADAPTIVE_INSTABILITY_ACCUMULATION" in signals

        # 3. Long-cycle entropy growth: rolling 20-mean variance increasing
        rolling = _rolling_means(nets, window=min(20, n))
        long_cycle = False
        if len(rolling) >= 6:
            first_half = rolling[:len(rolling)//2]
            second_half = rolling[len(rolling)//2:]
            try:
                if stdev(second_half) > stdev(first_half) * 1.3:
                    signals.append("LONG_CYCLE_ENTROPY_GROWTH")
                    long_cycle = True
            except Exception:
                pass

        # 4. Hidden degradation momentum: Q4 net_exp significantly worse than Q1
        hidden_deg = False
        if exps and seg_stats["Q1"]["net_exp"] is not None and seg_stats["Q4"]["net_exp"] is not None:
            if seg_stats["Q4"]["net_exp"] < seg_stats["Q1"]["net_exp"] - 0.5:
                signals.append("HIDDEN_DEGRADATION_MOMENTUM")
                hidden_deg = True

        # 5. Persistence weakening: count of positive rolling-mean windows declining Q1→Q4
        persistence_weak = False
        if len(rolling) >= 4:
            half = len(rolling) // 2
            pos_early = sum(1 for v in rolling[:half] if v > 0)
            pos_late  = sum(1 for v in rolling[half:] if v > 0)
            if pos_late < pos_early * 0.7 and half >= 3:
                signals.append("PERSISTENCE_WEAKENING")
                persistence_weak = True

        # 6. Structural exhaustion: Q4 net_exp < 0 AND Q4 vol > Q1 vol
        struct_exhausted = False
        if (seg_stats["Q4"]["net_exp"] is not None and seg_stats["Q4"]["net_exp"] < 0
                and seg_stats["Q1"]["vol"] is not None and seg_stats["Q4"]["vol"] is not None
                and seg_stats["Q4"]["vol"] > seg_stats["Q1"]["vol"]):
            signals.append("STRUCTURAL_EXHAUSTION")
            struct_exhausted = True

        sc = len(signals)
        if sc <= 1:
            state = "DURABLE"
        elif sc <= 3:
            state = "AGING"
        elif sc <= 5:
            state = "FRAGILE"
        else:
            state = "EXHAUSTED"

        return {
            "report":                            "LONG_HORIZON_ENTROPY_REPORT",
            "total_trades":                      len(trades),
            "entropy_state":                     state,
            "degradation_signal_count":          sc,
            "degradation_signals":               signals,
            "slow_survivability_erosion":        slow_erosion,
            "adaptive_instability_accumulation": instability,
            "long_cycle_entropy_growth":         long_cycle,
            "hidden_degradation_momentum":       hidden_deg,
            "persistence_weakening":             persistence_weak,
            "structural_exhaustion":             struct_exhausted,
            "segment_analysis":                  seg_stats,
            "diagnostic_only":                   True,
            "auto_authorized":                   False,
            "generated_ts":                      ts_ms,
        }

    except Exception as exc:
        return {
            "report":                            "LONG_HORIZON_ENTROPY_REPORT",
            "error":                             str(exc),
            "total_trades":                      len(trades) if trades else 0,
            "entropy_state":                     "DURABLE",
            "degradation_signal_count":          0,
            "degradation_signals":               [],
            "slow_survivability_erosion":        False,
            "adaptive_instability_accumulation": False,
            "long_cycle_entropy_growth":         False,
            "hidden_degradation_momentum":       False,
            "persistence_weakening":             False,
            "structural_exhaustion":             False,
            "segment_analysis":                  {},
            "diagnostic_only":                   True,
            "auto_authorized":                   False,
            "generated_ts":                      ts_ms,
        }
