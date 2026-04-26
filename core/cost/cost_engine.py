"""
EOW Quant Engine — qFTD-033 Cost-Aware Alpha Engine

Principle: Trade तभी valid है जब Net PnL > 0 (after ALL costs).
Hard rule (Q15:B): NO trade bypasses cost validation. Ever.

Configuration (from qFTD-033 questionnaire):
  Q1:A  Fixed % fee (taker entry + maker exit via cfg.TAKER_FEE / MAKER_FEE)
  Q2:C  ATR-linked slippage (cfg.SLIPPAGE_EST + cfg.ATR_SLIPPAGE_MULT × atr_pct)
  Q3:A  Spread cost included (cfg.COST_SPREAD_EST_PCT)
  Q4:B  Net edge > cfg.COST_MIN_NET_EDGE_PCT threshold (not just > 0)
  Q5:B  Cost-adjusted RR: (net_tp) / (sl + total_cost)
  Q6:A  Exploration mode allowed (controlled)
  Q7:A  Exploration: allow barely-negative edge with 50% size + EXPLORE tag
  Q8:A  Cost-aware learning — CostTradeRecord for post-trade update
  Q9:C  Negative patterns → reduce confidence + blacklist (via NegativeMemory)
  Q10:A Cost-adjusted position sizing (size_factor applied pre-order)
  Q11:C Adaptive sizing: marginal edge → 75%, rejected → 0%
  Q12:C Gross + net PnL both exposed via cost_report_section()
  Q13:A Full breakdown: fee_entry, fee_exit, slippage×2, spread
  Q14:C Pre-trade gate + post-trade analysis (CostTradeRecord.outcome_* fields)
  Q15:B STRICT NO — size_factor=0.0 on every reject verdict
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# Safe config import — fall back to matching defaults when pydantic_settings
# is unavailable (unit-test environments without all deps installed).
try:
    import config as _cfg
    _TAKER_FEE            = _cfg.cfg.TAKER_FEE
    _MAKER_FEE            = _cfg.cfg.MAKER_FEE
    _SLIPPAGE_EST         = _cfg.cfg.SLIPPAGE_EST
    _ATR_SLIPPAGE_MULT    = _cfg.cfg.ATR_SLIPPAGE_MULT
    _COST_MIN_NET_EDGE_PCT     = getattr(_cfg.cfg, "COST_MIN_NET_EDGE_PCT",     0.001)
    _COST_EXPLORE_LOSS_MAX_PCT = getattr(_cfg.cfg, "COST_EXPLORE_LOSS_MAX_PCT", 0.0005)
    _COST_HIGH_EDGE_FACTOR     = getattr(_cfg.cfg, "COST_HIGH_EDGE_FACTOR",     0.75)
    _COST_SPREAD_EST_PCT       = getattr(_cfg.cfg, "COST_SPREAD_EST_PCT",       0.0002)
    _COST_SLIPPAGE_MAX_PCT     = getattr(_cfg.cfg, "COST_SLIPPAGE_MAX_PCT",     0.0010)
    _EXPLORE_SIZE_MULT         = _cfg.cfg.EXPLORE_SIZE_MULT
    # qFTD-033R Q5:C — adaptive fee handling
    _COST_HIGH_FEE_TP_PCT      = getattr(_cfg.cfg, "COST_HIGH_FEE_TP_PCT",      20.0)
    _COST_ADAPTIVE_FEE_MULT    = getattr(_cfg.cfg, "COST_ADAPTIVE_FEE_MULT",    0.65)
except Exception:
    _TAKER_FEE                 = 0.0004
    _MAKER_FEE                 = 0.0002
    _SLIPPAGE_EST              = 0.0003
    _ATR_SLIPPAGE_MULT         = 0.10
    _COST_MIN_NET_EDGE_PCT     = 0.001
    _COST_EXPLORE_LOSS_MAX_PCT = 0.0005
    _COST_HIGH_EDGE_FACTOR     = 0.75
    _COST_SPREAD_EST_PCT       = 0.0002
    _COST_SLIPPAGE_MAX_PCT     = 0.0010
    _EXPLORE_SIZE_MULT         = 0.25
    _COST_HIGH_FEE_TP_PCT      = 20.0
    _COST_ADAPTIVE_FEE_MULT    = 0.65

# ── Public constant aliases (for tests and callers) ───────────────────────────
TAKER_FEE             = _TAKER_FEE
MAKER_FEE             = _MAKER_FEE
SLIPPAGE_EST          = _SLIPPAGE_EST
ATR_SLIPPAGE_MULT     = _ATR_SLIPPAGE_MULT
COST_MIN_NET_EDGE_PCT = _COST_MIN_NET_EDGE_PCT
COST_EXPLORE_LOSS_MAX_PCT = _COST_EXPLORE_LOSS_MAX_PCT
COST_HIGH_EDGE_FACTOR = _COST_HIGH_EDGE_FACTOR
COST_SPREAD_EST_PCT   = _COST_SPREAD_EST_PCT
COST_SLIPPAGE_MAX_PCT = _COST_SLIPPAGE_MAX_PCT
EXPLORE_SIZE_MULT     = _EXPLORE_SIZE_MULT
COST_HIGH_FEE_TP_PCT  = _COST_HIGH_FEE_TP_PCT
COST_ADAPTIVE_FEE_MULT = _COST_ADAPTIVE_FEE_MULT


# ── Verdict constants ─────────────────────────────────────────────────────────
APPROVE             = "APPROVE"
EXPLORE             = "EXPLORE"
REJECT_NEG_EDGE     = "REJECT_NEG_EDGE"
REJECT_BELOW_THRESH = "REJECT_BELOW_THRESH"


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class CostBreakdown:
    """Q13:A — Full per-trade cost itemisation."""
    fee_entry:            float = 0.0  # taker fee on entry notional (USDT)
    fee_exit:             float = 0.0  # maker fee on exit notional (USDT)
    slippage_entry:       float = 0.0  # ATR-linked fill slippage at entry (USDT)
    slippage_exit:        float = 0.0  # ATR-linked fill slippage at exit (USDT)
    spread_cost:          float = 0.0  # bid-ask spread half-cost (USDT)
    total_cost:           float = 0.0  # sum of all five items (USDT)
    cost_pct_of_notional: float = 0.0  # total_cost / notional × 100
    cost_pct_of_tp:       float = 0.0  # total_cost / gross_tp × 100


@dataclass
class NetEdgeResult:
    """
    Complete pre-trade cost verdict.

    Verdicts:
      APPROVE            — net edge > COST_MIN_NET_EDGE_PCT × notional
      EXPLORE            — Q7: barely negative (≥ -COST_EXPLORE_LOSS_MAX_PCT),
                           exploration_mode=True, size reduced to EXPLORE_SIZE_MULT
      REJECT_BELOW_THRESH — positive but below minimum edge threshold
      REJECT_NEG_EDGE    — negative edge below exploration floor (Q15:B → size=0)
    """
    gross_edge:           float = 0.0
    total_cost:           float = 0.0
    net_edge:             float = 0.0   # gross_edge - total_cost (USDT)
    net_edge_pct:         float = 0.0   # net_edge / notional × 100
    cost_adjusted_rr:     float = 0.0   # Q5:B — (gross_tp - cost) / (sl_usdt + cost)
    raw_rr:               float = 0.0   # unadjusted TP/SL ratio (for comparison)
    is_profitable:        bool  = False  # net_edge > 0
    has_min_edge:         bool  = False  # net_edge_pct > COST_MIN_NET_EDGE_PCT × 100
    verdict:              str   = "PENDING"
    rejection_reason:     str   = ""
    exploration_eligible: bool  = False
    size_factor:          float = 1.0   # Q10+Q11 — apply to base_qty before order
    cost_breakdown:       CostBreakdown = field(default_factory=CostBreakdown)


@dataclass
class CostTradeRecord:
    """
    Q8:A + Q14:C — Per-trade record for cost-aware learning and post-trade analysis.

    Pre-trade fields are filled by make_trade_record().
    Post-trade fields (outcome_*) are filled by the caller after the trade closes.
    """
    trade_id:           str
    symbol:             str
    strategy_id:        str
    verdict:            str
    exploration:        bool       # True when EXPLORE verdict taken
    net_edge:           float
    net_edge_pct:       float
    cost_adjusted_rr:   float
    size_factor:        float
    cost_breakdown:     CostBreakdown
    outcome_gross_pnl:  Optional[float] = None  # Q12:C — filled post-trade
    outcome_net_pnl:    Optional[float] = None  # Q12:C — net of actual costs
    cost_was_accurate:  Optional[bool]  = None  # estimated vs actual cost


# ── Cost calculation (Q1+Q2+Q3) ───────────────────────────────────────────────

def _slippage_pct(atr_pct: float) -> float:
    """Q2:C — ATR-linked slippage: base + ATR_SLIPPAGE_MULT × atr_pct, capped."""
    raw = SLIPPAGE_EST + ATR_SLIPPAGE_MULT * atr_pct
    return min(raw, COST_SLIPPAGE_MAX_PCT)


def calculate_cost(
    entry_price: float,
    take_profit: float,
    stop_loss:   float,
    qty:         float,
    atr_pct:     float,
    side:        str = "LONG",
) -> CostBreakdown:
    """
    Q1:A + Q2:C + Q3:A — Full round-trip cost model.

    Covers both entry and exit legs:
      - Entry: taker fee + slippage + half-spread
      - Exit:  maker fee + slippage

    Args:
        entry_price: signal entry price
        take_profit: target price
        stop_loss:   stop price
        qty:         position size (units)
        atr_pct:     ATR as fraction of price (e.g., 0.008 = 0.8%)
        side:        "LONG" or "SHORT"
    """
    if qty <= 0 or entry_price <= 0:
        return CostBreakdown()

    notional  = entry_price * qty
    slip_pct  = _slippage_pct(atr_pct)

    fee_entry     = notional * TAKER_FEE          # Q1:A taker
    fee_exit      = notional * MAKER_FEE          # Q1:A maker
    slip_entry    = notional * slip_pct           # Q2:C ATR-based
    slip_exit     = notional * slip_pct           # Q2:C exit also slips
    spread_cost   = notional * COST_SPREAD_EST_PCT  # Q3:A

    total_cost = fee_entry + fee_exit + slip_entry + slip_exit + spread_cost

    if side.upper() == "LONG":
        gross_tp_usdt = max((take_profit - entry_price) * qty, 1e-9)
    else:
        gross_tp_usdt = max((entry_price - take_profit) * qty, 1e-9)

    return CostBreakdown(
        fee_entry            = round(fee_entry,    6),
        fee_exit             = round(fee_exit,     6),
        slippage_entry       = round(slip_entry,   6),
        slippage_exit        = round(slip_exit,    6),
        spread_cost          = round(spread_cost,  6),
        total_cost           = round(total_cost,   6),
        cost_pct_of_notional = round(total_cost / notional * 100,       4),
        cost_pct_of_tp       = round(total_cost / gross_tp_usdt * 100,  2),
    )


# ── Net edge evaluation (Q4+Q5+Q6+Q7+Q11) ────────────────────────────────────

def evaluate_net_edge(
    entry_price:      float,
    take_profit:      float,
    stop_loss:        float,
    qty:              float,
    atr_pct:          float,
    side:             str  = "LONG",
    exploration_mode: bool = False,
) -> NetEdgeResult:
    """
    Core pre-trade decision: compute net edge and issue verdict.

    Verdict priority:
      1. net_edge_pct > COST_MIN_NET_EDGE_PCT → APPROVE (full or adaptive size)
      2. 0 < net_edge < threshold AND exploration_mode → EXPLORE (reduced size)
      3. 0 < net_edge < threshold AND no exploration → REJECT_BELOW_THRESH
      4. net_edge < 0 AND within exploration floor AND exploration_mode → EXPLORE
      5. net_edge < 0 AND outside floor (or no exploration) → REJECT_NEG_EDGE

    Q15:B STRICT: every reject sets size_factor = 0.0.
    """
    cb = calculate_cost(entry_price, take_profit, stop_loss, qty, atr_pct, side)

    notional = max(entry_price * qty, 1e-9)

    if side.upper() == "LONG":
        gross_tp  = max((take_profit - entry_price) * qty, 0.0)
        sl_usdt   = max((entry_price - stop_loss)   * qty, 1e-9)
    else:
        gross_tp  = max((entry_price - take_profit) * qty, 0.0)
        sl_usdt   = max((stop_loss   - entry_price) * qty, 1e-9)

    raw_rr    = gross_tp / sl_usdt

    net_edge     = gross_tp - cb.total_cost
    net_edge_pct = net_edge / notional * 100

    # Q5:B — cost-adjusted RR
    net_tp  = gross_tp - cb.total_cost
    net_sl  = sl_usdt + cb.total_cost
    cost_adj_rr = (net_tp / net_sl) if net_sl > 1e-9 else 0.0

    is_profitable = net_edge > 0
    min_edge_pct  = COST_MIN_NET_EDGE_PCT * 100   # convert to % scale
    has_min_edge  = net_edge_pct > min_edge_pct

    # Q4:B + Q11:C — approve with adaptive sizing
    if has_min_edge:
        double_thresh = min_edge_pct * 2
        size_factor   = 1.0 if net_edge_pct >= double_thresh else COST_HIGH_EDGE_FACTOR

        # qFTD-033R Q5:C — adaptive fee: reduce size when cost eats > threshold% of TP
        if cb.cost_pct_of_tp > COST_HIGH_FEE_TP_PCT:
            size_factor = min(size_factor, COST_ADAPTIVE_FEE_MULT)

        return NetEdgeResult(
            gross_edge           = round(gross_tp,       4),
            total_cost           = round(cb.total_cost,  4),
            net_edge             = round(net_edge,        4),
            net_edge_pct         = round(net_edge_pct,   4),
            cost_adjusted_rr     = round(cost_adj_rr,    3),
            raw_rr               = round(raw_rr,          3),
            is_profitable        = True,
            has_min_edge         = True,
            verdict              = APPROVE,
            rejection_reason     = "",
            exploration_eligible = False,
            size_factor          = size_factor,
            cost_breakdown       = cb,
        )

    # Below minimum threshold — check exploration eligibility
    explore_floor_pct = -(COST_EXPLORE_LOSS_MAX_PCT * 100)
    exploration_ok = exploration_mode and net_edge_pct >= explore_floor_pct

    if exploration_ok:
        return NetEdgeResult(
            gross_edge           = round(gross_tp,      4),
            total_cost           = round(cb.total_cost, 4),
            net_edge             = round(net_edge,       4),
            net_edge_pct         = round(net_edge_pct,  4),
            cost_adjusted_rr     = round(cost_adj_rr,   3),
            raw_rr               = round(raw_rr,         3),
            is_profitable        = is_profitable,
            has_min_edge         = False,
            verdict              = EXPLORE,
            rejection_reason     = "",
            exploration_eligible = True,
            size_factor          = EXPLORE_SIZE_MULT,   # Q7:A
            cost_breakdown       = cb,
        )

    # Q15:B STRICT — all reject paths → size_factor = 0.0
    if is_profitable:
        reason = (
            f"Net edge {net_edge_pct:.3f}% positive but below "
            f"{min_edge_pct:.2f}% threshold — marginal trade rejected "
            f"(enable exploration_mode to allow with reduced size)"
        )
        verdict = REJECT_BELOW_THRESH
    else:
        reason = (
            f"Net edge {net_edge_pct:.3f}% — trade loses ${abs(net_edge):.4f} "
            f"after all costs (fees+slippage+spread = ${cb.total_cost:.4f})"
        )
        verdict = REJECT_NEG_EDGE

    return NetEdgeResult(
        gross_edge           = round(gross_tp,      4),
        total_cost           = round(cb.total_cost, 4),
        net_edge             = round(net_edge,       4),
        net_edge_pct         = round(net_edge_pct,  4),
        cost_adjusted_rr     = round(cost_adj_rr,   3),
        raw_rr               = round(raw_rr,         3),
        is_profitable        = is_profitable,
        has_min_edge         = False,
        verdict              = verdict,
        rejection_reason     = reason,
        exploration_eligible = not is_profitable and exploration_mode,
        size_factor          = 0.0,
        cost_breakdown       = cb,
    )


# ── Sizing adapter (Q10+Q11) ──────────────────────────────────────────────────

def adapt_size(base_qty: float, result: NetEdgeResult) -> float:
    """
    Q10:A + Q11:C — Apply cost-adjusted, adaptive position size.

    Returns 0.0 for any rejected verdict (Q15:B).
    """
    if result.size_factor <= 0.0:
        return 0.0
    return round(base_qty * result.size_factor, 6)


# ── Learning integration (Q8+Q9) ─────────────────────────────────────────────

def make_trade_record(
    trade_id:    str,
    symbol:      str,
    strategy_id: str,
    result:      NetEdgeResult,
) -> CostTradeRecord:
    """
    Q8:A — Create a pre-trade cost record.

    The caller fills outcome_gross_pnl, outcome_net_pnl, cost_was_accurate
    after the trade closes, then passes the record to NegativeMemory / learning
    engine (Q9:C — both reduce-confidence and blacklist).
    """
    return CostTradeRecord(
        trade_id         = trade_id,
        symbol           = symbol,
        strategy_id      = strategy_id,
        verdict          = result.verdict,
        exploration      = result.verdict == EXPLORE,
        net_edge         = result.net_edge,
        net_edge_pct     = result.net_edge_pct,
        cost_adjusted_rr = result.cost_adjusted_rr,
        size_factor      = result.size_factor,
        cost_breakdown   = result.cost_breakdown,
    )


# ── Report section (Q12+Q13) ─────────────────────────────────────────────────

def cost_report_section(result: NetEdgeResult) -> dict:
    """
    Q12:C + Q13:A — Structured cost data for report integration.

    Exposes both gross and net edge, plus the full cost breakdown.
    Designed to slot into the unified report engine's data dict under
    the key 'cost_analysis'.
    """
    cb = result.cost_breakdown
    return {
        "verdict":          result.verdict,
        "gross_edge_usdt":  result.gross_edge,
        "total_cost_usdt":  result.total_cost,
        "net_edge_usdt":    result.net_edge,
        "net_edge_pct":     result.net_edge_pct,
        "raw_rr":           result.raw_rr,
        "cost_adjusted_rr": result.cost_adjusted_rr,
        "size_factor":      result.size_factor,
        "exploration":      result.verdict == EXPLORE,
        "rejection_reason": result.rejection_reason,
        "breakdown": {
            "fee_entry":         cb.fee_entry,
            "fee_exit":          cb.fee_exit,
            "slippage_entry":    cb.slippage_entry,
            "slippage_exit":     cb.slippage_exit,
            "spread":            cb.spread_cost,
            "total":             cb.total_cost,
            "cost_pct_notional": cb.cost_pct_of_notional,
            "cost_pct_tp":       cb.cost_pct_of_tp,
        },
    }
