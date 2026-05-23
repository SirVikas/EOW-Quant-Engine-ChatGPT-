"""
PRP-PHASED.2 — Fee Drag Intelligence Engine.

Models true economic destruction caused by fees, slippage, and execution costs.
Detects "profitable before fees, dead after fees" conditions with statistical
precision. Prioritises truth over optically favourable presentation.

DIAGNOSTIC ONLY — no execution authority, no deployment authority.

Pure module — accepts trades: List[dict], no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from collections import defaultdict
from statistics import mean
from typing import Any, Dict, List, Optional


# ── Classification thresholds (mirrors economic_truth.py) ─────────────────────
_HIGH_FEE_DRAG_PCT      = 80.0   # above this = UNSURVIVABLE payoff geometry
_SURVIVABLE_FEE_DRAG_PCT = 50.0  # 50–80% = borderline survivable


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


def _fee_drag_pct(fees: float, gross: float) -> Optional[float]:
    if gross <= 1e-9:
        return None
    return round(fees / gross * 100.0, 2)


def compute_fee_drag_intelligence(trades: List[dict]) -> dict:
    """
    PRP-PHASED.2 — Compute comprehensive fee drag intelligence.

    Detects "profitable before fees, dead after fees" conditions.
    Identifies trade frequency toxicity (too many trades → cumulative fee destruction).

    Args:
        trades: Combined session + historical trade dicts.

    Returns FEE_DRAG_INTELLIGENCE_REPORT; never raises.
    """
    try:
        if not trades:
            return {
                "report":                      "FEE_DRAG_INTELLIGENCE_REPORT",
                "total_trades":                0,
                "note":                        "No trades available.",
                "gross_expectancy":            None,
                "net_expectancy":              None,
                "fee_destruction_ratio":       None,
                "slippage_destruction":        None,
                "execution_inefficiency":      None,
                "cost_adjusted_survivability": "NO_DATA",
                "trade_frequency_toxicity":    "NO_DATA",
                "fee_collapsed_trade_count":   0,
                "fee_collapsed_pct":           None,
                "fee_drag_distribution":       {},
                "session_fee_analysis":        {},
                "regime_fee_analysis":         {},
                "worst_fee_patterns":          [],
                "diagnostic_only":             True,
                "auto_authorized":             False,
                "generated_ts":               int(_time.time() * 1000),
            }

        # ── Global aggregates ─────────────────────────────────────────────────
        total   = len(trades)
        nets    = [_net(t)   for t in trades]
        grosses = [_gross(t) for t in trades]
        fees    = [_fees(t)  for t in trades]

        total_gross = sum(grosses)
        total_net   = sum(nets)
        total_fees  = sum(fees)
        total_slippage = sum(t.get("slippage_cost", 0.0) for t in trades)

        gross_exp = round(mean(grosses), 4)
        net_exp   = round(mean(nets),    4)

        # Fee destruction ratio: what fraction of gross expectancy is consumed
        fee_destruction_ratio: Optional[float] = None
        if abs(gross_exp) > 1e-9:
            fee_destruction_ratio = round((gross_exp - net_exp) / abs(gross_exp), 4)

        # Slippage destruction (slippage as fraction of gross)
        slippage_destruction: Optional[float] = None
        if abs(total_gross) > 1e-9:
            slippage_destruction = round(total_slippage / abs(total_gross), 4)

        # Execution inefficiency: total_fees / total_gross
        execution_inefficiency: Optional[float] = None
        if abs(total_gross) > 1e-9:
            execution_inefficiency = round(total_fees / abs(total_gross), 4)

        # ── "Profitable before fees, dead after fees" detection ───────────────
        fee_collapsed: List[dict] = []
        for t in trades:
            gross = _gross(t)
            net   = _net(t)
            if gross > 0 and net <= 0:
                fee_collapsed.append(t)

        fee_collapsed_pct = round(len(fee_collapsed) / total * 100, 1) if total else None

        # ── Cost-adjusted survivability ───────────────────────────────────────
        if total == 0 or gross_exp is None:
            cas = "NO_DATA"
        elif net_exp > 0 and fee_destruction_ratio is not None and fee_destruction_ratio < 0.50:
            cas = "SURVIVABLE"
        elif net_exp > 0:
            cas = "MARGINALLY_SURVIVABLE"
        elif gross_exp > 0 and net_exp <= 0:
            cas = "FEE_COLLAPSED"
        else:
            cas = "NOT_SURVIVABLE"

        # ── Trade frequency toxicity ──────────────────────────────────────────
        # Too many trades → cumulative fee drag exceeds gross expectancy
        # Heuristic: if avg fee per trade > |net_exp|, frequency is toxic
        avg_fee_per_trade = round(mean(fees), 6) if fees else 0.0
        if avg_fee_per_trade == 0:
            tft = "NO_COST_DATA"
        elif net_exp <= 0 and total_fees > abs(total_net):
            tft = "CRITICALLY_TOXIC"
        elif net_exp > 0 and avg_fee_per_trade > abs(net_exp) * 0.80:
            tft = "HIGH_RISK"
        elif avg_fee_per_trade > abs(net_exp) * 0.50:
            tft = "ELEVATED"
        else:
            tft = "ACCEPTABLE"

        # ── Fee drag distribution by bucket ───────────────────────────────────
        drag_dist: Dict[str, Dict[str, Any]] = {
            "UNSURVIVABLE":    {"count": 0, "trades": []},  # fee_drag > 80%
            "HIGH_DRAG":       {"count": 0, "trades": []},  # 50–80%
            "MODERATE_DRAG":   {"count": 0, "trades": []},  # 20–50%
            "LOW_DRAG":        {"count": 0, "trades": []},  # 0–20%
            "NEGATIVE_GROSS":  {"count": 0, "trades": []},  # gross ≤ 0 (drag undefined)
        }
        for t in trades:
            gross = _gross(t)
            fee   = _fees(t)
            drag  = _fee_drag_pct(fee, gross)
            if drag is None:
                drag_dist["NEGATIVE_GROSS"]["count"] += 1
            elif drag >= _HIGH_FEE_DRAG_PCT:
                drag_dist["UNSURVIVABLE"]["count"] += 1
            elif drag >= _SURVIVABLE_FEE_DRAG_PCT:
                drag_dist["HIGH_DRAG"]["count"] += 1
            elif drag >= 20.0:
                drag_dist["MODERATE_DRAG"]["count"] += 1
            else:
                drag_dist["LOW_DRAG"]["count"] += 1

        # ── Session-level fee analysis ────────────────────────────────────────
        sess_groups: Dict[str, List[dict]] = defaultdict(list)
        for t in trades:
            sess_groups[t.get("origin_session", "UNKNOWN") or "UNKNOWN"].append(t)

        session_fee_analysis: Dict[str, Any] = {}
        for sess, sess_trades in sorted(sess_groups.items()):
            s_gross = sum(_gross(t) for t in sess_trades)
            s_net   = sum(_net(t)   for t in sess_trades)
            s_fees  = sum(_fees(t)  for t in sess_trades)
            s_fdr   = None
            if abs(s_gross) > 1e-9:
                s_fdr = round(s_fees / abs(s_gross) * 100, 1)
            session_fee_analysis[sess] = {
                "count":          len(sess_trades),
                "total_gross":    round(s_gross, 4),
                "total_net":      round(s_net, 4),
                "total_fees":     round(s_fees, 4),
                "fee_drag_pct":   s_fdr,
                "verdict":        (
                    "FEE_COLLAPSED" if s_gross > 0 and s_net <= 0 else
                    "SURVIVABLE"    if s_net > 0 else
                    "TRUE_NEGATIVE"
                ),
            }

        # ── Regime-level fee analysis ─────────────────────────────────────────
        regime_groups: Dict[str, List[dict]] = defaultdict(list)
        for t in trades:
            regime_groups[t.get("regime", "UNKNOWN") or "UNKNOWN"].append(t)

        regime_fee_analysis: Dict[str, Any] = {}
        for regime, r_trades in sorted(regime_groups.items()):
            r_gross = sum(_gross(t) for t in r_trades)
            r_net   = sum(_net(t)   for t in r_trades)
            r_fees  = sum(_fees(t)  for t in r_trades)
            r_fdr   = None
            if abs(r_gross) > 1e-9:
                r_fdr = round(r_fees / abs(r_gross) * 100, 1)
            regime_fee_analysis[regime] = {
                "count":        len(r_trades),
                "total_gross":  round(r_gross, 4),
                "total_net":    round(r_net, 4),
                "fee_drag_pct": r_fdr,
            }

        # ── Worst fee patterns (top 5 fee-collapsed groups) ───────────────────
        worst_patterns: List[dict] = []
        all_analysis = (
            [{"dim": "session", "key": k, **v}
             for k, v in session_fee_analysis.items()]
            + [{"dim": "regime", "key": k, **v}
               for k, v in regime_fee_analysis.items()]
        )
        worst_patterns = sorted(
            [p for p in all_analysis
             if p.get("fee_drag_pct") is not None and p.get("fee_drag_pct", 0) >= 50],
            key=lambda p: p.get("fee_drag_pct", 0),
            reverse=True,
        )[:5]

        return {
            "report":                      "FEE_DRAG_INTELLIGENCE_REPORT",
            "total_trades":                total,
            "gross_expectancy":            gross_exp,
            "net_expectancy":              net_exp,
            "total_gross_pnl":             round(total_gross, 4),
            "total_net_pnl":               round(total_net, 4),
            "total_fees_paid":             round(total_fees, 4),
            "total_slippage":              round(total_slippage, 4),
            "avg_fee_per_trade":           avg_fee_per_trade,
            "fee_destruction_ratio":       fee_destruction_ratio,
            "slippage_destruction":        slippage_destruction,
            "execution_inefficiency":      execution_inefficiency,
            "cost_adjusted_survivability": cas,
            "trade_frequency_toxicity":    tft,
            "fee_collapsed_trade_count":   len(fee_collapsed),
            "fee_collapsed_pct":           fee_collapsed_pct,
            "fee_drag_distribution":       {k: v["count"] for k, v in drag_dist.items()},
            "session_fee_analysis":        session_fee_analysis,
            "regime_fee_analysis":         regime_fee_analysis,
            "worst_fee_patterns":          worst_patterns,
            "diagnostic_only":             True,
            "auto_authorized":             False,
            "generated_ts":               int(_time.time() * 1000),
        }

    except Exception as exc:
        return {
            "report":                      "FEE_DRAG_INTELLIGENCE_REPORT",
            "error":                       str(exc),
            "total_trades":                len(trades) if trades else 0,
            "gross_expectancy":            None,
            "net_expectancy":              None,
            "fee_destruction_ratio":       None,
            "slippage_destruction":        None,
            "execution_inefficiency":      None,
            "cost_adjusted_survivability": "ERROR",
            "trade_frequency_toxicity":    "ERROR",
            "fee_collapsed_trade_count":   0,
            "fee_collapsed_pct":           None,
            "fee_drag_distribution":       {},
            "session_fee_analysis":        {},
            "regime_fee_analysis":         {},
            "worst_fee_patterns":          [],
            "diagnostic_only":             True,
            "auto_authorized":             False,
            "generated_ts":               int(_time.time() * 1000),
        }
