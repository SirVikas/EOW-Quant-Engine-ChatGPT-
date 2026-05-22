"""
Tests for FTD-LHEO: Long-Horizon Constitutional Evolution Observatory.

Verifies:
  - Immutable lineage guarantees
  - Era continuity correctness
  - Drift metric stability
  - No autonomous doctrine mutation
  - Constitutional invariants
  - Fail-open behavior
  - Backward compatibility
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from core.evolution_observatory import (
    CONSTITUTIONALLY_RESILIENT,
    IDEOLOGICAL_RIGIDIFICATION,
    EXPLORATION_EXTINCTION,
    SURVIVABILITY_MONOCULTURE,
    ADAPTIVE_MEMORY_DECAY,
    LONG_HORIZON_LOCKDOWN_RISK,
    EVOLUTION_HARD_PRINCIPLES,
    _segment_eras,
    _era_snapshot,
    _constitutional_stability_metric,
    _drift_acceleration_metric,
    _governance_ideology_concentration_metric,
    _plasticity_half_life_metric,
    _exploration_extinction_risk_metric,
    _survivability_monoculture_risk_metric,
    _cognitive_diversity_retention_metric,
    _long_horizon_replay_dependence_metric,
    _long_horizon_stability_score,
    _classify_evolution,
    _build_cognitive_lineage,
    _generate_evolution_recommendations,
    _generate_evolution_audit_entry,
    compute_long_horizon_evolution,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────

def _trade(net_pnl=1.0, gross_pnl=1.2, fee_entry=0.05, fee_exit=0.05,
           slippage_cost=0.02, entry_ts=1000, regime="TRENDING",
           session="NY", was_exploration=False):
    t = {
        "net_pnl": net_pnl, "gross_pnl": gross_pnl,
        "fee_entry": fee_entry, "fee_exit": fee_exit,
        "slippage_cost": slippage_cost,
        "entry_ts": entry_ts, "exit_ts": entry_ts + 3600,
        "regime": regime, "origin_session": session,
    }
    if was_exploration:
        t["exploration_origin"] = {"was_exploration_trade": True}
    return t


def _trades(n=50, regime="TRENDING", session="NY", net_pnl=1.0,
            was_exploration=False, ts_start=0):
    return [
        _trade(net_pnl=net_pnl, regime=regime, session=session,
               was_exploration=was_exploration, entry_ts=ts_start + i * 100)
        for i in range(n)
    ]


def _era_snap(era_idx=0, net_exp=1.0, explore=0.10, win_rate=0.55,
              regime_hhi=40.0, session_hhi=60.0, const_health=80.0,
              dominant="TRENDING"):
    return {
        "era_index":               era_idx,
        "trade_count":             100,
        "dominant_regime":         dominant,
        "exploration_ratio":       explore,
        "net_expectancy":          net_exp,
        "win_rate":                win_rate,
        "fee_gross_ratio":         5.0,
        "slippage_gross_ratio":    2.0,
        "regime_hhi":              regime_hhi,
        "session_hhi":             session_hhi,
        "era_constitutional_health": const_health,
    }


# ── TestEraSegmentation ────────────────────────────────────────────────────────

class TestEraSegmentation:
    def test_empty_trades_returns_empty(self):
        assert _segment_eras([], 5) == []

    def test_zero_eras_returns_empty(self):
        assert _segment_eras(_trades(50), 0) == []

    def test_one_hundred_trades_five_eras(self):
        eras = _segment_eras(_trades(100), 5)
        assert len(eras) == 5
        assert all(len(e) == 20 for e in eras)

    def test_last_era_gets_remainder(self):
        eras = _segment_eras(_trades(103), 5)
        assert len(eras) == 5
        total = sum(len(e) for e in eras)
        assert total == 103

    def test_sorted_by_entry_ts(self):
        ts_list = [500, 100, 300, 200, 400]
        trades  = [_trade(entry_ts=ts) for ts in ts_list]
        eras    = _segment_eras(trades, 1)
        assert len(eras) == 1
        ts_out = [t["entry_ts"] for t in eras[0]]
        assert ts_out == sorted(ts_out)


# ── TestEraSnapshot ────────────────────────────────────────────────────────────

class TestEraSnapshot:
    def test_empty_trades_zero_values(self):
        r = _era_snapshot([], 0)
        assert r["trade_count"] == 0
        assert r["net_expectancy"] == 0.0
        assert r["era_index"] == 0

    def test_net_expectancy_and_win_rate(self):
        trades = [_trade(net_pnl=1.0)] * 6 + [_trade(net_pnl=-1.0)] * 4
        r      = _era_snapshot(trades, 0)
        assert r["net_expectancy"] == pytest.approx(0.2)
        assert r["win_rate"]       == pytest.approx(0.6)

    def test_exploration_ratio_detected(self):
        trades = [_trade(was_exploration=True)] * 3 + [_trade()] * 7
        r      = _era_snapshot(trades, 0)
        assert r["exploration_ratio"] == pytest.approx(0.3)

    def test_regime_hhi_single_regime(self):
        trades = _trades(20, regime="TRENDING")
        r      = _era_snapshot(trades, 0)
        assert r["regime_hhi"] == pytest.approx(100.0)
        assert r["dominant_regime"] == "TRENDING"

    def test_regime_hhi_two_regimes(self):
        trades = _trades(10, regime="TRENDING") + _trades(10, regime="MEAN_REV")
        r      = _era_snapshot(trades, 0)
        assert r["regime_hhi"] == pytest.approx(50.0)


# ── TestConstitutionalStabilityMetric ─────────────────────────────────────────

class TestConstitutionalStabilityMetric:
    def test_single_era_insufficient(self):
        r = _constitutional_stability_metric([_era_snap()])
        assert r["tier"] == "INSUFFICIENT"
        assert r["score"] == 0.0

    def test_stable_across_eras_low_score(self):
        snaps = [_era_snap(const_health=80.0) for _ in range(5)]
        r     = _constitutional_stability_metric(snaps)
        assert r["score"] < 5.0
        assert r["tier"] == "STABLE"

    def test_volatile_across_eras_high_score(self):
        snaps = [_era_snap(const_health=v) for v in [20.0, 90.0, 10.0, 85.0, 15.0]]
        r     = _constitutional_stability_metric(snaps)
        assert r["score"] > 20.0
        assert r["tier"] in ("VOLATILE", "UNSTABLE")

    def test_mean_health_reported(self):
        snaps = [_era_snap(const_health=60.0), _era_snap(const_health=80.0)]
        r     = _constitutional_stability_metric(snaps)
        assert r["mean_constitutional_health"] == pytest.approx(70.0)

    def test_score_bounded_0_100(self):
        snaps = [_era_snap(const_health=v) for v in [0.0, 100.0, 0.0, 100.0, 0.0]]
        r     = _constitutional_stability_metric(snaps)
        assert 0.0 <= r["score"] <= 100.0


# ── TestDriftAccelerationMetric ───────────────────────────────────────────────

class TestDriftAccelerationMetric:
    def test_single_era_insufficient(self):
        r = _drift_acceleration_metric([_era_snap()])
        assert r["tier"] == "INSUFFICIENT"

    def test_stable_net_expectancy_low_score(self):
        snaps = [_era_snap(net_exp=1.0) for _ in range(5)]
        r     = _drift_acceleration_metric(snaps)
        assert r["score"] == 0.0
        assert r["tier"] == "MINIMAL"

    def test_volatile_net_expectancy_high_score(self):
        snaps = [_era_snap(net_exp=v) for v in [0.0, 5.0, 0.0, 5.0]]
        r     = _drift_acceleration_metric(snaps)
        assert r["score"] > 30.0
        assert r["tier"] in ("MODERATE", "HIGH")

    def test_sample_count_correct(self):
        snaps = [_era_snap() for _ in range(4)]
        r     = _drift_acceleration_metric(snaps)
        assert r["sample_count"] == 4


# ── TestGovernanceIdeologyConcentration ───────────────────────────────────────

class TestGovernanceIdeologyConcentration:
    def test_empty_insufficient(self):
        r = _governance_ideology_concentration_metric([])
        assert r["tier"] == "INSUFFICIENT"

    def test_diverse_regimes_low_score(self):
        snaps = [_era_snap(regime_hhi=20.0, dominant=f"R{i}") for i in range(5)]
        r     = _governance_ideology_concentration_metric(snaps)
        assert r["score"] < 50.0
        assert r["tier"] in ("DIVERSE", "MODERATE")

    def test_single_regime_always_high_score(self):
        snaps = [_era_snap(regime_hhi=100.0, dominant="TRENDING")] * 5
        r     = _governance_ideology_concentration_metric(snaps)
        assert r["score"] >= 70.0
        assert r["tier"] == "MONOCULTURE"

    def test_cross_era_hhi_reported(self):
        snaps = [_era_snap(dominant="TRENDING"), _era_snap(dominant="TRENDING")]
        r     = _governance_ideology_concentration_metric(snaps)
        assert r["cross_era_regime_hhi"] == pytest.approx(100.0)

    def test_score_bounded(self):
        snaps = [_era_snap(regime_hhi=100.0)] * 5
        r     = _governance_ideology_concentration_metric(snaps)
        assert 0.0 <= r["score"] <= 100.0


# ── TestPlasticityHalfLife ────────────────────────────────────────────────────

class TestPlasticityHalfLife:
    def test_single_era_insufficient(self):
        r = _plasticity_half_life_metric([_era_snap()])
        assert r["tier"] == "INSUFFICIENT"

    def test_same_exploration_healthy(self):
        snaps = [_era_snap(explore=0.15), _era_snap(explore=0.15)]
        r     = _plasticity_half_life_metric(snaps)
        assert r["score"] == 0.0
        assert r["tier"] == "HEALTHY"

    def test_rapid_decay_high_score(self):
        snaps = [_era_snap(explore=0.20), _era_snap(explore=0.02)]
        r     = _plasticity_half_life_metric(snaps)
        assert r["score"] >= 45.0
        assert r["tier"] in ("RAPID_DECAY", "EXTINCT")

    def test_zero_early_exploration_no_decay(self):
        snaps = [_era_snap(explore=0.0), _era_snap(explore=0.0)]
        r     = _plasticity_half_life_metric(snaps)
        assert r["score"] == 0.0
        assert r["tier"] == "HEALTHY"

    def test_full_decay_extinct_tier(self):
        snaps = [_era_snap(explore=0.20), _era_snap(explore=0.0)]
        r     = _plasticity_half_life_metric(snaps)
        assert r["score"] >= 70.0
        assert r["tier"] == "EXTINCT"


# ── TestExplorationExtinctionRisk ─────────────────────────────────────────────

class TestExplorationExtinctionRisk:
    def test_empty_insufficient(self):
        r = _exploration_extinction_risk_metric([])
        assert r["tier"] == "INSUFFICIENT"

    def test_high_late_exploration_low_risk(self):
        snaps = [_era_snap(explore=0.25)]
        r     = _exploration_extinction_risk_metric(snaps)
        assert r["score"] == 0.0
        assert r["tier"] == "LOW"

    def test_zero_late_exploration_critical(self):
        snaps = [_era_snap(explore=0.0)]
        r     = _exploration_extinction_risk_metric(snaps)
        assert r["score"] == pytest.approx(100.0)
        assert r["tier"] == "CRITICAL"

    def test_moderate_exploration_moderate_risk(self):
        snaps = [_era_snap(explore=0.10)]
        r     = _exploration_extinction_risk_metric(snaps)
        assert r["tier"] in ("MODERATE", "HIGH")

    def test_score_bounded(self):
        for exp in [0.0, 0.05, 0.10, 0.20, 0.50]:
            r = _exploration_extinction_risk_metric([_era_snap(explore=exp)])
            assert 0.0 <= r["score"] <= 100.0


# ── TestSurvivabilityMonocultureRisk ──────────────────────────────────────────

class TestSurvivabilityMonocultureRisk:
    def test_empty_insufficient(self):
        r = _survivability_monoculture_risk_metric([])
        assert r["tier"] == "INSUFFICIENT"

    def test_diverse_regime_hhi_diverse_tier(self):
        snaps = [_era_snap(regime_hhi=20.0)] * 3
        r     = _survivability_monoculture_risk_metric(snaps)
        assert r["tier"] == "DIVERSE"

    def test_single_regime_monoculture(self):
        snaps = [_era_snap(regime_hhi=100.0)] * 3
        r     = _survivability_monoculture_risk_metric(snaps)
        assert r["tier"] == "MONOCULTURE"

    def test_score_equals_mean_hhi(self):
        snaps = [_era_snap(regime_hhi=50.0), _era_snap(regime_hhi=70.0)]
        r     = _survivability_monoculture_risk_metric(snaps)
        assert r["score"] == pytest.approx(60.0)


# ── TestCognitiveDiversityRetention ───────────────────────────────────────────

class TestCognitiveDiversityRetention:
    def test_single_era_insufficient(self):
        r = _cognitive_diversity_retention_metric([_era_snap()])
        assert r["tier"] == "INSUFFICIENT"

    def test_diverse_sessions_regimes_high_diversity(self):
        snaps = [_era_snap(session_hhi=20.0, regime_hhi=20.0, win_rate=0.50 + i * 0.01)
                 for i in range(4)]
        r     = _cognitive_diversity_retention_metric(snaps)
        assert r["tier"] in ("HIGH_DIVERSITY", "MODERATE")

    def test_single_session_concentrated_score(self):
        snaps = [_era_snap(session_hhi=100.0, regime_hhi=100.0)] * 3
        r     = _cognitive_diversity_retention_metric(snaps)
        assert r["score"] > 50.0

    def test_sample_count_reported(self):
        snaps = [_era_snap(), _era_snap(), _era_snap()]
        r     = _cognitive_diversity_retention_metric(snaps)
        assert r["sample_count"] == 3


# ── TestLongHorizonReplayDependence ───────────────────────────────────────────

class TestLongHorizonReplayDependence:
    def test_single_era_insufficient(self):
        r = _long_horizon_replay_dependence_metric([_era_snap()])
        assert r["tier"] == "INSUFFICIENT"

    def test_high_late_exploration_minimal(self):
        snaps = [_era_snap(explore=0.15, win_rate=0.55), _era_snap(explore=0.15, win_rate=0.55)]
        r     = _long_horizon_replay_dependence_metric(snaps)
        assert r["tier"] in ("MINIMAL", "LOW")

    def test_low_explore_declining_win_high_tier(self):
        snaps = [_era_snap(explore=0.20, win_rate=0.60), _era_snap(explore=0.01, win_rate=0.30)]
        r     = _long_horizon_replay_dependence_metric(snaps)
        assert r["tier"] in ("MODERATE", "HIGH")

    def test_stable_win_low_explore_moderate(self):
        snaps = [_era_snap(explore=0.05, win_rate=0.55), _era_snap(explore=0.02, win_rate=0.53)]
        r     = _long_horizon_replay_dependence_metric(snaps)
        assert r["tier"] in ("LOW", "MODERATE")


# ── TestLongHorizonStabilityScore ─────────────────────────────────────────────

class TestLongHorizonStabilityScore:
    def _zero_metrics(self):
        keys = ["constitutional_stability", "drift_acceleration",
                "governance_ideology_concentration", "plasticity_half_life",
                "exploration_extinction_risk", "survivability_monoculture_risk",
                "cognitive_diversity_retention", "long_horizon_replay_dependence"]
        return {k: {"score": 0.0, "tier": "STABLE"} for k in keys}

    def _max_metrics(self):
        keys = ["constitutional_stability", "drift_acceleration",
                "governance_ideology_concentration", "plasticity_half_life",
                "exploration_extinction_risk", "survivability_monoculture_risk",
                "cognitive_diversity_retention", "long_horizon_replay_dependence"]
        return {k: {"score": 100.0, "tier": "HIGH"} for k in keys}

    def test_insufficient_for_single_era(self):
        r = _long_horizon_stability_score(self._zero_metrics(), 1)
        assert r["tier"] == "INSUFFICIENT"

    def test_all_zeros_score_100(self):
        r = _long_horizon_stability_score(self._zero_metrics(), 3)
        assert r["score"] == pytest.approx(100.0)
        assert r["tier"] == "RESILIENT"

    def test_all_hundreds_score_0(self):
        r = _long_horizon_stability_score(self._max_metrics(), 3)
        assert r["score"] == pytest.approx(0.0)
        assert r["tier"] == "CRITICAL"

    def test_score_bounded_0_100(self):
        for n in range(1, 6):
            r = _long_horizon_stability_score(self._zero_metrics(), n)
            assert 0.0 <= r["score"] <= 100.0

    def test_tier_assignment_adequate(self):
        metrics = {k: {"score": 35.0} for k in self._zero_metrics()}
        r       = _long_horizon_stability_score(metrics, 3)
        assert r["tier"] in ("RESILIENT", "ADEQUATE", "VULNERABLE")


# ── TestClassification ────────────────────────────────────────────────────────

class TestClassification:
    def _metrics(self, cs="STABLE", da="MINIMAL", ic="DIVERSE",
                 pl="HEALTHY", ee="LOW", mc="DIVERSE", dr="MINIMAL", rd="MINIMAL"):
        return {
            "constitutional_stability":          {"tier": cs},
            "drift_acceleration":                {"tier": da},
            "governance_ideology_concentration": {"tier": ic},
            "plasticity_half_life":              {"tier": pl},
            "exploration_extinction_risk":       {"tier": ee},
            "survivability_monoculture_risk":    {"tier": mc},
            "cognitive_diversity_retention":     {"tier": dr},
            "long_horizon_replay_dependence":    {"tier": rd},
        }

    def test_constitutionally_resilient_default(self):
        r = _classify_evolution(self._metrics(), 3)
        assert r == CONSTITUTIONALLY_RESILIENT

    def test_ideological_rigidification_concentrated(self):
        r = _classify_evolution(self._metrics(ic="CONCENTRATED"), 3)
        assert r == IDEOLOGICAL_RIGIDIFICATION

    def test_ideological_rigidification_high_replay(self):
        r = _classify_evolution(self._metrics(rd="HIGH"), 3)
        assert r == IDEOLOGICAL_RIGIDIFICATION

    def test_exploration_extinction(self):
        r = _classify_evolution(self._metrics(ee="CRITICAL", pl="EXTINCT"), 3)
        assert r == EXPLORATION_EXTINCTION

    def test_survivability_monoculture(self):
        r = _classify_evolution(self._metrics(mc="MONOCULTURE", ic="MONOCULTURE"), 3)
        assert r == SURVIVABILITY_MONOCULTURE

    def test_adaptive_memory_decay(self):
        r = _classify_evolution(self._metrics(da="HIGH", cs="MODERATE"), 3)
        assert r == ADAPTIVE_MEMORY_DECAY

    def test_long_horizon_lockdown_unstable(self):
        r = _classify_evolution(self._metrics(cs="UNSTABLE"), 3)
        assert r == LONG_HORIZON_LOCKDOWN_RISK

    def test_single_era_defaults_resilient(self):
        r = _classify_evolution(self._metrics(cs="UNSTABLE"), 1)
        assert r == CONSTITUTIONALLY_RESILIENT


# ── TestCognitiveLineage ──────────────────────────────────────────────────────

class TestCognitiveLineage:
    def test_empty_snapshots_eras_zero(self):
        r = _build_cognitive_lineage([])
        assert r["eras"] == 0
        assert r["early_era"] is None

    def test_single_era_early_equals_late(self):
        snap = _era_snap(era_idx=0, net_exp=1.5)
        r    = _build_cognitive_lineage([snap])
        assert r["early_era"]["net_expectancy"] == r["late_era"]["net_expectancy"]

    def test_multi_era_correct_extraction(self):
        snaps = [_era_snap(era_idx=i, net_exp=float(i)) for i in range(5)]
        r     = _build_cognitive_lineage(snaps)
        assert r["eras"] == 5
        assert r["early_era"]["era_index"] == 0
        assert r["late_era"]["era_index"] == 4
        assert r["mid_era"]["era_index"] == 2

    def test_trajectory_improving_detected(self):
        snaps = [_era_snap(net_exp=0.5), _era_snap(net_exp=1.5)]
        r     = _build_cognitive_lineage(snaps)
        assert r["trajectory"]["net_expectancy"] == "IMPROVING"

    def test_trajectory_declining_detected(self):
        snaps = [_era_snap(explore=0.20), _era_snap(explore=0.05)]
        r     = _build_cognitive_lineage(snaps)
        assert r["trajectory"]["exploration_ratio"] == "DECLINING"

    def test_required_keys_in_era_snap(self):
        snaps = [_era_snap(), _era_snap()]
        r     = _build_cognitive_lineage(snaps)
        assert "trajectory" in r
        assert "constitutional_health" in r["trajectory"]


# ── TestRecommendations ───────────────────────────────────────────────────────

class TestRecommendations:
    def _stab(self, score=80.0, tier="RESILIENT"):
        return {"score": score, "tier": tier}

    def _insuf_metrics(self):
        keys = ["constitutional_stability", "drift_acceleration",
                "governance_ideology_concentration", "plasticity_half_life",
                "exploration_extinction_risk", "survivability_monoculture_risk",
                "cognitive_diversity_retention", "long_horizon_replay_dependence"]
        return {k: {"score": 0.0, "tier": "INSUFFICIENT"} for k in keys}

    def test_insufficient_eras_accumulate_rec(self):
        recs = _generate_evolution_recommendations(CONSTITUTIONALLY_RESILIENT, self._insuf_metrics(), 1, self._stab())
        assert any(r["type"] == "LONG_HORIZON_READINESS" for r in recs)

    def test_lockdown_risk_critical_rec(self):
        recs = _generate_evolution_recommendations(LONG_HORIZON_LOCKDOWN_RISK, self._insuf_metrics(), 3, self._stab(20.0))
        assert any(r["priority"] == "CRITICAL" for r in recs)

    def test_exploration_extinction_critical_rec(self):
        recs = _generate_evolution_recommendations(EXPLORATION_EXTINCTION, self._insuf_metrics(), 3, self._stab(30.0))
        assert any(r["type"] == "EXPLORATION_COLLAPSE" for r in recs)

    def test_constitutionally_resilient_low_priority(self):
        recs = _generate_evolution_recommendations(CONSTITUTIONALLY_RESILIENT, self._insuf_metrics(), 3, self._stab(85.0))
        assert all(r["priority"] in ("LOW", "MEDIUM") for r in recs)

    def test_all_auto_authorized_false(self):
        for cls in (CONSTITUTIONALLY_RESILIENT, IDEOLOGICAL_RIGIDIFICATION,
                    EXPLORATION_EXTINCTION, SURVIVABILITY_MONOCULTURE,
                    ADAPTIVE_MEMORY_DECAY, LONG_HORIZON_LOCKDOWN_RISK):
            recs = _generate_evolution_recommendations(cls, self._insuf_metrics(), 3, self._stab())
            for r in recs:
                assert r["auto_authorized"] is False


# ── TestAuditEntry ─────────────────────────────────────────────────────────────

class TestAuditEntry:
    def _entry(self, cls=CONSTITUTIONALLY_RESILIENT, n_eras=3, total=200):
        return _generate_evolution_audit_entry(
            cls, {"score": 75.0, "tier": "RESILIENT"}, n_eras, total, []
        )

    def test_entry_id_starts_with_lheo(self):
        assert self._entry()["entry_id"].startswith("LHEO-")

    def test_auto_authorized_always_false(self):
        for cls in (CONSTITUTIONALLY_RESILIENT, LONG_HORIZON_LOCKDOWN_RISK):
            assert self._entry(cls)["auto_authorized"] is False

    def test_immutable_always_true(self):
        assert self._entry()["immutable"] is True

    def test_entry_type_analysis(self):
        assert self._entry()["entry_type"] == "ANALYSIS"

    def test_human_approval_required_when_eras_gte_2(self):
        assert self._entry(n_eras=2)["human_approval_required"] is True

    def test_human_approval_required_false_for_insufficient(self):
        assert self._entry(n_eras=1)["human_approval_required"] is False


# ── TestComputeStructure ───────────────────────────────────────────────────────

class TestComputeStructure:
    _REQUIRED_KEYS = {
        "scope_note", "total_trades", "eras_analyzed", "era_snapshots",
        "evolution_classification", "classification_description",
        "long_horizon_stability", "evolution_metrics", "cognitive_lineage",
        "recommendations", "evolution_hard_principles", "audit_entry",
    }

    def test_returns_dict(self):
        assert isinstance(compute_long_horizon_evolution([]), dict)

    def test_required_keys_present(self):
        r = compute_long_horizon_evolution(_trades(100))
        assert self._REQUIRED_KEYS.issubset(r.keys())

    def test_empty_trades_does_not_crash(self):
        r = compute_long_horizon_evolution([])
        assert isinstance(r, dict)

    def test_small_corpus_graceful(self):
        r = compute_long_horizon_evolution(_trades(5))
        assert r["eras_analyzed"] >= 1

    def test_large_corpus_five_eras(self):
        r = compute_long_horizon_evolution(_trades(500))
        assert r["eras_analyzed"] == 5
        assert r["total_trades"] == 500

    def test_scope_note_research_only(self):
        r = compute_long_horizon_evolution([])
        assert "research" in r.get("scope_note", "").lower() or "FTD-LHEO" in r.get("scope_note", "")

    def test_classification_valid_value(self):
        valid = {CONSTITUTIONALLY_RESILIENT, IDEOLOGICAL_RIGIDIFICATION,
                 EXPLORATION_EXTINCTION, SURVIVABILITY_MONOCULTURE,
                 ADAPTIVE_MEMORY_DECAY, LONG_HORIZON_LOCKDOWN_RISK}
        r = compute_long_horizon_evolution(_trades(100))
        assert r["evolution_classification"] in valid

    def test_hard_principles_present(self):
        r = compute_long_horizon_evolution([])
        hp = r.get("evolution_hard_principles", {})
        assert hp.get("human_authority_over_evolution") is True

    def test_audit_entry_auto_authorized_false(self):
        r = compute_long_horizon_evolution(_trades(100))
        assert r["audit_entry"]["auto_authorized"] is False

    def test_eight_evolution_metrics_present(self):
        r = compute_long_horizon_evolution(_trades(100))
        em = r.get("evolution_metrics", {})
        expected = {"constitutional_stability", "drift_acceleration",
                    "governance_ideology_concentration", "plasticity_half_life",
                    "exploration_extinction_risk", "survivability_monoculture_risk",
                    "cognitive_diversity_retention", "long_horizon_replay_dependence"}
        assert expected.issubset(em.keys())


# ── TestProductionIsolation ────────────────────────────────────────────────────

class TestProductionIsolation:
    def test_no_import_from_main(self):
        import core.evolution_observatory as m
        src = Path(m.__file__).read_text()
        assert "from main" not in src
        assert "import main" not in src

    def test_fail_open_corrupted_trades(self):
        bad = [None, "string", 42, {"entry_ts": "bad"}]
        r = compute_long_horizon_evolution(bad)
        assert isinstance(r, dict)

    def test_input_trades_not_mutated(self):
        original = _trades(40)
        copy     = [dict(t) for t in original]
        compute_long_horizon_evolution(original)
        for a, b in zip(original, copy):
            assert a == b

    def test_era_snapshots_list_of_dicts(self):
        r = compute_long_horizon_evolution(_trades(100))
        for snap in r.get("era_snapshots", []):
            assert isinstance(snap, dict)

    def test_scope_note_contains_constitution(self):
        r = compute_long_horizon_evolution(_trades(40))
        assert "constitutional" in r.get("scope_note", "").lower()


# ── TestConstitutionalPrinciples ───────────────────────────────────────────────

class TestConstitutionalPrinciples:
    def test_self_rewriting_doctrine_false(self):
        assert EVOLUTION_HARD_PRINCIPLES["self_rewriting_doctrine"] is False

    def test_autonomous_governance_evolution_false(self):
        assert EVOLUTION_HARD_PRINCIPLES["autonomous_governance_evolution"] is False

    def test_sovereign_adaptive_succession_false(self):
        assert EVOLUTION_HARD_PRINCIPLES["sovereign_adaptive_succession"] is False

    def test_human_authority_over_evolution_true(self):
        assert EVOLUTION_HARD_PRINCIPLES["human_authority_over_evolution"] is True

    def test_all_recommendations_auto_authorized_false(self):
        r = compute_long_horizon_evolution(_trades(200))
        for rec in r.get("recommendations", []):
            assert rec["auto_authorized"] is False

    def test_audit_entry_immutable_true(self):
        r = compute_long_horizon_evolution(_trades(100))
        assert r["audit_entry"]["immutable"] is True

    def test_hard_principles_recursive_mutation_false(self):
        assert EVOLUTION_HARD_PRINCIPLES["recursive_constitutional_mutation"] is False


# ── TestEdgeCases ──────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_single_trade(self):
        r = compute_long_horizon_evolution([_trade()])
        assert r["total_trades"] == 1
        assert r["eras_analyzed"] >= 1

    def test_very_large_corpus(self):
        r = compute_long_horizon_evolution(_trades(10000))
        assert r["total_trades"] == 10000
        assert r["eras_analyzed"] == 5

    def test_all_same_regime_monoculture_possible(self):
        trades = _trades(200, regime="TRENDING")
        r      = compute_long_horizon_evolution(trades)
        mc     = r["evolution_metrics"]["survivability_monoculture_risk"]
        assert mc["score"] == pytest.approx(100.0)
        assert mc["tier"] == "MONOCULTURE"

    def test_none_exploration_origin_handled(self):
        trades = [_trade(), _trade(was_exploration=True)] * 20
        for t in trades:
            if "exploration_origin" not in t:
                t["exploration_origin"] = None
        r = compute_long_horizon_evolution(trades)
        assert isinstance(r, dict)

    def test_eras_capped_at_five(self):
        r = compute_long_horizon_evolution(_trades(1000))
        assert r["eras_analyzed"] <= 5
