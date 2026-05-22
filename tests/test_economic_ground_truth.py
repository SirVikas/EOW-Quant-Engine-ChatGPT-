"""
FTD-ECO-TRUTH — Economic Ground Truth Layer Tests

Verifies:
  • TradeRecord.economic_truth field (existence, default, backward compat)
  • classify_trade_economics() — all 6 classifications, fee drag, payoff geometry
  • compute_economic_ground_truth() — all required keys and calculations
  • Fee drag distribution statistics
  • Payoff geometry metrics (winner/loser duration, asymmetry, buckets)
  • Subsystem attribution (by explore_type, session, cross-boundary)
  • Session economics
  • Survivability score components
  • FALSE_EDGE detection
  • Fail-open on malformed input
  • No execution mutation
"""
from __future__ import annotations

import sys
from dataclasses import asdict, fields
from pathlib import Path
from typing import Optional
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.economic_truth import (
    classify_trade_economics,
    compute_economic_ground_truth,
    _economic_class,
    _fee_drag_pct,
    NOISE_WIN_THRESHOLD,
    HIGH_FEE_DRAG_PCT,
    SURVIVABLE_FEE_DRAG_PCT,
    FAST_WINNER_SEC,
    EXTENDED_LOSER_SEC,
)


# ── Shared helpers ────────────────────────────────────────────────────────────

def _make_trade(
    trade_id: str = "T001",
    gross_pnl: float = 10.0,
    net_pnl: float = 5.0,
    fee_entry: float = 2.0,
    fee_exit: float = 3.0,
    entry_ts: int = 0,
    exit_ts: int = 120_000,        # 120 sec = 2 min hold
    entry_price: float = 50_000.0,
    qty: float = 0.01,
    stop_loss: float = 49_500.0,
    take_profit: float = 51_000.0,
    r_multiple: float = 1.0,
    origin_session: str = "NY",
    close_session: str = "NY",
    crossed_session_boundary: bool = False,
    exploration_origin: Optional[dict] = None,
    economic_truth: Optional[dict] = None,
) -> dict:
    return {
        "trade_id":                trade_id,
        "symbol":                  "BTCUSDT",
        "side":                    "BUY",
        "entry_price":             entry_price,
        "exit_price":              entry_price * 1.001,
        "qty":                     qty,
        "entry_ts":                entry_ts,
        "exit_ts":                 exit_ts,
        "gross_pnl":               gross_pnl,
        "net_pnl":                 net_pnl,
        "fee_entry":               fee_entry,
        "fee_exit":                fee_exit,
        "slippage_cost":           0.0,
        "borrow_cost":             0.0,
        "net_pnl_pct":             net_pnl / (entry_price * qty) * 100,
        "r_multiple":              r_multiple,
        "stop_loss":               stop_loss,
        "take_profit":             take_profit,
        "origin_session":          origin_session,
        "close_session":           close_session,
        "crossed_session_boundary": crossed_session_boundary,
        "exploration_origin":      exploration_origin,
        "economic_truth":          economic_truth,
    }


def _rule4_origin(q: float = -0.08, n: int = 6) -> dict:
    return {"explore_type": "RULE4_MIN_EXPLORE", "was_exploration_trade": True,
            "q_value_at_entry": q, "visit_count_at_entry": n, "explore_floor_active": True}


def _exploit_origin() -> dict:
    return {"explore_type": "EXPLOIT", "was_exploration_trade": False,
            "q_value_at_entry": 0.1, "visit_count_at_entry": 20, "explore_floor_active": False}


# ═══════════════════════════════════════════════════════════════════════
# Part 1: TradeRecord field
# ═══════════════════════════════════════════════════════════════════════

class TestTradeRecordEconomicTruth:
    def test_economic_truth_field_exists(self):
        from core.pnl_calculator import TradeRecord
        field_names = {f.name for f in fields(TradeRecord)}
        assert "economic_truth" in field_names

    def test_economic_truth_default_none(self):
        from core.pnl_calculator import TradeRecord
        t = TradeRecord(
            trade_id="X", symbol="BTCUSDT", side="BUY",
            entry_price=50000.0, exit_price=50100.0, qty=0.01,
            entry_ts=1000, exit_ts=2000,
        )
        assert t.economic_truth is None

    def test_asdict_includes_economic_truth(self):
        from core.pnl_calculator import TradeRecord
        t = TradeRecord(
            trade_id="X", symbol="BTCUSDT", side="BUY",
            entry_price=50000.0, exit_price=50100.0, qty=0.01,
            entry_ts=1000, exit_ts=2000,
            economic_truth={"economic_classification": "TRUE_POSITIVE_ALPHA"},
        )
        d = asdict(t)
        assert "economic_truth" in d
        assert d["economic_truth"]["economic_classification"] == "TRUE_POSITIVE_ALPHA"

    def test_replay_handles_missing_economic_truth(self):
        """Legacy DataLake records without economic_truth must restore cleanly."""
        from core.pnl_calculator import PurePnLCalculator
        calc = PurePnLCalculator(starting_capital=1000.0)
        legacy = {
            "trade_id": "L001", "symbol": "BTCUSDT", "side": "BUY",
            "entry_price": 50000.0, "exit_price": 50100.0, "qty": 0.01,
            "entry_ts": 1000, "exit_ts": 2000, "net_pnl": 5.0, "gross_pnl": 6.0,
            # economic_truth intentionally absent
        }
        restored = calc.replay_from_history([legacy])
        assert restored == 1
        assert calc.trades[-1].economic_truth is None


# ═══════════════════════════════════════════════════════════════════════
# Part 2: Fee drag helper
# ═══════════════════════════════════════════════════════════════════════

class TestFeeDragPct:
    def test_basic_calculation(self):
        assert _fee_drag_pct(5.0, 10.0) == pytest.approx(50.0)

    def test_zero_gross_returns_none(self):
        assert _fee_drag_pct(5.0, 0.0) is None

    def test_negative_gross_returns_none(self):
        assert _fee_drag_pct(5.0, -2.0) is None

    def test_full_fee_drag(self):
        # fees = gross → 100%
        assert _fee_drag_pct(10.0, 10.0) == pytest.approx(100.0)

    def test_tiny_gross(self):
        # fees > gross → drag > 100%
        assert _fee_drag_pct(10.0, 5.0) == pytest.approx(200.0)


# ═══════════════════════════════════════════════════════════════════════
# Part 3: Economic classification
# ═══════════════════════════════════════════════════════════════════════

class TestEconomicClass:
    def test_true_negative_when_gross_zero(self):
        assert _economic_class(0.0, -1.0, None) == "TRUE_NEGATIVE"

    def test_true_negative_when_gross_negative(self):
        assert _economic_class(-5.0, -6.0, None) == "TRUE_NEGATIVE"

    def test_micro_edge_eroded_when_gross_pos_net_zero(self):
        assert _economic_class(5.0, 0.0, 60.0) == "MICRO_EDGE_ERODED"

    def test_micro_edge_eroded_when_gross_pos_net_negative(self):
        assert _economic_class(5.0, -1.0, 120.0) == "MICRO_EDGE_ERODED"

    def test_unsurvivable_when_fee_drag_above_threshold(self):
        drag = HIGH_FEE_DRAG_PCT + 1.0
        assert _economic_class(10.0, 0.5, drag) == "UNSURVIVABLE"

    def test_noise_win_when_net_below_threshold(self):
        net = NOISE_WIN_THRESHOLD / 2
        assert _economic_class(5.0, net, 20.0) == "NOISE_WIN"

    def test_survivable_when_fee_drag_in_mid_zone(self):
        drag = (SURVIVABLE_FEE_DRAG_PCT + HIGH_FEE_DRAG_PCT) / 2
        net  = NOISE_WIN_THRESHOLD * 2
        assert _economic_class(5.0, net, drag) == "SURVIVABLE"

    def test_true_positive_alpha_when_all_clear(self):
        assert _economic_class(10.0, 5.0, 30.0) == "TRUE_POSITIVE_ALPHA"

    def test_true_positive_alpha_when_fee_drag_none(self):
        # fee_drag=None (gross was very small) but net positive and above noise threshold
        assert _economic_class(5.0, 2.0, None) == "TRUE_POSITIVE_ALPHA"

    def test_priority_gross_before_net(self):
        # gross <= 0 → TRUE_NEGATIVE even if fee_drag is high
        assert _economic_class(0.0, -100.0, 999.0) == "TRUE_NEGATIVE"


# ═══════════════════════════════════════════════════════════════════════
# Part 4: classify_trade_economics (single trade)
# ═══════════════════════════════════════════════════════════════════════

class TestClassifyTradeEconomics:
    def test_required_keys_present(self):
        eco = classify_trade_economics(_make_trade())
        for key in ("gross_pnl", "net_pnl", "fees_paid", "fee_drag_pct",
                    "hold_duration_sec", "risk_reward_realized",
                    "economic_classification", "payoff_geometry"):
            assert key in eco

    def test_payoff_geometry_keys_present(self):
        eco = classify_trade_economics(_make_trade())
        pg = eco["payoff_geometry"]
        assert "winner_fast" in pg
        assert "loser_extended" in pg
        assert "crossed_boundary" in pg

    def test_fees_paid_sum(self):
        eco = classify_trade_economics(_make_trade(fee_entry=2.0, fee_exit=3.0))
        assert eco["fees_paid"] == pytest.approx(5.0)

    def test_fee_drag_pct_correct(self):
        # gross=10, fees=5 → drag=50%
        eco = classify_trade_economics(_make_trade(gross_pnl=10.0, fee_entry=2.5, fee_exit=2.5))
        assert eco["fee_drag_pct"] == pytest.approx(50.0)

    def test_fee_drag_none_when_gross_zero(self):
        eco = classify_trade_economics(_make_trade(gross_pnl=0.0, net_pnl=-1.0))
        assert eco["fee_drag_pct"] is None

    def test_hold_duration_sec_correct(self):
        # exit_ts - entry_ts = 90_000 ms → 90 sec
        eco = classify_trade_economics(_make_trade(entry_ts=0, exit_ts=90_000))
        assert eco["hold_duration_sec"] == pytest.approx(90.0)

    def test_r_multiple_used(self):
        eco = classify_trade_economics(_make_trade(r_multiple=2.5))
        assert eco["risk_reward_realized"] == pytest.approx(2.5)

    def test_winner_fast_true_when_short_hold(self):
        eco = classify_trade_economics(_make_trade(
            net_pnl=5.0,
            entry_ts=0, exit_ts=int(FAST_WINNER_SEC * 1000) - 1,  # just under threshold
        ))
        assert eco["payoff_geometry"]["winner_fast"] is True

    def test_winner_fast_false_when_long_hold(self):
        eco = classify_trade_economics(_make_trade(
            net_pnl=5.0,
            entry_ts=0, exit_ts=int(FAST_WINNER_SEC * 1000) + 1,
        ))
        assert eco["payoff_geometry"]["winner_fast"] is False

    def test_loser_extended_true_when_long_hold(self):
        eco = classify_trade_economics(_make_trade(
            net_pnl=-3.0,
            entry_ts=0, exit_ts=int(EXTENDED_LOSER_SEC * 1000) + 1,
        ))
        assert eco["payoff_geometry"]["loser_extended"] is True

    def test_loser_extended_false_for_short_loss(self):
        eco = classify_trade_economics(_make_trade(
            net_pnl=-3.0,
            entry_ts=0, exit_ts=int(EXTENDED_LOSER_SEC * 1000) - 1,
        ))
        assert eco["payoff_geometry"]["loser_extended"] is False

    def test_crossed_boundary_propagated(self):
        eco = classify_trade_economics(_make_trade(crossed_session_boundary=True))
        assert eco["payoff_geometry"]["crossed_boundary"] is True

    def test_fail_open_on_empty_dict(self):
        eco = classify_trade_economics({})
        assert isinstance(eco, dict)
        assert "economic_classification" in eco

    def test_fail_open_on_garbage(self):
        eco = classify_trade_economics({"entry_ts": "not_an_int", "exit_ts": "also_not"})
        assert isinstance(eco, dict)


# ═══════════════════════════════════════════════════════════════════════
# Part 5: compute_economic_ground_truth (portfolio level)
# ═══════════════════════════════════════════════════════════════════════

REQUIRED_PORTFOLIO_KEYS = {
    "scope_note",
    "total_trades",
    "total_net_pnl",
    "net_expectancy",
    "gross_expectancy",
    "fee_drag_distribution",
    "economic_classification",
    "payoff_geometry",
    "subsystem_attribution",
    "session_economics",
    "survivability_score",
}


class TestComputeEconomicGroundTruth:
    def test_empty_returns_valid_dict(self):
        result = compute_economic_ground_truth([])
        assert result["total_trades"] == 0
        assert "scope_note" in result

    def test_required_keys_present(self):
        trades = [_make_trade("T1"), _make_trade("T2", net_pnl=-2.0)]
        result = compute_economic_ground_truth(trades)
        for key in REQUIRED_PORTFOLIO_KEYS:
            assert key in result, f"Missing required key: {key}"

    def test_scope_note_present(self):
        result = compute_economic_ground_truth([])
        assert "DIAGNOSTIC" in result["scope_note"].upper()

    def test_net_expectancy_calculation(self):
        trades = [
            _make_trade("T1", net_pnl=10.0),
            _make_trade("T2", net_pnl=-4.0),
        ]
        result = compute_economic_ground_truth(trades)
        assert result["net_expectancy"] == pytest.approx(3.0)

    def test_gross_expectancy_calculation(self):
        trades = [
            _make_trade("T1", gross_pnl=12.0),
            _make_trade("T2", gross_pnl=8.0),
        ]
        result = compute_economic_ground_truth(trades)
        assert result["gross_expectancy"] == pytest.approx(10.0)

    def test_total_net_pnl(self):
        trades = [_make_trade(f"T{i}", net_pnl=3.0) for i in range(5)]
        result = compute_economic_ground_truth(trades)
        assert result["total_net_pnl"] == pytest.approx(15.0)

    def test_never_raises_on_malformed(self):
        bad = [
            {"trade_id": "X1"},
            {"trade_id": "X2", "gross_pnl": "not_float"},
            {"net_pnl": 5.0},
        ]
        result = compute_economic_ground_truth(bad)
        assert isinstance(result, dict)


# ═══════════════════════════════════════════════════════════════════════
# Part 6: Fee drag distribution
# ═══════════════════════════════════════════════════════════════════════

class TestFeeDragDistribution:
    def test_distribution_keys(self):
        trades = [_make_trade("T1", gross_pnl=10.0, fee_entry=2.0, fee_exit=2.0)]
        result = compute_economic_ground_truth(trades)
        fd = result["fee_drag_distribution"]
        for key in ("count", "mean", "min", "median", "max",
                    "above_80pct_count", "above_50pct_count"):
            assert key in fd

    def test_distribution_values_correct(self):
        # gross=10, fees=4 → drag=40%
        trades = [_make_trade("T1", gross_pnl=10.0, fee_entry=2.0, fee_exit=2.0, net_pnl=6.0)]
        result = compute_economic_ground_truth(trades)
        fd = result["fee_drag_distribution"]
        assert fd["mean"] == pytest.approx(40.0)

    def test_above_80pct_counted(self):
        # gross=10, fees=9 → drag=90% → above 80%
        trades = [
            _make_trade("T1", gross_pnl=10.0, fee_entry=4.5, fee_exit=4.5, net_pnl=1.0),
            _make_trade("T2", gross_pnl=10.0, fee_entry=2.0, fee_exit=2.0, net_pnl=6.0),
        ]
        result = compute_economic_ground_truth(trades)
        assert result["fee_drag_distribution"]["above_80pct_count"] == 1

    def test_empty_count_when_no_positive_gross(self):
        trades = [_make_trade("T1", gross_pnl=-5.0, net_pnl=-6.0)]
        result = compute_economic_ground_truth(trades)
        assert result["fee_drag_distribution"]["count"] == 0


# ═══════════════════════════════════════════════════════════════════════
# Part 7: Payoff geometry
# ═══════════════════════════════════════════════════════════════════════

class TestPayoffGeometry:
    def test_geometry_required_keys(self):
        trades = [_make_trade("T1")]
        result = compute_economic_ground_truth(trades)
        geo = result["payoff_geometry"]
        for key in ("winner_count", "loser_count", "avg_winner_hold_sec",
                    "avg_loser_hold_sec", "fee_adjusted_win_rate_pct",
                    "payoff_asymmetry_ratio", "hold_duration_buckets"):
            assert key in geo

    def test_winner_loser_count_correct(self):
        trades = [
            _make_trade("T1", net_pnl=5.0),
            _make_trade("T2", net_pnl=3.0),
            _make_trade("T3", net_pnl=-2.0),
        ]
        result = compute_economic_ground_truth(trades)
        geo = result["payoff_geometry"]
        assert geo["winner_count"] == 2
        assert geo["loser_count"]  == 1

    def test_fee_adjusted_wr(self):
        trades = [
            _make_trade("T1", net_pnl= 5.0),
            _make_trade("T2", net_pnl=-3.0),
        ]
        result = compute_economic_ground_truth(trades)
        assert result["payoff_geometry"]["fee_adjusted_win_rate_pct"] == pytest.approx(50.0)

    def test_payoff_asymmetry_correct(self):
        trades = [
            _make_trade("T1", net_pnl=10.0),
            _make_trade("T2", net_pnl=-5.0),
        ]
        result = compute_economic_ground_truth(trades)
        # avg_win=10, avg_loss=5 → asymmetry=2.0
        assert result["payoff_geometry"]["payoff_asymmetry_ratio"] == pytest.approx(2.0)

    def test_avg_hold_sec_correct(self):
        trades = [
            _make_trade("T1", net_pnl=5.0, entry_ts=0, exit_ts=60_000),   # 60 sec
            _make_trade("T2", net_pnl=3.0, entry_ts=0, exit_ts=120_000),  # 120 sec
        ]
        result = compute_economic_ground_truth(trades)
        geo = result["payoff_geometry"]
        assert geo["avg_winner_hold_sec"] == pytest.approx(90.0)

    def test_hold_duration_buckets_populated(self):
        # 2 min hold → "1–5 min" bucket
        trades = [_make_trade("T1", entry_ts=0, exit_ts=120_000)]
        result = compute_economic_ground_truth(trades)
        buckets = result["payoff_geometry"]["hold_duration_buckets"]
        one_to_five = next((b for b in buckets if b["bucket"] == "1–5 min"), None)
        assert one_to_five is not None
        assert one_to_five["count"] == 1

    def test_asymmetry_none_when_no_losers(self):
        trades = [_make_trade("T1", net_pnl=5.0)]
        result = compute_economic_ground_truth(trades)
        assert result["payoff_geometry"]["payoff_asymmetry_ratio"] is None


# ═══════════════════════════════════════════════════════════════════════
# Part 8: Subsystem attribution
# ═══════════════════════════════════════════════════════════════════════

class TestSubsystemAttribution:
    def test_attribution_required_keys(self):
        trades = [_make_trade("T1", exploration_origin=_rule4_origin())]
        result = compute_economic_ground_truth(trades)
        sub = result["subsystem_attribution"]
        for key in ("RULE4_MIN_EXPLORE_expectancy", "EXPLOIT_expectancy",
                    "RULE1_UCB_expectancy", "cross_boundary_expectancy",
                    "within_session_expectancy", "cross_boundary_count",
                    "within_session_count", "rl_approved_count",
                    "ecology_note", "negmem_conflict_note"):
            assert key in sub

    def test_rule4_expectancy_correct(self):
        trades = [
            _make_trade("T1", net_pnl=6.0,  exploration_origin=_rule4_origin()),
            _make_trade("T2", net_pnl=-2.0, exploration_origin=_rule4_origin()),
        ]
        result = compute_economic_ground_truth(trades)
        assert result["subsystem_attribution"]["RULE4_MIN_EXPLORE_expectancy"] == pytest.approx(2.0)

    def test_exploit_expectancy_correct(self):
        trades = [_make_trade("T1", net_pnl=10.0, exploration_origin=_exploit_origin())]
        result = compute_economic_ground_truth(trades)
        assert result["subsystem_attribution"]["EXPLOIT_expectancy"] == pytest.approx(10.0)

    def test_cross_boundary_expectancy(self):
        trades = [
            _make_trade("T1", net_pnl=5.0, crossed_session_boundary=True),
            _make_trade("T2", net_pnl=3.0, crossed_session_boundary=True),
            _make_trade("T3", net_pnl=-1.0, crossed_session_boundary=False),
        ]
        result = compute_economic_ground_truth(trades)
        sub = result["subsystem_attribution"]
        assert sub["cross_boundary_expectancy"] == pytest.approx(4.0)
        assert sub["cross_boundary_count"] == 2

    def test_within_session_count(self):
        trades = [
            _make_trade("T1", crossed_session_boundary=False),
            _make_trade("T2", crossed_session_boundary=True),
        ]
        result = compute_economic_ground_truth(trades)
        assert result["subsystem_attribution"]["within_session_count"] == 1

    def test_rl_approved_count_equals_total(self):
        trades = [_make_trade(f"T{i}") for i in range(5)]
        result = compute_economic_ground_truth(trades)
        assert result["subsystem_attribution"]["rl_approved_count"] == 5


# ═══════════════════════════════════════════════════════════════════════
# Part 9: Session economics
# ═══════════════════════════════════════════════════════════════════════

class TestSessionEconomics:
    def test_session_economics_is_list(self):
        trades = [_make_trade("T1", origin_session="NY")]
        result = compute_economic_ground_truth(trades)
        assert isinstance(result["session_economics"], list)

    def test_ny_session_appears_when_trades_exist(self):
        trades = [_make_trade("T1", origin_session="NY")]
        result = compute_economic_ground_truth(trades)
        sessions = {r["session"] for r in result["session_economics"]}
        assert "NY" in sessions

    def test_origin_expectancy_correct(self):
        trades = [
            _make_trade("T1", net_pnl=10.0, origin_session="LONDON"),
            _make_trade("T2", net_pnl=-2.0, origin_session="LONDON"),
        ]
        result = compute_economic_ground_truth(trades)
        london = next(r for r in result["session_economics"] if r["session"] == "LONDON")
        assert london["origin_expectancy"] == pytest.approx(4.0)

    def test_session_row_keys(self):
        trades = [_make_trade("T1", origin_session="ASIA")]
        result = compute_economic_ground_truth(trades)
        row = result["session_economics"][0]
        for key in ("session", "origin_trade_count", "origin_expectancy",
                    "close_trade_count", "close_expectancy"):
            assert key in row

    def test_origin_win_rate_correct(self):
        trades = [
            _make_trade("T1", net_pnl= 5.0, origin_session="NY"),
            _make_trade("T2", net_pnl=-3.0, origin_session="NY"),
        ]
        result = compute_economic_ground_truth(trades)
        ny = next(r for r in result["session_economics"] if r["session"] == "NY")
        assert ny["origin_win_rate_pct"] == pytest.approx(50.0)


# ═══════════════════════════════════════════════════════════════════════
# Part 10: Economic classification breakdown
# ═══════════════════════════════════════════════════════════════════════

class TestClassificationBreakdown:
    def test_true_positive_alpha_counted(self):
        # net>0, gross>0, fee_drag<50%, net>noise
        trades = [_make_trade("T1", gross_pnl=10.0, net_pnl=7.0, fee_entry=1.5, fee_exit=1.5)]
        result = compute_economic_ground_truth(trades)
        cls = result["economic_classification"]["TRUE_POSITIVE_ALPHA"]
        assert cls["count"] == 1

    def test_micro_edge_eroded_counted(self):
        # gross>0, net<=0
        trades = [_make_trade("T1", gross_pnl=5.0, net_pnl=-1.0, fee_entry=3.0, fee_exit=3.0)]
        result = compute_economic_ground_truth(trades)
        cls = result["economic_classification"]["MICRO_EDGE_ERODED"]
        assert cls["count"] == 1

    def test_true_negative_counted(self):
        # gross<=0
        trades = [_make_trade("T1", gross_pnl=-5.0, net_pnl=-6.0)]
        result = compute_economic_ground_truth(trades)
        cls = result["economic_classification"]["TRUE_NEGATIVE"]
        assert cls["count"] == 1

    def test_false_edge_portfolio_detection(self):
        # WR > 50% but avg net < 0 → FALSE_EDGE
        trades = [
            _make_trade("T1", net_pnl= 0.1),   # win but tiny
            _make_trade("T2", net_pnl= 0.1),   # win
            _make_trade("T3", net_pnl=-10.0),  # big loss
        ]
        result = compute_economic_ground_truth(trades)
        fe = result["economic_classification"]["FALSE_EDGE"]
        assert fe.get("portfolio_detected") is True

    def test_no_false_edge_when_expectancy_positive(self):
        trades = [
            _make_trade("T1", net_pnl=5.0),
            _make_trade("T2", net_pnl=3.0),
        ]
        result = compute_economic_ground_truth(trades)
        fe = result["economic_classification"]["FALSE_EDGE"]
        assert fe.get("portfolio_detected") is not True

    def test_classification_shares_sum_to_100(self):
        trades = [
            _make_trade("T1", gross_pnl=10.0, net_pnl=5.0, fee_entry=2.0, fee_exit=3.0),
            _make_trade("T2", gross_pnl=5.0,  net_pnl=-1.0, fee_entry=3.0, fee_exit=3.0),
        ]
        result = compute_economic_ground_truth(trades)
        cls = result["economic_classification"]
        total_count = sum(
            v.get("count", 0) for v in cls.values()
            if isinstance(v, dict) and "count" in v
        )
        assert total_count == 2


# ═══════════════════════════════════════════════════════════════════════
# Part 11: Survivability score
# ═══════════════════════════════════════════════════════════════════════

class TestSurvivabilityScore:
    def test_score_keys_present(self):
        trades = [_make_trade("T1")]
        result = compute_economic_ground_truth(trades)
        surv = result["survivability_score"]
        for key in ("score", "max_score", "tier", "evidence"):
            assert key in surv

    def test_max_score_is_100(self):
        result = compute_economic_ground_truth([_make_trade("T1")])
        assert result["survivability_score"]["max_score"] == 100

    def test_score_range_valid(self):
        trades = [_make_trade("T1"), _make_trade("T2", net_pnl=-3.0)]
        result = compute_economic_ground_truth(trades)
        s = result["survivability_score"]["score"]
        assert 0 <= s <= 100

    def test_full_score_conditions(self):
        """Trade with positive expectancy, low fee drag, good asymmetry, winner faster."""
        # Winner: net=10, hold=60s; Loser: net=-4, hold=600s → asymmetry=2.5, winner faster
        trades = [
            _make_trade("T1", gross_pnl=11.0, net_pnl=10.0, fee_entry=0.5, fee_exit=0.5,
                        entry_ts=0, exit_ts=60_000,  exploration_origin=_rule4_origin()),
            _make_trade("T2", gross_pnl=5.0,  net_pnl=4.0,  fee_entry=0.5, fee_exit=0.5,
                        entry_ts=0, exit_ts=60_000,  exploration_origin=_rule4_origin()),
            _make_trade("T3", gross_pnl=-3.0, net_pnl=-4.0, fee_entry=0.5, fee_exit=0.5,
                        entry_ts=0, exit_ts=600_000, exploration_origin=_exploit_origin()),
        ]
        result = compute_economic_ground_truth(trades)
        s = result["survivability_score"]["score"]
        assert s >= 50  # should earn multiple components

    def test_tier_critical_when_low_score(self):
        # All losers → score = 0 → CRITICAL
        trades = [_make_trade("T1", gross_pnl=-5.0, net_pnl=-6.0)]
        result = compute_economic_ground_truth(trades)
        assert result["survivability_score"]["tier"] == "CRITICAL"

    def test_evidence_dict_present_for_all_components(self):
        trades = [_make_trade("T1", net_pnl=5.0)]
        result = compute_economic_ground_truth(trades)
        ev = result["survivability_score"]["evidence"]
        assert isinstance(ev, dict)
        assert len(ev) > 0


# ═══════════════════════════════════════════════════════════════════════
# Part 12: No execution mutation
# ═══════════════════════════════════════════════════════════════════════

class TestNoExecutionMutation:
    def test_classify_trade_economics_pure(self):
        """classify_trade_economics must not modify input dict."""
        trade = _make_trade("T1")
        original_keys = set(trade.keys())
        classify_trade_economics(trade)
        assert set(trade.keys()) == original_keys

    def test_compute_does_not_mutate_trades(self):
        """compute_economic_ground_truth must not modify input list or dicts."""
        trades = [_make_trade("T1"), _make_trade("T2", net_pnl=-3.0)]
        original_ids = [t["trade_id"] for t in trades]
        compute_economic_ground_truth(trades)
        assert [t["trade_id"] for t in trades] == original_ids

    def test_uses_existing_economic_truth_when_present(self):
        """If economic_truth already in trade dict, portfolio analytics use it."""
        pre = {"economic_classification": "TRUE_POSITIVE_ALPHA",
               "fee_drag_pct": 10.0}
        trades = [_make_trade("T1", economic_truth=pre)]
        # Should not raise and should include the pre-computed classification
        result = compute_economic_ground_truth(trades)
        assert result["economic_classification"]["TRUE_POSITIVE_ALPHA"]["count"] >= 1
