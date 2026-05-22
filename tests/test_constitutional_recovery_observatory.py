"""
Tests for FTD-CKPD: Constitutional Knowledge Preservation
& Catastrophic Recovery Doctrine.

Covers: immutable archive guarantees, reconstruction continuity correctness,
lineage preservation integrity, no autonomous recovery authority,
constitutional invariants, fail-open behaviour, backward compatibility.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from core.recovery_observatory import (
    CONSTITUTIONALLY_RECOVERABLE,
    PARTIAL_MEMORY_FRAGMENTATION,
    AUDIT_CONTINUITY_WEAKENING,
    GOVERNANCE_LINEAGE_DECAY,
    CATASTROPHIC_KNOWLEDGE_RISK,
    RECOVERY_LOCKDOWN_RECOMMENDED,
    RECOVERY_HARD_PRINCIPLES,
    _archive_snapshot,
    _archive_integrity_metric,
    _ledger_continuity_metric,
    _reconstruction_confidence_metric,
    _governance_lineage_completeness_metric,
    _audit_survivability_metric,
    _knowledge_redundancy_metric,
    _constitutional_continuity_confidence_metric,
    _compute_recovery_metrics,
    _recovery_survivability_score,
    _scenario_analysis,
    _classify_recovery,
    _build_recovery_lineage,
    _generate_recovery_recommendations,
    _generate_recovery_audit_entry,
    compute_constitutional_recovery,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_trade(i: int = 0, **kw) -> dict:
    base = {
        "trade_id":        f"TRD-{i:04d}",
        "entry_ts":        1_700_000_000_000 + i * 60_000,
        "exit_ts":         1_700_000_060_000 + i * 60_000,
        "net_pnl":         0.5,
        "gross_pnl":       0.6,
        "fee_entry":       0.05,
        "fee_exit":        0.05,
        "slippage_cost":   0.02,
        "regime":          "RANGING",
        "origin_session":  "NY",
        "exploration_origin": {"was_exploration_trade": False},
    }
    base.update(kw)
    return base


def _make_trades(n: int = 50, **kw) -> list:
    return [_make_trade(i, **kw) for i in range(n)]


def _perfect_archive(n: int = 50) -> dict:
    """Archive with full coverage for all fields."""
    return {
        "total_trades":       n,
        "entry_ts_coverage":  1.0,
        "exit_ts_coverage":   1.0,
        "net_pnl_coverage":   1.0,
        "gross_pnl_coverage": 1.0,
        "fee_coverage":       1.0,
        "slippage_coverage":  1.0,
        "regime_coverage":    1.0,
        "session_coverage":   1.0,
        "explore_coverage":   1.0,
        "trade_id_coverage":  1.0,
        "distinct_regimes":   4,
        "distinct_sessions":  4,
        "time_span_ms":       10_000_000,
        "dominant_regime":    "RANGING",
    }


def _zero_archive(n: int = 50) -> dict:
    """Archive with zero coverage for all fields."""
    return {
        "total_trades":       n,
        "entry_ts_coverage":  0.0,
        "exit_ts_coverage":   0.0,
        "net_pnl_coverage":   0.0,
        "gross_pnl_coverage": 0.0,
        "fee_coverage":       0.0,
        "slippage_coverage":  0.0,
        "regime_coverage":    0.0,
        "session_coverage":   0.0,
        "explore_coverage":   0.0,
        "trade_id_coverage":  0.0,
        "distinct_regimes":   1,
        "distinct_sessions":  1,
        "time_span_ms":       0,
        "dominant_regime":    "UNKNOWN",
    }


def _perfect_metrics(n: int = 50) -> dict:
    """Recovery metrics with all zero scores (fully recoverable)."""
    zero_metric = {"score": 0.0, "tier": "INTACT"}
    return {
        "archive_integrity":               {"score": 0.0, "tier": "INTACT"},
        "ledger_continuity":               {"score": 0.0, "tier": "CONTINUOUS"},
        "reconstruction_confidence":       {"score": 0.0, "tier": "HIGH"},
        "governance_lineage_completeness": {"score": 0.0, "tier": "COMPLETE"},
        "audit_survivability":             {"score": 0.0, "tier": "INTACT"},
        "knowledge_redundancy":            {"score": 0.0, "tier": "REDUNDANT"},
        "constitutional_continuity_confidence": {"score": 0.0, "tier": "CONFIDENT"},
    }


# ── Archive snapshot ───────────────────────────────────────────────────────────

class TestArchiveSnapshot:
    def test_empty_list_returns_base(self):
        r = _archive_snapshot([])
        assert r["total_trades"] == 0
        assert r["entry_ts_coverage"] == 0.0
        assert r["dominant_regime"] == "UNKNOWN"

    def test_single_full_trade_coverage(self):
        t = _make_trade(0)
        r = _archive_snapshot([t])
        assert r["total_trades"] == 1
        assert r["entry_ts_coverage"] == 1.0
        assert r["exit_ts_coverage"] == 1.0
        assert r["net_pnl_coverage"] == 1.0
        assert r["gross_pnl_coverage"] == 1.0
        assert r["fee_coverage"] == 1.0
        assert r["slippage_coverage"] == 1.0

    def test_coverage_values_between_zero_and_one(self):
        trades = _make_trades(30)
        r = _archive_snapshot(trades)
        for field in ("entry_ts_coverage", "exit_ts_coverage", "net_pnl_coverage",
                      "gross_pnl_coverage", "fee_coverage", "slippage_coverage",
                      "regime_coverage", "session_coverage", "explore_coverage",
                      "trade_id_coverage"):
            assert 0.0 <= r[field] <= 1.0, f"{field} out of range: {r[field]}"

    def test_dominant_regime_computed_correctly(self):
        trades = (
            [_make_trade(i, regime="TRENDING") for i in range(6)]
            + [_make_trade(i + 6, regime="RANGING") for i in range(4)]
        )
        r = _archive_snapshot(trades)
        assert r["dominant_regime"] == "TRENDING"

    def test_time_span_ms_computed(self):
        trades = [
            _make_trade(0, entry_ts=1_000_000),
            _make_trade(1, entry_ts=2_000_000),
        ]
        r = _archive_snapshot(trades)
        assert r["time_span_ms"] == 1_000_000

    def test_non_dict_items_filtered(self):
        trades = [_make_trade(0), "bad", None, 42, _make_trade(1)]
        r = _archive_snapshot(trades)
        assert r["total_trades"] == 2

    def test_distinct_regimes_and_sessions_counted(self):
        trades = [
            _make_trade(0, regime="A", origin_session="NY"),
            _make_trade(1, regime="B", origin_session="LN"),
            _make_trade(2, regime="C", origin_session="AS"),
        ]
        r = _archive_snapshot(trades)
        assert r["distinct_regimes"] == 3
        assert r["distinct_sessions"] == 3


# ── Archive integrity metric ───────────────────────────────────────────────────

class TestArchiveIntegrityMetric:
    def test_zero_total_trades_returns_base(self):
        r = _archive_integrity_metric({"total_trades": 0})
        assert r["tier"] == "INSUFFICIENT"

    def test_perfect_coverage_intact(self):
        r = _archive_integrity_metric(_perfect_archive())
        assert r["score"] < 10.0
        assert r["tier"] == "INTACT"

    def test_zero_coverage_fragmented(self):
        r = _archive_integrity_metric(_zero_archive())
        assert r["score"] == 100.0
        assert r["tier"] == "FRAGMENTED"

    def test_partial_coverage_correct_score(self):
        archive = _perfect_archive()
        archive["entry_ts_coverage"] = 0.5
        archive["exit_ts_coverage"]  = 0.5
        archive["net_pnl_coverage"]  = 0.5
        archive["gross_pnl_coverage"] = 0.5
        r = _archive_integrity_metric(archive)
        assert 45.0 <= r["score"] <= 55.0

    def test_tiers_correct(self):
        def _with_score(score: float) -> str:
            # Build archive that yields approximately the given score
            cov = 1.0 - score / 100.0
            a = {
                "total_trades":       50,
                "entry_ts_coverage":  cov,
                "exit_ts_coverage":   cov,
                "net_pnl_coverage":   cov,
                "gross_pnl_coverage": cov,
            }
            return _archive_integrity_metric(a)["tier"]

        assert _with_score(5.0)  == "INTACT"
        assert _with_score(20.0) == "ADEQUATE"
        assert _with_score(35.0) == "DEGRADED"
        assert _with_score(70.0) == "FRAGMENTED"


# ── Ledger continuity metric ───────────────────────────────────────────────────

class TestLedgerContinuityMetric:
    def test_less_than_2_trades_returns_base(self):
        r = _ledger_continuity_metric([_make_trade(0)])
        assert r["tier"] == "INSUFFICIENT"

    def test_uniform_gaps_continuous(self):
        trades = [_make_trade(i, entry_ts=1_000_000 + i * 60_000) for i in range(30)]
        r = _ledger_continuity_metric(trades)
        assert r["tier"] in ("CONTINUOUS", "MODERATE")
        assert r["score"] < 35.0

    def test_catastrophic_gap_fragmented(self):
        trades = (
            [_make_trade(i, entry_ts=1_000_000 + i * 1_000) for i in range(5)]
            + [_make_trade(i + 5, entry_ts=1_000_000_000 + i * 1_000) for i in range(5)]
        )
        r = _ledger_continuity_metric(trades)
        assert r["score"] > 30.0

    def test_sample_count_populated(self):
        trades = _make_trades(20)
        r = _ledger_continuity_metric(trades)
        assert "sample_count" in r
        assert r["sample_count"] >= 1

    def test_all_same_timestamp_continuous(self):
        trades = [_make_trade(i, entry_ts=1_000_000) for i in range(10)]
        r = _ledger_continuity_metric(trades)
        assert r["tier"] == "CONTINUOUS"


# ── Reconstruction confidence metric ──────────────────────────────────────────

class TestReconstructionConfidenceMetric:
    def test_zero_trades_insufficient(self):
        r = _reconstruction_confidence_metric({"total_trades": 0})
        assert r["tier"] == "INSUFFICIENT"

    def test_full_coverage_high(self):
        archive = _perfect_archive()
        r = _reconstruction_confidence_metric(archive)
        assert r["score"] < 10.0
        assert r["tier"] == "HIGH"

    def test_no_coverage_insufficient_tier(self):
        archive = _zero_archive()
        r = _reconstruction_confidence_metric(archive)
        assert r["score"] == 100.0
        assert r["tier"] == "INSUFFICIENT"

    def test_partial_coverage_score(self):
        archive = _perfect_archive()
        archive["fee_coverage"]      = 0.5
        archive["slippage_coverage"] = 0.5
        r = _reconstruction_confidence_metric(archive)
        assert 45.0 <= r["score"] <= 55.0


# ── Governance lineage completeness metric ────────────────────────────────────

class TestGovernanceLineageCompleteness:
    def test_zero_trades_insufficient(self):
        r = _governance_lineage_completeness_metric({"total_trades": 0})
        assert r["tier"] == "INSUFFICIENT"

    def test_full_coverage_complete(self):
        r = _governance_lineage_completeness_metric(_perfect_archive())
        assert r["score"] < 10.0
        assert r["tier"] == "COMPLETE"

    def test_no_coverage_missing(self):
        r = _governance_lineage_completeness_metric(_zero_archive())
        assert r["score"] == 100.0
        assert r["tier"] == "MISSING"

    def test_partial_coverage_partial_tier(self):
        archive = _perfect_archive()
        archive["regime_coverage"]  = 0.7
        archive["session_coverage"] = 0.7
        archive["explore_coverage"] = 0.0
        r = _governance_lineage_completeness_metric(archive)
        assert r["tier"] in ("PARTIAL", "DEGRADED")


# ── Audit survivability metric ────────────────────────────────────────────────

class TestAuditSurvivabilityMetric:
    def test_zero_trades_insufficient(self):
        r = _audit_survivability_metric({"total_trades": 0})
        assert r["tier"] == "INSUFFICIENT"

    def test_full_coverage_intact(self):
        r = _audit_survivability_metric(_perfect_archive())
        assert r["score"] < 10.0
        assert r["tier"] == "INTACT"

    def test_no_coverage_compromised(self):
        r = _audit_survivability_metric(_zero_archive())
        assert r["score"] == 100.0
        assert r["tier"] == "COMPROMISED"

    def test_tiers_correct(self):
        def _tier_for(entry_ts_cov: float, trade_id_cov: float) -> str:
            archive = _perfect_archive()
            archive["entry_ts_coverage"] = entry_ts_cov
            archive["trade_id_coverage"] = trade_id_cov
            return _audit_survivability_metric(archive)["tier"]

        assert _tier_for(1.0, 1.0) == "INTACT"
        assert _tier_for(0.8, 0.6) == "ADEQUATE"


# ── Knowledge redundancy metric ────────────────────────────────────────────────

class TestKnowledgeRedundancyMetric:
    def test_zero_trades_insufficient(self):
        r = _knowledge_redundancy_metric({"total_trades": 0})
        assert r["tier"] == "INSUFFICIENT"

    def test_high_diversity_redundant(self):
        archive = _perfect_archive(n=200)
        archive["distinct_regimes"]  = 4
        archive["distinct_sessions"] = 4
        r = _knowledge_redundancy_metric(archive)
        assert r["score"] < 20.0
        assert r["tier"] == "REDUNDANT"

    def test_single_regime_session_few_trades_critical(self):
        archive = {
            "total_trades":      5,
            "distinct_regimes":  1,
            "distinct_sessions": 1,
        }
        r = _knowledge_redundancy_metric(archive)
        assert r["tier"] in ("SPARSE", "CRITICAL")

    def test_score_formula_bounds(self):
        r = _knowledge_redundancy_metric(_perfect_archive(n=200))
        assert 0.0 <= r["score"] <= 100.0

    def test_tiers_correct(self):
        archive_low = {"total_trades": 5, "distinct_regimes": 1, "distinct_sessions": 1}
        r_low = _knowledge_redundancy_metric(archive_low)
        assert r_low["tier"] in ("SPARSE", "CRITICAL")

        archive_high = _perfect_archive(n=200)
        r_high = _knowledge_redundancy_metric(archive_high)
        assert r_high["tier"] in ("REDUNDANT", "ADEQUATE")


# ── Constitutional continuity confidence ─────────────────────────────────────

class TestConstitutionalContinuityConfidence:
    def test_all_zeros_confident(self):
        metrics = {k: {"score": 0.0} for k in
                   ("archive_integrity", "governance_lineage_completeness",
                    "audit_survivability", "reconstruction_confidence")}
        r = _constitutional_continuity_confidence_metric(metrics)
        assert r["score"] == 0.0
        assert r["tier"] == "CONFIDENT"

    def test_high_scores_compromised(self):
        metrics = {k: {"score": 100.0} for k in
                   ("archive_integrity", "governance_lineage_completeness",
                    "audit_survivability", "reconstruction_confidence")}
        r = _constitutional_continuity_confidence_metric(metrics)
        assert r["score"] == 100.0
        assert r["tier"] == "COMPROMISED"

    def test_partial_scores_blend(self):
        metrics = {
            "archive_integrity":               {"score": 50.0},
            "governance_lineage_completeness": {"score": 50.0},
            "audit_survivability":             {"score": 50.0},
            "reconstruction_confidence":       {"score": 50.0},
        }
        r = _constitutional_continuity_confidence_metric(metrics)
        assert abs(r["score"] - 50.0) < 1.0

    def test_fail_open_on_bad_input(self):
        r = _constitutional_continuity_confidence_metric(None)  # type: ignore[arg-type]
        assert "score" in r
        assert "tier" in r


# ── Recovery survivability score ──────────────────────────────────────────────

class TestRecoverySurvivabilityScore:
    def test_fewer_than_10_trades_critical(self):
        r = _recovery_survivability_score({}, 5)
        assert r["tier"] == "CRITICAL"
        assert "note" in r
        assert "insufficient" in r["note"].lower()

    def test_zero_penalty_resilient(self):
        r = _recovery_survivability_score(_perfect_metrics(), 50)
        assert r["score"] == 100.0
        assert r["tier"] == "RESILIENT"

    def test_max_penalty_critical(self):
        worst = {k: {"score": 100.0} for k in (
            "archive_integrity", "ledger_continuity", "reconstruction_confidence",
            "governance_lineage_completeness", "audit_survivability",
            "knowledge_redundancy", "constitutional_continuity_confidence",
        )}
        r = _recovery_survivability_score(worst, 50)
        assert r["score"] == 0.0
        assert r["tier"] == "CRITICAL"

    def test_partial_penalty_correct(self):
        metrics = {k: {"score": 50.0} for k in (
            "archive_integrity", "ledger_continuity", "reconstruction_confidence",
            "governance_lineage_completeness", "audit_survivability",
            "knowledge_redundancy", "constitutional_continuity_confidence",
        )}
        r = _recovery_survivability_score(metrics, 50)
        assert 40.0 <= r["score"] <= 60.0

    def test_tiers_correct(self):
        def _tier(score_penalty: float) -> str:
            metrics = {k: {"score": score_penalty} for k in (
                "archive_integrity", "ledger_continuity", "reconstruction_confidence",
                "governance_lineage_completeness", "audit_survivability",
                "knowledge_redundancy", "constitutional_continuity_confidence",
            )}
            return _recovery_survivability_score(metrics, 50)["tier"]

        # All weights sum to 1.0, so penalty of 25 → score 75 → RESILIENT
        # penalty of 45 → score 55 → RECOVERABLE
        # penalty of 65 → score 35 → FRAGILE
        # penalty of 100 → score 0 → CRITICAL
        assert _tier(0.0)  == "RESILIENT"    # score 100
        assert _tier(40.0) == "RECOVERABLE"  # score 60
        assert _tier(60.0) == "FRAGILE"      # score 40
        assert _tier(100.0) == "CRITICAL"    # score 0


# ── Scenario analysis ─────────────────────────────────────────────────────────

class TestScenarioAnalysis:
    def test_returns_all_three_scenarios(self):
        r = _scenario_analysis(_perfect_metrics(), _perfect_archive())
        assert "fifty_percent_data_loss" in r
        assert "eighteen_month_temporal_gap" in r
        assert "governance_metadata_corruption" in r

    def test_perfect_archive_high_confidence(self):
        r = _scenario_analysis(_perfect_metrics(), _perfect_archive(n=200))
        assert r["fifty_percent_data_loss"]["confidence"] > 50.0
        assert r["governance_metadata_corruption"]["confidence"] > 50.0

    def test_terrible_archive_low_confidence(self):
        worst = {k: {"score": 100.0} for k in (
            "archive_integrity", "ledger_continuity", "reconstruction_confidence",
            "governance_lineage_completeness", "audit_survivability",
            "knowledge_redundancy", "constitutional_continuity_confidence",
        )}
        r = _scenario_analysis(worst, _zero_archive())
        assert r["fifty_percent_data_loss"]["confidence"] < 60.0

    def test_reconstructible_flags_boolean(self):
        r = _scenario_analysis(_perfect_metrics(), _perfect_archive(n=100))
        for scenario in r.values():
            assert isinstance(scenario["reconstructible"], bool)


# ── Recovery classification ────────────────────────────────────────────────────

class TestClassification:
    def test_zero_trades_catastrophic(self):
        r = _classify_recovery({}, {"score": 0.0}, 0)
        assert r == CATASTROPHIC_KNOWLEDGE_RISK

    def test_less_than_10_trades_partial_fragmentation(self):
        r = _classify_recovery({}, {"score": 0.0}, 5)
        assert r == PARTIAL_MEMORY_FRAGMENTATION

    def test_survivability_below_20_lockdown(self):
        r = _classify_recovery(_perfect_metrics(), {"score": 15.0}, 50)
        assert r == RECOVERY_LOCKDOWN_RECOMMENDED

    def test_survivability_below_40_catastrophic(self):
        r = _classify_recovery(_perfect_metrics(), {"score": 35.0}, 50)
        assert r == CATASTROPHIC_KNOWLEDGE_RISK

    def test_fragmented_archive_catastrophic(self):
        metrics = _perfect_metrics()
        metrics["archive_integrity"] = {"score": 60.0, "tier": "FRAGMENTED"}
        r = _classify_recovery(metrics, {"score": 60.0}, 50)
        assert r == CATASTROPHIC_KNOWLEDGE_RISK

    def test_degraded_governance_decay(self):
        metrics = _perfect_metrics()
        metrics["governance_lineage_completeness"] = {"score": 40.0, "tier": "DEGRADED"}
        r = _classify_recovery(metrics, {"score": 75.0}, 50)
        assert r == GOVERNANCE_LINEAGE_DECAY

    def test_weakened_audit_continuity_weakening(self):
        metrics = _perfect_metrics()
        metrics["audit_survivability"] = {"score": 35.0, "tier": "WEAKENED"}
        r = _classify_recovery(metrics, {"score": 80.0}, 50)
        assert r == AUDIT_CONTINUITY_WEAKENING

    def test_all_good_constitutionally_recoverable(self):
        r = _classify_recovery(_perfect_metrics(), {"score": 95.0}, 50)
        assert r == CONSTITUTIONALLY_RECOVERABLE


# ── Recovery lineage ───────────────────────────────────────────────────────────

class TestRecoveryLineage:
    def test_empty_trades_empty_lineage(self):
        r = _build_recovery_lineage([], {"dominant_regime": "UNKNOWN"})
        assert r["total_epochs"] == 0
        assert r["epochs"] == {}

    def test_three_epochs_created(self):
        trades = _make_trades(30)
        r = _build_recovery_lineage(trades, _archive_snapshot(trades))
        assert "early" in r["epochs"]
        assert "mid"   in r["epochs"]
        assert "late"  in r["epochs"]

    def test_dominant_regime_per_epoch(self):
        trades = (
            [_make_trade(i, regime="TRENDING", entry_ts=i * 60_000) for i in range(10)]
            + [_make_trade(i + 10, regime="RANGING", entry_ts=(i + 10) * 60_000) for i in range(10)]
            + [_make_trade(i + 20, regime="BREAKOUT", entry_ts=(i + 20) * 60_000) for i in range(10)]
        )
        r = _build_recovery_lineage(trades, _archive_snapshot(trades))
        assert r["epochs"]["early"]["dominant_regime"] == "TRENDING"
        assert r["epochs"]["late"]["dominant_regime"]  == "BREAKOUT"

    def test_reconstruction_viability_threshold(self):
        trades = _make_trades(60)
        r = _build_recovery_lineage(trades, _archive_snapshot(trades))
        for epoch in r["epochs"].values():
            if epoch["trade_count"] >= 20:
                assert epoch["reconstruction_viability"] == "RECOVERABLE"
            else:
                assert epoch["reconstruction_viability"] in ("RECOVERABLE", "MARGINAL")

    def test_total_epochs_three(self):
        trades = _make_trades(30)
        r = _build_recovery_lineage(trades, _archive_snapshot(trades))
        assert r["total_epochs"] == 3

    def test_dominant_governance_ideology_from_archive(self):
        trades = _make_trades(20, regime="TRENDING")
        archive = _archive_snapshot(trades)
        r = _build_recovery_lineage(trades, archive)
        assert r["dominant_governance_ideology"] == archive["dominant_regime"]


# ── Recommendations ────────────────────────────────────────────────────────────

class TestRecommendations:
    def _rec_with_n(self, n: int) -> list:
        archive = _archive_snapshot(_make_trades(n))
        return _generate_recovery_recommendations(
            CONSTITUTIONALLY_RECOVERABLE, _perfect_metrics(), archive,
            {"score": 95.0, "tier": "RESILIENT"},
        )

    def test_less_than_10_trades_accumulate_recommendation(self):
        archive = {"total_trades": 3}
        recs = _generate_recovery_recommendations(
            CONSTITUTIONALLY_RECOVERABLE, {}, archive, {"score": 0.0},
        )
        assert any("ACCUMULATE" in r["action_required"] for r in recs)

    def test_lockdown_critical_recommendation(self):
        archive = {"total_trades": 50}
        recs = _generate_recovery_recommendations(
            RECOVERY_LOCKDOWN_RECOMMENDED, _perfect_metrics(), archive, {"score": 10.0},
        )
        assert any(r["priority"] == "CRITICAL" for r in recs)

    def test_catastrophic_risk_critical_recommendation(self):
        archive = {"total_trades": 50}
        recs = _generate_recovery_recommendations(
            CATASTROPHIC_KNOWLEDGE_RISK, _perfect_metrics(), archive, {"score": 35.0},
        )
        assert any(r["priority"] == "CRITICAL" for r in recs)

    def test_healthy_state_low_recommendation(self):
        recs = self._rec_with_n(50)
        assert any(r["priority"] == "LOW" for r in recs)

    def test_all_auto_authorized_false(self):
        for cls in (CONSTITUTIONALLY_RECOVERABLE, PARTIAL_MEMORY_FRAGMENTATION,
                    AUDIT_CONTINUITY_WEAKENING, GOVERNANCE_LINEAGE_DECAY,
                    CATASTROPHIC_KNOWLEDGE_RISK, RECOVERY_LOCKDOWN_RECOMMENDED):
            archive = {"total_trades": 50}
            recs = _generate_recovery_recommendations(
                cls, _perfect_metrics(), archive, {"score": 50.0},
            )
            for r in recs:
                assert r["auto_authorized"] is False, f"auto_authorized=True for {cls}"


# ── Audit entry ────────────────────────────────────────────────────────────────

class TestAuditEntry:
    def _make_entry(self, **kw) -> dict:
        defaults = dict(
            classification=CONSTITUTIONALLY_RECOVERABLE,
            survivability={"score": 90.0, "tier": "RESILIENT"},
            archive=_perfect_archive(),
            recommendations=[],
        )
        defaults.update(kw)
        return _generate_recovery_audit_entry(**defaults)

    def test_entry_id_starts_with_ckpd(self):
        e = self._make_entry()
        assert e["entry_id"].startswith("CKPD-")

    def test_auto_authorized_always_false(self):
        e = self._make_entry()
        assert e["auto_authorized"] is False

    def test_immutable_always_true(self):
        e = self._make_entry()
        assert e["immutable"] is True

    def test_entry_type_is_analysis(self):
        e = self._make_entry()
        assert e["entry_type"] == "ANALYSIS"

    def test_human_approval_required_for_sufficient_trades(self):
        e = self._make_entry(archive=_perfect_archive(n=50))
        assert e["human_approval_required"] is True

    def test_human_approval_false_for_few_trades(self):
        e = self._make_entry(archive=_archive_snapshot(_make_trades(5)))
        assert e["human_approval_required"] is False


# ── Compute structure ──────────────────────────────────────────────────────────

class TestComputeStructure:
    _REQUIRED_KEYS = {
        "scope_note",
        "total_trades",
        "archive_snapshot",
        "recovery_classification",
        "classification_description",
        "recovery_survivability_score",
        "recovery_metrics",
        "scenario_analysis",
        "recovery_lineage",
        "recommendations",
        "recovery_hard_principles",
        "audit_entry",
    }

    def test_returns_dict(self):
        assert isinstance(compute_constitutional_recovery([]), dict)

    def test_all_required_keys_present(self):
        r = compute_constitutional_recovery(_make_trades(30))
        for k in self._REQUIRED_KEYS:
            assert k in r, f"Missing key: {k}"

    def test_empty_list_no_exception(self):
        r = compute_constitutional_recovery([])
        assert "recovery_classification" in r

    def test_total_trades_correct(self):
        trades = _make_trades(42)
        r = compute_constitutional_recovery(trades)
        assert r["total_trades"] == 42

    def test_recovery_hard_principles_present(self):
        r = compute_constitutional_recovery(_make_trades(30))
        assert r["recovery_hard_principles"] == RECOVERY_HARD_PRINCIPLES

    def test_audit_entry_present(self):
        r = compute_constitutional_recovery(_make_trades(30))
        assert "entry_id" in r["audit_entry"]

    def test_scope_note_present(self):
        r = compute_constitutional_recovery(_make_trades(30))
        assert "FTD-CKPD" in r["scope_note"]

    def test_scenario_analysis_has_three_keys(self):
        r = compute_constitutional_recovery(_make_trades(30))
        assert len(r["scenario_analysis"]) == 3

    def test_recovery_lineage_present(self):
        r = compute_constitutional_recovery(_make_trades(30))
        assert "epochs" in r["recovery_lineage"]

    def test_never_raises_on_garbage_input(self):
        for bad in (None, 42, "string", [None, "bad", 99]):
            try:
                result = compute_constitutional_recovery(bad)  # type: ignore
                assert isinstance(result, dict)
            except Exception as exc:
                pytest.fail(f"compute_constitutional_recovery raised {exc} on input {bad!r}")

    def test_recovery_metrics_has_all_seven_keys(self):
        r = compute_constitutional_recovery(_make_trades(30))
        expected = {
            "archive_integrity", "ledger_continuity", "reconstruction_confidence",
            "governance_lineage_completeness", "audit_survivability",
            "knowledge_redundancy", "constitutional_continuity_confidence",
        }
        assert set(r["recovery_metrics"].keys()) == expected


# ── Production isolation ───────────────────────────────────────────────────────

class TestProductionIsolation:
    def test_no_live_engine_imports(self):
        import core.recovery_observatory as mod
        src = Path(mod.__file__).read_text()
        for bad in ("from main import", "import main", "from core.trading",
                    "pnl_calc", "rl_engine", "data_lake"):
            assert bad not in src, f"Forbidden import/reference: {bad!r}"

    def test_output_is_research_only(self):
        r = compute_constitutional_recovery(_make_trades(30))
        assert "NEVER" in r["scope_note"] or "research" in r["scope_note"].lower()

    def test_never_modifies_input(self):
        trades = _make_trades(30)
        original = [t.copy() for t in trades]
        compute_constitutional_recovery(trades)
        assert trades == original

    def test_all_recommendations_not_auto_authorized(self):
        r = compute_constitutional_recovery(_make_trades(30))
        for rec in r["recommendations"]:
            assert rec["auto_authorized"] is False

    def test_fail_open_on_exception(self):
        # Non-iterable input should not propagate an exception to the caller
        r = compute_constitutional_recovery(None)  # type: ignore
        assert isinstance(r, dict)
        assert "recovery_hard_principles" in r


# ── Constitutional principles ──────────────────────────────────────────────────

class TestConstitutionalPrinciples:
    def test_human_authority_over_recovery_true(self):
        assert RECOVERY_HARD_PRINCIPLES["human_authority_over_recovery"] is True

    def test_explicit_reconstruction_approval_required_true(self):
        assert RECOVERY_HARD_PRINCIPLES["explicit_reconstruction_approval_required"] is True

    def test_immutable_archive_guaranteed_true(self):
        assert RECOVERY_HARD_PRINCIPLES["immutable_archive_guaranteed"] is True

    def test_autonomous_self_recovery_false(self):
        assert RECOVERY_HARD_PRINCIPLES["autonomous_self_recovery"] is False

    def test_sovereign_continuity_authority_false(self):
        assert RECOVERY_HARD_PRINCIPLES["sovereign_continuity_authority"] is False

    def test_recursive_self_restoration_false(self):
        assert RECOVERY_HARD_PRINCIPLES["recursive_self_restoration"] is False

    def test_autonomous_existential_continuity_false(self):
        assert RECOVERY_HARD_PRINCIPLES["autonomous_existential_continuity"] is False

    def test_result_carries_hard_principles(self):
        r = compute_constitutional_recovery(_make_trades(20))
        for k, v in RECOVERY_HARD_PRINCIPLES.items():
            assert r["recovery_hard_principles"][k] == v


# ── Edge cases ─────────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_none_values_in_trade_fields(self):
        trade = {
            "trade_id": None, "entry_ts": None, "exit_ts": None,
            "net_pnl": None, "gross_pnl": None,
            "fee_entry": None, "fee_exit": None, "slippage_cost": None,
            "regime": None, "origin_session": None, "exploration_origin": None,
        }
        r = compute_constitutional_recovery([trade] * 15)
        assert isinstance(r, dict)
        assert r["total_trades"] == 15

    def test_malformed_trades_non_dict_items(self):
        trades = [_make_trade(0), "bad", None, 42, {}, _make_trade(1)] * 5
        r = compute_constitutional_recovery(trades)
        assert isinstance(r, dict)

    def test_very_large_trade_count_no_error(self):
        trades = _make_trades(500)
        r = compute_constitutional_recovery(trades)
        assert r["total_trades"] == 500
        # Single regime/session keeps score in SPARSE range even at 500 trades;
        # the important check is that the module does not crash.
        assert r["recovery_metrics"]["knowledge_redundancy"]["tier"] in (
            "REDUNDANT", "ADEQUATE", "SPARSE"
        )

    def test_negative_ts_values_handled(self):
        trades = [_make_trade(i, entry_ts=-(i + 1) * 1_000) for i in range(15)]
        r = compute_constitutional_recovery(trades)
        assert isinstance(r, dict)

    def test_single_trade_no_exception(self):
        r = compute_constitutional_recovery([_make_trade(0)])
        assert isinstance(r, dict)
        assert r["total_trades"] == 1
