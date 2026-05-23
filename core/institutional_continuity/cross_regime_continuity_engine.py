"""
PRP-PHASED.H.5 — Cross-Regime Continuity Engine.

Measures whether survivability persists across radically different market
environments: trending eras, ranging eras, volatility expansions, compressions,
liquidity shifts, and structural instability eras.

Distinguishes environment-specific survivability from cross-regime continuity.

DIAGNOSTIC ONLY — no execution authority, no deployment authority.

Pure module — accepts trades: List[dict], no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from collections import defaultdict
from statistics import mean
from typing import Any, Dict, List, Optional


def _net(t: dict) -> float:
    return t.get("net_pnl", 0.0)


def _hold_sec(t: dict) -> float:
    return max(0.0, ((t.get("exit_ts") or 0) - (t.get("entry_ts") or 0)) / 1000.0)


def _classify_env(t: dict) -> str:
    regime = (t.get("regime") or "UNKNOWN").upper()
    hold   = _hold_sec(t)
    if regime == "TRENDING":
        return "TRENDING"
    if regime == "MEAN_REVERTING":
        if hold < 300:
            return "COMPRESSION"
        return "RANGING"
    if regime == "VOLATILITY_EXPANSION":
        return "VOLATILITY_EXPANSION"
    if regime == "UNKNOWN":
        return "STRUCTURAL_INSTABILITY"
    return "STRUCTURAL_INSTABILITY"


def _env_metrics(env: str, trades: List[dict]) -> Dict[str, Any]:
    if not trades:
        return {"environment": env, "trade_count": 0, "survivability": "NO_DATA"}
    nets   = [_net(t) for t in trades]
    ne     = round(mean(nets), 4)
    wins   = sum(1 for n in nets if n > 0)
    wr     = round(wins / len(trades) * 100, 1)
    if len(trades) < 3:
        surv = "INSUFFICIENT_DATA"
    elif ne > 0 and wr >= 40:
        surv = "SURVIVABLE"
    elif ne > 0:
        surv = "MARGINAL"
    else:
        surv = "NOT_SURVIVABLE"
    return {
        "environment":   env,
        "trade_count":   len(trades),
        "net_expectancy": ne,
        "win_rate":       wr,
        "survivability":  surv,
    }


def compute_cross_regime_continuity(trades: List[dict]) -> dict:
    """
    PRP-PHASED.H.5 — Evaluate survivability continuity across 6 environments.

    Args:
        trades: Combined session + historical trade dicts.

    Returns CROSS_REGIME_CONTINUITY_REPORT; never raises.
    """
    ts_ms = int(_time.time() * 1000)

    try:
        if not trades:
            return {
                "report":                    "CROSS_REGIME_CONTINUITY_REPORT",
                "total_trades":              0,
                "note":                      "No trades available.",
                "environment_analysis":      {},
                "survivable_environments":   [],
                "non_survivable_environments": [],
                "continuity_score":          0,
                "continuity_type":           "ENVIRONMENT_SPECIFIC",
                "continuity_verdict":        "NO_DATA",
                "diagnostic_only":           True,
                "auto_authorized":           False,
                "generated_ts":              ts_ms,
            }

        # ── Detect liquidity-shift environment: fast-trade-dense windows ──────
        sorted_t = sorted(trades, key=lambda t: t.get("entry_ts", 0))
        liquidity_shift_ids: set = set()
        window_ms = 300_000  # 5-minute windows
        if sorted_t:
            first_ts = sorted_t[0].get("entry_ts", 0) or 0
            last_ts  = sorted_t[-1].get("entry_ts", 0) or 0
            ws = first_ts
            while ws <= last_ts:
                we = ws + window_ms
                win_trades = [t for t in sorted_t
                              if (t.get("entry_ts") or 0) >= ws and (t.get("entry_ts") or 0) < we]
                if len(win_trades) >= 5:
                    fast = sum(1 for t in win_trades if _hold_sec(t) < 60)
                    if fast / len(win_trades) > 0.50:
                        for t in win_trades:
                            liquidity_shift_ids.add(t.get("trade_id", ""))
                ws += window_ms

        # ── Group by environment ───────────────────────────────────────────────
        env_groups: Dict[str, List[dict]] = defaultdict(list)
        for t in sorted_t:
            tid = t.get("trade_id", "")
            if tid in liquidity_shift_ids:
                env_groups["LIQUIDITY_SHIFT"].append(t)
            else:
                env_groups[_classify_env(t)].append(t)

        env_analysis: Dict[str, Any] = {}
        for env in ("TRENDING","RANGING","VOLATILITY_EXPANSION","COMPRESSION",
                    "LIQUIDITY_SHIFT","STRUCTURAL_INSTABILITY"):
            env_analysis[env] = _env_metrics(env, env_groups.get(env, []))

        survivable     = [e for e, m in env_analysis.items()
                          if m.get("survivability") in ("SURVIVABLE", "MARGINAL")
                          and m.get("trade_count", 0) >= 3]
        non_survivable = [e for e, m in env_analysis.items()
                          if m.get("survivability") == "NOT_SURVIVABLE"
                          and m.get("trade_count", 0) >= 3]

        qualified = [e for e, m in env_analysis.items() if m.get("trade_count", 0) >= 3]
        score = round(len(survivable) / max(1, len(qualified)) * 100) if qualified else 0

        if len(survivable) >= 4:
            ctype   = "CROSS_REGIME_CONTINUITY"
            verdict = "UNIVERSAL"
        elif len(survivable) >= 2:
            ctype   = "CROSS_REGIME_CONTINUITY"
            verdict = "BROAD"
        elif len(survivable) == 1:
            ctype   = "ENVIRONMENT_SPECIFIC"
            verdict = "NARROW"
        elif survivable:
            ctype   = "ENVIRONMENT_SPECIFIC"
            verdict = "FRAGILE"
        else:
            ctype   = "ENVIRONMENT_SPECIFIC"
            verdict = "NO_DATA" if not qualified else "NOT_SURVIVABLE_ANY"

        return {
            "report":                      "CROSS_REGIME_CONTINUITY_REPORT",
            "total_trades":                len(trades),
            "environment_analysis":        env_analysis,
            "survivable_environments":     survivable,
            "non_survivable_environments": non_survivable,
            "continuity_score":            score,
            "continuity_type":             ctype,
            "continuity_verdict":          verdict,
            "qualified_environment_count": len(qualified),
            "diagnostic_only":             True,
            "auto_authorized":             False,
            "generated_ts":                ts_ms,
        }

    except Exception as exc:
        return {
            "report":                      "CROSS_REGIME_CONTINUITY_REPORT",
            "error":                       str(exc),
            "total_trades":                len(trades) if trades else 0,
            "environment_analysis":        {},
            "survivable_environments":     [],
            "non_survivable_environments": [],
            "continuity_score":            0,
            "continuity_type":             "ENVIRONMENT_SPECIFIC",
            "continuity_verdict":          "NO_DATA",
            "diagnostic_only":             True,
            "auto_authorized":             False,
            "generated_ts":                ts_ms,
        }
