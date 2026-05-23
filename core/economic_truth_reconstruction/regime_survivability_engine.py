"""
PRP-PHASED.5 — Regime Survivability Engine.

Determines which market regimes are economically survivable by classifying
6 regime categories and computing regime-specific alpha persistence,
expectancy decay, fee vulnerability, instability risk, and transition fragility.

DIAGNOSTIC ONLY — no execution authority, no deployment authority.

Pure module — accepts trades: List[dict], no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from collections import defaultdict
from statistics import mean, stdev
from typing import Any, Dict, List, Optional


# ── 6 mandatory regime classifications ───────────────────────────────────────
# Trade records use: TRENDING, MEAN_REVERTING, VOLATILITY_EXPANSION, UNKNOWN
# Map to the 6 FTD-required categories:
_REGIME_MAP: Dict[str, str] = {
    "TRENDING":            "TRENDING",
    "MEAN_REVERTING":      "RANGING",
    "VOLATILITY_EXPANSION":"EXPANSION",
    "UNKNOWN":             "UNCLASSIFIED",
}
_REQUIRED_REGIMES = frozenset({
    "TRENDING", "RANGING", "EXPANSION",
    "COMPRESSION",   # inferred: mean-reverting with low volatility
    "HIGH_VOLATILITY",   # inferred: vol_expansion + fast trades
    "LOW_VOLATILITY",    # inferred: slow trades in ranging regime
    "UNCLASSIFIED",
})
_MIN_REGIME_SAMPLE = 5


def _net(t: dict) -> float:
    return t.get("net_pnl", 0.0)


def _gross(t: dict) -> float:
    return t.get("gross_pnl", 0.0)


def _fees(t: dict) -> float:
    return t.get("fee_entry", 0.0) + t.get("fee_exit", 0.0) + t.get("slippage_cost", 0.0)


def _hold_sec(t: dict) -> float:
    entry = t.get("entry_ts", 0) or 0
    exit_ = t.get("exit_ts",  0) or 0
    return max(0.0, (exit_ - entry) / 1000.0)


def _map_regime(t: dict) -> str:
    raw = (t.get("regime") or "UNKNOWN").upper()
    return _REGIME_MAP.get(raw, "UNCLASSIFIED")


def _infer_extended_regime(t: dict, base: str) -> str:
    """Infer compression/high_volatility/low_volatility from base regime + hold time."""
    hold = _hold_sec(t)
    if base == "EXPANSION" and hold < 60:
        return "HIGH_VOLATILITY"
    if base == "RANGING" and hold > 900:
        return "LOW_VOLATILITY"
    if base == "RANGING" and hold < 300:
        return "COMPRESSION"
    return base


def _regime_metrics(regime: str, trades: List[dict]) -> Dict[str, Any]:
    if not trades:
        return {"regime": regime, "trade_count": 0, "survivability": "NO_DATA"}

    nets   = [_net(t)   for t in trades]
    grosses = [_gross(t) for t in trades]
    fees_list = [_fees(t) for t in trades]

    net_exp   = round(mean(nets),    4)
    gross_exp = round(mean(grosses), 4)
    total_fees = sum(fees_list)
    total_gross = sum(grosses)

    wins = [t for t in trades if _net(t) > 0]
    win_rate = round(len(wins) / len(trades) * 100, 1)

    # Fee vulnerability: fees / gross PnL
    fee_vulnerability: Optional[float] = None
    if abs(total_gross) > 1e-9:
        fee_vulnerability = round(total_fees / abs(total_gross), 4)

    # Alpha persistence: ratio of consecutive positive runs
    positive_runs = 0
    total_runs    = 0
    in_run = False
    for net in nets:
        if net > 0:
            if not in_run:
                positive_runs += 1
                in_run = True
        else:
            in_run = False
        total_runs += 1
    alpha_persistence = round(positive_runs / total_runs, 4) if total_runs else 0.0

    # Expectancy stability (stdev / |mean|)
    stability: Optional[float] = None
    if len(nets) >= 3 and abs(net_exp) > 1e-9:
        try:
            stability = round(stdev(nets) / abs(net_exp), 2)
        except Exception:
            pass

    # Survivability classification
    if len(trades) < _MIN_REGIME_SAMPLE:
        surv = "INSUFFICIENT_DATA"
    elif net_exp > 0 and win_rate >= 40:
        surv = "SURVIVABLE"
    elif net_exp > 0:
        surv = "MARGINAL"
    elif gross_exp > 0 and net_exp <= 0:
        surv = "FEE_COLLAPSED"
    else:
        surv = "NOT_SURVIVABLE"

    # Expectancy decay: early vs late in this regime
    sorted_t = sorted(trades, key=lambda t: t.get("entry_ts", 0))
    half = len(sorted_t) // 2
    early_exp = round(mean([_net(t) for t in sorted_t[:half]]), 4) if half > 0 else None
    late_exp  = round(mean([_net(t) for t in sorted_t[half:]]), 4) if len(sorted_t) > half else None
    decay_delta = round(late_exp - early_exp, 4) if early_exp is not None and late_exp is not None else None

    # Instability risk: high stdev relative to mean, or many flip-flops
    instability_risk = "UNKNOWN"
    if stability is not None:
        if stability > 3.0:
            instability_risk = "HIGH"
        elif stability > 1.5:
            instability_risk = "MODERATE"
        else:
            instability_risk = "LOW"

    return {
        "regime":             regime,
        "trade_count":        len(trades),
        "net_expectancy":     net_exp,
        "gross_expectancy":   gross_exp,
        "win_rate":           win_rate,
        "fee_vulnerability":  fee_vulnerability,
        "alpha_persistence":  alpha_persistence,
        "stability_coeff":    stability,
        "early_expectancy":   early_exp,
        "late_expectancy":    late_exp,
        "expectancy_decay_delta": decay_delta,
        "instability_risk":   instability_risk,
        "survivability":      surv,
    }


def compute_regime_survivability(trades: List[dict]) -> dict:
    """
    PRP-PHASED.5 — Classify survivability across 6 regime categories.

    Detects regime-specific alpha persistence, expectancy decay, fee
    vulnerability, instability risk, and transition fragility.

    Args:
        trades: Combined session + historical trade dicts.

    Returns REGIME_SURVIVABILITY_REPORT; never raises.
    """
    try:
        if not trades:
            return {
                "report":              "REGIME_SURVIVABILITY_REPORT",
                "total_trades":        0,
                "note":                "No trades available.",
                "regime_analysis":     {},
                "survivable_regimes":  [],
                "collapsed_regimes":   [],
                "transition_fragility": {},
                "dominant_regime":     None,
                "overall_regime_health": "NO_DATA",
                "diagnostic_only":     True,
                "auto_authorized":     False,
                "generated_ts":        int(_time.time() * 1000),
            }

        # ── Group trades by extended regime ────────────────────────────────────
        regime_groups: Dict[str, List[dict]] = defaultdict(list)
        for t in trades:
            base = _map_regime(t)
            ext  = _infer_extended_regime(t, base)
            regime_groups[ext].append(t)

        # ── Analyse each regime ────────────────────────────────────────────────
        regime_analysis: Dict[str, Any] = {}
        survivable_regimes: List[str]   = []
        collapsed_regimes:  List[str]   = []

        for regime, r_trades in sorted(regime_groups.items()):
            metrics = _regime_metrics(regime, r_trades)
            regime_analysis[regime] = metrics
            if metrics["survivability"] == "SURVIVABLE":
                survivable_regimes.append(regime)
            elif metrics["survivability"] in ("FEE_COLLAPSED", "NOT_SURVIVABLE"):
                collapsed_regimes.append(regime)

        # ── Transition fragility: expectancy delta between consecutive regime pairs ─
        sorted_trades = sorted(trades, key=lambda t: t.get("entry_ts", 0))
        transition_pairs: Dict[str, List[float]] = defaultdict(list)
        prev_regime = None
        for t in sorted_trades:
            base = _map_regime(t)
            curr_regime = _infer_extended_regime(t, base)
            if prev_regime and prev_regime != curr_regime:
                pair_key = f"{prev_regime}→{curr_regime}"
                transition_pairs[pair_key].append(_net(t))
            prev_regime = curr_regime

        transition_fragility: Dict[str, Any] = {}
        for pair, nets in transition_pairs.items():
            exp = round(mean(nets), 4)
            transition_fragility[pair] = {
                "count":          len(nets),
                "net_expectancy": exp,
                "fragile":        exp < 0,
            }

        # ── Dominant regime ───────────────────────────────────────────────────
        dominant_regime: Optional[str] = None
        if regime_groups:
            dominant_regime = max(regime_groups, key=lambda k: len(regime_groups[k]))

        # ── Overall regime health ─────────────────────────────────────────────
        if not regime_groups:
            overall_health = "NO_DATA"
        elif len(survivable_regimes) >= 2:
            overall_health = "MULTI_REGIME_VIABLE"
        elif len(survivable_regimes) == 1:
            overall_health = "SINGLE_REGIME_VIABLE"
        elif len(collapsed_regimes) == len(regime_groups):
            overall_health = "ALL_REGIMES_COLLAPSED"
        else:
            overall_health = "REGIME_FRAGMENTED"

        return {
            "report":               "REGIME_SURVIVABILITY_REPORT",
            "total_trades":         len(trades),
            "regime_analysis":      regime_analysis,
            "regime_count":         len(regime_analysis),
            "survivable_regimes":   survivable_regimes,
            "collapsed_regimes":    collapsed_regimes,
            "survivable_regime_count": len(survivable_regimes),
            "collapsed_regime_count":  len(collapsed_regimes),
            "transition_fragility": transition_fragility,
            "dominant_regime":      dominant_regime,
            "overall_regime_health": overall_health,
            "diagnostic_only":      True,
            "auto_authorized":      False,
            "generated_ts":         int(_time.time() * 1000),
        }

    except Exception as exc:
        return {
            "report":              "REGIME_SURVIVABILITY_REPORT",
            "error":               str(exc),
            "total_trades":        len(trades) if trades else 0,
            "regime_analysis":     {},
            "survivable_regimes":  [],
            "collapsed_regimes":   [],
            "transition_fragility": {},
            "dominant_regime":     None,
            "overall_regime_health": "ERROR",
            "diagnostic_only":     True,
            "auto_authorized":     False,
            "generated_ts":        int(_time.time() * 1000),
        }
