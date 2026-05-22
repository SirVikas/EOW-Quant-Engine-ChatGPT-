"""
FTD-EXPLORE-ATTR: Exploration economic survivability analytics.

Pure functions — accept trade records as dicts, return metrics.
No I/O, no side effects, no RL mutations, no execution authority.
"""
from __future__ import annotations

import re
from collections import defaultdict
from statistics import mean, correlation
from typing import Any, Dict, List, Optional

# ── Exploration type taxonomy ─────────────────────────────────────────────────

RULE1_UCB         = "RULE1_UCB"       # natural UCB exploration (min-visits guarantee)
RULE4_MIN_EXPLORE = "RULE4_MIN_EXPLORE"  # anti-starvation floor exploration
EXPLOIT           = "EXPLOIT"         # normal exploitation (UCB positive, rules 1/4 not fired)
UNKNOWN           = "UNKNOWN"         # legacy / bypass / unrecognised

EXPLORATION_TYPES = (RULE1_UCB, RULE4_MIN_EXPLORE, EXPLOIT, UNKNOWN)

SESSION_ORDER = ["ASIA", "LONDON", "NY", "LATE"]


# ── Parser: RL reason string → exploration_origin dict ───────────────────────

def build_exploration_origin(rl_reason: str) -> dict:
    """
    Parse an RL reason string (from rl_engine.should_trade) into the
    exploration_origin dict attached to TradeRecord.

    Fail-open: any parse error returns explore_type=UNKNOWN rather than raising.

    Reason string formats (from rl_engine.py):
      Rule 1: "RL_EXPLORE(visits=N<MIN)"
      Rule 4: "RL_FLOOR_EXPLORE(q=±D.DDD n=N<MAX)"
      Rule 3: "RL_TRADE(q=±D.DDD ucb=±D.DDD wr=P% n=N)"
      Blocked: "RL_TOXIC(…)" | "RL_SKIP(…)"  → explore_type=UNKNOWN
    """
    try:
        if rl_reason.startswith("RL_EXPLORE("):
            m = re.search(r"visits=(\d+)", rl_reason)
            visits = int(m.group(1)) if m else None
            return {
                "explore_type":          RULE1_UCB,
                "was_exploration_trade": True,
                "q_value_at_entry":      None,   # not present in Rule-1 reason string
                "visit_count_at_entry":  visits,
                "explore_floor_active":  False,
            }

        if rl_reason.startswith("RL_FLOOR_EXPLORE("):
            m_q = re.search(r"q=([+-]?\d+\.\d+)", rl_reason)
            m_n = re.search(r"n=(\d+)", rl_reason)
            return {
                "explore_type":          RULE4_MIN_EXPLORE,
                "was_exploration_trade": True,
                "q_value_at_entry":      float(m_q.group(1)) if m_q else None,
                "visit_count_at_entry":  int(m_n.group(1))   if m_n else None,
                "explore_floor_active":  True,
            }

        if rl_reason.startswith("RL_TRADE("):
            m_q = re.search(r"q=([+-]?\d+\.\d+)", rl_reason)
            m_n = re.search(r"n=(\d+)", rl_reason)
            return {
                "explore_type":          EXPLOIT,
                "was_exploration_trade": False,
                "q_value_at_entry":      float(m_q.group(1)) if m_q else None,
                "visit_count_at_entry":  int(m_n.group(1))   if m_n else None,
                "explore_floor_active":  False,
            }

    except Exception:
        pass

    return {
        "explore_type":          UNKNOWN,
        "was_exploration_trade": False,
        "q_value_at_entry":      None,
        "visit_count_at_entry":  None,
        "explore_floor_active":  False,
    }


# ── Private helpers ───────────────────────────────────────────────────────────

def _explore_type(trade: dict) -> str:
    eo = trade.get("exploration_origin") or {}
    return eo.get("explore_type", UNKNOWN) if isinstance(eo, dict) else UNKNOWN


def _is_exploration(trade: dict) -> bool:
    eo = trade.get("exploration_origin") or {}
    if not isinstance(eo, dict):
        return False
    return bool(eo.get("was_exploration_trade", False))


def _hold_ms(trade: dict) -> float:
    return max(0.0, float(trade.get("exit_ts", 0)) - float(trade.get("entry_ts", 0)))


def _fee_drag_pct(trade: dict) -> float:
    """Fee drag as percentage of entry notional (entry_price × qty)."""
    notional = trade.get("entry_price", 0.0) * trade.get("qty", 0.0)
    fees = trade.get("fee_entry", 0.0) + trade.get("fee_exit", 0.0)
    return (fees / notional * 100.0) if notional > 0 else 0.0


def _q_at_entry(trade: dict) -> Optional[float]:
    eo = trade.get("exploration_origin") or {}
    if not isinstance(eo, dict):
        return None
    return eo.get("q_value_at_entry")


def _survivability_category(trade: dict) -> str:
    """
    Single category per exploration trade.
    Priority: UNRESOLVED → RECOVERY → NOISE → POSITIVE → NEGATIVE.
    Non-exploration trades: NOT_EXPLORATION.
    """
    et = _explore_type(trade)
    if et == EXPLOIT:
        return "NOT_EXPLORATION"

    eo        = trade.get("exploration_origin") or {}
    visits    = eo.get("visit_count_at_entry") if isinstance(eo, dict) else None
    net_pnl   = trade.get("net_pnl", 0.0)
    q_entry   = _q_at_entry(trade)

    # Brand-new context: insufficient evidence for any classification
    if et == RULE1_UCB and visits is not None and visits < 3:
        return "EXPLORATION_UNRESOLVED"

    if net_pnl > 0:
        # Q was negative at entry → positive outcome = Q recovery signal
        if q_entry is not None and q_entry < 0:
            return "EXPLORATION_RECOVERY"
        return "EXPLORATION_POSITIVE"
    else:
        # Q already deeply negative → loss = further noise accumulation
        if q_entry is not None and q_entry < -0.10:
            return "EXPLORATION_NOISE"
        return "EXPLORATION_NEGATIVE"


# ── Per-type aggregates ───────────────────────────────────────────────────────

def _per_type_metrics(trades: List[dict], explore_type: str) -> dict:
    subset = [t for t in trades if _explore_type(t) == explore_type]
    if not subset:
        return {
            "count": 0, "win_rate_pct": None,
            "avg_net_pnl": None, "avg_hold_ms": None, "avg_fee_drag_pct": None,
        }
    wins = [t for t in subset if t.get("net_pnl", 0.0) > 0]
    return {
        "count":            len(subset),
        "win_rate_pct":     round(len(wins) / len(subset) * 100, 1),
        "avg_net_pnl":      round(mean(t.get("net_pnl", 0.0) for t in subset), 4),
        "avg_hold_ms":      round(mean(_hold_ms(t) for t in subset), 0),
        "avg_fee_drag_pct": round(mean(_fee_drag_pct(t) for t in subset), 4),
    }


# ── Q-delta diagnostics ───────────────────────────────────────────────────────

def _q_delta_diagnostics(trades: List[dict]) -> dict:
    """
    Directional Q-delta for Rule4 trades.
    Entry Q is known from exploration_origin.q_value_at_entry.
    Post-trade Q direction is approximated via net_pnl sign (positive trade → Q improves).
    """
    rule4 = [t for t in trades if _explore_type(t) == RULE4_MIN_EXPLORE]
    if not rule4:
        return {
            "rule4_count": 0, "q_improved_pct": None,
            "avg_q_at_entry": None, "avg_net_pnl": None,
        }
    q_entries = [_q_at_entry(t) for t in rule4 if _q_at_entry(t) is not None]
    improved  = [t for t in rule4 if t.get("net_pnl", 0.0) > 0]
    return {
        "rule4_count":    len(rule4),
        "q_improved_pct": round(len(improved) / len(rule4) * 100, 1),
        "avg_q_at_entry": round(mean(q_entries), 4) if q_entries else None,
        "avg_net_pnl":    round(mean(t.get("net_pnl", 0.0) for t in rule4), 4),
    }


# ── Exploration-to-profitability correlation ──────────────────────────────────

def _profitability_correlation(trades: List[dict]) -> Optional[float]:
    """Pearson correlation: is_exploration (0/1) vs net_pnl."""
    if len(trades) < 3:
        return None
    x = [1.0 if _is_exploration(t) else 0.0 for t in trades]
    y = [t.get("net_pnl", 0.0) for t in trades]
    if len(set(x)) < 2:
        return None
    try:
        return round(correlation(x, y), 4)
    except Exception:
        return None


# ── Session breakdown ─────────────────────────────────────────────────────────

def _session_breakdown(trades: List[dict]) -> List[dict]:
    by_sess: dict[str, List[dict]] = defaultdict(list)
    for t in trades:
        sess = t.get("origin_session", "UNKNOWN")
        by_sess[sess].append(t)

    rows = []
    for sess in SESSION_ORDER + ["UNKNOWN"]:
        all_t = by_sess.get(sess, [])
        if not all_t:
            continue
        rule4   = [t for t in all_t if _explore_type(t) == RULE4_MIN_EXPLORE]
        r4_wins = [t for t in rule4 if t.get("net_pnl", 0.0) > 0]
        q_ents  = [_q_at_entry(t) for t in rule4 if _q_at_entry(t) is not None]
        rows.append({
            "session":           sess,
            "total_trades":      len(all_t),
            "rule4_count":       len(rule4),
            "rule4_wr_pct":      round(len(r4_wins) / len(rule4) * 100, 1) if rule4 else None,
            "rule4_avg_q_entry": round(mean(q_ents), 4) if q_ents else None,
            "rule4_avg_net_pnl": round(mean(t.get("net_pnl", 0.0) for t in rule4), 4)
                                 if rule4 else None,
        })
    return rows


# ── Rolling effectiveness windows ─────────────────────────────────────────────

def _rolling_effectiveness(trades: List[dict], window: int) -> List[dict]:
    """Exploration effectiveness in each rolling window of `window` trades."""
    results = []
    for i in range(window, len(trades) + 1):
        chunk = trades[i - window: i]
        exp   = [t for t in chunk if _is_exploration(t)]
        if not exp:
            results.append({"window_end": i, "explore_share_pct": 0.0, "explore_wr_pct": None})
            continue
        wins = [t for t in exp if t.get("net_pnl", 0.0) > 0]
        results.append({
            "window_end":        i,
            "explore_share_pct": round(len(exp) / window * 100, 1),
            "explore_wr_pct":    round(len(wins) / len(exp) * 100, 1),
        })
    return results


# ── Survivability classification summary ─────────────────────────────────────

def _survivability_summary(trades: List[dict]) -> dict:
    explore = [t for t in trades if _is_exploration(t)]
    cats: dict[str, int] = defaultdict(int)
    for t in explore:
        cats[_survivability_category(t)] += 1
    total = len(explore)
    return {
        "total_exploration_trades": total,
        "EXPLORATION_POSITIVE":     cats.get("EXPLORATION_POSITIVE", 0),
        "EXPLORATION_NEGATIVE":     cats.get("EXPLORATION_NEGATIVE", 0),
        "EXPLORATION_RECOVERY":     cats.get("EXPLORATION_RECOVERY", 0),
        "EXPLORATION_NOISE":        cats.get("EXPLORATION_NOISE", 0),
        "EXPLORATION_UNRESOLVED":   cats.get("EXPLORATION_UNRESOLVED", 0),
        "positive_ratio":  round(cats.get("EXPLORATION_POSITIVE", 0) / max(total, 1), 3),
        "recovery_ratio":  round(cats.get("EXPLORATION_RECOVERY", 0) / max(total, 1), 3),
        "noise_ratio":     round(cats.get("EXPLORATION_NOISE", 0)    / max(total, 1), 3),
    }


# ── Longitudinal dynamics ─────────────────────────────────────────────────────

def _longitudinal_dynamics(trades: List[dict]) -> dict:
    total         = len(trades)
    explore       = [t for t in trades if _is_exploration(t)]
    rule4         = [t for t in trades if _explore_type(t) == RULE4_MIN_EXPLORE]
    explore_share = round(len(explore) / max(total, 1), 3)
    rule4_dep     = round(len(rule4)   / max(total, 1), 3)

    rolling10 = _rolling_effectiveness(trades, 10)
    rolling25 = _rolling_effectiveness(trades, 25)

    # Survival-rate correlation: explore_share per window vs explore_wr in that window
    survival_corr: Optional[float] = None
    if len(rolling10) >= 3:
        share_s = [r["explore_share_pct"] for r in rolling10]
        wr_s    = [r["explore_wr_pct"] if r["explore_wr_pct"] is not None else 50.0
                   for r in rolling10]
        try:
            if len(set(share_s)) > 1:
                survival_corr = round(correlation(share_s, wr_s), 4)
        except Exception:
            pass

    return {
        "total_trades":                               total,
        "explore_share":                              explore_share,
        "rule4_dependency_ratio":                     rule4_dep,
        "survival_rate_correlation_vs_exploration":   survival_corr,
        "rolling_10_trade_windows_last5":             rolling10[-5:],
        "rolling_25_trade_windows_last5":             rolling25[-5:],
    }


# ── Main entry point ──────────────────────────────────────────────────────────

def compute_exploration_economics(trades: List[dict]) -> dict:
    """
    Full exploration economic survivability diagnostics.

    Args:
        trades: Trade record dicts sorted chronologically
                (from pnl_calc.trades via asdict, or DataLake JSON blobs).

    Returns:
        Structured metrics dict. Never raises.
    """
    try:
        if not trades:
            return {
                "scope_note": (
                    "DIAGNOSTIC ONLY — non-governing. "
                    "No execution, RL, or threshold mutations."
                ),
                "total_trades": 0,
                "note": "No trades recorded yet.",
            }

        explore       = [t for t in trades if _is_exploration(t)]
        cross_boundary = [t for t in explore if t.get("crossed_session_boundary", False)]

        session_rows   = _session_breakdown(trades)
        ny_diagnostics = next(
            (r for r in session_rows if r["session"] == "NY"),
            {"session": "NY", "note": "no NY trades yet"},
        )

        return {
            "scope_note": (
                "DIAGNOSTIC ONLY — non-governing. "
                "No execution, RL, or threshold mutations."
            ),
            "total_trades":             len(trades),
            "exploration_trades_count": len(explore),
            "per_type_metrics": {
                RULE1_UCB:         _per_type_metrics(trades, RULE1_UCB),
                RULE4_MIN_EXPLORE: _per_type_metrics(trades, RULE4_MIN_EXPLORE),
                EXPLOIT:           _per_type_metrics(trades, EXPLOIT),
                UNKNOWN:           _per_type_metrics(trades, UNKNOWN),
            },
            "q_delta_diagnostics":                  _q_delta_diagnostics(trades),
            "exploration_profitability_correlation": _profitability_correlation(trades),
            "session_breakdown":                     session_rows,
            "ny_rule4_diagnostics":                  ny_diagnostics,
            "cross_boundary_exploration_trades":     len(cross_boundary),
            "survivability_classification":          _survivability_summary(trades),
            "longitudinal_dynamics":                 _longitudinal_dynamics(trades),
        }

    except Exception as exc:
        return {
            "scope_note": "DIAGNOSTIC ONLY",
            "total_trades": len(trades),
            "error": str(exc),
        }
