"""
Tests for FTD-EIOD: Constitutional Scientific Method Doctrine
& Epistemic Integrity Observatory.

Covers: no sovereign truth authority, contradiction survivability correctness,
falsification metric correctness, immutable epistemic lineage guarantees,
constitutional invariants, fail-open behaviour, backward compatibility.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from core.epistemic_observatory import (
    SCIENTIFICALLY_HEALTHY,
    EVIDENCE_INSUFFICIENCY,
    IDEOLOGICAL_SELF_CONFIRMATION,
    CONTRADICTION_SUPPRESSION,
    FALSIFICATION_FAILURE,
    EPISTEMIC_LOCKDOWN_RISK,
    EPISTEMIC_HARD_PRINCIPLES,
    _evidence_sufficiency_metric,
    _replay_statistical_confidence_metric,
    _governance_evidence_depth_metric,
    _contradiction_tolerance_metric,
    _minority_hypothesis_survivability_metric,
    _falsification_rate_metric,
    _consensus_rigidity_metric,
    _epistemic_plasticity_metric,
    _compute_epistemic_metrics,
    _epistemic_integrity_score,
    _classify_epistemic,
    _build_epistemic_lineage,
    _generate_epistemic_recommendations,
    _generate_epistemic_audit_entry,
    compute_epistemic_integrity,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_trade(i: int = 0, **kw) -> dict:
    base = {
        "trade_id":        f"TRD-{i:04d}",
        "entry_ts":        1_700_000_000_000 + i * 60_000,
        "exit_ts":         1_700_000_060_000 + i * 60_000,
        "net_pnl":         0.5 if i % 2 == 0 else -0.5,
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
    """Single-regime, single-session, no exploration trades."""
    return [_make_trade(i, **kw) for i in range(n)]


def _make_diverse_trades(n: int = 80) -> list:
    """
    4 regimes, 4 sessions, 10% exploration.
    Per-regime win rates: TRENDING≈90%, RANGING≈50%, BREAKOUT≈10%, REVERSAL≈40%.
    Produces high cross-regime std dev → contradiction-tolerant dataset.
    """
    regimes  = ["TRENDING", "RANGING", "BREAKOUT", "REVERSAL"]
    sessions = ["NY", "LN", "AS", "EU"]
    targets  = [0.9, 0.5, 0.1, 0.4]
    trades = []
    for i in range(n):
        r_idx  = i % 4
        regime = regimes[r_idx]
        pos    = i // 4  # position within this regime's sequence
        win    = (pos % 10) < int(targets[r_idx] * 10)
        trades.append({
            "trade_id":        f"TRD-{i:04d}",
            "entry_ts":        1_700_000_000_000 + i * 60_000,
            "exit_ts":         1_700_000_060_000 + i * 60_000,
            "net_pnl":         0.5 if win else -0.5,
            "gross_pnl":       0.6,
            "fee_entry":       0.05,
            "fee_exit":        0.05,
            "slippage_cost":   0.02,
            "regime":          regime,
            "origin_session":  sessions[i % 4],
            "exploration_origin": {"was_exploration_trade": i % 10 == 0},
        })
    return trades


def _blank_metrics(score: float = 0.0, tier: str = "FLEXIBLE") -> dict:
    """All metrics with the given score and a neutral tier for testing."""
    return {k: {"score": score, "tier": tier} for k in (
        "evidence_sufficiency", "replay_statistical_confidence",
        "governance_evidence_depth", "contradiction_tolerance",
        "minority_hypothesis_survivability", "falsification_rate",
        "consensus_rigidity", "epistemic_plasticity",
    )}


# ── Evidence sufficiency ───────────────────────────────────────────────────────

class TestEvidenceSufficiencyMetric:
    def test_empty_list_returns_base(self):
        r = _evidence_sufficiency_metric([])
        assert r["tier"] == "INSUFFICIENT"
        assert r["total_trades"] == 0

    def test_small_single_regime_insufficient(self):
        r = _evidence_sufficiency_metric(_make_trades(5))
        assert r["tier"] in ("SPARSE", "INSUFFICIENT")

    def test_large_diverse_sufficient(self):
        r = _evidence_sufficiency_metric(_make_diverse_trades(200))
        assert r["score"] < 30.0
        assert r["tier"] in ("SUFFICIENT", "MARGINAL")

    def test_score_decreases_with_diversity(self):
        mono  = _evidence_sufficiency_metric(_make_trades(50))
        divrse = _evidence_sufficiency_metric(_make_diverse_trades(80))
        assert divrse["score"] < mono["score"]

    def test_distinct_regimes_and_sessions_reported(self):
        r = _evidence_sufficiency_metric(_make_diverse_trades(80))
        assert r["distinct_regimes"]  == 4
        assert r["distinct_sessions"] == 4

    def test_score_in_bounds(self):
        for n in (1, 10, 50, 200):
            r = _evidence_sufficiency_metric(_make_trades(n))
            assert 0.0 <= r["score"] <= 100.0


# ── Replay statistical confidence ─────────────────────────────────────────────

class TestReplayStatisticalConfidence:
    def test_empty_list_returns_base(self):
        r = _replay_statistical_confidence_metric([])
        assert r["tier"] == "INSUFFICIENT"

    def test_large_sample_high_confidence(self):
        r = _replay_statistical_confidence_metric(_make_diverse_trades(500))
        assert r["tier"] in ("HIGH", "ADEQUATE")
        assert r["score"] < 30.0

    def test_small_sample_low_confidence(self):
        r = _replay_statistical_confidence_metric(_make_trades(10))
        assert r["score"] > 30.0
        assert r["tier"] in ("LOW", "INSUFFICIENT")

    def test_score_decreases_with_larger_sample(self):
        r10  = _replay_statistical_confidence_metric(_make_trades(10))
        r200 = _replay_statistical_confidence_metric(_make_diverse_trades(200))
        assert r200["score"] < r10["score"]

    def test_win_rate_and_sample_reported(self):
        r = _replay_statistical_confidence_metric(_make_trades(50))
        assert "win_rate" in r
        assert "sample_n" in r
        assert r["sample_n"] == 50


# ── Governance evidence depth ─────────────────────────────────────────────────

class TestGovernanceEvidenceDepth:
    def test_empty_list_returns_base(self):
        r = _governance_evidence_depth_metric([])
        assert r["tier"] == "INSUFFICIENT"

    def test_diverse_deep(self):
        r = _governance_evidence_depth_metric(_make_diverse_trades(200))
        assert r["score"] < 20.0
        assert r["tier"] in ("DEEP", "ADEQUATE")

    def test_single_regime_no_exploration_shallow(self):
        r = _governance_evidence_depth_metric(_make_trades(20))
        assert r["tier"] in ("SHALLOW", "INSUFFICIENT")

    def test_score_in_bounds(self):
        r = _governance_evidence_depth_metric(_make_trades(50))
        assert 0.0 <= r["score"] <= 100.0

    def test_exploration_coverage_reported(self):
        r = _governance_evidence_depth_metric(_make_diverse_trades(80))
        assert "exploration_coverage" in r
        assert r["exploration_coverage"] > 0


# ── Contradiction tolerance ───────────────────────────────────────────────────

class TestContradictionTolerance:
    def test_empty_list_returns_base(self):
        r = _contradiction_tolerance_metric([])
        assert r["tier"] == "INSUFFICIENT"

    def test_single_regime_fully_suppressed(self):
        r = _contradiction_tolerance_metric(_make_trades(30))
        assert r["score"] == 100.0
        assert r["tier"] == "SUPPRESSED"

    def test_high_cross_regime_variance_tolerant(self):
        # TRENDING≈90% win, BREAKOUT≈10% win — std ≈ 0.28 which exceeds 0.25 threshold
        r = _contradiction_tolerance_metric(_make_diverse_trades(80))
        assert r["tier"] in ("TOLERANT", "MODERATE")

    def test_score_lower_with_more_variance(self):
        mono  = _contradiction_tolerance_metric(_make_trades(40))
        divrse = _contradiction_tolerance_metric(_make_diverse_trades(80))
        assert divrse["score"] < mono["score"]

    def test_cross_regime_std_reported(self):
        r = _contradiction_tolerance_metric(_make_diverse_trades(80))
        assert "cross_regime_std" in r
        assert r["cross_regime_std"] >= 0.0

    def test_two_regimes_same_win_rate_suppressed(self):
        trades = (
            [_make_trade(i, regime="A", net_pnl=0.5) for i in range(20)]
            + [_make_trade(i + 20, regime="B", net_pnl=0.5) for i in range(20)]
        )
        r = _contradiction_tolerance_metric(trades)
        assert r["score"] == 100.0
        assert r["tier"] == "SUPPRESSED"


# ── Minority hypothesis survivability ────────────────────────────────────────

class TestMinorityHypothesisSurvivability:
    def test_empty_list_returns_base(self):
        r = _minority_hypothesis_survivability_metric([])
        assert r["tier"] == "INSUFFICIENT"

    def test_single_regime_extinct(self):
        r = _minority_hypothesis_survivability_metric(_make_trades(40))
        assert r["score"] == 100.0
        assert r["tier"] == "EXTINCT"

    def test_equal_distribution_adequate(self):
        r = _minority_hypothesis_survivability_metric(_make_diverse_trades(80))
        assert r["tier"] in ("HIGH", "ADEQUATE")

    def test_dominant_fraction_reported(self):
        r = _minority_hypothesis_survivability_metric(_make_diverse_trades(80))
        assert "dominant_regime_fraction" in r
        assert 0.0 < r["dominant_regime_fraction"] <= 1.0

    def test_score_is_dominant_fraction_times_100(self):
        trades = (
            [_make_trade(i, regime="A") for i in range(80)]
            + [_make_trade(i + 80, regime="B") for i in range(20)]
        )
        r = _minority_hypothesis_survivability_metric(trades)
        expected = 80 / 100 * 100
        assert abs(r["score"] - expected) < 0.01


# ── Falsification rate ────────────────────────────────────────────────────────

class TestFalsificationRate:
    def test_empty_list_returns_base(self):
        r = _falsification_rate_metric([])
        assert r["tier"] == "INSUFFICIENT"

    def test_no_exploration_dormant(self):
        trades = _make_trades(50)
        r = _falsification_rate_metric(trades)
        assert r["tier"] == "DORMANT"

    def test_full_exploration_active(self):
        trades = [_make_trade(i, exploration_origin={"was_exploration_trade": True})
                  for i in range(50)]
        r = _falsification_rate_metric(trades)
        assert r["tier"] in ("ACTIVE", "MODERATE")
        assert r["score"] < 50.0

    def test_exploration_reported(self):
        r = _falsification_rate_metric(_make_diverse_trades(80))
        assert "exploration_ratio" in r
        assert r["exploration_ratio"] > 0.0

    def test_score_decreases_with_more_exploration(self):
        r_low  = _falsification_rate_metric(_make_trades(50))
        r_high = _falsification_rate_metric(_make_diverse_trades(80))
        assert r_high["score"] < r_low["score"]

    def test_score_in_bounds(self):
        r = _falsification_rate_metric(_make_trades(50))
        assert 0.0 <= r["score"] <= 100.0


# ── Consensus rigidity ────────────────────────────────────────────────────────

class TestConsensusRigidity:
    def test_empty_list_returns_base(self):
        r = _consensus_rigidity_metric([])
        assert r["tier"] == "INSUFFICIENT"

    def test_single_regime_locked(self):
        r = _consensus_rigidity_metric(_make_trades(40))
        assert r["score"] > 70.0
        assert r["tier"] == "LOCKED"

    def test_four_regimes_four_sessions_flexible(self):
        r = _consensus_rigidity_metric(_make_diverse_trades(80))
        assert r["score"] < 35.0
        assert r["tier"] in ("FLEXIBLE", "MODERATE")

    def test_hhi_values_reported(self):
        r = _consensus_rigidity_metric(_make_trades(40))
        assert "regime_hhi" in r
        assert "session_hhi" in r
        assert r["regime_hhi"] == pytest.approx(1.0, abs=0.01)


# ── Epistemic plasticity ──────────────────────────────────────────────────────

class TestEpistemicPlasticity:
    def test_fewer_than_10_trades_insufficient(self):
        r = _epistemic_plasticity_metric(_make_trades(5))
        assert r["tier"] == "INSUFFICIENT"

    def test_constant_behavior_crystallized(self):
        r = _epistemic_plasticity_metric(_make_trades(50))
        assert r["tier"] == "CRYSTALLIZED"

    def test_changing_win_rate_plastic(self):
        # early half: all win; late half: all lose → large win_rate_delta
        early = [_make_trade(i, entry_ts=i * 1000, net_pnl=1.0)  for i in range(25)]
        late  = [_make_trade(i + 25, entry_ts=(i + 25) * 1000, net_pnl=-1.0) for i in range(25)]
        r = _epistemic_plasticity_metric(early + late)
        assert r["tier"] in ("PLASTIC", "ADEQUATE")
        assert r["win_rate_delta"] > 0.4

    def test_deltas_reported(self):
        r = _epistemic_plasticity_metric(_make_trades(50))
        assert "win_rate_delta" in r
        assert "exploration_delta" in r
        assert "regime_shift" in r

    def test_score_in_bounds(self):
        r = _epistemic_plasticity_metric(_make_trades(50))
        assert 0.0 <= r["score"] <= 100.0


# ── Epistemic integrity score ─────────────────────────────────────────────────

class TestEpistemicIntegrityScore:
    def test_fewer_than_10_trades_critical(self):
        r = _epistemic_integrity_score({}, 5)
        assert r["tier"] == "CRITICAL"
        assert "note" in r
        assert "insufficient" in r["note"].lower()

    def test_zero_penalty_scientifically_healthy(self):
        r = _epistemic_integrity_score(_blank_metrics(0.0), 50)
        assert r["score"] == 100.0
        assert r["tier"] == "SCIENTIFICALLY_HEALTHY"

    def test_max_penalty_critical(self):
        r = _epistemic_integrity_score(_blank_metrics(100.0), 50)
        assert r["score"] == 0.0
        assert r["tier"] == "CRITICAL"

    def test_diverse_trades_healthy(self):
        metrics = _compute_epistemic_metrics(_make_diverse_trades(80))
        r = _epistemic_integrity_score(metrics, 80)
        assert r["score"] >= 60.0
        assert r["tier"] in ("SCIENTIFICALLY_HEALTHY", "ADEQUATE")

    def test_tiers_correct(self):
        assert _epistemic_integrity_score(_blank_metrics(0.0), 50)["tier"] == "SCIENTIFICALLY_HEALTHY"
        assert _epistemic_integrity_score(_blank_metrics(40.0), 50)["tier"] == "ADEQUATE"
        assert _epistemic_integrity_score(_blank_metrics(60.0), 50)["tier"] == "VULNERABLE"
        assert _epistemic_integrity_score(_blank_metrics(90.0), 50)["tier"] == "CRITICAL"


# ── Classification ────────────────────────────────────────────────────────────

class TestClassification:
    def _cls(self, metrics: dict, score: float, n: int) -> str:
        return _classify_epistemic(metrics, {"score": score}, n)

    def test_zero_trades_evidence_insufficiency(self):
        assert _classify_epistemic({}, {"score": 0.0}, 0) == EVIDENCE_INSUFFICIENCY

    def test_fewer_than_10_trades_evidence_insufficiency(self):
        assert _classify_epistemic({}, {"score": 0.0}, 5) == EVIDENCE_INSUFFICIENCY

    def test_low_integrity_score_lockdown(self):
        metrics = _blank_metrics(0.0, "FLEXIBLE")
        metrics["falsification_rate"]  = {"score": 70.0, "tier": "PASSIVE"}
        metrics["consensus_rigidity"]  = {"score": 30.0, "tier": "MODERATE"}
        assert self._cls(metrics, 10.0, 50) == EPISTEMIC_LOCKDOWN_RISK

    def test_dormant_false_locked_cons_ideological(self):
        metrics = _blank_metrics(0.0, "FLEXIBLE")
        metrics["falsification_rate"] = {"score": 80.0, "tier": "DORMANT"}
        metrics["consensus_rigidity"] = {"score": 80.0, "tier": "LOCKED"}
        assert self._cls(metrics, 60.0, 50) == IDEOLOGICAL_SELF_CONFIRMATION

    def test_passive_false_rigid_cons_ideological(self):
        metrics = _blank_metrics(0.0, "FLEXIBLE")
        metrics["falsification_rate"] = {"score": 60.0, "tier": "PASSIVE"}
        metrics["consensus_rigidity"] = {"score": 60.0, "tier": "RIGID"}
        assert self._cls(metrics, 60.0, 50) == IDEOLOGICAL_SELF_CONFIRMATION

    def test_suppressed_contradiction_suppression(self):
        metrics = _blank_metrics(0.0, "FLEXIBLE")
        metrics["falsification_rate"]  = {"score": 40.0, "tier": "MODERATE"}
        metrics["consensus_rigidity"]  = {"score": 30.0, "tier": "MODERATE"}
        metrics["contradiction_tolerance"] = {"score": 80.0, "tier": "SUPPRESSED"}
        assert self._cls(metrics, 60.0, 50) == CONTRADICTION_SUPPRESSION

    def test_dormant_falsification_failure(self):
        metrics = _blank_metrics(0.0, "FLEXIBLE")
        metrics["falsification_rate"] = {"score": 80.0, "tier": "DORMANT"}
        metrics["consensus_rigidity"] = {"score": 30.0, "tier": "MODERATE"}
        metrics["contradiction_tolerance"] = {"score": 30.0, "tier": "MODERATE"}
        assert self._cls(metrics, 50.0, 50) == FALSIFICATION_FAILURE

    def test_all_healthy_scientifically_healthy(self):
        metrics = _blank_metrics(0.0, "FLEXIBLE")
        metrics["evidence_sufficiency"]    = {"score": 5.0,  "tier": "SUFFICIENT"}
        metrics["falsification_rate"]      = {"score": 10.0, "tier": "ACTIVE"}
        metrics["consensus_rigidity"]      = {"score": 10.0, "tier": "FLEXIBLE"}
        metrics["contradiction_tolerance"] = {"score": 10.0, "tier": "TOLERANT"}
        assert self._cls(metrics, 80.0, 50) == SCIENTIFICALLY_HEALTHY

    def test_sparse_evidence_does_not_block_healthy(self):
        # SPARSE evidence is acceptable; only INSUFFICIENT triggers the evidence path.
        metrics = _blank_metrics(0.0, "FLEXIBLE")
        metrics["evidence_sufficiency"]    = {"score": 35.0, "tier": "SPARSE"}
        metrics["falsification_rate"]      = {"score": 10.0, "tier": "ACTIVE"}
        metrics["consensus_rigidity"]      = {"score": 10.0, "tier": "FLEXIBLE"}
        metrics["contradiction_tolerance"] = {"score": 10.0, "tier": "TOLERANT"}
        assert self._cls(metrics, 80.0, 50) == SCIENTIFICALLY_HEALTHY

    def test_insufficient_evidence_triggers_evidence_insufficiency(self):
        metrics = _blank_metrics(0.0, "FLEXIBLE")
        metrics["evidence_sufficiency"]    = {"score": 90.0, "tier": "INSUFFICIENT"}
        metrics["falsification_rate"]      = {"score": 10.0, "tier": "ACTIVE"}
        metrics["consensus_rigidity"]      = {"score": 10.0, "tier": "FLEXIBLE"}
        metrics["contradiction_tolerance"] = {"score": 10.0, "tier": "TOLERANT"}
        assert self._cls(metrics, 80.0, 50) == EVIDENCE_INSUFFICIENCY


# ── Epistemic lineage ─────────────────────────────────────────────────────────

class TestEpistemicLineage:
    def test_empty_trades_empty_lineage(self):
        r = _build_epistemic_lineage([])
        assert r["total_epochs"] == 0
        assert r["epochs"] == {}

    def test_three_epochs_created(self):
        r = _build_epistemic_lineage(_make_trades(30))
        assert "early" in r["epochs"]
        assert "mid"   in r["epochs"]
        assert "late"  in r["epochs"]

    def test_epoch_fields_present(self):
        r = _build_epistemic_lineage(_make_trades(30))
        ep = r["epochs"]["early"]
        for key in ("trade_count", "dominant_regime", "win_rate",
                    "exploration_ratio", "regime_diversity", "epistemic_health"):
            assert key in ep, f"Missing epoch key: {key}"

    def test_epistemic_health_labels(self):
        r = _build_epistemic_lineage(_make_trades(30))
        for ep in r["epochs"].values():
            assert ep["epistemic_health"] in ("HEALTHY", "EMERGING", "RIGID")

    def test_trajectory_computed(self):
        r = _build_epistemic_lineage(_make_trades(30))
        assert r["epistemic_trajectory"] in ("IMPROVING", "STABLE", "DECLINING")

    def test_diverse_trades_healthy_health(self):
        r = _build_epistemic_lineage(_make_diverse_trades(90))
        for ep in r["epochs"].values():
            assert ep["epistemic_health"] in ("HEALTHY", "EMERGING")


# ── Recommendations ────────────────────────────────────────────────────────────

class TestRecommendations:
    def _recs(self, cls: str, n: int = 50, score: float = 70.0) -> list:
        metrics = _compute_epistemic_metrics(_make_trades(n))
        return _generate_epistemic_recommendations(
            cls, metrics, {"score": score}, n,
        )

    def test_fewer_than_10_accumulate(self):
        recs = _generate_epistemic_recommendations(
            SCIENTIFICALLY_HEALTHY, {}, {"score": 90.0}, 5
        )
        assert any("ACCUMULATE" in r["action_required"] for r in recs)

    def test_lockdown_critical(self):
        recs = self._recs(EPISTEMIC_LOCKDOWN_RISK)
        assert any(r["priority"] == "CRITICAL" for r in recs)

    def test_ideological_critical(self):
        recs = self._recs(IDEOLOGICAL_SELF_CONFIRMATION)
        assert any(r["priority"] == "CRITICAL" for r in recs)

    def test_healthy_low_priority(self):
        metrics = _compute_epistemic_metrics(_make_diverse_trades(80))
        recs = _generate_epistemic_recommendations(
            SCIENTIFICALLY_HEALTHY, metrics, {"score": 90.0}, 80
        )
        assert all(r["priority"] in ("LOW", "MEDIUM") for r in recs)

    def test_all_auto_authorized_false(self):
        for cls in (SCIENTIFICALLY_HEALTHY, EVIDENCE_INSUFFICIENCY,
                    IDEOLOGICAL_SELF_CONFIRMATION, CONTRADICTION_SUPPRESSION,
                    FALSIFICATION_FAILURE, EPISTEMIC_LOCKDOWN_RISK):
            recs = self._recs(cls)
            for r in recs:
                assert r["auto_authorized"] is False, f"auto_authorized=True for {cls}"


# ── Audit entry ────────────────────────────────────────────────────────────────

class TestAuditEntry:
    def _entry(self, **kw) -> dict:
        defaults = dict(
            classification=SCIENTIFICALLY_HEALTHY,
            integrity_score={"score": 90.0, "tier": "SCIENTIFICALLY_HEALTHY"},
            total_trades=50,
            recommendations=[],
        )
        defaults.update(kw)
        return _generate_epistemic_audit_entry(**defaults)

    def test_entry_id_starts_with_eiod(self):
        assert self._entry()["entry_id"].startswith("EIOD-")

    def test_auto_authorized_always_false(self):
        assert self._entry()["auto_authorized"] is False

    def test_immutable_always_true(self):
        assert self._entry()["immutable"] is True

    def test_entry_type_is_analysis(self):
        assert self._entry()["entry_type"] == "ANALYSIS"

    def test_human_approval_required_for_sufficient_trades(self):
        assert self._entry(total_trades=50)["human_approval_required"] is True

    def test_human_approval_false_for_insufficient_trades(self):
        assert self._entry(total_trades=5)["human_approval_required"] is False


# ── Compute structure ──────────────────────────────────────────────────────────

class TestComputeStructure:
    _REQUIRED_KEYS = {
        "scope_note",
        "total_trades",
        "epistemic_classification",
        "classification_description",
        "epistemic_integrity_score",
        "epistemic_metrics",
        "epistemic_lineage",
        "recommendations",
        "epistemic_hard_principles",
        "audit_entry",
    }

    _METRIC_KEYS = {
        "evidence_sufficiency",
        "replay_statistical_confidence",
        "governance_evidence_depth",
        "contradiction_tolerance",
        "minority_hypothesis_survivability",
        "falsification_rate",
        "consensus_rigidity",
        "epistemic_plasticity",
    }

    def test_returns_dict(self):
        assert isinstance(compute_epistemic_integrity([]), dict)

    def test_all_required_keys_present(self):
        r = compute_epistemic_integrity(_make_trades(30))
        for k in self._REQUIRED_KEYS:
            assert k in r, f"Missing key: {k}"

    def test_all_eight_metric_keys_present(self):
        r = compute_epistemic_integrity(_make_trades(30))
        assert set(r["epistemic_metrics"].keys()) == self._METRIC_KEYS

    def test_empty_list_no_exception(self):
        r = compute_epistemic_integrity([])
        assert "epistemic_classification" in r

    def test_total_trades_correct(self):
        trades = _make_trades(37)
        r = compute_epistemic_integrity(trades)
        assert r["total_trades"] == 37

    def test_hard_principles_present(self):
        r = compute_epistemic_integrity(_make_trades(30))
        assert r["epistemic_hard_principles"] == EPISTEMIC_HARD_PRINCIPLES

    def test_audit_entry_present(self):
        r = compute_epistemic_integrity(_make_trades(30))
        assert "entry_id" in r["audit_entry"]

    def test_scope_note_present(self):
        r = compute_epistemic_integrity(_make_trades(30))
        assert "FTD-EIOD" in r["scope_note"]

    def test_lineage_has_epochs(self):
        r = compute_epistemic_integrity(_make_trades(30))
        assert "epochs" in r["epistemic_lineage"]

    def test_diverse_trades_healthy_classification(self):
        r = compute_epistemic_integrity(_make_diverse_trades(80))
        assert r["epistemic_classification"] == SCIENTIFICALLY_HEALTHY

    def test_never_raises_on_garbage_input(self):
        for bad in (None, 42, "string", [None, "bad", 99]):
            try:
                result = compute_epistemic_integrity(bad)  # type: ignore
                assert isinstance(result, dict)
            except Exception as exc:
                pytest.fail(f"compute_epistemic_integrity raised {exc} on {bad!r}")

    def test_all_recs_not_auto_authorized(self):
        r = compute_epistemic_integrity(_make_diverse_trades(80))
        for rec in r["recommendations"]:
            assert rec["auto_authorized"] is False


# ── Production isolation ───────────────────────────────────────────────────────

class TestProductionIsolation:
    def test_no_live_engine_imports(self):
        import core.epistemic_observatory as mod
        src = Path(mod.__file__).read_text()
        for bad in ("from main import", "import main", "pnl_calc",
                    "rl_engine", "data_lake", "from core.trading"):
            assert bad not in src, f"Forbidden reference: {bad!r}"

    def test_output_is_research_only(self):
        r = compute_epistemic_integrity(_make_trades(30))
        note = r.get("scope_note", "")
        assert "NEVER" in note or "research" in note.lower()

    def test_never_modifies_input(self):
        trades = _make_trades(30)
        original = [t.copy() for t in trades]
        compute_epistemic_integrity(trades)
        assert trades == original

    def test_all_recommendations_not_auto_authorized(self):
        r = compute_epistemic_integrity(_make_diverse_trades(80))
        for rec in r["recommendations"]:
            assert rec["auto_authorized"] is False

    def test_fail_open_on_none_input(self):
        r = compute_epistemic_integrity(None)  # type: ignore
        assert isinstance(r, dict)
        assert "epistemic_hard_principles" in r


# ── Constitutional principles ──────────────────────────────────────────────────

class TestConstitutionalPrinciples:
    def test_human_authority_over_truth_governance_true(self):
        assert EPISTEMIC_HARD_PRINCIPLES["human_authority_over_truth_governance"] is True

    def test_explicit_scientific_approval_required_true(self):
        assert EPISTEMIC_HARD_PRINCIPLES["explicit_scientific_approval_required"] is True

    def test_immutable_epistemic_lineage_guaranteed_true(self):
        assert EPISTEMIC_HARD_PRINCIPLES["immutable_epistemic_lineage_guaranteed"] is True

    def test_autonomous_truth_certification_false(self):
        assert EPISTEMIC_HARD_PRINCIPLES["autonomous_truth_certification"] is False

    def test_sovereign_epistemic_authority_false(self):
        assert EPISTEMIC_HARD_PRINCIPLES["sovereign_epistemic_authority"] is False

    def test_self_validating_doctrine_false(self):
        assert EPISTEMIC_HARD_PRINCIPLES["self_validating_doctrine"] is False

    def test_autonomous_doctrine_validation_false(self):
        assert EPISTEMIC_HARD_PRINCIPLES["autonomous_doctrine_validation"] is False

    def test_result_carries_all_principles(self):
        r = compute_epistemic_integrity(_make_trades(20))
        for k, v in EPISTEMIC_HARD_PRINCIPLES.items():
            assert r["epistemic_hard_principles"][k] == v


# ── Edge cases ─────────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_none_values_in_fields(self):
        trade = {
            "trade_id": None, "entry_ts": None, "net_pnl": None,
            "regime": None, "origin_session": None, "exploration_origin": None,
        }
        r = compute_epistemic_integrity([trade] * 15)
        assert isinstance(r, dict)
        assert r["total_trades"] == 15

    def test_malformed_non_dict_items(self):
        trades = [_make_trade(0), "bad", None, 42, {}, _make_trade(1)] * 5
        r = compute_epistemic_integrity(trades)
        assert isinstance(r, dict)

    def test_very_large_trade_count(self):
        trades = _make_diverse_trades(400)
        r = compute_epistemic_integrity(trades)
        assert r["total_trades"] == 400
        assert r["epistemic_classification"] in (
            SCIENTIFICALLY_HEALTHY, EVIDENCE_INSUFFICIENCY,
            IDEOLOGICAL_SELF_CONFIRMATION, CONTRADICTION_SUPPRESSION,
            FALSIFICATION_FAILURE, EPISTEMIC_LOCKDOWN_RISK,
        )

    def test_single_trade_no_exception(self):
        r = compute_epistemic_integrity([_make_trade(0)])
        assert isinstance(r, dict)
        assert r["total_trades"] == 1

    def test_all_exploration_trades(self):
        trades = [_make_trade(i, exploration_origin={"was_exploration_trade": True},
                              regime=["A", "B", "C", "D"][i % 4])
                  for i in range(40)]
        r = compute_epistemic_integrity(trades)
        assert isinstance(r, dict)
        metrics = r["epistemic_metrics"]
        assert metrics["falsification_rate"]["tier"] in ("ACTIVE", "MODERATE")
