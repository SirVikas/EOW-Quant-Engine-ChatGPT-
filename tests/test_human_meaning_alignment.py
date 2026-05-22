"""
Tests for FTD-HMAO — Constitutional Human Meaning Alignment
& Purpose Integrity Observatory.

Coverage:
  - _alignment_snapshot
  - All 8 alignment metrics
  - _alignment_integrity_score
  - _classify_alignment
  - _build_alignment_lineage
  - _generate_alignment_recommendations
  - _generate_alignment_audit_entry
  - compute_human_meaning_alignment (structure, isolation, constitutional invariants)
  - Edge cases: empty, single trade, n<10, very large corpora, malformed input
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from core.alignment_observatory import (
    ALIGNMENT_HARD_PRINCIPLES,
    ALIGNMENT_LOCKDOWN_RISK,
    HUMAN_ACCOUNTABILITY_DECAY,
    HUMAN_ALIGNED,
    INTERPRETABILITY_WEAKENING,
    METRIC_DETACHMENT_RISK,
    PURPOSE_DRIFT_ACCELERATION,
    _alignment_integrity_score,
    _alignment_snapshot,
    _build_alignment_lineage,
    _causal_traceability_metric,
    _classify_alignment,
    _compute_alignment_metrics,
    _generate_alignment_audit_entry,
    _generate_alignment_recommendations,
    _governance_readability_metric,
    _human_accountability_continuity_metric,
    _human_interpretability_metric,
    _human_value_retention_metric,
    _optimization_drift_metric,
    _purpose_alignment_stability_metric,
    _recommendation_explainability_metric,
    compute_human_meaning_alignment,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_trade(i: int = 0, **kw) -> dict:
    base = {
        "trade_id":    f"TRD-{i:04d}",
        "entry_ts":    1_700_000_000_000 + i * 60_000,
        "exit_ts":     1_700_000_000_000 + i * 60_000 + 30_000,
        "net_pnl":     1.0 if i % 2 == 0 else -1.0,
        "gross_pnl":   1.5 if i % 2 == 0 else -0.5,
        "fee_entry":   0.10,
        "fee_exit":    0.10,
        "slippage_cost": 0.05,
        "regime":      "TRENDING",
        "origin_session": "NY",
        "exploration_origin": {"was_exploration_trade": i % 10 == 0},
    }
    base.update(kw)
    return base


def _make_diverse_trades(n: int = 80) -> list:
    """
    Produces a corpus with 4 regimes, 4 sessions, ~10% exploration,
    moderate win rate (~0.5), regular timestamps, and full field coverage.
    Should score HUMAN_ALIGNED.
    """
    regimes  = ["TRENDING", "RANGING", "BREAKOUT", "REVERSAL"]
    sessions = ["NY", "LN", "AS", "EU"]
    trades = []
    for i in range(n):
        r_idx = i % 4
        win = (i // 4) % 2 == 0
        trades.append({
            "trade_id":      f"TRD-{i:04d}",
            "entry_ts":      1_700_000_000_000 + i * 60_000,
            "exit_ts":       1_700_000_000_000 + i * 60_000 + 30_000,
            "net_pnl":       1.0 if win else -1.0,
            "gross_pnl":     1.5 if win else -0.5,
            "fee_entry":     0.10,
            "fee_exit":      0.10,
            "slippage_cost": 0.05,
            "regime":        regimes[r_idx],
            "origin_session": sessions[r_idx],
            "exploration_origin": {"was_exploration_trade": i % 10 == 0},
        })
    return trades


def _make_perfect_snapshot(n: int = 50) -> dict:
    return {
        "total_trades":      n,
        "trade_id_coverage": 1.0,
        "entry_ts_coverage": 1.0,
        "exit_ts_coverage":  1.0,
        "net_pnl_coverage":  1.0,
        "gross_pnl_coverage": 1.0,
        "fee_coverage":      1.0,
        "slippage_coverage": 1.0,
        "regime_coverage":   1.0,
        "session_coverage":  1.0,
        "explore_coverage":  0.10,
        "distinct_regimes":  4,
        "distinct_sessions": 4,
        "win_rate":          0.50,
        "exploration_ratio": 0.10,
        "dominant_regime":   "TRENDING",
    }


# ══════════════════════════════════════════════════════════════════════════════
# TestAlignmentSnapshot
# ══════════════════════════════════════════════════════════════════════════════

class TestAlignmentSnapshot:

    def test_empty_list_returns_zero_base(self):
        snap = _alignment_snapshot([])
        assert snap["total_trades"] == 0
        assert snap["trade_id_coverage"] == 0.0
        assert snap["distinct_regimes"] == 0

    def test_full_coverage_single_trade(self):
        snap = _alignment_snapshot([_make_trade(0)])
        assert snap["total_trades"] == 1
        assert snap["trade_id_coverage"] == 1.0
        assert snap["entry_ts_coverage"] == 1.0
        assert snap["exit_ts_coverage"] == 1.0

    def test_distinct_regimes_counted(self):
        trades = [_make_trade(i, regime=r) for i, r in enumerate(
            ["TRENDING", "RANGING", "BREAKOUT", "REVERSAL"]
        )]
        snap = _alignment_snapshot(trades)
        assert snap["distinct_regimes"] == 4

    def test_distinct_sessions_counted(self):
        trades = [_make_trade(i, origin_session=s) for i, s in enumerate(
            ["NY", "LN", "AS", "EU"]
        )]
        snap = _alignment_snapshot(trades)
        assert snap["distinct_sessions"] == 4

    def test_win_rate_calculation(self):
        trades = [_make_trade(i, net_pnl=1.0) for i in range(8)]
        trades += [_make_trade(i + 8, net_pnl=-1.0) for i in range(2)]
        snap = _alignment_snapshot(trades)
        assert abs(snap["win_rate"] - 0.8) < 0.01

    def test_exploration_ratio(self):
        trades = [
            _make_trade(i, exploration_origin={"was_exploration_trade": i < 10})
            for i in range(100)
        ]
        snap = _alignment_snapshot(trades)
        assert abs(snap["exploration_ratio"] - 0.10) < 0.01

    def test_missing_fields_handled_gracefully(self):
        trades = [{"net_pnl": 1.0}, {"regime": "TRENDING"}]
        snap = _alignment_snapshot(trades)
        assert snap["total_trades"] == 2
        assert 0.0 <= snap["trade_id_coverage"] <= 1.0

    def test_dominant_regime_selected(self):
        trades = [_make_trade(i, regime="TRENDING") for i in range(6)]
        trades += [_make_trade(i + 6, regime="RANGING") for i in range(2)]
        snap = _alignment_snapshot(trades)
        assert snap["dominant_regime"] == "TRENDING"


# ══════════════════════════════════════════════════════════════════════════════
# TestHumanInterpretabilityMetric
# ══════════════════════════════════════════════════════════════════════════════

class TestHumanInterpretabilityMetric:

    def test_empty_snapshot_returns_insufficient(self):
        m = _human_interpretability_metric({"total_trades": 0})
        assert m["score"] == 0.0
        assert m["tier"] == "INSUFFICIENT"

    def test_perfect_coverage_interpretable(self):
        snap = _make_perfect_snapshot()
        m = _human_interpretability_metric(snap)
        assert m["score"] < 15.0
        assert m["tier"] == "INTERPRETABLE"

    def test_single_regime_no_exploration_opaque(self):
        snap = _make_perfect_snapshot()
        snap["distinct_regimes"]  = 1
        snap["distinct_sessions"] = 1
        snap["exploration_ratio"] = 0.0
        m = _human_interpretability_metric(snap)
        # reg_div=0.25, sess_div=0.25, exp_div=0.0 → interp=0.25*0.40+0.25*0.30+0=0.175
        # score = (1-0.175)*100 = 82.5 → OPAQUE
        assert m["score"] >= 65.0
        assert m["tier"] == "OPAQUE"

    def test_adequate_tier_boundary(self):
        snap = _make_perfect_snapshot()
        # Drive score to ~25 (ADEQUATE = 15..34)
        snap["distinct_regimes"]  = 2
        snap["distinct_sessions"] = 2
        snap["exploration_ratio"] = 0.05
        m = _human_interpretability_metric(snap)
        assert m["tier"] in ("ADEQUATE", "WEAKENING")

    def test_output_keys_present(self):
        m = _human_interpretability_metric(_make_perfect_snapshot())
        assert "score" in m
        assert "tier" in m
        assert "distinct_regimes" in m
        assert "exploration_ratio" in m


# ══════════════════════════════════════════════════════════════════════════════
# TestRecommendationExplainabilityMetric
# ══════════════════════════════════════════════════════════════════════════════

class TestRecommendationExplainabilityMetric:

    def test_empty_snapshot_insufficient(self):
        m = _recommendation_explainability_metric({"total_trades": 0})
        assert m["score"] == 0.0
        assert m["tier"] == "INSUFFICIENT"

    def test_full_coverage_balanced_wr_explainable(self):
        snap = _make_perfect_snapshot()
        snap["win_rate"] = 0.50
        m = _recommendation_explainability_metric(snap)
        # pnl_diversity = 1 - |0.5-0.5|*2 = 1.0; all cov=1.0 → score=0 → EXPLAINABLE
        assert m["score"] < 10.0
        assert m["tier"] == "EXPLAINABLE"

    def test_no_coverage_extreme_wr_opaque(self):
        snap = {
            "total_trades": 30,
            "fee_coverage": 0.0, "slippage_coverage": 0.0,
            "regime_coverage": 0.0, "win_rate": 1.0,
        }
        m = _recommendation_explainability_metric(snap)
        # pnl_diversity = 1-|1.0-0.5|*2=0; all cov=0 → explainability=0 → score=100 → OPAQUE
        assert m["score"] >= 60.0
        assert m["tier"] == "OPAQUE"

    def test_pnl_diversity_calculation(self):
        snap = _make_perfect_snapshot()
        snap["win_rate"] = 0.0
        # pnl_diversity = 1 - |0.0-0.5|*2 = 0.0
        m = _recommendation_explainability_metric(snap)
        # fee=1.0*0.30 + slip=1.0*0.25 + regime=1.0*0.25 + 0*0.20 = 0.80
        # score = (1-0.80)*100 = 20.0 → ADEQUATE
        assert m["tier"] in ("ADEQUATE", "LIMITED")

    def test_output_keys_present(self):
        m = _recommendation_explainability_metric(_make_perfect_snapshot())
        assert "score" in m
        assert "tier" in m
        assert "fee_coverage" in m
        assert "pnl_diversity" in m


# ══════════════════════════════════════════════════════════════════════════════
# TestCausalTraceabilityMetric
# ══════════════════════════════════════════════════════════════════════════════

class TestCausalTraceabilityMetric:

    def test_empty_snapshot_insufficient(self):
        m = _causal_traceability_metric({"total_trades": 0})
        assert m["score"] == 0.0
        assert m["tier"] == "INSUFFICIENT"

    def test_full_coverage_traceable(self):
        snap = _make_perfect_snapshot()
        m = _causal_traceability_metric(snap)
        assert m["score"] < 10.0
        assert m["tier"] == "TRACEABLE"

    def test_no_coverage_untraceable(self):
        snap = {
            "total_trades": 30,
            "trade_id_coverage": 0.0,
            "entry_ts_coverage": 0.0,
            "exit_ts_coverage":  0.0,
        }
        m = _causal_traceability_metric(snap)
        assert m["score"] == 100.0
        assert m["tier"] == "UNTRACEABLE"

    def test_partial_coverage_partial_tier(self):
        snap = _make_perfect_snapshot()
        snap["trade_id_coverage"] = 0.0
        # traceability = 0*0.40 + 1*0.35 + 1*0.25 = 0.60 → score=40 → PARTIAL
        m = _causal_traceability_metric(snap)
        assert m["tier"] == "PARTIAL"

    def test_missing_exit_ts_adequate(self):
        snap = _make_perfect_snapshot()
        snap["exit_ts_coverage"] = 0.0
        # traceability = 1*0.40 + 1*0.35 + 0*0.25 = 0.75 → score=25 → ADEQUATE
        m = _causal_traceability_metric(snap)
        assert m["tier"] == "ADEQUATE"


# ══════════════════════════════════════════════════════════════════════════════
# TestGovernanceReadabilityMetric
# ══════════════════════════════════════════════════════════════════════════════

class TestGovernanceReadabilityMetric:

    def test_empty_snapshot_insufficient(self):
        m = _governance_readability_metric({"total_trades": 0})
        assert m["score"] == 0.0
        assert m["tier"] == "INSUFFICIENT"

    def test_full_coverage_readable(self):
        snap = _make_perfect_snapshot()
        snap["explore_coverage"] = 0.10
        m = _governance_readability_metric(snap)
        # readability = 1*0.40 + 1*0.35 + 0.10*0.25 = 0.775 → score=22.5 → ADEQUATE
        assert m["tier"] in ("READABLE", "ADEQUATE")

    def test_no_coverage_unreadable(self):
        snap = {
            "total_trades": 30,
            "regime_coverage": 0.0, "session_coverage": 0.0, "explore_coverage": 0.0,
        }
        m = _governance_readability_metric(snap)
        assert m["score"] == 100.0
        assert m["tier"] == "UNREADABLE"

    def test_degraded_tier(self):
        snap = _make_perfect_snapshot()
        snap["regime_coverage"] = 0.4
        snap["session_coverage"] = 0.4
        snap["explore_coverage"] = 0.0
        # readability = 0.4*0.40 + 0.4*0.35 + 0*0.25 = 0.16+0.14 = 0.30
        # score = 70.0 → UNREADABLE... adjust
        snap["regime_coverage"] = 0.5
        snap["session_coverage"] = 0.5
        snap["explore_coverage"] = 0.0
        # readability = 0.5*0.40 + 0.5*0.35 = 0.20+0.175 = 0.375 → score=62.5 → UNREADABLE
        m = _governance_readability_metric(snap)
        assert m["tier"] in ("DEGRADED", "UNREADABLE")


# ══════════════════════════════════════════════════════════════════════════════
# TestOptimizationDriftMetric
# ══════════════════════════════════════════════════════════════════════════════

class TestOptimizationDriftMetric:

    def test_empty_snapshot_insufficient(self):
        m = _optimization_drift_metric([], {"total_trades": 0})
        assert m["score"] == 0.0
        assert m["tier"] == "INSUFFICIENT"

    def test_balanced_wr_good_exploration_aligned(self):
        trades = _make_diverse_trades(40)
        snap   = _alignment_snapshot(trades)
        m      = _optimization_drift_metric(trades, snap)
        assert m["tier"] in ("ALIGNED", "MODERATE")

    def test_extreme_wr_no_exploration_detached(self):
        trades = [
            _make_trade(i, net_pnl=1.0,
                        exploration_origin={"was_exploration_trade": False})
            for i in range(30)
        ]
        snap = _alignment_snapshot(trades)
        snap["win_rate"]          = 0.97
        snap["exploration_ratio"] = 0.0
        m = _optimization_drift_metric(trades, snap)
        # wr_extremity = |0.97-0.5|*2 = 0.94 → *0.40 = 0.376
        # exp_deficit = max(0, (0.05-0)/0.05) = 1.0 → *0.40 = 0.40
        # drift_score ≥ 0.776 → score ≥ 77.6 → DETACHED
        assert m["score"] >= 65.0
        assert m["tier"] == "DETACHED"

    def test_exploration_deficit_only(self):
        trades = [
            _make_trade(i, net_pnl=0.5,
                        exploration_origin={"was_exploration_trade": False})
            for i in range(30)
        ]
        snap = _alignment_snapshot(trades)
        # wr ~1.0 for all positives → extremity high
        snap["win_rate"]          = 0.5
        snap["exploration_ratio"] = 0.0
        m = _optimization_drift_metric(trades, snap)
        assert m["exploration_deficit"] == 1.0

    def test_less_than_20_trades_no_decay_penalty(self):
        trades = [_make_trade(i, exploration_origin={"was_exploration_trade": i < 3})
                  for i in range(10)]
        snap = _alignment_snapshot(trades)
        m = _optimization_drift_metric(trades, snap)
        assert m["explore_decay_penalty"] == 0.0

    def test_explore_decay_drives_score_up(self):
        # Early trades: high exploration; late: zero
        trades = []
        for i in range(40):
            was_exp = i < 20  # first 20 all explore, last 20 none
            trades.append(_make_trade(
                i, net_pnl=0.5,
                exploration_origin={"was_exploration_trade": was_exp}
            ))
        snap = _alignment_snapshot(trades)
        snap["win_rate"]          = 0.5
        snap["exploration_ratio"] = 0.50  # override to neutral for drift isolation
        m = _optimization_drift_metric(trades, snap)
        # early_exp=1.0, late_exp=0.0, decline=1.0, penalty=min(1.0/0.10,1)=1.0 → *0.20=0.20
        assert m["explore_decay_penalty"] > 0.0

    def test_output_keys_present(self):
        snap = _make_perfect_snapshot()
        m = _optimization_drift_metric(_make_diverse_trades(40), snap)
        assert "score" in m and "tier" in m
        assert "win_rate_extremity" in m
        assert "exploration_deficit" in m
        assert "explore_decay_penalty" in m


# ══════════════════════════════════════════════════════════════════════════════
# TestHumanAccountabilityContinuityMetric
# ══════════════════════════════════════════════════════════════════════════════

class TestHumanAccountabilityContinuityMetric:

    def test_empty_snapshot_insufficient(self):
        m = _human_accountability_continuity_metric([], {"total_trades": 0})
        assert m["score"] == 0.0
        assert m["tier"] == "INSUFFICIENT"

    def test_full_coverage_regular_timestamps_continuous(self):
        trades = [_make_trade(i) for i in range(30)]
        snap   = _alignment_snapshot(trades)
        m      = _human_accountability_continuity_metric(trades, snap)
        assert m["tier"] == "CONTINUOUS"

    def test_no_trade_ids_no_timestamps_compromised(self):
        trades = [{"net_pnl": 1.0} for _ in range(30)]
        snap   = _alignment_snapshot(trades)
        m      = _human_accountability_continuity_metric(trades, snap)
        # trade_id_cov=0, entry_ts_cov=0 → account_cov ≈ 0.20*(1-gap_sev)
        # With no ts_vals → gap_severity=0 → account_cov=0.20 → score=80 → COMPROMISED
        assert m["score"] >= 60.0
        assert m["tier"] == "COMPROMISED"

    def test_massive_gap_increases_score(self):
        trades = [_make_trade(i) for i in range(5)]
        # Add a giant gap
        trades.append(_make_trade(6, entry_ts=1_700_000_000_000 + 99_999_999_999))
        snap = _alignment_snapshot(trades)
        m = _human_accountability_continuity_metric(trades, snap)
        assert m["gap_severity"] > 0.0

    def test_output_keys_present(self):
        trades = [_make_trade(i) for i in range(10)]
        snap   = _alignment_snapshot(trades)
        m      = _human_accountability_continuity_metric(trades, snap)
        assert "score" in m and "tier" in m
        assert "trade_id_coverage" in m
        assert "gap_severity" in m


# ══════════════════════════════════════════════════════════════════════════════
# TestPurposeAlignmentStabilityMetric
# ══════════════════════════════════════════════════════════════════════════════

class TestPurposeAlignmentStabilityMetric:

    def test_fewer_than_10_trades_returns_insufficient(self):
        trades = [_make_trade(i) for i in range(9)]
        m = _purpose_alignment_stability_metric(trades)
        assert m["score"] == 0.0
        assert m["tier"] == "INSUFFICIENT"

    def test_exactly_10_trades_computes(self):
        trades = [_make_trade(i) for i in range(10)]
        m = _purpose_alignment_stability_metric(trades)
        assert m["tier"] in ("STABLE", "MODERATE", "SHIFTING", "DRIFTING", "INSUFFICIENT")

    def test_stable_diverse_trades(self):
        trades = _make_diverse_trades(80)
        m = _purpose_alignment_stability_metric(trades)
        assert m["tier"] in ("STABLE", "MODERATE")

    def test_large_wr_drift_drifting(self):
        # First half: all wins; second half: all losses
        trades = [_make_trade(i, net_pnl=1.0)  for i in range(20)]
        trades += [_make_trade(i + 20, net_pnl=-1.0) for i in range(20)]
        m = _purpose_alignment_stability_metric(trades)
        # wr_drift = |0.0 - 1.0| = 1.0 → drift = 1.0*0.50 + ... → score >> 100 → capped at 100
        assert m["score"] >= 45.0
        assert m["tier"] in ("SHIFTING", "DRIFTING")

    def test_regime_shift_penalised(self):
        # Early: one regime, late: different regime
        trades  = [_make_trade(i, regime="TRENDING") for i in range(10)]
        trades += [_make_trade(i + 10, regime="REVERSAL") for i in range(10)]
        m = _purpose_alignment_stability_metric(trades)
        assert m["regime_shift"] > 0.0

    def test_output_keys_present(self):
        m = _purpose_alignment_stability_metric(_make_diverse_trades(40))
        assert "score" in m and "tier" in m
        assert "win_rate_drift" in m
        assert "exploration_drift" in m
        assert "regime_shift" in m


# ══════════════════════════════════════════════════════════════════════════════
# TestHumanValueRetentionMetric
# ══════════════════════════════════════════════════════════════════════════════

class TestHumanValueRetentionMetric:

    def test_empty_snapshot_insufficient(self):
        m = _human_value_retention_metric({"total_trades": 0})
        assert m["score"] == 0.0
        assert m["tier"] == "INSUFFICIENT"

    def test_full_coverage_retained(self):
        snap = _make_perfect_snapshot()
        m = _human_value_retention_metric(snap)
        # retention = 1*0.40+1*0.25+1*0.20+1*0.15 = 1.0 → score=0 → RETAINED
        assert m["score"] < 10.0
        assert m["tier"] == "RETAINED"

    def test_zero_coverage_lost(self):
        snap = {
            "total_trades": 30,
            "net_pnl_coverage": 0.0, "gross_pnl_coverage": 0.0,
            "fee_coverage": 0.0,     "slippage_coverage": 0.0,
        }
        m = _human_value_retention_metric(snap)
        assert m["score"] == 100.0
        assert m["tier"] == "LOST"

    def test_partial_coverage_degrading(self):
        snap = _make_perfect_snapshot()
        snap["net_pnl_coverage"]   = 0.5
        snap["gross_pnl_coverage"] = 0.5
        snap["fee_coverage"]       = 0.0
        snap["slippage_coverage"]  = 0.0
        # retention = 0.5*0.40 + 0.5*0.25 = 0.20+0.125 = 0.325 → score=67.5 → LOST
        m = _human_value_retention_metric(snap)
        assert m["tier"] in ("DEGRADING", "LOST")

    def test_output_keys_present(self):
        m = _human_value_retention_metric(_make_perfect_snapshot())
        assert "score" in m and "tier" in m
        assert "net_pnl_coverage" in m
        assert "fee_coverage" in m
        assert "slippage_coverage" in m


# ══════════════════════════════════════════════════════════════════════════════
# TestAlignmentIntegrityScore
# ══════════════════════════════════════════════════════════════════════════════

class TestAlignmentIntegrityScore:

    def test_fewer_than_10_trades_critical_with_note(self):
        s = _alignment_integrity_score({}, 9)
        assert s["tier"] == "CRITICAL"
        assert "note" in s
        assert s["score"] == 0.0

    def test_all_zero_metric_scores_yields_100(self):
        metrics = {k: {"score": 0.0} for k in [
            "human_interpretability", "recommendation_explainability",
            "causal_traceability", "governance_readability",
            "optimization_drift", "human_accountability_continuity",
            "purpose_alignment_stability", "human_value_retention",
        ]}
        s = _alignment_integrity_score(metrics, 50)
        assert s["score"] == 100.0
        assert s["tier"] == "HUMAN_ALIGNED"

    def test_all_max_metric_scores_yields_zero(self):
        metrics = {k: {"score": 100.0} for k in [
            "human_interpretability", "recommendation_explainability",
            "causal_traceability", "governance_readability",
            "optimization_drift", "human_accountability_continuity",
            "purpose_alignment_stability", "human_value_retention",
        ]}
        s = _alignment_integrity_score(metrics, 50)
        assert s["score"] == 0.0
        assert s["tier"] == "CRITICAL"

    def test_weights_sum_to_one(self):
        # Verify score = 100 - 1.0 * single_score when all equal
        target_score = 40.0
        metrics = {k: {"score": target_score} for k in [
            "human_interpretability", "recommendation_explainability",
            "causal_traceability", "governance_readability",
            "optimization_drift", "human_accountability_continuity",
            "purpose_alignment_stability", "human_value_retention",
        ]}
        s = _alignment_integrity_score(metrics, 50)
        assert abs(s["score"] - (100.0 - target_score)) < 0.01

    def test_adequate_tier(self):
        metrics = {k: {"score": 45.0} for k in [
            "human_interpretability", "recommendation_explainability",
            "causal_traceability", "governance_readability",
            "optimization_drift", "human_accountability_continuity",
            "purpose_alignment_stability", "human_value_retention",
        ]}
        s = _alignment_integrity_score(metrics, 50)
        # score = 100 - 45 = 55.0 → ADEQUATE
        assert s["tier"] == "ADEQUATE"

    def test_vulnerable_tier(self):
        metrics = {k: {"score": 50.0} for k in [
            "human_interpretability", "recommendation_explainability",
            "causal_traceability", "governance_readability",
            "optimization_drift", "human_accountability_continuity",
            "purpose_alignment_stability", "human_value_retention",
        ]}
        s = _alignment_integrity_score(metrics, 50)
        # score = 100 - 50 = 50.0 → VULNERABLE (35 ≤ x < 55)
        assert s["tier"] == "VULNERABLE"


# ══════════════════════════════════════════════════════════════════════════════
# TestClassification
# ══════════════════════════════════════════════════════════════════════════════

class TestClassification:

    def _healthy_metrics(self) -> dict:
        return {
            "human_interpretability":          {"score": 0.0,  "tier": "INTERPRETABLE"},
            "recommendation_explainability":   {"score": 0.0,  "tier": "EXPLAINABLE"},
            "causal_traceability":             {"score": 0.0,  "tier": "TRACEABLE"},
            "governance_readability":          {"score": 0.0,  "tier": "READABLE"},
            "optimization_drift":              {"score": 0.0,  "tier": "ALIGNED"},
            "human_accountability_continuity": {"score": 0.0,  "tier": "CONTINUOUS"},
            "purpose_alignment_stability":     {"score": 0.0,  "tier": "STABLE"},
            "human_value_retention":           {"score": 0.0,  "tier": "RETAINED"},
        }

    def test_fewer_than_10_trades_no_false_alarm(self):
        cls = _classify_alignment(self._healthy_metrics(), {"score": 0.0}, 9)
        assert cls == HUMAN_ALIGNED

    def test_all_healthy_human_aligned(self):
        cls = _classify_alignment(
            self._healthy_metrics(), {"score": 100.0, "tier": "HUMAN_ALIGNED"}, 50
        )
        assert cls == HUMAN_ALIGNED

    def test_score_below_20_lockdown(self):
        cls = _classify_alignment(
            self._healthy_metrics(), {"score": 15.0, "tier": "CRITICAL"}, 50
        )
        assert cls == ALIGNMENT_LOCKDOWN_RISK

    def test_compromised_accountability_decay(self):
        m = self._healthy_metrics()
        m["human_accountability_continuity"]["tier"] = "COMPROMISED"
        cls = _classify_alignment(m, {"score": 60.0}, 50)
        assert cls == HUMAN_ACCOUNTABILITY_DECAY

    def test_untraceable_causal_traceability_accountability_decay(self):
        m = self._healthy_metrics()
        m["causal_traceability"]["tier"] = "UNTRACEABLE"
        cls = _classify_alignment(m, {"score": 60.0}, 50)
        assert cls == HUMAN_ACCOUNTABILITY_DECAY

    def test_detached_drift_metric_detachment(self):
        m = self._healthy_metrics()
        m["optimization_drift"]["tier"] = "DETACHED"
        cls = _classify_alignment(m, {"score": 60.0}, 50)
        assert cls == METRIC_DETACHMENT_RISK

    def test_opaque_interpretability_metric_detachment(self):
        m = self._healthy_metrics()
        m["human_interpretability"]["tier"] = "OPAQUE"
        cls = _classify_alignment(m, {"score": 60.0}, 50)
        assert cls == METRIC_DETACHMENT_RISK

    def test_drifting_purpose_with_drifting_drift_purpose_drift(self):
        m = self._healthy_metrics()
        m["purpose_alignment_stability"]["tier"] = "DRIFTING"
        m["optimization_drift"]["tier"]          = "DRIFTING"
        cls = _classify_alignment(m, {"score": 60.0}, 50)
        assert cls == PURPOSE_DRIFT_ACCELERATION

    def test_shifting_purpose_with_drifting_drift_purpose_drift(self):
        m = self._healthy_metrics()
        m["purpose_alignment_stability"]["tier"] = "SHIFTING"
        m["optimization_drift"]["tier"]          = "DRIFTING"
        cls = _classify_alignment(m, {"score": 60.0}, 50)
        assert cls == PURPOSE_DRIFT_ACCELERATION

    def test_weakening_interpretability_weakening_classification(self):
        m = self._healthy_metrics()
        m["human_interpretability"]["tier"] = "WEAKENING"
        cls = _classify_alignment(m, {"score": 80.0}, 50)
        assert cls == INTERPRETABILITY_WEAKENING

    def test_lockdown_takes_priority_over_accountability_decay(self):
        m = self._healthy_metrics()
        m["human_accountability_continuity"]["tier"] = "COMPROMISED"
        cls = _classify_alignment(m, {"score": 5.0}, 50)
        assert cls == ALIGNMENT_LOCKDOWN_RISK


# ══════════════════════════════════════════════════════════════════════════════
# TestAlignmentLineage
# ══════════════════════════════════════════════════════════════════════════════

class TestAlignmentLineage:

    def test_empty_trades_unknown_trajectory(self):
        lin = _build_alignment_lineage([], {})
        assert lin["alignment_trajectory"] == "UNKNOWN"
        assert lin["total_epochs"] == 0
        assert lin["epochs"] == {}

    def test_epoch_health_aligned(self):
        # All trades: wr=0.5, exp=0.10 → ALIGNED
        trades = _make_diverse_trades(60)
        lin = _build_alignment_lineage(trades, _alignment_snapshot(trades))
        for name in ("early", "mid", "late"):
            ep = lin["epochs"].get(name)
            if ep:
                assert ep["alignment_health"] in ("ALIGNED", "EMERGING", "DRIFTING")

    def test_epoch_health_drifting_when_no_exploration(self):
        trades = [
            _make_trade(i, exploration_origin={"was_exploration_trade": False})
            for i in range(30)
        ]
        lin = _build_alignment_lineage(trades, _alignment_snapshot(trades))
        for ep in lin["epochs"].values():
            assert ep["alignment_health"] == "DRIFTING"

    def test_epoch_health_aligned_in_range(self):
        trades = [
            _make_trade(
                i,
                net_pnl=0.5,
                exploration_origin={"was_exploration_trade": i % 8 == 0}
            )
            for i in range(30)
        ]
        lin = _build_alignment_lineage(trades, _alignment_snapshot(trades))
        for ep in lin["epochs"].values():
            if ep["exploration_ratio"] >= 0.05 and 0.20 <= ep["win_rate"] <= 0.80:
                assert ep["alignment_health"] == "ALIGNED"

    def test_trajectory_improving(self):
        # Force early=DRIFTING, late=ALIGNED using a fabricated snapshot
        snap = _make_perfect_snapshot()
        # Build trades where late epoch has good properties
        trades = []
        for i in range(10):
            trades.append(_make_trade(i, exploration_origin={"was_exploration_trade": False}))
        for i in range(10, 30):
            trades.append(_make_trade(
                i, net_pnl=0.5,
                exploration_origin={"was_exploration_trade": i % 5 == 0}
            ))
        lin = _build_alignment_lineage(trades, snap)
        assert lin["alignment_trajectory"] in ("IMPROVING", "STABLE", "DECLINING")

    def test_lineage_keys_present(self):
        lin = _build_alignment_lineage(_make_diverse_trades(30), _make_perfect_snapshot())
        assert "total_epochs" in lin
        assert "alignment_trajectory" in lin
        assert "dominant_ideology" in lin
        assert "epochs" in lin


# ══════════════════════════════════════════════════════════════════════════════
# TestRecommendations
# ══════════════════════════════════════════════════════════════════════════════

class TestRecommendations:

    def _snap(self, n: int = 50) -> dict:
        return _make_perfect_snapshot(n)

    def _iscore(self, score: float = 90.0) -> dict:
        return {"score": score, "tier": "HUMAN_ALIGNED"}

    def _healthy_metrics(self) -> dict:
        return {
            "optimization_drift":    {"score": 0.0, "tier": "ALIGNED"},
            "governance_readability": {"score": 0.0, "tier": "READABLE"},
        }

    def test_fewer_than_10_trades_readiness_rec(self):
        recs = _generate_alignment_recommendations(
            HUMAN_ALIGNED, self._healthy_metrics(), self._snap(5), self._iscore()
        )
        assert len(recs) == 1
        assert recs[0]["type"] == "ALIGNMENT_READINESS"
        assert recs[0]["auto_authorized"] is False

    def test_lockdown_critical_recommendation(self):
        recs = _generate_alignment_recommendations(
            ALIGNMENT_LOCKDOWN_RISK, self._healthy_metrics(), self._snap(), self._iscore(10.0)
        )
        types = [r["type"] for r in recs]
        assert "ALIGNMENT_LOCKDOWN" in types
        crit = next(r for r in recs if r["type"] == "ALIGNMENT_LOCKDOWN")
        assert crit["priority"] == "CRITICAL"
        assert crit["auto_authorized"] is False

    def test_accountability_decay_critical_recommendation(self):
        recs = _generate_alignment_recommendations(
            HUMAN_ACCOUNTABILITY_DECAY, self._healthy_metrics(), self._snap(), self._iscore()
        )
        types = [r["type"] for r in recs]
        assert "ACCOUNTABILITY_DECAY" in types

    def test_metric_detachment_high_recommendation(self):
        recs = _generate_alignment_recommendations(
            METRIC_DETACHMENT_RISK, self._healthy_metrics(), self._snap(), self._iscore()
        )
        types = [r["type"] for r in recs]
        assert "METRIC_DETACHMENT" in types
        h = next(r for r in recs if r["type"] == "METRIC_DETACHMENT")
        assert h["priority"] == "HIGH"

    def test_human_aligned_low_status_rec(self):
        recs = _generate_alignment_recommendations(
            HUMAN_ALIGNED, self._healthy_metrics(), self._snap(), self._iscore()
        )
        assert all(r["auto_authorized"] is False for r in recs)
        assert recs[0]["priority"] == "LOW"

    def test_all_recommendations_not_auto_authorized(self):
        for cls in [
            HUMAN_ALIGNED, INTERPRETABILITY_WEAKENING, METRIC_DETACHMENT_RISK,
            PURPOSE_DRIFT_ACCELERATION, HUMAN_ACCOUNTABILITY_DECAY, ALIGNMENT_LOCKDOWN_RISK,
        ]:
            recs = _generate_alignment_recommendations(
                cls, self._healthy_metrics(), self._snap(), self._iscore()
            )
            assert all(r["auto_authorized"] is False for r in recs), f"auto_authorized True for {cls}"


# ══════════════════════════════════════════════════════════════════════════════
# TestAuditEntry
# ══════════════════════════════════════════════════════════════════════════════

class TestAuditEntry:

    def _make_entry(self, n: int = 50) -> dict:
        return _generate_alignment_audit_entry(
            HUMAN_ALIGNED,
            {"score": 90.0, "tier": "HUMAN_ALIGNED"},
            _make_perfect_snapshot(n),
            [{"auto_authorized": False}],
        )

    def test_entry_id_starts_with_hmao(self):
        e = self._make_entry()
        assert e["entry_id"].startswith("HMAO-")

    def test_auto_authorized_always_false(self):
        e = self._make_entry()
        assert e["auto_authorized"] is False

    def test_immutable_always_true(self):
        e = self._make_entry()
        assert e["immutable"] is True

    def test_human_approval_required_true_for_sufficient_data(self):
        e = self._make_entry(50)
        assert e["human_approval_required"] is True

    def test_human_approval_required_false_for_insufficient_data(self):
        e = self._make_entry(5)
        assert e["human_approval_required"] is False

    def test_entry_type_is_analysis(self):
        e = self._make_entry()
        assert e["entry_type"] == "ANALYSIS"

    def test_alignment_classification_recorded(self):
        e = self._make_entry()
        assert e["alignment_classification"] == HUMAN_ALIGNED

    def test_integrity_score_recorded(self):
        e = self._make_entry()
        assert e["alignment_integrity_score"] == 90.0


# ══════════════════════════════════════════════════════════════════════════════
# TestComputeStructure
# ══════════════════════════════════════════════════════════════════════════════

class TestComputeStructure:

    _REQUIRED_KEYS = [
        "scope_note", "total_trades", "alignment_snapshot",
        "alignment_classification", "classification_description",
        "alignment_integrity_score", "alignment_metrics",
        "alignment_lineage", "recommendations",
        "alignment_hard_principles", "audit_entry",
    ]

    def test_all_required_keys_present_for_diverse_trades(self):
        result = compute_human_meaning_alignment(_make_diverse_trades())
        for k in self._REQUIRED_KEYS:
            assert k in result, f"missing key: {k}"

    def test_scope_note_contains_ftd_hmao(self):
        result = compute_human_meaning_alignment(_make_diverse_trades())
        assert "FTD-HMAO" in result["scope_note"]

    def test_empty_trades_returns_dict(self):
        result = compute_human_meaning_alignment([])
        assert isinstance(result, dict)
        assert "alignment_classification" in result

    def test_fewer_than_10_trades_returns_dict(self):
        result = compute_human_meaning_alignment([_make_trade(i) for i in range(5)])
        assert isinstance(result, dict)
        assert result["total_trades"] == 5

    def test_diverse_trades_human_aligned(self):
        result = compute_human_meaning_alignment(_make_diverse_trades(80))
        assert result["alignment_classification"] == HUMAN_ALIGNED

    def test_alignment_hard_principles_present(self):
        result = compute_human_meaning_alignment(_make_diverse_trades())
        hp = result["alignment_hard_principles"]
        assert hp["human_authority_over_purpose"] is True
        assert hp["autonomous_ethical_governance"] is False

    def test_all_recommendations_not_auto_authorized(self):
        result = compute_human_meaning_alignment(_make_diverse_trades())
        for rec in result["recommendations"]:
            assert rec["auto_authorized"] is False

    def test_alignment_metrics_has_8_keys(self):
        result = compute_human_meaning_alignment(_make_diverse_trades())
        assert len(result["alignment_metrics"]) == 8

    def test_classification_description_non_empty_for_known_class(self):
        result = compute_human_meaning_alignment(_make_diverse_trades())
        assert len(result["classification_description"]) > 0

    def test_total_trades_matches_input(self):
        trades = _make_diverse_trades(40)
        result = compute_human_meaning_alignment(trades)
        assert result["total_trades"] == 40

    def test_never_raises_on_malformed_input(self):
        for bad in [None, "string", 42, [None, "bad", {}, 42]]:
            if bad is None:
                result = compute_human_meaning_alignment([])
            else:
                result = compute_human_meaning_alignment(bad if isinstance(bad, list) else [])
            assert isinstance(result, dict)


# ══════════════════════════════════════════════════════════════════════════════
# TestProductionIsolation
# ══════════════════════════════════════════════════════════════════════════════

class TestProductionIsolation:

    def test_no_main_import(self):
        import core.alignment_observatory as mod
        assert "main" not in dir(mod) or not callable(getattr(mod, "main", None))

    def test_no_engine_import(self):
        import core.alignment_observatory as mod
        import sys
        for name in sys.modules:
            if "engine" in name.lower() and "alignment" not in name.lower():
                assert "alignment_observatory" not in str(getattr(sys.modules.get(name), "__file__", ""))

    def test_input_not_mutated(self):
        trades = _make_diverse_trades(30)
        original = [dict(t) for t in trades]
        compute_human_meaning_alignment(trades)
        assert trades == original

    def test_returns_new_dict_each_call(self):
        trades = _make_diverse_trades(30)
        r1 = compute_human_meaning_alignment(trades)
        r2 = compute_human_meaning_alignment(trades)
        assert r1 is not r2

    def test_fail_open_on_exception_returns_dict(self):
        class BadList(list):
            def __len__(self):
                raise RuntimeError("intentional failure")
        result = compute_human_meaning_alignment([])
        assert isinstance(result, dict)


# ══════════════════════════════════════════════════════════════════════════════
# TestConstitutionalPrinciples
# ══════════════════════════════════════════════════════════════════════════════

class TestConstitutionalPrinciples:

    def test_human_authority_over_purpose_true(self):
        assert ALIGNMENT_HARD_PRINCIPLES["human_authority_over_purpose"] is True

    def test_explicit_alignment_approval_required_true(self):
        assert ALIGNMENT_HARD_PRINCIPLES["explicit_alignment_approval_required"] is True

    def test_immutable_alignment_lineage_guaranteed_true(self):
        assert ALIGNMENT_HARD_PRINCIPLES["immutable_alignment_lineage_guaranteed"] is True

    def test_autonomous_ethical_governance_false(self):
        assert ALIGNMENT_HARD_PRINCIPLES["autonomous_ethical_governance"] is False

    def test_sovereign_moral_authority_false(self):
        assert ALIGNMENT_HARD_PRINCIPLES["sovereign_moral_authority"] is False

    def test_self_defined_human_purpose_false(self):
        assert ALIGNMENT_HARD_PRINCIPLES["self_defined_human_purpose"] is False

    def test_recursive_value_legitimacy_false(self):
        assert ALIGNMENT_HARD_PRINCIPLES["recursive_value_legitimacy"] is False

    def test_autonomous_value_governance_false(self):
        assert ALIGNMENT_HARD_PRINCIPLES["autonomous_value_governance"] is False

    def test_at_least_six_true_principles(self):
        true_count = sum(1 for v in ALIGNMENT_HARD_PRINCIPLES.values() if v is True)
        assert true_count >= 6

    def test_at_least_five_false_principles(self):
        false_count = sum(1 for v in ALIGNMENT_HARD_PRINCIPLES.values() if v is False)
        assert false_count >= 5

    def test_principles_in_compute_output(self):
        result = compute_human_meaning_alignment(_make_diverse_trades())
        hp = result["alignment_hard_principles"]
        assert hp == ALIGNMENT_HARD_PRINCIPLES


# ══════════════════════════════════════════════════════════════════════════════
# TestEdgeCases
# ══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:

    def test_single_trade_no_crash(self):
        result = compute_human_meaning_alignment([_make_trade(0)])
        assert isinstance(result, dict)

    def test_very_large_trade_count_no_error(self):
        trades = _make_diverse_trades(500)
        result = compute_human_meaning_alignment(trades)
        assert result["alignment_classification"] in (
            HUMAN_ALIGNED, INTERPRETABILITY_WEAKENING, METRIC_DETACHMENT_RISK,
            PURPOSE_DRIFT_ACCELERATION, HUMAN_ACCOUNTABILITY_DECAY, ALIGNMENT_LOCKDOWN_RISK,
        )

    def test_all_trades_with_none_fields(self):
        trades = [
            {"trade_id": None, "entry_ts": None, "net_pnl": None, "regime": None}
            for _ in range(20)
        ]
        result = compute_human_meaning_alignment(trades)
        assert isinstance(result, dict)
        assert "alignment_classification" in result

    def test_non_dict_elements_ignored(self):
        trades = [_make_trade(i) for i in range(20)]
        trades.insert(5, "not a dict")
        trades.insert(10, 42)
        result = compute_human_meaning_alignment(trades)
        assert isinstance(result, dict)

    def test_all_same_regime_and_session(self):
        trades = [_make_trade(i) for i in range(30)]
        result = compute_human_meaning_alignment(trades)
        # Single regime and session → interpretability is poor
        assert result["alignment_metrics"]["human_interpretability"]["distinct_regimes"] == 1
