"""
FTD-TF-SURVIV — Timeframe Survivability Test Suite

Verifies:
  * shadow projection arithmetic (gross scales, fees constant, hold scales)
  * alpha persistence category correctness (all 5 categories)
  * compute_timeframe_survivability structure and fail-open behaviour
  * fee drag reduction at higher timeframes
  * loser-to-winner flip when MICRO_EDGE_ERODED at 1m but viable at 5m
  * NY and Rule4 session/subset filtering
  * backward compatibility with legacy DataLake records
  * no mutation of input trade dicts
"""
from __future__ import annotations

import copy
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.timeframe_economics import (
    TF_ALPHA_PERSISTENT,
    TIMEFRAME_CONSISTENT,
    MICROSTRUCTURE_ERODED,
    HIGHER_TF_RECOVERY,
    TF_NOISE_COLLAPSE,
    classify_alpha_persistence,
    compute_timeframe_survivability,
    project_trade_to_tf,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _trade(
    *,
    gross_pnl: float = 1.0,
    net_pnl:   float = 0.5,
    fee_entry: float = 0.2,
    fee_exit:  float = 0.3,
    slippage_cost: float = 0.0,
    borrow_cost:   float = 0.0,
    r_multiple: float = 1.0,
    hold_sec:   int   = 60,
    origin_session: str = "NY",
    close_session:  str = "NY",
    crossed_session_boundary: bool = False,
    explore_type: str | None = None,
) -> dict:
    """Minimal trade dict for testing."""
    entry_ts = 1_700_000_000_000
    exit_ts  = entry_ts + hold_sec * 1000
    t: dict = {
        "trade_id":       f"T{int(time.time()*1e6)}",
        "gross_pnl":      gross_pnl,
        "net_pnl":        net_pnl,
        "fee_entry":      fee_entry,
        "fee_exit":       fee_exit,
        "slippage_cost":  slippage_cost,
        "borrow_cost":    borrow_cost,
        "r_multiple":     r_multiple,
        "entry_ts":       entry_ts,
        "exit_ts":        exit_ts,
        "origin_session": origin_session,
        "close_session":  close_session,
        "crossed_session_boundary": crossed_session_boundary,
        "economic_truth": {
            "gross_pnl":               round(gross_pnl, 4),
            "net_pnl":                 round(net_pnl, 4),
            "fees_paid":               round(fee_entry + fee_exit, 4),
            "fee_drag_pct":            round((fee_entry + fee_exit) / gross_pnl * 100, 1)
                                       if gross_pnl > 0 else None,
            "hold_duration_sec":       float(hold_sec),
            "risk_reward_realized":    round(r_multiple, 3),
            "economic_classification": "SURVIVABLE",
            "payoff_geometry":         {"winner_fast": True,
                                        "loser_extended": False,
                                        "crossed_boundary": False},
        },
    }
    if explore_type is not None:
        t["exploration_origin"] = {
            "explore_type":         explore_type,
            "was_exploration_trade": explore_type != "EXPLOIT",
        }
    return t


def _winning_trade(**kw) -> dict:
    kw.setdefault("gross_pnl", 2.0)
    kw.setdefault("net_pnl",   1.5)
    kw.setdefault("fee_entry", 0.25)
    kw.setdefault("fee_exit",  0.25)
    return _trade(**kw)


def _losing_trade(**kw) -> dict:
    kw.setdefault("gross_pnl", 0.5)
    kw.setdefault("net_pnl",  -0.1)
    kw.setdefault("fee_entry", 0.3)
    kw.setdefault("fee_exit",  0.3)
    return _trade(**kw)


def _micro_edge_trade(**kw) -> dict:
    """Gross positive but net negative at 1m → MICRO_EDGE_ERODED."""
    kw.setdefault("gross_pnl", 0.5)
    kw.setdefault("net_pnl",  -0.3)  # fees exceed gross
    kw.setdefault("fee_entry", 0.4)
    kw.setdefault("fee_exit",  0.4)
    return _trade(**kw)


# ── TestProjectTradeToTf ──────────────────────────────────────────────────────

class TestProjectTradeToTf:
    def test_multiplier_1_returns_copy(self):
        t = _trade()
        proj = project_trade_to_tf(t, 1)
        assert proj is not t           # new dict
        assert proj["gross_pnl"] == t["gross_pnl"]

    def test_multiplier_1_preserves_economic_truth(self):
        t = _trade()
        assert project_trade_to_tf(t, 1).get("economic_truth") is not None

    def test_multiplier_5_scales_gross(self):
        t = _trade(gross_pnl=1.0)
        proj = project_trade_to_tf(t, 5)
        assert abs(proj["gross_pnl"] - 5.0) < 1e-9

    def test_multiplier_15_scales_gross(self):
        t = _trade(gross_pnl=2.0)
        proj = project_trade_to_tf(t, 15)
        assert abs(proj["gross_pnl"] - 30.0) < 1e-9

    def test_fees_unchanged_at_5m(self):
        t = _trade(fee_entry=0.2, fee_exit=0.3)
        proj = project_trade_to_tf(t, 5)
        assert proj["fee_entry"] == 0.2
        assert proj["fee_exit"]  == 0.3

    def test_net_pnl_recomputed_correctly(self):
        # gross=1.0 → 5.0, fees=0.2+0.3=0.5, slippage=0, borrow=0, net=4.5
        t = _trade(gross_pnl=1.0, fee_entry=0.2, fee_exit=0.3,
                   slippage_cost=0.0, borrow_cost=0.0)
        proj = project_trade_to_tf(t, 5)
        assert abs(proj["net_pnl"] - 4.5) < 1e-9

    def test_exit_ts_scaled(self):
        t = _trade(hold_sec=120)   # 120 s = 120 000 ms
        proj = project_trade_to_tf(t, 5)
        expected_hold_ms = 120_000 * 5
        assert proj["exit_ts"] == t["entry_ts"] + expected_hold_ms

    def test_economic_truth_removed_for_5m(self):
        t = _trade()
        proj = project_trade_to_tf(t, 5)
        assert "economic_truth" not in proj

    def test_r_multiple_scaled(self):
        t = _trade(r_multiple=2.0)
        proj = project_trade_to_tf(t, 5)
        assert abs(proj["r_multiple"] - 10.0) < 1e-9

    def test_does_not_mutate_original(self):
        t = _trade(gross_pnl=1.0)
        original_gross = t["gross_pnl"]
        project_trade_to_tf(t, 5)
        assert t["gross_pnl"] == original_gross


# ── TestClassifyAlphaPersistence ──────────────────────────────────────────────

class TestClassifyAlphaPersistence:
    def _snap(self, score: int, exp: float) -> dict:
        return {"survivability_score": score, "net_expectancy": exp}

    def test_tf_alpha_persistent_when_all_above_75(self):
        snaps = {
            "1m":  self._snap(80, 0.5),
            "5m":  self._snap(85, 1.0),
            "15m": self._snap(90, 2.0),
        }
        assert classify_alpha_persistence(snaps) == TF_ALPHA_PERSISTENT

    def test_timeframe_consistent_when_all_above_50(self):
        snaps = {
            "1m":  self._snap(55, 0.3),
            "5m":  self._snap(60, 0.5),
            "15m": self._snap(65, 0.8),
        }
        assert classify_alpha_persistence(snaps) == TIMEFRAME_CONSISTENT

    def test_microstructure_eroded_when_1m_fails_5m_survives(self):
        snaps = {
            "1m":  self._snap(30, -0.2),
            "5m":  self._snap(55, 0.5),
            "15m": self._snap(45, 0.1),
        }
        assert classify_alpha_persistence(snaps) == MICROSTRUCTURE_ERODED

    def test_microstructure_eroded_when_1m_fails_15m_survives(self):
        snaps = {
            "1m":  self._snap(20, -0.5),
            "5m":  self._snap(40, 0.0),
            "15m": self._snap(60, 0.8),
        }
        assert classify_alpha_persistence(snaps) == MICROSTRUCTURE_ERODED

    def test_higher_tf_recovery_when_expectancy_improves(self):
        snaps = {
            "1m":  self._snap(25, -0.3),
            "5m":  self._snap(40, 0.1),     # expectancy improves
            "15m": self._snap(45, 0.2),
        }
        assert classify_alpha_persistence(snaps) == HIGHER_TF_RECOVERY

    def test_tf_noise_collapse_when_all_low_no_recovery(self):
        snaps = {
            "1m":  self._snap(10, -0.5),
            "5m":  self._snap(15, -0.4),
            "15m": self._snap(20, -0.3),
        }
        # expectancy -0.4 > -0.5 at 5m → still HIGHER_TF_RECOVERY because e5m > e1m
        # To force TF_NOISE_COLLAPSE, expectancy must NOT improve
        snaps2 = {
            "1m":  self._snap(10, -0.5),
            "5m":  self._snap(15, -0.6),
            "15m": self._snap(20, -0.7),
        }
        assert classify_alpha_persistence(snaps2) == TF_NOISE_COLLAPSE

    def test_none_score_treated_as_zero(self):
        snaps = {
            "1m":  {"survivability_score": None, "net_expectancy": None},
            "5m":  {"survivability_score": None, "net_expectancy": None},
            "15m": {"survivability_score": None, "net_expectancy": None},
        }
        result = classify_alpha_persistence(snaps)
        assert result == TF_NOISE_COLLAPSE


# ── TestComputeTimeframeSurvivabilityStructure ────────────────────────────────

class TestComputeTimeframeSurvivabilityStructure:
    REQUIRED_KEYS = {
        "scope_note", "total_trades", "timeframe_comparison",
        "alpha_persistence_category", "fee_drag_reduction",
        "ny_session_comparison", "rule4_comparison", "exploration_comparison",
    }
    TF_SNAPSHOT_KEYS = {
        "net_expectancy", "gross_expectancy", "win_rate_pct", "fee_drag_mean_pct",
        "payoff_asymmetry", "avg_hold_sec", "survivability_score",
        "survivability_tier", "trade_count", "is_shadow", "shadow_multiplier",
    }

    def test_empty_returns_valid_dict(self):
        result = compute_timeframe_survivability([])
        assert result["total_trades"] == 0
        assert "scope_note" in result

    def test_required_keys_present(self):
        trades = [_winning_trade(), _losing_trade()]
        result = compute_timeframe_survivability(trades)
        assert self.REQUIRED_KEYS <= result.keys()

    def test_timeframe_comparison_has_all_tfs(self):
        result = compute_timeframe_survivability([_winning_trade()])
        tc = result["timeframe_comparison"]
        assert "1m" in tc and "5m" in tc and "15m" in tc

    def test_tf_snapshot_has_required_keys(self):
        result = compute_timeframe_survivability([_winning_trade(), _losing_trade()])
        for tf in ("1m", "5m", "15m"):
            snap = result["timeframe_comparison"][tf]
            assert self.TF_SNAPSHOT_KEYS <= snap.keys(), f"Missing keys in {tf} snapshot"

    def test_1m_is_not_shadow(self):
        result = compute_timeframe_survivability([_winning_trade()])
        assert result["timeframe_comparison"]["1m"]["is_shadow"] is False

    def test_5m_is_shadow(self):
        result = compute_timeframe_survivability([_winning_trade()])
        assert result["timeframe_comparison"]["5m"]["is_shadow"] is True

    def test_total_trades_correct(self):
        trades = [_winning_trade() for _ in range(7)]
        result = compute_timeframe_survivability(trades)
        assert result["total_trades"] == 7

    def test_alpha_persistence_category_is_valid_string(self):
        trades = [_winning_trade(), _losing_trade()]
        result = compute_timeframe_survivability(trades)
        assert result["alpha_persistence_category"] in (
            TF_ALPHA_PERSISTENT, TIMEFRAME_CONSISTENT,
            MICROSTRUCTURE_ERODED, HIGHER_TF_RECOVERY, TF_NOISE_COLLAPSE,
        )

    def test_never_raises_on_garbage(self):
        result = compute_timeframe_survivability([{"bad": "data"}, {}])
        assert "error" in result or "total_trades" in result

    def test_scope_note_contains_shadow_disclaimer(self):
        result = compute_timeframe_survivability([_winning_trade()])
        assert "shadow" in result["scope_note"].lower()


# ── TestFeeScaling ────────────────────────────────────────────────────────────

class TestFeeScaling:
    """Fee drag should decrease proportionally at higher TFs."""

    def _trades_with_known_fee_drag(self) -> list[dict]:
        # gross=1.0, fees=0.5 → fee_drag_1m = 50%
        return [
            _trade(gross_pnl=1.0, net_pnl=0.5, fee_entry=0.25, fee_exit=0.25,
                   slippage_cost=0.0, borrow_cost=0.0)
            for _ in range(5)
        ]

    def test_fee_drag_lower_at_5m(self):
        trades = self._trades_with_known_fee_drag()
        result = compute_timeframe_survivability(trades)
        fd1 = result["timeframe_comparison"]["1m"]["fee_drag_mean_pct"]
        fd5 = result["timeframe_comparison"]["5m"]["fee_drag_mean_pct"]
        assert fd1 is not None and fd5 is not None
        assert fd5 < fd1

    def test_fee_drag_lower_at_15m(self):
        trades = self._trades_with_known_fee_drag()
        result = compute_timeframe_survivability(trades)
        fd1  = result["timeframe_comparison"]["1m"]["fee_drag_mean_pct"]
        fd15 = result["timeframe_comparison"]["15m"]["fee_drag_mean_pct"]
        assert fd1 is not None and fd15 is not None
        assert fd15 < fd1

    def test_fee_drag_reduction_dict_keys_present(self):
        result = compute_timeframe_survivability(self._trades_with_known_fee_drag())
        fdr = result["fee_drag_reduction"]
        for key in ("1m_mean_pct", "5m_shadow_mean_pct", "15m_shadow_mean_pct",
                    "1m_to_5m_delta_pct", "1m_to_15m_delta_pct"):
            assert key in fdr, f"Missing key: {key}"

    def test_fee_drag_delta_is_positive_when_drag_drops(self):
        trades = self._trades_with_known_fee_drag()
        result = compute_timeframe_survivability(trades)
        fdr = result["fee_drag_reduction"]
        # 1m drag > 5m drag → delta should be positive
        d5  = fdr.get("1m_to_5m_delta_pct")
        d15 = fdr.get("1m_to_15m_delta_pct")
        if d5 is not None:
            assert d5 > 0
        if d15 is not None:
            assert d15 > 0


# ── TestWinnerLoserFlip ───────────────────────────────────────────────────────

class TestWinnerLoserFlip:
    """MICRO_EDGE_ERODED at 1m (gross > 0, net < 0) → net positive at 5m."""

    def _micro_edge_trades(self) -> list[dict]:
        # gross=0.5, fees=0.4+0.4=0.8 → net=-0.3 at 1m
        # at 5m: gross=2.5, fees=0.8 → net=1.7 → WINNER
        return [
            _trade(gross_pnl=0.5, net_pnl=-0.3, fee_entry=0.4, fee_exit=0.4,
                   slippage_cost=0.0, borrow_cost=0.0)
            for _ in range(6)
        ]

    def test_net_pnl_positive_at_5m_projection(self):
        t = _trade(gross_pnl=0.5, net_pnl=-0.3, fee_entry=0.4, fee_exit=0.4,
                   slippage_cost=0.0, borrow_cost=0.0)
        proj = project_trade_to_tf(t, 5)
        # expected: gross=2.5, fees=0.8, net=1.7
        assert proj["net_pnl"] > 0

    def test_expectancy_improves_at_5m(self):
        trades = self._micro_edge_trades()
        result = compute_timeframe_survivability(trades)
        e1m = result["timeframe_comparison"]["1m"]["net_expectancy"]
        e5m = result["timeframe_comparison"]["5m"]["net_expectancy"]
        assert e5m > e1m

    def test_category_indicates_recovery(self):
        trades = self._micro_edge_trades()
        result = compute_timeframe_survivability(trades)
        cat = result["alpha_persistence_category"]
        assert cat in (MICROSTRUCTURE_ERODED, HIGHER_TF_RECOVERY, TIMEFRAME_CONSISTENT,
                       TF_ALPHA_PERSISTENT)


# ── TestNySessionFilter ───────────────────────────────────────────────────────

class TestNySessionFilter:
    def test_ny_comparison_session_key(self):
        trades = [_trade(origin_session="NY"), _trade(origin_session="ASIA")]
        result = compute_timeframe_survivability(trades)
        assert result["ny_session_comparison"].get("session") == "NY"

    def test_ny_trade_count_excludes_other_sessions(self):
        trades = [
            _trade(origin_session="NY"),
            _trade(origin_session="NY"),
            _trade(origin_session="LONDON"),
        ]
        result = compute_timeframe_survivability(trades)
        assert result["ny_session_comparison"].get("trade_count") == 2

    def test_ny_comparison_has_tf_keys(self):
        trades = [_trade(origin_session="NY")]
        result = compute_timeframe_survivability(trades)
        ny = result["ny_session_comparison"]
        if "note" not in ny:
            for tf in ("1m", "5m", "15m"):
                assert tf in ny, f"Missing TF key {tf} in ny_session_comparison"

    def test_no_ny_trades_returns_note(self):
        trades = [_trade(origin_session="ASIA")]
        result = compute_timeframe_survivability(trades)
        ny = result["ny_session_comparison"]
        assert "note" in ny or ny.get("trade_count", 0) == 0


# ── TestRule4Filter ───────────────────────────────────────────────────────────

class TestRule4Filter:
    def test_rule4_comparison_label(self):
        trades = [_trade(explore_type="RULE4_MIN_EXPLORE")]
        result = compute_timeframe_survivability(trades)
        assert result["rule4_comparison"].get("label") == "RULE4_MIN_EXPLORE"

    def test_rule4_trade_count_only_rule4(self):
        trades = [
            _trade(explore_type="RULE4_MIN_EXPLORE"),
            _trade(explore_type="RULE4_MIN_EXPLORE"),
            _trade(explore_type="EXPLOIT"),
        ]
        result = compute_timeframe_survivability(trades)
        rc = result["rule4_comparison"]
        if "note" not in rc:
            assert rc.get("trade_count") == 2

    def test_no_rule4_trades_returns_note(self):
        trades = [_trade(explore_type="EXPLOIT")]
        result = compute_timeframe_survivability(trades)
        rc = result["rule4_comparison"]
        assert "note" in rc


# ── TestBackwardCompatibility ─────────────────────────────────────────────────

class TestBackwardCompatibility:
    def test_trades_without_economic_truth_work(self):
        t = _trade()
        del t["economic_truth"]
        result = compute_timeframe_survivability([t])
        assert result["total_trades"] == 1

    def test_trades_without_exploration_origin_work(self):
        t = _trade()
        t.pop("exploration_origin", None)
        result = compute_timeframe_survivability([t])
        assert "timeframe_comparison" in result

    def test_trades_missing_many_fields_do_not_crash(self):
        result = compute_timeframe_survivability([{"net_pnl": 0.5, "gross_pnl": 1.0}])
        assert result.get("total_trades") == 1

    def test_pre_existing_economic_truth_used_at_1m(self):
        t = _trade(gross_pnl=1.0, net_pnl=0.5, fee_entry=0.25, fee_exit=0.25)
        # Override economic_truth with a known fee_drag_pct
        t["economic_truth"]["fee_drag_pct"] = 50.0
        proj = project_trade_to_tf(t, 1)
        assert proj["economic_truth"]["fee_drag_pct"] == 50.0


# ── TestNoExecutionMutation ───────────────────────────────────────────────────

class TestNoExecutionMutation:
    def test_project_trade_does_not_mutate_original(self):
        t = _trade(gross_pnl=1.0)
        before = copy.deepcopy(t)
        project_trade_to_tf(t, 5)
        assert t["gross_pnl"]  == before["gross_pnl"]
        assert t["net_pnl"]    == before["net_pnl"]
        assert t["exit_ts"]    == before["exit_ts"]
        assert t.get("economic_truth") == before.get("economic_truth")

    def test_compute_does_not_mutate_input_list(self):
        trades = [_winning_trade(), _losing_trade()]
        original_ids = [id(t) for t in trades]
        original_gross = [t["gross_pnl"] for t in trades]
        compute_timeframe_survivability(trades)
        assert [id(t) for t in trades] == original_ids
        assert [t["gross_pnl"] for t in trades] == original_gross

    def test_compute_does_not_mutate_individual_trade_dicts(self):
        t = _trade(gross_pnl=2.0)
        gross_before = t["gross_pnl"]
        compute_timeframe_survivability([t])
        assert t["gross_pnl"] == gross_before
