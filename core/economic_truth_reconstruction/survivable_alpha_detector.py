"""
PRP-PHASED.3 — Survivable Alpha Detector.

Locates statistically survivable alpha pockets across 8 detection domains.
Prioritises localised survivability over global optimism — a negative global
result is reported honestly even if isolated pockets are positive.

DIAGNOSTIC ONLY — no execution authority, no deployment authority.

Pure module — accepts trades: List[dict], no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from collections import defaultdict
from statistics import mean, stdev
from typing import Any, Dict, List, Optional


_MIN_POCKET_SAMPLE = 5   # minimum trades to declare an alpha pocket survivable


def _net(t: dict) -> float:
    return t.get("net_pnl", 0.0)


def _gross(t: dict) -> float:
    return t.get("gross_pnl", 0.0)


def _hold_sec(t: dict) -> float:
    entry = t.get("entry_ts", 0) or 0
    exit_ = t.get("exit_ts",  0) or 0
    return max(0.0, (exit_ - entry) / 1000.0)


def _vol_state(t: dict) -> str:
    """Infer volatility state from regime field."""
    regime = (t.get("regime") or "UNKNOWN").upper()
    if regime == "VOLATILITY_EXPANSION":
        return "HIGH"
    if regime == "MEAN_REVERTING":
        return "LOW"
    if regime == "TRENDING":
        return "MEDIUM"
    return "UNKNOWN"


def _dir_state(t: dict) -> str:
    side = (t.get("side") or "").upper()
    if side in ("BUY", "LONG"):
        return "LONG"
    if side in ("SELL", "SHORT"):
        return "SHORT"
    return "UNKNOWN"


def _trade_density_bucket(count: int) -> str:
    if count >= 50:
        return "DENSE"
    if count >= 20:
        return "MODERATE"
    if count >= 10:
        return "SPARSE"
    return "INSUFFICIENT"


def _alpha_pocket(group_key: str, dimension: str, trades_in_group: List[dict]) -> Optional[dict]:
    """
    Return an alpha pocket dict if this group has statistically survivable alpha.
    Returns None if insufficient data or not survivable.
    """
    if len(trades_in_group) < _MIN_POCKET_SAMPLE:
        return None
    nets = [_net(t) for t in trades_in_group]
    net_exp = mean(nets)
    if net_exp <= 0:
        return None

    wins = [t for t in trades_in_group if _net(t) > 0]
    win_rate = len(wins) / len(trades_in_group)

    # Stability: require win_rate >= 0.40 AND net_exp > 0 for true survivability
    if win_rate < 0.40:
        return None

    std = None
    if len(nets) >= 3:
        try:
            std = round(stdev(nets), 4)
        except Exception:
            pass

    return {
        "dimension":     dimension,
        "group":         group_key,
        "trade_count":   len(trades_in_group),
        "net_expectancy": round(net_exp, 4),
        "win_rate":      round(win_rate * 100, 1),
        "total_net_pnl": round(sum(nets), 4),
        "net_pnl_stdev": std,
        "density":       _trade_density_bucket(len(trades_in_group)),
    }


def detect_survivable_alpha(trades: List[dict]) -> dict:
    """
    PRP-PHASED.3 — Detect survivable alpha pockets across 8 dimensions.

    Detection domains: session, timeframe (hold duration), volatility state,
    market structure (regime), confidence regime, directional state,
    trade density, ecological context (explore vs exploit).

    Args:
        trades: Combined session + historical trade dicts.

    Returns SURVIVABLE_ALPHA_REPORT; never raises.
    """
    try:
        if not trades:
            return {
                "report":              "SURVIVABLE_ALPHA_REPORT",
                "total_trades":        0,
                "note":                "No trades available.",
                "alpha_pockets":       [],
                "pocket_count":        0,
                "dimension_coverage":  {},
                "global_alpha_state":  "NO_DATA",
                "strongest_pocket":    None,
                "survivability_index": 0,
                "diagnostic_only":     True,
                "auto_authorized":     False,
                "generated_ts":        int(_time.time() * 1000),
            }

        alpha_pockets: List[dict] = []
        dimension_coverage: Dict[str, Dict[str, Any]] = {}

        # ── Dimension 1: Session ──────────────────────────────────────────────
        d1: Dict[str, List[dict]] = defaultdict(list)
        for t in trades:
            d1[t.get("origin_session", "UNKNOWN") or "UNKNOWN"].append(t)
        dim_pockets: List[dict] = []
        for k, v in d1.items():
            p = _alpha_pocket(k, "session", v)
            if p:
                dim_pockets.append(p)
                alpha_pockets.append(p)
        dimension_coverage["session"] = {
            "groups_analyzed": len(d1),
            "survivable_pockets": len(dim_pockets),
            "groups": list(d1.keys()),
        }

        # ── Dimension 2: Timeframe (hold duration) ────────────────────────────
        d2: Dict[str, List[dict]] = defaultdict(list)
        _tf_buckets = [
            ("< 1 min", 0, 60), ("1–5 min", 60, 300),
            ("5–15 min", 300, 900), ("15–30 min", 900, 1800),
            ("> 30 min", 1800, float("inf")),
        ]
        for t in trades:
            hold = _hold_sec(t)
            for label, lo, hi in _tf_buckets:
                if lo <= hold < hi:
                    d2[label].append(t)
                    break
        dim_pockets = []
        for k, v in d2.items():
            p = _alpha_pocket(k, "timeframe", v)
            if p:
                dim_pockets.append(p)
                alpha_pockets.append(p)
        dimension_coverage["timeframe"] = {
            "groups_analyzed": len(d2),
            "survivable_pockets": len(dim_pockets),
        }

        # ── Dimension 3: Volatility State ─────────────────────────────────────
        d3: Dict[str, List[dict]] = defaultdict(list)
        for t in trades:
            d3[_vol_state(t)].append(t)
        dim_pockets = []
        for k, v in d3.items():
            p = _alpha_pocket(k, "volatility", v)
            if p:
                dim_pockets.append(p)
                alpha_pockets.append(p)
        dimension_coverage["volatility"] = {
            "groups_analyzed": len(d3),
            "survivable_pockets": len(dim_pockets),
        }

        # ── Dimension 4: Market Structure (Regime) ────────────────────────────
        d4: Dict[str, List[dict]] = defaultdict(list)
        for t in trades:
            d4[t.get("regime", "UNKNOWN") or "UNKNOWN"].append(t)
        dim_pockets = []
        for k, v in d4.items():
            p = _alpha_pocket(k, "market_structure", v)
            if p:
                dim_pockets.append(p)
                alpha_pockets.append(p)
        dimension_coverage["market_structure"] = {
            "groups_analyzed": len(d4),
            "survivable_pockets": len(dim_pockets),
            "regimes_seen": sorted(d4.keys()),
        }

        # ── Dimension 5: Confidence Regime ────────────────────────────────────
        d5: Dict[str, List[dict]] = defaultdict(list)
        for t in trades:
            ds = t.get("decision_snapshot") or {}
            conf = ds.get("confidence", None)
            if conf is None:
                bucket = "NO_CONFIDENCE_DATA"
            elif conf >= 0.80:
                bucket = "HIGH (≥0.80)"
            elif conf >= 0.60:
                bucket = "MEDIUM"
            else:
                bucket = "LOW (<0.60)"
            d5[bucket].append(t)
        dim_pockets = []
        for k, v in d5.items():
            p = _alpha_pocket(k, "confidence_regime", v)
            if p:
                dim_pockets.append(p)
                alpha_pockets.append(p)
        dimension_coverage["confidence_regime"] = {
            "groups_analyzed": len(d5),
            "survivable_pockets": len(dim_pockets),
        }

        # ── Dimension 6: Directional State ────────────────────────────────────
        d6: Dict[str, List[dict]] = defaultdict(list)
        for t in trades:
            d6[_dir_state(t)].append(t)
        dim_pockets = []
        for k, v in d6.items():
            p = _alpha_pocket(k, "directional_state", v)
            if p:
                dim_pockets.append(p)
                alpha_pockets.append(p)
        dimension_coverage["directional_state"] = {
            "groups_analyzed": len(d6),
            "survivable_pockets": len(dim_pockets),
        }

        # ── Dimension 7: Trade Density ────────────────────────────────────────
        d7: Dict[str, List[dict]] = defaultdict(list)
        for t in trades:
            regime = t.get("regime", "UNKNOWN") or "UNKNOWN"
            sess   = t.get("origin_session", "UNKNOWN") or "UNKNOWN"
            key    = f"{regime}|{sess}"
            d7[key].append(t)
        dim_pockets = []
        for k, v in sorted(d7.items()):
            if len(v) >= _MIN_POCKET_SAMPLE:
                p = _alpha_pocket(k, "trade_density", v)
                if p:
                    dim_pockets.append(p)
                    alpha_pockets.append(p)
        dimension_coverage["trade_density"] = {
            "groups_analyzed": len(d7),
            "survivable_pockets": len(dim_pockets),
        }

        # ── Dimension 8: Ecological Context ───────────────────────────────────
        d8: Dict[str, List[dict]] = defaultdict(list)
        for t in trades:
            eo = t.get("exploration_origin") or {}
            if eo.get("was_exploration_trade"):
                eco_ctx = "EXPLORATION"
            else:
                eco_ctx = "EXPLOITATION"
            d8[eco_ctx].append(t)
        dim_pockets = []
        for k, v in d8.items():
            p = _alpha_pocket(k, "ecological_context", v)
            if p:
                dim_pockets.append(p)
                alpha_pockets.append(p)
        dimension_coverage["ecological_context"] = {
            "groups_analyzed": len(d8),
            "survivable_pockets": len(dim_pockets),
        }

        # ── Global alpha state ────────────────────────────────────────────────
        all_nets = [_net(t) for t in trades]
        global_net_exp = mean(all_nets)

        pocket_count = len(alpha_pockets)
        if global_net_exp > 0 and pocket_count >= 3:
            global_state = "VIABLE"
        elif global_net_exp > 0 or pocket_count >= 2:
            global_state = "LOCALIZED"
        elif pocket_count >= 1:
            global_state = "MICRO_POCKETS_ONLY"
        else:
            global_state = "NO_SURVIVABLE_ALPHA"

        # Strongest pocket by net expectancy
        strongest = (
            max(alpha_pockets, key=lambda p: p["net_expectancy"])
            if alpha_pockets else None
        )

        # Survivability index: pockets found / dimensions checked (0–100)
        survivability_index = min(100, round(pocket_count / 8 * 100))

        return {
            "report":              "SURVIVABLE_ALPHA_REPORT",
            "total_trades":        len(trades),
            "alpha_pockets":       alpha_pockets,
            "pocket_count":        pocket_count,
            "dimension_coverage":  dimension_coverage,
            "global_net_expectancy": round(global_net_exp, 4),
            "global_alpha_state":  global_state,
            "strongest_pocket":    strongest,
            "survivability_index": survivability_index,
            "diagnostic_only":     True,
            "auto_authorized":     False,
            "generated_ts":        int(_time.time() * 1000),
        }

    except Exception as exc:
        return {
            "report":              "SURVIVABLE_ALPHA_REPORT",
            "error":               str(exc),
            "total_trades":        len(trades) if trades else 0,
            "alpha_pockets":       [],
            "pocket_count":        0,
            "dimension_coverage":  {},
            "global_alpha_state":  "ERROR",
            "strongest_pocket":    None,
            "survivability_index": 0,
            "diagnostic_only":     True,
            "auto_authorized":     False,
            "generated_ts":        int(_time.time() * 1000),
        }
