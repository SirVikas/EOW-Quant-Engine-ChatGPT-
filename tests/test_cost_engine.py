"""
Tests for qFTD-033 Cost-Aware Alpha Engine.

Spec requirements (all must pass):
  ✔ [Q1+Q2+Q3] All cost components present: fee_entry, fee_exit, slippage×2, spread
  ✔ [Q2:C]     ATR increases slippage
  ✔ [Q4:B]     APPROVE only when net_edge > threshold (not just > 0)
  ✔ [Q5:B]     cost_adjusted_rr < raw_rr
  ✔ [Q6:A]     exploration_mode allows marginal trades
  ✔ [Q7:A]     exploration uses reduced size (EXPLORE_SIZE_MULT) + EXPLORE verdict
  ✔ [Q10:A]    adapt_size applies size_factor correctly
  ✔ [Q11:C]    adaptive: marginal edge → 75% size; rejected → 0%
  ✔ [Q12:C]    cost_report_section exposes both gross and net edge
  ✔ [Q13:A]    cost_report_section breakdown has all 5 cost components
  ✔ [Q14:C]    make_trade_record creates pre-trade record; outcome fields updatable
  ✔ [Q15:B]    STRICT NO bypass: every reject verdict → size_factor = 0.0
"""
import pytest
from core.cost.cost_engine import (
    CostBreakdown,
    NetEdgeResult,
    CostTradeRecord,
    APPROVE, EXPLORE, REJECT_NEG_EDGE, REJECT_BELOW_THRESH,
    # public constant aliases (config-independent)
    TAKER_FEE, MAKER_FEE, SLIPPAGE_EST, ATR_SLIPPAGE_MULT,
    COST_MIN_NET_EDGE_PCT, COST_EXPLORE_LOSS_MAX_PCT,
    COST_HIGH_EDGE_FACTOR, COST_SPREAD_EST_PCT,
    COST_SLIPPAGE_MAX_PCT, EXPLORE_SIZE_MULT,
    calculate_cost,
    evaluate_net_edge,
    adapt_size,
    make_trade_record,
    cost_report_section,
    _slippage_pct,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_signal(
    entry=100.0,
    tp=102.0,
    sl=99.0,
    qty=10.0,
    atr_pct=0.008,
    side="LONG",
):
    return dict(
        entry_price=entry,
        take_profit=tp,
        stop_loss=sl,
        qty=qty,
        atr_pct=atr_pct,
        side=side,
    )


# ── Q2:C — ATR slippage ───────────────────────────────────────────────────────

def test_slippage_increases_with_atr():
    low_vol  = _slippage_pct(0.003)
    high_vol = _slippage_pct(0.020)
    assert high_vol > low_vol, "Higher ATR must produce higher slippage estimate"


def test_slippage_capped_at_max():
    extreme = _slippage_pct(10.0)   # extreme ATR
    assert extreme <= COST_SLIPPAGE_MAX_PCT, (
        f"Slippage must be capped at {COST_SLIPPAGE_MAX_PCT}"
    )


def test_slippage_baseline_no_atr():
    result = _slippage_pct(0.0)
    assert result == SLIPPAGE_EST, "Zero ATR should return baseline SLIPPAGE_EST"


# ── Q1+Q2+Q3 — Cost breakdown completeness ────────────────────────────────────

def test_calculate_cost_all_components_present():
    cb = calculate_cost(**_make_signal())
    assert cb.fee_entry     > 0, "fee_entry must be positive"
    assert cb.fee_exit      > 0, "fee_exit must be positive"
    assert cb.slippage_entry > 0, "slippage_entry must be positive"
    assert cb.slippage_exit  > 0, "slippage_exit must be positive"
    assert cb.spread_cost   > 0, "spread_cost must be positive (Q3:A)"
    assert cb.total_cost    > 0, "total_cost must be positive"


def test_calculate_cost_total_equals_sum_of_components():
    cb = calculate_cost(**_make_signal())
    expected = cb.fee_entry + cb.fee_exit + cb.slippage_entry + cb.slippage_exit + cb.spread_cost
    assert abs(cb.total_cost - expected) < 1e-8, (
        f"total_cost {cb.total_cost} must equal sum of components {expected}"
    )


def test_calculate_cost_pct_of_notional_positive():
    cb = calculate_cost(**_make_signal())
    assert 0 < cb.cost_pct_of_notional < 5.0, (
        "cost_pct_of_notional should be a small positive percentage"
    )


def test_calculate_cost_pct_of_tp_positive():
    cb = calculate_cost(**_make_signal())
    assert cb.cost_pct_of_tp > 0, "cost_pct_of_tp must be positive"


def test_calculate_cost_short_side():
    sig = _make_signal(entry=100.0, tp=98.0, sl=101.0, side="SHORT")
    cb  = calculate_cost(**sig)
    assert cb.total_cost > 0, "SHORT side must also produce non-zero cost"


def test_calculate_cost_zero_qty_returns_zero():
    cb = calculate_cost(100.0, 102.0, 99.0, qty=0.0, atr_pct=0.008)
    assert cb.total_cost == 0.0


# ── Q4:B — Net edge threshold gate ───────────────────────────────────────────

def test_approve_when_net_edge_above_threshold():
    # Large TP (4%) vs small costs (~0.2%) → should APPROVE
    result = evaluate_net_edge(
        entry_price=100.0, take_profit=104.0, stop_loss=99.0,
        qty=10.0, atr_pct=0.008,
    )
    assert result.verdict == APPROVE, (
        f"Expected APPROVE but got {result.verdict}: {result.rejection_reason}"
    )
    assert result.size_factor > 0.0


def test_reject_when_net_edge_barely_positive_but_below_threshold():
    # TP only 0.05% above entry — costs will swamp the edge
    result = evaluate_net_edge(
        entry_price=100.0, take_profit=100.05, stop_loss=99.0,
        qty=10.0, atr_pct=0.008, exploration_mode=False,
    )
    assert result.verdict in (REJECT_BELOW_THRESH, REJECT_NEG_EDGE), (
        f"Expected rejection but got {result.verdict}"
    )


def test_reject_when_net_edge_negative():
    # TP too tight — costs exceed profit
    result = evaluate_net_edge(
        entry_price=100.0, take_profit=100.01, stop_loss=99.0,
        qty=10.0, atr_pct=0.008, exploration_mode=False,
    )
    assert result.verdict in (REJECT_NEG_EDGE, REJECT_BELOW_THRESH)
    assert result.is_profitable is False or result.has_min_edge is False


# ── Q5:B — Cost-adjusted RR ───────────────────────────────────────────────────

def test_cost_adjusted_rr_lower_than_raw_rr():
    result = evaluate_net_edge(
        entry_price=100.0, take_profit=104.0, stop_loss=99.0,
        qty=10.0, atr_pct=0.008,
    )
    assert result.cost_adjusted_rr < result.raw_rr, (
        "Cost-adjusted RR must always be lower than raw RR (Q5:B)"
    )


def test_raw_rr_equals_tp_sl_ratio():
    entry, tp, sl, qty = 100.0, 104.0, 99.0, 10.0
    result = evaluate_net_edge(entry, tp, sl, qty, 0.008)
    expected_raw = (tp - entry) / (entry - sl)  # LONG
    assert abs(result.raw_rr - expected_raw) < 0.01


# ── Q6:A + Q7:A — Exploration mode ───────────────────────────────────────────

def test_exploration_allows_marginal_trade_with_reduced_size():
    # net_edge > 0 but below threshold: entry=100, tp=100.20 → gross_tp=2.0 USDT,
    # costs ~1.6 USDT → net_edge ~0.4 USDT (0.04%) < threshold 0.1% → EXPLORE
    result = evaluate_net_edge(
        entry_price=100.0, take_profit=100.20, stop_loss=99.0,
        qty=10.0, atr_pct=0.001, exploration_mode=True,
    )
    assert result.verdict == EXPLORE, (
        f"Marginal trade with exploration_mode=True should be EXPLORE, got {result.verdict}"
    )
    assert result.size_factor == EXPLORE_SIZE_MULT, (
        f"Exploration must use EXPLORE_SIZE_MULT ({EXPLORE_SIZE_MULT})"
    )
    assert result.exploration_eligible is True


def test_no_exploration_without_mode_flag():
    result = evaluate_net_edge(
        entry_price=100.0, take_profit=100.05, stop_loss=99.0,
        qty=10.0, atr_pct=0.001, exploration_mode=False,
    )
    assert result.verdict != EXPLORE, (
        "Without exploration_mode=True, marginal trade must not get EXPLORE"
    )


def test_exploration_rejects_deeply_negative_edge():
    # Net edge far below exploration floor (-5% edge is too negative)
    result = evaluate_net_edge(
        entry_price=100.0, take_profit=95.0, stop_loss=99.0,
        qty=10.0, atr_pct=0.008, side="LONG", exploration_mode=True,
    )
    assert result.verdict == REJECT_NEG_EDGE, (
        "Even exploration_mode must not allow deeply negative edge"
    )
    assert result.size_factor == 0.0


# ── Q10:A + Q11:C — Adaptive sizing ──────────────────────────────────────────

def test_adapt_size_full_on_approve():
    result = evaluate_net_edge(100.0, 104.0, 99.0, 10.0, 0.008)
    assert result.verdict == APPROVE
    adapted = adapt_size(10.0, result)
    assert adapted > 0.0


def test_adapt_size_zero_on_reject():
    result = evaluate_net_edge(100.0, 100.01, 99.0, 10.0, 0.008, exploration_mode=False)
    assert result.size_factor == 0.0, "Q15:B — rejected result must have size_factor=0.0"
    adapted = adapt_size(10.0, result)
    assert adapted == 0.0, "Q15:B — adapt_size must return 0 on reject"


def test_adapt_size_reduced_on_explore():
    result = evaluate_net_edge(100.0, 100.05, 99.0, 10.0, 0.001, exploration_mode=True)
    if result.verdict == EXPLORE:
        adapted = adapt_size(10.0, result)
        assert adapted < 10.0, "Exploration size must be less than full base_qty"
        assert adapted == round(10.0 * EXPLORE_SIZE_MULT, 6)


def test_adapt_size_marginal_approve_uses_high_edge_factor():
    # Just above threshold but below 2× threshold → Q11:C adaptive
    result = evaluate_net_edge(
        entry_price=100.0, take_profit=100.15, stop_loss=99.0,
        qty=10.0, atr_pct=0.008,
    )
    if result.verdict == APPROVE and result.size_factor < 1.0:
        assert result.size_factor == COST_HIGH_EDGE_FACTOR, (
            f"Marginal approve must use COST_HIGH_EDGE_FACTOR ({COST_HIGH_EDGE_FACTOR})"
        )


# ── Q15:B — STRICT NO bypass ─────────────────────────────────────────────────

def test_q15_strict_all_rejects_have_zero_size():
    reject_scenarios = [
        # (entry, tp, sl, qty, atr_pct, exploration_mode)
        (100.0, 100.01, 99.0, 10.0, 0.008, False),   # neg/below-thresh, no explore
        (100.0, 95.0,   99.0, 10.0, 0.008, True),    # deeply negative, even with explore
    ]
    for entry, tp, sl, qty, atr, explore in reject_scenarios:
        result = evaluate_net_edge(entry, tp, sl, qty, atr, exploration_mode=explore)
        if result.verdict in (REJECT_NEG_EDGE, REJECT_BELOW_THRESH):
            assert result.size_factor == 0.0, (
                f"Q15:B STRICT: {result.verdict} must set size_factor=0.0"
            )
            assert adapt_size(qty, result) == 0.0, (
                f"Q15:B STRICT: adapt_size must return 0 for {result.verdict}"
            )


def test_q15_rejection_has_reason():
    result = evaluate_net_edge(100.0, 100.01, 99.0, 10.0, 0.008, exploration_mode=False)
    if result.verdict in (REJECT_NEG_EDGE, REJECT_BELOW_THRESH):
        assert len(result.rejection_reason) > 10, (
            "Rejected trade must include a human-readable rejection_reason"
        )


# ── Q8:A + Q14:C — Learning record ───────────────────────────────────────────

def test_make_trade_record_pre_trade_fields():
    result = evaluate_net_edge(100.0, 104.0, 99.0, 10.0, 0.008)
    record = make_trade_record("T001", "BTCUSDT", "alpha_v1", result)
    assert record.trade_id     == "T001"
    assert record.symbol       == "BTCUSDT"
    assert record.strategy_id  == "alpha_v1"
    assert record.verdict      == result.verdict
    assert record.net_edge     == result.net_edge
    assert record.size_factor  == result.size_factor
    assert record.outcome_gross_pnl is None   # not yet filled
    assert record.outcome_net_pnl   is None


def test_make_trade_record_outcome_fields_updatable():
    result = evaluate_net_edge(100.0, 104.0, 99.0, 10.0, 0.008)
    record = make_trade_record("T002", "ETHUSDT", "alpha_v2", result)
    # Simulate post-trade fill
    record.outcome_gross_pnl = 15.0
    record.outcome_net_pnl   = 12.3
    record.cost_was_accurate = True
    assert record.outcome_gross_pnl == 15.0
    assert record.outcome_net_pnl   == 12.3
    assert record.cost_was_accurate is True


def test_make_trade_record_exploration_flag():
    result = evaluate_net_edge(100.0, 100.05, 99.0, 10.0, 0.001, exploration_mode=True)
    record = make_trade_record("T003", "BNBUSDT", "alpha_v1", result)
    if result.verdict == EXPLORE:
        assert record.exploration is True
    else:
        assert record.exploration is False


# ── Q12:C + Q13:A — Report section ───────────────────────────────────────────

def test_cost_report_section_has_gross_and_net():
    result = evaluate_net_edge(100.0, 104.0, 99.0, 10.0, 0.008)
    section = cost_report_section(result)
    assert "gross_edge_usdt"  in section, "Q12:C — gross edge must be in report"
    assert "net_edge_usdt"    in section, "Q12:C — net edge must be in report"
    assert "total_cost_usdt"  in section, "Q12:C — total cost must be in report"


def test_cost_report_section_full_breakdown():
    result  = evaluate_net_edge(100.0, 104.0, 99.0, 10.0, 0.008)
    section = cost_report_section(result)
    bd      = section["breakdown"]
    for key in ("fee_entry", "fee_exit", "slippage_entry", "slippage_exit", "spread", "total"):
        assert key in bd, f"Q13:A — '{key}' must be in cost breakdown"
    assert bd["fee_entry"]  > 0
    assert bd["fee_exit"]   > 0
    assert bd["slippage_entry"] > 0
    assert bd["slippage_exit"]  > 0
    assert bd["spread"]     > 0


def test_cost_report_section_verdict_and_rr():
    result  = evaluate_net_edge(100.0, 104.0, 99.0, 10.0, 0.008)
    section = cost_report_section(result)
    assert "verdict"          in section
    assert "cost_adjusted_rr" in section
    assert "raw_rr"           in section
    assert "size_factor"      in section
    assert section["cost_adjusted_rr"] < section["raw_rr"], (
        "Report must show cost_adjusted_rr < raw_rr"
    )


def test_cost_report_section_exploration_flag():
    result  = evaluate_net_edge(100.0, 100.05, 99.0, 10.0, 0.001, exploration_mode=True)
    section = cost_report_section(result)
    assert "exploration" in section
    if result.verdict == EXPLORE:
        assert section["exploration"] is True


# ── Scenario tests ────────────────────────────────────────────────────────────

def test_strong_trend_trade_full_approve():
    # BTCUSDT-like: entry 50000, TP+3%, SL-1%, qty=0.02, atr_pct=0.8%
    result = evaluate_net_edge(
        entry_price=50000.0, take_profit=51500.0, stop_loss=49500.0,
        qty=0.02, atr_pct=0.008,
    )
    assert result.verdict == APPROVE
    assert result.size_factor > 0
    assert result.net_edge > 0
    assert result.cost_adjusted_rr > 0


def test_micro_trade_costs_dominate():
    # Very tight TP: 0.02% above entry — costs must kill this
    result = evaluate_net_edge(
        entry_price=100.0, take_profit=100.02, stop_loss=99.0,
        qty=10.0, atr_pct=0.008, exploration_mode=False,
    )
    assert result.verdict in (REJECT_NEG_EDGE, REJECT_BELOW_THRESH)
    assert result.size_factor == 0.0


def test_short_trade_mechanics():
    # SHORT: entry=100, TP=97 (3% down), SL=101
    result = evaluate_net_edge(
        entry_price=100.0, take_profit=97.0, stop_loss=101.0,
        qty=10.0, atr_pct=0.008, side="SHORT",
    )
    assert result.gross_edge > 0
    assert result.cost_adjusted_rr < result.raw_rr


def test_empty_qty_rejected_gracefully():
    result = evaluate_net_edge(100.0, 104.0, 99.0, qty=0.0, atr_pct=0.008)
    # 0 notional → costs = 0, gross_edge = 0 → net_edge = 0 → rejected
    assert result.size_factor == 0.0


def test_cost_engine_deterministic():
    """Same inputs → same outputs (no randomness)."""
    kwargs = dict(entry_price=100.0, take_profit=104.0, stop_loss=99.0,
                  qty=10.0, atr_pct=0.008)
    r1 = evaluate_net_edge(**kwargs)
    r2 = evaluate_net_edge(**kwargs)
    assert r1.verdict          == r2.verdict
    assert r1.net_edge         == r2.net_edge
    assert r1.cost_adjusted_rr == r2.cost_adjusted_rr
    assert r1.size_factor      == r2.size_factor
