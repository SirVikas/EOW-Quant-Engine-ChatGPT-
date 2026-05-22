"""
FTD-TF-SURVIV: Timeframe Economics Comparator & Alpha Survivability Mapping.

Pure analytics — no I/O, no side effects, no execution authority.

Shadow 5m/15m projections are HYPOTHETICAL: they assume the same directional
signal, if held for multiplier× longer, captures proportionally more gross PnL.
Fees remain constant (same notional). Research instrumentation only.

All execution decisions after evidence accumulation remain at developer discretion.
"""
from __future__ import annotations

from statistics import mean
from typing import Dict, List, Optional

from core.economic_truth import compute_economic_ground_truth

# ── Timeframe multiplier map ──────────────────────────────────────────────────
TF_MULTIPLIERS: Dict[str, int] = {"1m": 1, "5m": 5, "15m": 15}

# ── Alpha persistence research categories ─────────────────────────────────────
TF_ALPHA_PERSISTENT   = "TF_ALPHA_PERSISTENT"    # score >= 75 at every TF
TIMEFRAME_CONSISTENT  = "TIMEFRAME_CONSISTENT"   # score >= 50 at every TF
MICROSTRUCTURE_ERODED = "MICROSTRUCTURE_ERODED"  # fails at 1m, survives at 5m or 15m
HIGHER_TF_RECOVERY    = "HIGHER_TF_RECOVERY"     # expectancy improves toward higher TF
TF_NOISE_COLLAPSE     = "TF_NOISE_COLLAPSE"      # edge absent at all TFs


# ── Per-trade TF projection ───────────────────────────────────────────────────

def project_trade_to_tf(trade: dict, multiplier: int) -> dict:
    """
    Return a projected trade dict for shadow TF analysis.

    multiplier=1 (1m): shallow copy, pre-computed economic_truth preserved so
    downstream analytics use the actual cached classification.

    multiplier>1: gross_pnl scaled by multiplier, fees unchanged, net_pnl
    recomputed, exit_ts scaled to simulate longer hold duration. economic_truth
    removed so _get_eco recomputes from projected values.

    Never mutates the input dict. Fail-open: projection errors return a copy.
    """
    proj = dict(trade)
    if multiplier == 1:
        return proj

    try:
        actual_gross = float(trade.get("gross_pnl",      0.0))
        fee_entry    = float(trade.get("fee_entry",       0.0))
        fee_exit     = float(trade.get("fee_exit",        0.0))
        slippage     = float(trade.get("slippage_cost",   0.0))
        borrow       = float(trade.get("borrow_cost",     0.0))
        r_multiple   = float(trade.get("r_multiple",      0.0))
        entry_ts     = int(trade.get("entry_ts",  0))
        exit_ts      = int(trade.get("exit_ts",   0))

        scaled_gross   = actual_gross * multiplier
        total_costs    = fee_entry + fee_exit + slippage + borrow
        scaled_net     = scaled_gross - total_costs
        hold_ms        = max(0, exit_ts - entry_ts)
        scaled_exit_ts = entry_ts + hold_ms * multiplier

        proj["gross_pnl"]  = scaled_gross
        proj["net_pnl"]    = scaled_net
        proj["exit_ts"]    = scaled_exit_ts
        proj["r_multiple"] = r_multiple * multiplier if r_multiple != 0.0 else 0.0
        proj.pop("economic_truth", None)   # force recompute from projected field values
    except Exception:
        pass
    return proj


# ── Per-TF economic snapshot ──────────────────────────────────────────────────

def _compute_tf_snapshot(trades: List[dict], multiplier: int) -> dict:
    """Project all trades to a TF multiplier and return summary economics."""
    if not trades:
        return {
            "net_expectancy":      None,
            "gross_expectancy":    None,
            "win_rate_pct":        None,
            "fee_drag_mean_pct":   None,
            "payoff_asymmetry":    None,
            "avg_hold_sec":        None,
            "survivability_score": None,
            "survivability_tier":  None,
            "trade_count":         0,
            "is_shadow":           multiplier != 1,
            "shadow_multiplier":   multiplier,
        }

    projected = [project_trade_to_tf(t, multiplier) for t in trades]
    full = compute_economic_ground_truth(projected)

    geo  = full.get("payoff_geometry",       {})
    surv = full.get("survivability_score",   {})
    fdd  = full.get("fee_drag_distribution", {})

    holds = [
        max(0.0, (t.get("exit_ts", 0) - t.get("entry_ts", 0)) / 1000.0)
        for t in projected
    ]
    avg_hold = round(mean(holds), 1) if holds else None

    return {
        "net_expectancy":      full.get("net_expectancy"),
        "gross_expectancy":    full.get("gross_expectancy"),
        "win_rate_pct":        geo.get("fee_adjusted_win_rate_pct"),
        "fee_drag_mean_pct":   fdd.get("mean"),
        "payoff_asymmetry":    geo.get("payoff_asymmetry_ratio"),
        "avg_hold_sec":        avg_hold,
        "survivability_score": surv.get("score"),
        "survivability_tier":  surv.get("tier"),
        "trade_count":         full.get("total_trades", 0),
        "is_shadow":           multiplier != 1,
        "shadow_multiplier":   multiplier,
    }


# ── Alpha persistence classification ─────────────────────────────────────────

def classify_alpha_persistence(tf_snapshots: dict) -> str:
    """
    Classify engine alpha persistence across timeframes.

    Priority order (best → worst):
      TF_ALPHA_PERSISTENT   score >= 75 at every TF
      TIMEFRAME_CONSISTENT  score >= 50 at every TF
      MICROSTRUCTURE_ERODED score < 50 at 1m, survives (>= 50) at 5m or 15m
      HIGHER_TF_RECOVERY    expectancy improves at higher TF, scores still low
      TF_NOISE_COLLAPSE     edge absent at all TFs

    Research category only — not an execution authority.
    """
    s1m  = tf_snapshots.get("1m",  {}).get("survivability_score") or 0
    s5m  = tf_snapshots.get("5m",  {}).get("survivability_score") or 0
    s15m = tf_snapshots.get("15m", {}).get("survivability_score") or 0
    e1m  = float(tf_snapshots.get("1m",  {}).get("net_expectancy") or 0.0)
    e5m  = float(tf_snapshots.get("5m",  {}).get("net_expectancy") or 0.0)
    e15m = float(tf_snapshots.get("15m", {}).get("net_expectancy") or 0.0)

    if s1m >= 75 and s5m >= 75 and s15m >= 75:
        return TF_ALPHA_PERSISTENT
    if s1m >= 50 and s5m >= 50 and s15m >= 50:
        return TIMEFRAME_CONSISTENT
    if s1m < 50 and (s5m >= 50 or s15m >= 50):
        return MICROSTRUCTURE_ERODED
    if e5m > e1m or e15m > e1m:
        return HIGHER_TF_RECOVERY
    return TF_NOISE_COLLAPSE


# ── Session and subset helpers ────────────────────────────────────────────────

def _explore_type(trade: dict) -> str:
    eo = trade.get("exploration_origin") or {}
    return eo.get("explore_type", "UNKNOWN") if isinstance(eo, dict) else "UNKNOWN"


def _tf_session_comparison(trades: List[dict], session: str) -> dict:
    """Per-TF economics for a specific origin_session filter."""
    subset = [t for t in trades if t.get("origin_session", "") == session]
    if not subset:
        return {"session": session, "note": f"No {session} trades in dataset"}

    result: dict = {"session": session, "trade_count": len(subset)}
    for tf_label, mult in TF_MULTIPLIERS.items():
        snap = _compute_tf_snapshot(subset, mult)
        result[tf_label] = {
            "net_expectancy":      snap.get("net_expectancy"),
            "fee_drag_mean_pct":   snap.get("fee_drag_mean_pct"),
            "win_rate_pct":        snap.get("win_rate_pct"),
            "survivability_score": snap.get("survivability_score"),
            "survivability_tier":  snap.get("survivability_tier"),
        }
    return result


def _tf_comparison_for_subset(subset: List[dict], label: str) -> dict:
    """Per-TF economics for an arbitrary subset of trades."""
    if not subset:
        return {"label": label, "note": "No trades in subset"}

    result: dict = {"label": label, "trade_count": len(subset)}
    for tf_label, mult in TF_MULTIPLIERS.items():
        snap = _compute_tf_snapshot(subset, mult)
        result[tf_label] = {
            "net_expectancy":      snap.get("net_expectancy"),
            "fee_drag_mean_pct":   snap.get("fee_drag_mean_pct"),
            "win_rate_pct":        snap.get("win_rate_pct"),
            "survivability_score": snap.get("survivability_score"),
            "survivability_tier":  snap.get("survivability_tier"),
        }
    return result


# ── Main entry point ──────────────────────────────────────────────────────────

def compute_timeframe_survivability(trades: List[dict]) -> dict:
    """
    Full timeframe survivability comparison for a portfolio of closed trades.

    1m column uses actual per-trade economics.
    5m and 15m are shadow projections: hypothetical economics if the same
    directional signals played out over higher-timeframe bars.

    Projection assumption: gross_pnl scales linearly with TF multiplier;
    fees remain constant (same notional). Hold duration scales proportionally.

    Returns structured comparison dict. Never raises.
    """
    SCOPE = (
        "FTD-TF-SURVIV: Research instrumentation only — non-governing. "
        "5m and 15m columns are shadow projections from 1m data assuming "
        "proportional gross PnL scaling with constant fees. "
        "Not actual execution results. "
        "All execution decisions remain at developer discretion."
    )

    try:
        if not trades:
            return {
                "scope_note":   SCOPE,
                "total_trades": 0,
                "note":         "No trades recorded yet.",
            }

        # Per-TF snapshots (1m = actual; 5m/15m = shadow)
        tf_snapshots: dict = {}
        for tf_label, mult in TF_MULTIPLIERS.items():
            tf_snapshots[tf_label] = _compute_tf_snapshot(trades, mult)

        category = classify_alpha_persistence(tf_snapshots)

        # Fee drag reduction across TFs
        fd_1m  = tf_snapshots["1m"].get("fee_drag_mean_pct")
        fd_5m  = tf_snapshots["5m"].get("fee_drag_mean_pct")
        fd_15m = tf_snapshots["15m"].get("fee_drag_mean_pct")
        fee_drag_reduction = {
            "1m_mean_pct":         fd_1m,
            "5m_shadow_mean_pct":  fd_5m,
            "15m_shadow_mean_pct": fd_15m,
            "1m_to_5m_delta_pct":
                round(fd_1m - fd_5m, 2)
                if fd_1m is not None and fd_5m is not None else None,
            "1m_to_15m_delta_pct":
                round(fd_1m - fd_15m, 2)
                if fd_1m is not None and fd_15m is not None else None,
        }

        # NY session comparison (consistently least-negative outlier)
        ny_comparison = _tf_session_comparison(trades, "NY")

        # Rule4 exploration comparison per TF
        rule4_trades = [t for t in trades if _explore_type(t) == "RULE4_MIN_EXPLORE"]
        rule4_comparison = (
            _tf_comparison_for_subset(rule4_trades, "RULE4_MIN_EXPLORE")
            if rule4_trades
            else {"label": "RULE4_MIN_EXPLORE", "note": "No Rule4 trades in dataset"}
        )

        # All exploration comparison (RULE1_UCB + RULE4_MIN_EXPLORE)
        explore_trades = [
            t for t in trades
            if _explore_type(t) in ("RULE1_UCB", "RULE4_MIN_EXPLORE")
        ]
        exploration_comparison = (
            _tf_comparison_for_subset(explore_trades, "ALL_EXPLORATION")
            if explore_trades
            else {"label": "ALL_EXPLORATION", "note": "No exploration trades in dataset"}
        )

        return {
            "scope_note":               SCOPE,
            "total_trades":             len(trades),
            "timeframe_comparison":     tf_snapshots,
            "alpha_persistence_category": category,
            "fee_drag_reduction":       fee_drag_reduction,
            "ny_session_comparison":    ny_comparison,
            "rule4_comparison":         rule4_comparison,
            "exploration_comparison":   exploration_comparison,
            "ontology_conflict_note": (
                "NegMem ontology conflicts require cross-reference with "
                "/api/learning-intelligence/exploration-diagnostics negmem_forensics."
            ),
        }

    except Exception as exc:
        return {
            "scope_note":   SCOPE,
            "total_trades": len(trades) if isinstance(trades, list) else 0,
            "error":        str(exc),
        }
