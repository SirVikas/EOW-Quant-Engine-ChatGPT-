"""
FTD-ECO-TRUTH: Economic ground truth analytics.

Pure functions — no I/O, no side effects, no execution authority.
Classification thresholds are diagnostic constants only; they govern no gate.
"""
from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any, Dict, List, Optional

# ── Diagnostic thresholds (NOT execution authorities) ─────────────────────────
NOISE_WIN_THRESHOLD    = 0.50   # USDT — net win below this is statistically negligible
HIGH_FEE_DRAG_PCT      = 80.0   # fee drag above this = UNSURVIVABLE payoff geometry
SURVIVABLE_FEE_DRAG_PCT = 50.0  # 50–80% fee drag zone = SURVIVABLE (borderline)
FAST_WINNER_SEC        = 300.0  # < 5 min = winner_fast signal
EXTENDED_LOSER_SEC     = 900.0  # > 15 min = loser_extended signal

HOLD_BUCKETS = [
    ("< 1 min",   0,      60),
    ("1–5 min",   60,     300),
    ("5–15 min",  300,    900),
    ("15–30 min", 900,    1800),
    ("> 30 min",  1800,   float("inf")),
]


# ── Single-trade classification ───────────────────────────────────────────────

def _fee_drag_pct(fees_paid: float, gross_pnl: float) -> Optional[float]:
    """Fee drag as % of gross profit. None when gross ≤ 0 (undefined)."""
    if gross_pnl <= 1e-9:
        return None
    return fees_paid / gross_pnl * 100.0


def _economic_class(
    gross_pnl: float,
    net_pnl:   float,
    fee_drag:  Optional[float],
) -> str:
    if gross_pnl <= 0.0:
        return "TRUE_NEGATIVE"
    if net_pnl <= 0.0:
        return "MICRO_EDGE_ERODED"
    # net_pnl > 0
    if fee_drag is not None and fee_drag > HIGH_FEE_DRAG_PCT:
        return "UNSURVIVABLE"
    if net_pnl < NOISE_WIN_THRESHOLD:
        return "NOISE_WIN"
    if fee_drag is not None and fee_drag > SURVIVABLE_FEE_DRAG_PCT:
        return "SURVIVABLE"
    return "TRUE_POSITIVE_ALPHA"


def classify_trade_economics(trade: dict) -> dict:
    """
    Compute the economic_truth dict for a single closed trade.

    Fail-open: any exception returns a minimal dict with UNKNOWN classification.
    Called at trade close in main.py — must never raise.
    """
    try:
        gross_pnl  = float(trade.get("gross_pnl",   0.0))
        net_pnl    = float(trade.get("net_pnl",     0.0))
        fee_entry  = float(trade.get("fee_entry",   0.0))
        fee_exit   = float(trade.get("fee_exit",    0.0))
        entry_ts   = int(trade.get("entry_ts", 0))
        exit_ts    = int(trade.get("exit_ts",  0))
        r_multiple = float(trade.get("r_multiple", 0.0))
        crossed    = bool(trade.get("crossed_session_boundary", False))

        fees_paid = fee_entry + fee_exit
        hold_sec  = max(0.0, (exit_ts - entry_ts) / 1000.0)
        fee_drag  = _fee_drag_pct(fees_paid, gross_pnl)
        econ_cls  = _economic_class(gross_pnl, net_pnl, fee_drag)

        return {
            "gross_pnl":               round(gross_pnl, 4),
            "net_pnl":                 round(net_pnl, 4),
            "fees_paid":               round(fees_paid, 4),
            "fee_drag_pct":            round(fee_drag, 1) if fee_drag is not None else None,
            "hold_duration_sec":       round(hold_sec, 1),
            "risk_reward_realized":    round(r_multiple, 3),
            "economic_classification": econ_cls,
            "payoff_geometry": {
                "winner_fast":    net_pnl > 0 and hold_sec < FAST_WINNER_SEC,
                "loser_extended": net_pnl <= 0 and hold_sec > EXTENDED_LOSER_SEC,
                "crossed_boundary": crossed,
            },
        }
    except Exception as exc:
        return {"economic_classification": "UNKNOWN", "error": str(exc)}


# ── Portfolio-level helpers ───────────────────────────────────────────────────

def _get_eco(trade: dict) -> dict:
    """Return economic_truth from trade dict, recomputing if absent."""
    eco = trade.get("economic_truth")
    if isinstance(eco, dict) and "economic_classification" in eco:
        return eco
    return classify_trade_economics(trade)


def _explore_type(trade: dict) -> str:
    eo = trade.get("exploration_origin") or {}
    return eo.get("explore_type", "UNKNOWN") if isinstance(eo, dict) else "UNKNOWN"


def _expectancy(subset: List[dict]) -> Optional[float]:
    if not subset:
        return None
    return round(mean(t.get("net_pnl", 0.0) for t in subset), 4)


def _session_economics(trades: List[dict]) -> List[dict]:
    SESSION_ORDER = ["ASIA", "LONDON", "NY", "LATE", "UNKNOWN"]
    by_orig: dict[str, list] = defaultdict(list)
    by_cls:  dict[str, list] = defaultdict(list)
    for t in trades:
        by_orig[t.get("origin_session", "UNKNOWN")].append(t)
        by_cls[t.get("close_session",   "UNKNOWN")].append(t)

    rows = []
    for sess in SESSION_ORDER:
        orig_t = by_orig.get(sess, [])
        cls_t  = by_cls.get(sess, [])
        if not orig_t and not cls_t:
            continue
        orig_wins = [t for t in orig_t if t.get("net_pnl", 0) > 0]
        rows.append({
            "session":               sess,
            "origin_trade_count":    len(orig_t),
            "origin_expectancy":     _expectancy(orig_t),
            "origin_win_rate_pct":   round(len(orig_wins) / len(orig_t) * 100, 1)
                                     if orig_t else None,
            "close_trade_count":     len(cls_t),
            "close_expectancy":      _expectancy(cls_t),
        })
    return rows


def _payoff_geometry(trades: List[dict]) -> dict:
    winners = [t for t in trades if t.get("net_pnl", 0) > 0]
    losers  = [t for t in trades if t.get("net_pnl", 0) <= 0]

    def _avg_hold_sec(subset: List[dict]) -> Optional[float]:
        if not subset:
            return None
        vals = [max(0.0, (t.get("exit_ts", 0) - t.get("entry_ts", 0)) / 1000.0)
                for t in subset]
        return round(mean(vals), 1)

    def _avg_fee_drag(subset: List[dict]) -> Optional[float]:
        drags = []
        for t in subset:
            eco = _get_eco(t)
            fd = eco.get("fee_drag_pct")
            if fd is not None:
                drags.append(fd)
        return round(mean(drags), 2) if drags else None

    avg_win  = mean(t.get("net_pnl", 0) for t in winners) if winners else 0.0
    avg_loss = mean(t.get("net_pnl", 0) for t in losers)  if losers  else 0.0

    asymmetry = (avg_win / abs(avg_loss)) if losers and abs(avg_loss) > 1e-9 else None

    # Hold duration buckets
    bucket_data: dict[str, list] = {b[0]: [] for b in HOLD_BUCKETS}
    for t in trades:
        hold = max(0.0, (t.get("exit_ts", 0) - t.get("entry_ts", 0)) / 1000.0)
        for label, lo, hi in HOLD_BUCKETS:
            if lo <= hold < hi:
                bucket_data[label].append(t.get("net_pnl", 0.0))
                break
    hold_buckets = [
        {"bucket": b[0], "count": len(bucket_data[b[0]]),
         "avg_net_pnl": round(mean(bucket_data[b[0]]), 4) if bucket_data[b[0]] else None}
        for b in HOLD_BUCKETS
    ]

    total = len(trades)
    fee_adj_wr = round(len(winners) / total * 100, 1) if total else None

    return {
        "winner_count":             len(winners),
        "loser_count":              len(losers),
        "avg_winner_hold_sec":      _avg_hold_sec(winners),
        "avg_loser_hold_sec":       _avg_hold_sec(losers),
        "avg_winner_fee_drag_pct":  _avg_fee_drag(winners),
        "avg_loser_fee_drag_pct":   _avg_fee_drag(losers),
        "fee_adjusted_win_rate_pct": fee_adj_wr,
        "payoff_asymmetry_ratio":   round(asymmetry, 3) if asymmetry is not None else None,
        "avg_win_usdt":             round(avg_win, 4),
        "avg_loss_usdt":            round(avg_loss, 4),
        "hold_duration_buckets":    hold_buckets,
    }


def _subsystem_attribution(trades: List[dict]) -> dict:
    by_type: dict[str, list] = defaultdict(list)
    for t in trades:
        by_type[_explore_type(t)].append(t)

    cross_boundary     = [t for t in trades if t.get("crossed_session_boundary", False)]
    not_cross_boundary = [t for t in trades if not t.get("crossed_session_boundary", False)]

    return {
        "RULE1_UCB_expectancy":         _expectancy(by_type.get("RULE1_UCB", [])),
        "RULE4_MIN_EXPLORE_expectancy": _expectancy(by_type.get("RULE4_MIN_EXPLORE", [])),
        "EXPLOIT_expectancy":           _expectancy(by_type.get("EXPLOIT", [])),
        "UNKNOWN_expectancy":           _expectancy(by_type.get("UNKNOWN", [])),
        "cross_boundary_expectancy":    _expectancy(cross_boundary),
        "within_session_expectancy":    _expectancy(not_cross_boundary),
        "cross_boundary_count":         len(cross_boundary),
        "within_session_count":         len(not_cross_boundary),
        "rl_approved_count":            len(trades),
        "ecology_note": (
            "All executed trades passed or bypassed ecology gate. "
            "Ecology-specific expectancy equals all-trades expectancy in bypass mode."
        ),
        "negmem_conflict_note": (
            "NegMem-conflict economics require cross-reference with live pattern index. "
            "Use /api/learning-intelligence/exploration-diagnostics negmem_forensics."
        ),
    }


def _classification_breakdown(trades: List[dict]) -> dict:
    cats: dict[str, list] = defaultdict(list)
    for t in trades:
        eco = _get_eco(t)
        cats[eco.get("economic_classification", "UNKNOWN")].append(t)

    total = len(trades)
    out = {}
    for cat in ("TRUE_POSITIVE_ALPHA", "MICRO_EDGE_ERODED", "NOISE_WIN",
                "FALSE_EDGE", "TRUE_NEGATIVE", "SURVIVABLE", "UNSURVIVABLE", "UNKNOWN"):
        subset = cats.get(cat, [])
        out[cat] = {
            "count":       len(subset),
            "share_pct":   round(len(subset) / max(total, 1) * 100, 1),
            "expectancy":  _expectancy(subset),
        }

    # Portfolio-level FALSE_EDGE detection
    wins = [t for t in trades if t.get("net_pnl", 0) > 0]
    wr   = len(wins) / max(total, 1)
    avg_net = mean(t.get("net_pnl", 0) for t in trades) if trades else 0
    if wr > 0.5 and avg_net < 0:
        out["FALSE_EDGE"]["portfolio_detected"] = True
        out["FALSE_EDGE"]["portfolio_wr"]       = round(wr * 100, 1)
        out["FALSE_EDGE"]["portfolio_avg_net"]  = round(avg_net, 4)

    return out


def _fee_drag_distribution(trades: List[dict]) -> dict:
    drags = []
    for t in trades:
        eco = _get_eco(t)
        fd  = eco.get("fee_drag_pct")
        if fd is not None:
            drags.append(fd)
    if not drags:
        return {"count": 0}
    drags_sorted = sorted(drags)
    n = len(drags_sorted)
    return {
        "count":   n,
        "mean":    round(mean(drags), 2),
        "min":     round(drags_sorted[0], 2),
        "p25":     round(drags_sorted[int(n * 0.25)], 2),
        "median":  round(drags_sorted[int(n * 0.50)], 2),
        "p75":     round(drags_sorted[int(n * 0.75)], 2),
        "max":     round(drags_sorted[-1], 2),
        "above_80pct_count": sum(1 for d in drags if d > 80),
        "above_50pct_count": sum(1 for d in drags if d > 50),
    }


def _survivability_score(
    trades:       List[dict],
    net_exp:      Optional[float],
    geo:          dict,
    subsystem:    dict,
) -> dict:
    """
    Composite survivability score 0–100.
    Components are diagnostic only — not execution authorities.
    """
    score    = 0
    evidence = {}

    # +30: net expectancy positive
    if net_exp is not None and net_exp > 0:
        score += 30
        evidence["net_expectancy_positive"] = True
    else:
        evidence["net_expectancy_positive"] = False

    # +20: avg winner fee drag < 50%
    wfd = geo.get("avg_winner_fee_drag_pct")
    if wfd is not None and wfd < 50.0:
        score += 20
        evidence["low_winner_fee_drag"] = True
    else:
        evidence["low_winner_fee_drag"] = False

    # +20: payoff asymmetry > 1.0 (winners larger than losers)
    asym = geo.get("payoff_asymmetry_ratio")
    if asym is not None and asym > 1.0:
        score += 20
        evidence["payoff_asymmetry_positive"] = True
    else:
        evidence["payoff_asymmetry_positive"] = False

    # +15: winners faster than losers
    wh = geo.get("avg_winner_hold_sec")
    lh = geo.get("avg_loser_hold_sec")
    if wh is not None and lh is not None and wh < lh:
        score += 15
        evidence["winners_faster_than_losers"] = True
    else:
        evidence["winners_faster_than_losers"] = False

    # +15: exploration contribution ≥ 0
    r4_exp = subsystem.get("RULE4_MIN_EXPLORE_expectancy")
    r1_exp = subsystem.get("RULE1_UCB_expectancy")
    explore_exp = r4_exp if r4_exp is not None else r1_exp
    if explore_exp is not None and explore_exp >= 0:
        score += 15
        evidence["exploration_contribution_positive"] = True
    else:
        evidence["exploration_contribution_positive"] = False

    tier = ("CRITICAL" if score < 25 else
            "WEAK"     if score < 50 else
            "EMERGING" if score < 75 else
            "VIABLE")

    return {"score": score, "max_score": 100, "tier": tier, "evidence": evidence}


# ── Main entry point ──────────────────────────────────────────────────────────

def compute_economic_ground_truth(trades: List[dict]) -> dict:
    """
    Full economic ground truth analytics for a portfolio of closed trades.

    Args:
        trades: Trade record dicts (DataLake JSON or asdict(TradeRecord)).

    Returns:
        Structured metrics dict. Never raises.
    """
    try:
        if not trades:
            return {
                "scope_note": (
                    "DIAGNOSTIC ONLY — non-governing. "
                    "No execution, fee, RL, or strategy mutations."
                ),
                "total_trades": 0,
                "note": "No trades recorded yet.",
            }

        net_pnls   = [t.get("net_pnl",   0.0) for t in trades]
        gross_pnls = [t.get("gross_pnl", 0.0) for t in trades]

        net_expectancy   = round(mean(net_pnls),   4)
        gross_expectancy = round(mean(gross_pnls), 4)
        total_net_pnl    = round(sum(net_pnls),    4)

        geo       = _payoff_geometry(trades)
        subsystem = _subsystem_attribution(trades)
        surv      = _survivability_score(trades, net_expectancy, geo, subsystem)

        return {
            "scope_note": (
                "DIAGNOSTIC ONLY — non-governing. "
                "No execution, fee, RL, or strategy mutations."
            ),
            "total_trades":            len(trades),
            "total_net_pnl":           total_net_pnl,
            "net_expectancy":          net_expectancy,
            "gross_expectancy":        gross_expectancy,
            "fee_drag_distribution":   _fee_drag_distribution(trades),
            "economic_classification": _classification_breakdown(trades),
            "payoff_geometry":         geo,
            "subsystem_attribution":   subsystem,
            "session_economics":       _session_economics(trades),
            "survivability_score":     surv,
        }

    except Exception as exc:
        return {
            "scope_note": "DIAGNOSTIC ONLY",
            "total_trades": len(trades),
            "error": str(exc),
        }
