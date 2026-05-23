"""
PRP-PHASED.1 — Expectancy Reconstruction Engine.

Decomposes expectancy across 7 dimensional axes to locate where alpha is
created, destroyed, degraded, or temporarily surviving.

Detects:
  - false expectancy (gross positive but net negative)
  - fee-induced expectancy collapse
  - unstable alpha pockets (high variance, low sample size)
  - survivable micro-regions (net positive with sufficient evidence)
  - expectancy decay curves (early vs late trade performance)

DIAGNOSTIC ONLY — no execution authority, no deployment authority.

Pure module — accepts trades: List[dict], no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from collections import defaultdict
from statistics import mean, stdev
from typing import Any, Dict, List, Optional


# ── Hold duration buckets (mirrors economic_truth.py) ────────────────────────
_HOLD_BUCKETS = [
    ("< 1 min",   0,     60),
    ("1–5 min",   60,    300),
    ("5–15 min",  300,   900),
    ("15–30 min", 900,   1800),
    ("> 30 min",  1800,  float("inf")),
]

_MIN_SURVIVABLE_SAMPLE = 5   # min trades in a group to declare survivable micro-region


def _fees(t: dict) -> float:
    return t.get("fee_entry", 0.0) + t.get("fee_exit", 0.0) + t.get("slippage_cost", 0.0)


def _net(t: dict) -> float:
    return t.get("net_pnl", 0.0)


def _gross(t: dict) -> float:
    return t.get("gross_pnl", 0.0)


def _hold_sec(t: dict) -> float:
    entry = t.get("entry_ts", 0) or 0
    exit_ = t.get("exit_ts",  0) or 0
    return max(0.0, (exit_ - entry) / 1000.0)


def _hold_bucket(t: dict) -> str:
    hold = _hold_sec(t)
    for label, lo, hi in _HOLD_BUCKETS:
        if lo <= hold < hi:
            return label
    return "> 30 min"


def _expectancy_stats(subset: List[dict]) -> Dict[str, Any]:
    if not subset:
        return {"count": 0, "net_expectancy": None, "gross_expectancy": None,
                "win_rate": None, "fee_destruction_ratio": None}
    nets   = [_net(t)   for t in subset]
    grosses= [_gross(t) for t in subset]
    wins   = [t for t in subset if _net(t) > 0]
    net_exp   = round(mean(nets),    4)
    gross_exp = round(mean(grosses), 4)

    # Fee destruction ratio: fraction of gross expectancy consumed by costs
    if abs(gross_exp) > 1e-9:
        fdr = round((gross_exp - net_exp) / abs(gross_exp), 4)
    else:
        fdr = None

    # Stability: stdev / |mean|; lower is more stable
    stability: Optional[float] = None
    if len(nets) >= 3 and abs(net_exp) > 1e-9:
        try:
            stability = round(stdev(nets) / abs(net_exp), 2)
        except Exception:
            stability = None

    return {
        "count":                 len(subset),
        "net_expectancy":        net_exp,
        "gross_expectancy":      gross_exp,
        "win_rate":              round(len(wins) / len(subset) * 100, 1),
        "fee_destruction_ratio": fdr,
        "stability_coefficient": stability,
    }


def _classify_group(stats: Dict[str, Any]) -> str:
    """Classify a trade group's expectancy status."""
    if stats["count"] < _MIN_SURVIVABLE_SAMPLE:
        return "INSUFFICIENT_DATA"
    net = stats.get("net_expectancy")
    gross = stats.get("gross_expectancy")
    if net is None or gross is None:
        return "UNKNOWN"
    if net > 0 and gross > 0:
        return "SURVIVABLE"
    if gross > 0 and net <= 0:
        return "FEE_COLLAPSED"  # profitable before fees, dead after
    if net <= 0 and gross <= 0:
        return "TRUE_NEGATIVE"
    return "AMBIGUOUS"


def compute_expectancy_reconstruction(trades: List[dict]) -> dict:
    """
    PRP-PHASED.1 — Decompose expectancy across 7 axes.

    Args:
        trades: Combined session + historical trade dicts.

    Returns EXPECTANCY_RECONSTRUCTION_REPORT; never raises.
    """
    try:
        if not trades:
            return {
                "report":              "EXPECTANCY_RECONSTRUCTION_REPORT",
                "total_trades":        0,
                "note":                "No trades available — diagnostic cannot be computed.",
                "decomposition":       {},
                "false_expectancy_groups": [],
                "fee_collapsed_groups":    [],
                "survivable_regions":      [],
                "expectancy_decay":        {},
                "overall_net_expectancy":  None,
                "overall_gross_expectancy": None,
                "survivability_verdict":   "NO_DATA",
                "diagnostic_only":         True,
                "auto_authorized":         False,
                "generated_ts":            int(_time.time() * 1000),
            }

        # ── Global metrics ───────────────────────────────────────────────────
        global_stats = _expectancy_stats(trades)
        overall_net   = global_stats["net_expectancy"]
        overall_gross = global_stats["gross_expectancy"]

        # ── Axis decomposition ────────────────────────────────────────────────
        axes = {
            "session":        defaultdict(list),
            "regime":         defaultdict(list),
            "strategy":       defaultdict(list),
            "hold_bucket":    defaultdict(list),
        }
        for t in trades:
            sess     = t.get("origin_session", "UNKNOWN") or "UNKNOWN"
            regime   = t.get("regime", "UNKNOWN")         or "UNKNOWN"
            strategy = t.get("strategy_id", "default")    or "default"
            bucket   = _hold_bucket(t)

            axes["session"][sess].append(t)
            axes["regime"][regime].append(t)
            axes["strategy"][strategy].append(t)
            axes["hold_bucket"][bucket].append(t)

        decomposition: Dict[str, Dict[str, Any]] = {}
        false_expectancy_groups: List[dict] = []
        fee_collapsed_groups:    List[dict] = []
        survivable_regions:      List[dict] = []

        for axis_name, groups in axes.items():
            axis_result: Dict[str, Any] = {}
            for group_key, group_trades in sorted(groups.items()):
                stats = _expectancy_stats(group_trades)
                classification = _classify_group(stats)
                entry = {
                    "group":          group_key,
                    "classification": classification,
                    **stats,
                }
                axis_result[group_key] = entry

                if classification == "FEE_COLLAPSED":
                    fee_collapsed_groups.append({
                        "axis": axis_name, "group": group_key, **stats
                    })
                    false_expectancy_groups.append({
                        "axis": axis_name, "group": group_key, **stats
                    })
                elif classification == "SURVIVABLE" and stats["count"] >= _MIN_SURVIVABLE_SAMPLE:
                    survivable_regions.append({
                        "axis": axis_name, "group": group_key, **stats
                    })

            decomposition[axis_name] = axis_result

        # ── Confidence bucket analysis ────────────────────────────────────────
        conf_buckets: Dict[str, List[dict]] = defaultdict(list)
        for t in trades:
            ds = t.get("decision_snapshot") or {}
            conf = ds.get("confidence", None)
            if conf is None:
                bucket = "NO_CONFIDENCE_DATA"
            elif conf >= 0.80:
                bucket = "HIGH (≥0.80)"
            elif conf >= 0.60:
                bucket = "MEDIUM (0.60–0.80)"
            elif conf >= 0.40:
                bucket = "LOW (0.40–0.60)"
            else:
                bucket = "VERY_LOW (<0.40)"
            conf_buckets[bucket].append(t)

        decomposition["confidence_bucket"] = {}
        for bucket, bucket_trades in sorted(conf_buckets.items()):
            stats = _expectancy_stats(bucket_trades)
            classification = _classify_group(stats)
            decomposition["confidence_bucket"][bucket] = {
                "group": bucket, "classification": classification, **stats
            }
            if classification == "FEE_COLLAPSED":
                fee_collapsed_groups.append(
                    {"axis": "confidence_bucket", "group": bucket, **stats}
                )
            elif classification == "SURVIVABLE" and stats["count"] >= _MIN_SURVIVABLE_SAMPLE:
                survivable_regions.append(
                    {"axis": "confidence_bucket", "group": bucket, **stats}
                )

        # ── Fee-adjusted expectancy summary ───────────────────────────────────
        fee_adj = {
            "gross_expectancy": overall_gross,
            "net_expectancy":   overall_net,
            "total_fees_paid":  round(sum(_fees(t) for t in trades), 4),
            "total_gross_pnl":  round(sum(_gross(t) for t in trades), 4),
            "total_net_pnl":    round(sum(_net(t) for t in trades), 4),
            "fee_destruction_ratio": global_stats["fee_destruction_ratio"],
        }
        decomposition["fee_adjusted"] = {"OVERALL": {"group": "OVERALL", **fee_adj}}

        # ── Expectancy decay curve (early vs late halves) ─────────────────────
        sorted_trades = sorted(trades, key=lambda t: t.get("entry_ts", 0))
        half = len(sorted_trades) // 2
        early_stats = _expectancy_stats(sorted_trades[:half]) if half > 0 else {}
        late_stats  = _expectancy_stats(sorted_trades[half:]) if half > 0 else {}
        decay: Optional[float] = None
        if (early_stats.get("net_expectancy") is not None
                and late_stats.get("net_expectancy") is not None):
            decay = round(
                late_stats["net_expectancy"] - early_stats["net_expectancy"], 4
            )
        expectancy_decay = {
            "early_half": early_stats,
            "late_half":  late_stats,
            "decay_delta": decay,
            "trend": (
                "IMPROVING" if decay is not None and decay > 0 else
                "DEGRADING"  if decay is not None and decay < 0 else
                "STABLE"
            ),
        }

        # ── Survivability verdict ─────────────────────────────────────────────
        if overall_net is None:
            verdict = "NO_DATA"
        elif overall_net > 0 and len(survivable_regions) >= 2:
            verdict = "VIABLE"
        elif overall_net > 0:
            verdict = "MARGINALLY_VIABLE"
        elif overall_gross is not None and overall_gross > 0:
            verdict = "FEE_COLLAPSED"  # profitable before fees
        else:
            verdict = "NOT_VIABLE"

        return {
            "report":                    "EXPECTANCY_RECONSTRUCTION_REPORT",
            "total_trades":              len(trades),
            "decomposition":             decomposition,
            "false_expectancy_groups":   false_expectancy_groups,
            "fee_collapsed_groups":      fee_collapsed_groups,
            "survivable_regions":        survivable_regions,
            "survivable_region_count":   len(survivable_regions),
            "expectancy_decay":          expectancy_decay,
            "overall_net_expectancy":    overall_net,
            "overall_gross_expectancy":  overall_gross,
            "total_net_pnl":             round(sum(_net(t) for t in trades), 4),
            "survivability_verdict":     verdict,
            "diagnostic_only":           True,
            "auto_authorized":           False,
            "generated_ts":              int(_time.time() * 1000),
        }

    except Exception as exc:
        return {
            "report":              "EXPECTANCY_RECONSTRUCTION_REPORT",
            "error":               str(exc),
            "total_trades":        len(trades) if trades else 0,
            "decomposition":       {},
            "false_expectancy_groups": [],
            "fee_collapsed_groups":    [],
            "survivable_regions":      [],
            "survivable_region_count": 0,
            "expectancy_decay":        {},
            "overall_net_expectancy":  None,
            "overall_gross_expectancy": None,
            "survivability_verdict":   "ERROR",
            "diagnostic_only":         True,
            "auto_authorized":         False,
            "generated_ts":            int(_time.time() * 1000),
        }
