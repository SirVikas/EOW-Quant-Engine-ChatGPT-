"""
FTD-PHOENIX-EXIT-ATTRIBUTION-001 — Exit Attribution Layer
Canonical constants, resolution logic, and reporting for exit method attribution.
Every trade close carries a permanent exit_method + exit_reason via TradeRecord.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional

# ── Canonical exit method constants ──────────────────────────────────────────

FAST_FAIL      = "FAST_FAIL"       # trend reversed within 90-300s; capped early
TIME_EXIT      = "TIME_EXIT"       # stale trade (>8 min, r < 0.15R); no BE set
STOP_LOSS      = "STOP_LOSS"       # initial SL hit
TAKE_PROFIT    = "TAKE_PROFIT"     # TP hit
TRAILING_STOP  = "TRAILING_STOP"   # ATR trail SL hit after BE
BREAK_EVEN     = "BREAK_EVEN"      # BE stop hit after breakeven armed
VTP_EXIT       = "VTP_EXIT"        # Volatile Take-Profit velocity stall exit
PARTIAL_TP     = "PARTIAL_TP"      # 50% partial booking (position remains open)
SPEED_EXIT     = "SPEED_EXIT"      # PAPER_SPEED mode velocity exit
EMERGENCY      = "EMERGENCY"       # risk_controller emergency close
MANUAL         = "MANUAL"          # operator-triggered close
UNKNOWN        = "UNKNOWN"         # attribution not captured

# Map from risk_controller close_tag → canonical exit method
CLOSE_TAG_MAP: Dict[str, str] = {
    "SL":        STOP_LOSS,
    "TP":        TAKE_PROFIT,
    "TSL+":      TRAILING_STOP,
    "BE":        BREAK_EVEN,
    "SPEED":     SPEED_EXIT,
    "EMERGENCY": EMERGENCY,
    "MANUAL":    MANUAL,
}


def resolve_exit_method(
    close_tag: Optional[str],
    pending_attr: Optional[dict],
) -> tuple[str, str]:
    """
    Resolve (exit_method, exit_reason) for a closed trade.

    pending_attr: dict with keys exit_method, exit_reason — set by trade_manager
                  TIME_EXIT handler before the SL-at-price fires; takes priority.
    close_tag:    raw string from risk_controller ("SL", "TP", "TSL+", "BE", …)
    """
    if pending_attr:
        return pending_attr.get("exit_method", UNKNOWN), pending_attr.get("exit_reason", "")
    if close_tag:
        return CLOSE_TAG_MAP.get(close_tag, UNKNOWN), close_tag
    return UNKNOWN, ""


# ── Exit attribution report ───────────────────────────────────────────────────

def compute_exit_attribution_report(trades: List[dict]) -> dict:
    """
    Compute per-exit-method performance breakdown from a list of trade dicts.
    Expects each trade dict to have: exit_method, net_pnl, gross_pnl, r_multiple,
    fee_entry, fee_exit fields (same schema as DataLake rows).
    """
    buckets: Dict[str, list] = defaultdict(list)
    for t in trades:
        method = t.get("exit_method") or UNKNOWN
        buckets[method].append(t)

    breakdown: Dict[str, dict] = {}
    total_trades = len(trades)

    for method, group in sorted(buckets.items()):
        count       = len(group)
        net_pnls    = [t.get("net_pnl", 0.0) for t in group]
        gross_pnls  = [t.get("gross_pnl", 0.0) for t in group]
        r_mults     = [t.get("r_multiple", 0.0) for t in group]
        fees        = [(t.get("fee_entry", 0.0) + t.get("fee_exit", 0.0)) for t in group]
        winners     = [p for p in net_pnls if p > 0]
        losers      = [p for p in net_pnls if p <= 0]

        total_net   = round(sum(net_pnls), 4)
        total_gross = round(sum(gross_pnls), 4)
        total_fees  = round(sum(fees), 4)
        avg_r       = round(sum(r_mults) / count, 4) if count else 0.0
        win_rate    = round(len(winners) / count * 100, 2) if count else 0.0
        avg_win     = round(sum(winners) / len(winners), 4) if winners else 0.0
        avg_loss    = round(sum(losers) / len(losers), 4) if losers else 0.0

        fdr = 0.0
        if total_gross != 0:
            fdr = round(abs(total_fees) / abs(total_gross) * 100, 2)

        share_pct = round(count / total_trades * 100, 2) if total_trades else 0.0

        breakdown[method] = {
            "exit_method":   method,
            "count":         count,
            "share_pct":     share_pct,
            "total_net_pnl": total_net,
            "total_fees":    total_fees,
            "fee_dr_pct":    fdr,
            "avg_r":         avg_r,
            "win_rate":      win_rate,
            "avg_win":       avg_win,
            "avg_loss":      avg_loss,
        }

    # Identify top destroyer and top alpha source
    sorted_by_net = sorted(breakdown.values(), key=lambda x: x["total_net_pnl"])
    top_destroyer = sorted_by_net[0]["exit_method"] if sorted_by_net else UNKNOWN
    top_alpha     = sorted_by_net[-1]["exit_method"] if sorted_by_net else UNKNOWN

    return {
        "total_trades":  total_trades,
        "top_destroyer": top_destroyer,
        "top_alpha":     top_alpha,
        "breakdown":     breakdown,
        "module":        "EXIT_ATTRIBUTION",
        "phase":         "PHOENIX-EXIT-ATTR-001",
    }
