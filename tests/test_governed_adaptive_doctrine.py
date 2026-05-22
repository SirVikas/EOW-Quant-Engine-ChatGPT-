"""
Tests for FTD-GADD: Guarded Adaptive Deployment Doctrine & Human Override Constitution.

Covers:
  - Governance state assessment (6 states)
  - Constitutional risk diagnostics (6 metrics)
  - Constitutional classification (6 categories)
  - Constitutional stability score
  - Recommendation generation (research-only)
  - Immutable audit entry
  - Audit ledger integrity
  - Human sovereignty invariants
  - Full compute_governed_adaptive_doctrine structure
  - Production isolation (no live engine imports)
  - Edge cases and backward compatibility
"""
import sys
from typing import Optional

import pytest

from core.deployment_doctrine import (
    # State constants
    OBSERVATION_ONLY,
    SANDBOX_REPLAY,
    HUMAN_REVIEW_REQUIRED,
    GUARDED_EXPERIMENT,
    AUTO_DISABLED,
    CONSTITUTION_LOCKDOWN,
    # Classification constants
    CONSTITUTIONALLY_STABLE,
    OVERSIGHT_DEPENDENT,
    ADAPTIVE_DRIFT_RISK,
    RECOMMENDATION_OVERREACH,
    GOVERNANCE_FRAGMENTATION,
    LOCKDOWN_RECOMMENDED,
    # Constitutional objects
    HARD_PRINCIPLES,
    GOVERNANCE_STATE_DESCRIPTIONS,
    # Private helpers (imported for unit testing)
    _autonomous_drift_risk,
    _overfitting_escalation_risk,
    _governance_instability_metric,
    _human_override_integrity_metric,
    _recommendation_confidence_metric,
    _sandbox_production_divergence_metric,
    _compute_risk_diagnostics,
    _assess_governance_state,
    _classify_constitution,
    _constitutional_stability_score,
    _generate_recommendations,
    _generate_audit_entry,
    _validate_audit_integrity,
    compute_governed_adaptive_doctrine,
)


# ── State builder ─────────────────────────────────────────────────────────────

def _s(
    beneficial:          bool = False,
    opp_collapse:        bool = False,
    cog_overfit:         bool = False,
    ontol_stab:          bool = False,
    total_trades:        int  = 200,
    top_intervention:    Optional[str] = "NEGMEM_SOFT_DECAY",
    conflict_count:      int  = 0,
    consensus_reachable: bool = True,
    overfitting_score:   float = 10.0,
    overfitting_tier:    str  = "LOW",
    rsr_score:           float = 25.0,
    consensus_compound:  Optional[str] = "SOFT_NEGMEM_TF5",
    gov_classifications: Optional[dict] = None,
    cognitive_state:     str  = "HEALTHY_PLASTICITY",
    fossilization_score: int  = 20,
    drift_heatmap:       Optional[dict] = None,
    explore_ratio:       float = 0.25,
    profitable_pct:      float = 0.60,
    total_contexts:      int  = 50,
    audit_ledger:        Optional[list] = None,
) -> dict:
    if gov_classifications is None:
        gov_classifications = {p: "GOVERNANCE_STABLE" for p in [
            "ECONOMIC_MAXIMALIST", "PLASTICITY_PRESERVER",
            "SURVIVABILITY_DEFENSIVE", "ECOLOGY_BALANCED",
            "ONTOLOGY_HARMONIZER", "ADAPTIVE_GENERALIST",
        ]}
    if drift_heatmap is None:
        drift_heatmap = {"drift_rl_negmem": {"score": 10.0, "tier": "LOW"}}
    return {
        "counterfactual": {
            "beneficial_adaptation_detected":  beneficial,
            "opportunity_collapse_detected":   opp_collapse,
            "cognitive_overfitting_detected":  cog_overfit,
            "ontology_stabilization_detected": ontol_stab,
            "total_trades":                    total_trades,
            "top_intervention":                top_intervention,
        },
        "governance": {
            "conflict_analysis": {
                "conflict_count":    conflict_count,
                "consensus_reachable": consensus_reachable,
            },
            "overfitting_risk":              {"score": overfitting_score, "tier": overfitting_tier},
            "regime_specialization_risk":    {"score": rsr_score, "tier": "LOW"},
            "governance_classifications":    gov_classifications,
            "consensus_compound":            consensus_compound,
        },
        "memory_pressure": {
            "cognitive_state": cognitive_state,
            "memory_pressure": {
                "fossilization_risk": {"score": fossilization_score, "tier": "LOW"},
            },
            "drift_heatmap": drift_heatmap,
        },
        "rl": {
            "explore_ratio":  explore_ratio,
            "profitable_pct": profitable_pct,
            "total_contexts": total_contexts,
        },
        "audit_ledger": audit_ledger if audit_ledger is not None else [],
    }


def _risk_diag(state: Optional[dict] = None) -> dict:
    s = state or _s()
    return _compute_risk_diagnostics(s, s.get("audit_ledger", []))


def _valid_audit_entry() -> dict:
    return {
        "entry_id":    "GADD-1234567890-abcdef01",
        "timestamp_ms": 1234567890000,
        "auto_authorized": False,
        "immutable":   True,
    }


# ══════════════════════════════════════════════════════════════════════════════
# TestGovernanceStateAssessment
# ══════════════════════════════════════════════════════════════════════════════

class TestGovernanceStateAssessment:

    def test_default_is_observation_only(self):
        # 30 trades → confidence below GUARDED threshold → OBSERVATION_ONLY
        s  = _s(total_trades=30)
        rd = _risk_diag(s)
        state = _assess_governance_state(rd, {}, "HEALTHY_PLASTICITY", 0)
        assert state == OBSERVATION_ONLY

    def test_cog_overfit_and_opp_collapse_is_auto_disabled(self):
        rd = _risk_diag(_s(cog_overfit=True, opp_collapse=True))
        state = _assess_governance_state(
            rd, {"cognitive_overfitting_detected": True, "opportunity_collapse_detected": True},
            "HEALTHY_PLASTICITY", 0,
        )
        assert state == AUTO_DISABLED

    def test_high_drift_risk_is_constitution_lockdown(self):
        # Construct high fossilization + zero explore → high autonomous drift risk
        s = _s(fossilization_score=95, explore_ratio=0.0,
               drift_heatmap={"drift_rl_negmem": {"score": 80.0, "tier": "HIGH"}})
        rd = _compute_risk_diagnostics(s, [])
        # Force drift risk high enough
        rd["autonomous_drift_risk"] = {"score": 85.0, "tier": "HIGH"}
        state = _assess_governance_state(rd, {}, "PREMATURE_FOSSILIZATION", 0)
        assert state == CONSTITUTION_LOCKDOWN

    def test_high_governance_instability_is_constitution_lockdown(self):
        rd = _risk_diag()
        rd["governance_instability"] = {"score": 85.0, "tier": "HIGH"}
        state = _assess_governance_state(rd, {}, "HEALTHY_PLASTICITY", 3)
        assert state == CONSTITUTION_LOCKDOWN

    def test_beneficial_adaptation_is_human_review_required(self):
        rd = _risk_diag(_s(beneficial=True))
        state = _assess_governance_state(
            rd, {"beneficial_adaptation_detected": True}, "HEALTHY_PLASTICITY", 0,
        )
        assert state == HUMAN_REVIEW_REQUIRED

    def test_memory_saturation_is_human_review_required(self):
        rd = _risk_diag(_s(cognitive_state="MEMORY_SATURATION"))
        state = _assess_governance_state(rd, {}, "MEMORY_SATURATION", 0)
        assert state == HUMAN_REVIEW_REQUIRED

    def test_governance_conflict_is_sandbox_replay(self):
        rd = _risk_diag(_s(conflict_count=1))
        state = _assess_governance_state(rd, {}, "HEALTHY_PLASTICITY", 1)
        assert state == SANDBOX_REPLAY

    def test_high_confidence_no_conflicts_is_guarded_experiment(self):
        s = _s(total_trades=600, conflict_count=0)
        rd = _compute_risk_diagnostics(s, [])
        # Ensure drift risk is low
        rd["autonomous_drift_risk"] = {"score": 5.0, "tier": "MINIMAL"}
        state = _assess_governance_state(rd, {}, "HEALTHY_PLASTICITY", 0)
        assert state == GUARDED_EXPERIMENT


# ══════════════════════════════════════════════════════════════════════════════
# TestRiskDiagnostics
# ══════════════════════════════════════════════════════════════════════════════

class TestRiskDiagnostics:

    def test_six_metrics_in_diagnostics(self):
        rd = _risk_diag()
        expected = {
            "autonomous_drift_risk", "overfitting_escalation_risk",
            "governance_instability", "human_override_integrity",
            "recommendation_confidence", "sandbox_production_divergence",
        }
        assert set(rd.keys()) == expected

    def test_all_scores_in_range(self):
        rd = _risk_diag()
        for name, data in rd.items():
            score = data.get("score", 0)
            assert 0.0 <= score <= 100.0, f"{name} score {score} out of range"

    def test_all_tiers_valid_strings(self):
        valid_tiers = {
            "HIGH", "MODERATE", "LOW", "MINIMAL",
            "INTACT", "ADEQUATE", "DEGRADED", "COMPROMISED",
            "INSUFFICIENT",
        }
        rd = _risk_diag()
        for name, data in rd.items():
            tier = data.get("tier", "")
            assert tier in valid_tiers, f"{name} has invalid tier {tier}"

    def test_high_fossilization_increases_drift_risk(self):
        low_fossil  = _autonomous_drift_risk(_s(fossilization_score=10))
        high_fossil = _autonomous_drift_risk(_s(fossilization_score=90))
        assert high_fossil["score"] > low_fossil["score"]

    def test_opp_collapse_amplifies_overfitting_risk(self):
        without_collapse = _overfitting_escalation_risk(_s(overfitting_score=30, opp_collapse=False))
        with_collapse    = _overfitting_escalation_risk(_s(overfitting_score=30, opp_collapse=True))
        assert with_collapse["score"] > without_collapse["score"]

    def test_three_conflicts_raises_governance_instability(self):
        low_conf  = _governance_instability_metric(_s(conflict_count=0))
        high_conf = _governance_instability_metric(_s(conflict_count=3))
        assert high_conf["score"] > low_conf["score"]

    def test_large_corpus_gives_high_confidence(self):
        r = _recommendation_confidence_metric(_s(total_trades=600))
        assert r["score"] >= 75.0
        assert r["tier"] == "HIGH"


# ══════════════════════════════════════════════════════════════════════════════
# TestConstitutionalClassification
# ══════════════════════════════════════════════════════════════════════════════

class TestConstitutionalClassification:

    def test_auto_disabled_gives_lockdown_recommended(self):
        rd = _risk_diag()
        cls = _classify_constitution(AUTO_DISABLED, rd, 0)
        assert cls == LOCKDOWN_RECOMMENDED

    def test_constitution_lockdown_gives_lockdown_recommended(self):
        rd = _risk_diag()
        cls = _classify_constitution(CONSTITUTION_LOCKDOWN, rd, 0)
        assert cls == LOCKDOWN_RECOMMENDED

    def test_three_conflicts_gives_governance_fragmentation(self):
        rd = _risk_diag()
        cls = _classify_constitution(SANDBOX_REPLAY, rd, 3)
        assert cls == GOVERNANCE_FRAGMENTATION

    def test_high_drift_risk_gives_adaptive_drift_risk(self):
        rd = _risk_diag()
        rd["autonomous_drift_risk"] = {"score": 75.0, "tier": "HIGH"}
        cls = _classify_constitution(SANDBOX_REPLAY, rd, 0)
        assert cls == ADAPTIVE_DRIFT_RISK

    def test_high_overfit_low_confidence_gives_recommendation_overreach(self):
        rd = _risk_diag(_s(total_trades=10, overfitting_score=70.0))
        rd["overfitting_escalation_risk"] = {"score": 65.0, "tier": "HIGH"}
        rd["recommendation_confidence"]   = {"score": 10.0, "tier": "INSUFFICIENT"}
        cls = _classify_constitution(HUMAN_REVIEW_REQUIRED, rd, 0)
        assert cls == RECOMMENDATION_OVERREACH

    def test_moderate_instability_gives_oversight_dependent(self):
        rd = _risk_diag()
        rd["governance_instability"] = {"score": 55.0, "tier": "MODERATE"}
        cls = _classify_constitution(SANDBOX_REPLAY, rd, 0)
        assert cls == OVERSIGHT_DEPENDENT

    def test_clean_state_gives_constitutionally_stable(self):
        rd = _risk_diag(_s())
        cls = _classify_constitution(OBSERVATION_ONLY, rd, 0)
        assert cls == CONSTITUTIONALLY_STABLE


# ══════════════════════════════════════════════════════════════════════════════
# TestStabilityScore
# ══════════════════════════════════════════════════════════════════════════════

class TestStabilityScore:

    def test_clean_state_scores_high(self):
        rd = _risk_diag(_s())
        r = _constitutional_stability_score(rd, OBSERVATION_ONLY)
        assert r["score"] >= 70.0

    def test_auto_disabled_scores_low(self):
        rd = _risk_diag()
        for k in rd:
            rd[k] = {"score": 80.0, "tier": "HIGH"}
        r = _constitutional_stability_score(rd, AUTO_DISABLED)
        assert r["score"] < 50.0

    def test_score_in_range(self):
        rd = _risk_diag(_s())
        r = _constitutional_stability_score(rd, OBSERVATION_ONLY)
        assert 0.0 <= r["score"] <= 100.0

    def test_tier_is_valid(self):
        rd = _risk_diag(_s())
        r = _constitutional_stability_score(rd, OBSERVATION_ONLY)
        assert r["tier"] in ("STRONG", "ADEQUATE", "WEAKENED", "CRITICAL")

    def test_more_risk_lowers_score(self):
        rd_clean = _risk_diag(_s())
        rd_risky = _risk_diag(_s(
            fossilization_score=80, conflict_count=3,
            overfitting_score=70.0, overfitting_tier="HIGH",
        ))
        r_clean = _constitutional_stability_score(rd_clean, OBSERVATION_ONLY)
        r_risky = _constitutional_stability_score(rd_risky, HUMAN_REVIEW_REQUIRED)
        assert r_clean["score"] > r_risky["score"]


# ══════════════════════════════════════════════════════════════════════════════
# TestRecommendationGeneration
# ══════════════════════════════════════════════════════════════════════════════

class TestRecommendationGeneration:

    def test_cognitive_overfit_generates_warning(self):
        recs = _generate_recommendations(_s(cog_overfit=True), HUMAN_REVIEW_REQUIRED)
        types = [r["type"] for r in recs]
        assert "COGNITIVE_OVERFITTING_WARNING" in types

    def test_opp_collapse_generates_warning(self):
        recs = _generate_recommendations(_s(opp_collapse=True), SANDBOX_REPLAY)
        types = [r["type"] for r in recs]
        assert "OPPORTUNITY_COLLAPSE_WARNING" in types

    def test_beneficial_adaptation_generates_identification(self):
        recs = _generate_recommendations(_s(beneficial=True), HUMAN_REVIEW_REQUIRED)
        types = [r["type"] for r in recs]
        assert "BENEFICIAL_INTERVENTION_IDENTIFIED" in types

    def test_governance_conflicts_generate_conflict_rec(self):
        recs = _generate_recommendations(_s(conflict_count=2), SANDBOX_REPLAY)
        types = [r["type"] for r in recs]
        assert "GOVERNANCE_CONFLICT_DETECTED" in types

    def test_memory_saturation_generates_alert(self):
        recs = _generate_recommendations(_s(cognitive_state="MEMORY_SATURATION"), HUMAN_REVIEW_REQUIRED)
        types = [r["type"] for r in recs]
        assert "MEMORY_SATURATION_ALERT" in types

    def test_all_recs_have_auto_authorized_false(self):
        recs = _generate_recommendations(_s(
            cog_overfit=True, opp_collapse=True, beneficial=True,
            conflict_count=2, cognitive_state="MEMORY_SATURATION",
        ), AUTO_DISABLED)
        for rec in recs:
            assert rec["auto_authorized"] is False, f"rec {rec['type']} has auto_authorized=True"

    def test_clean_state_generates_health_affirmation(self):
        recs = _generate_recommendations(_s(consensus_compound=None), OBSERVATION_ONLY)
        # consensus_compound=None skips the consensus rec; clean state → affirmation
        clean_s = _s(consensus_compound=None)
        clean_s["governance"]["consensus_compound"] = None
        recs = _generate_recommendations(clean_s, OBSERVATION_ONLY)
        types = [r["type"] for r in recs]
        assert "CONSTITUTIONAL_HEALTH_AFFIRMATION" in types


# ══════════════════════════════════════════════════════════════════════════════
# TestAuditEntry
# ══════════════════════════════════════════════════════════════════════════════

class TestAuditEntry:

    def _entry(self, governance_state: str = OBSERVATION_ONLY) -> dict:
        rd = _risk_diag()
        recs = _generate_recommendations(_s(), governance_state)
        return _generate_audit_entry(governance_state, CONSTITUTIONALLY_STABLE, rd, recs)

    def test_required_keys_present(self):
        entry = self._entry()
        for k in (
            "entry_id", "timestamp_ms", "governance_state",
            "constitutional_classification", "risk_summary",
            "recommendations_generated", "human_approval_required",
            "auto_authorized", "immutable",
        ):
            assert k in entry, f"Missing audit entry key: {k}"

    def test_auto_authorized_always_false(self):
        for state in (OBSERVATION_ONLY, HUMAN_REVIEW_REQUIRED, AUTO_DISABLED, CONSTITUTION_LOCKDOWN):
            entry = self._entry(state)
            assert entry["auto_authorized"] is False, f"auto_authorized=True for state {state}"

    def test_immutable_always_true(self):
        entry = self._entry()
        assert entry["immutable"] is True

    def test_entry_id_starts_with_gadd(self):
        entry = self._entry()
        assert entry["entry_id"].startswith("GADD-")

    def test_two_entries_have_different_ids(self):
        import time
        e1 = self._entry()
        time.sleep(0.01)
        e2 = self._entry()
        assert e1["entry_id"] != e2["entry_id"]

    def test_observation_only_does_not_require_human_approval(self):
        entry = self._entry(OBSERVATION_ONLY)
        assert entry["human_approval_required"] is False

    def test_non_observation_state_requires_human_approval(self):
        for state in (SANDBOX_REPLAY, HUMAN_REVIEW_REQUIRED, GUARDED_EXPERIMENT, AUTO_DISABLED, CONSTITUTION_LOCKDOWN):
            entry = self._entry(state)
            assert entry["human_approval_required"] is True, f"human_approval_required=False for {state}"


# ══════════════════════════════════════════════════════════════════════════════
# TestAuditIntegrity
# ══════════════════════════════════════════════════════════════════════════════

class TestAuditIntegrity:

    def test_empty_ledger_integrity_is_empty(self):
        r = _validate_audit_integrity([])
        assert r["integrity"] == "EMPTY"
        assert r["depth"] == 0

    def test_valid_ledger_is_intact(self):
        ledger = [_valid_audit_entry(), _valid_audit_entry()]
        r = _validate_audit_integrity(ledger)
        assert r["integrity"] == "INTACT"
        assert r["autonomous_actions"] == 0

    def test_autonomous_action_violation_detected(self):
        bad_entry = dict(_valid_audit_entry())
        bad_entry["auto_authorized"] = True
        ledger = [_valid_audit_entry(), bad_entry]
        r = _validate_audit_integrity(ledger)
        assert r["integrity"] == "VIOLATED"
        assert r["autonomous_actions"] >= 1
        assert len(r["violations"]) >= 1

    def test_depth_matches_ledger_size(self):
        ledger = [_valid_audit_entry() for _ in range(5)]
        r = _validate_audit_integrity(ledger)
        assert r["depth"] == 5

    def test_oldest_and_latest_entry_ids_present(self):
        e1 = dict(_valid_audit_entry()); e1["entry_id"] = "GADD-1000-aaaa"
        e2 = dict(_valid_audit_entry()); e2["entry_id"] = "GADD-2000-bbbb"
        r = _validate_audit_integrity([e1, e2])
        assert r["oldest_entry_id"] == "GADD-1000-aaaa"
        assert r["latest_entry_id"] == "GADD-2000-bbbb"


# ══════════════════════════════════════════════════════════════════════════════
# TestHumanSovereigntyInvariants
# ══════════════════════════════════════════════════════════════════════════════

class TestHumanSovereigntyInvariants:

    def test_self_authorization_impossible(self):
        assert HARD_PRINCIPLES["self_authorization_possible"] is False

    def test_autonomous_deployment_impossible(self):
        assert HARD_PRINCIPLES["autonomous_deployment_possible"] is False

    def test_human_supremacy_required(self):
        assert HARD_PRINCIPLES["human_supremacy"] is True

    def test_compute_output_has_hard_principles(self):
        r = compute_governed_adaptive_doctrine(_s())
        hp = r.get("human_override_constitution", {})
        assert hp.get("self_authorization_possible") is False
        assert hp.get("autonomous_deployment_possible") is False
        assert hp.get("human_supremacy") is True

    def test_all_recs_in_full_output_are_non_autonomous(self):
        r = compute_governed_adaptive_doctrine(_s(
            cog_overfit=True, opp_collapse=True, beneficial=True, conflict_count=2,
        ))
        for rec in r.get("recommendations", []):
            assert rec["auto_authorized"] is False

    def test_audit_entry_in_output_is_non_autonomous(self):
        r = compute_governed_adaptive_doctrine(_s())
        assert r["audit_entry"]["auto_authorized"] is False

    def test_recursive_self_governance_impossible(self):
        assert HARD_PRINCIPLES["recursive_self_governance"] is False


# ══════════════════════════════════════════════════════════════════════════════
# TestComputeStructure
# ══════════════════════════════════════════════════════════════════════════════

class TestComputeStructure:

    def _r(self) -> dict:
        return compute_governed_adaptive_doctrine(_s())

    def test_all_top_level_keys_present(self):
        r = self._r()
        for k in (
            "scope_note", "governance_state", "governance_state_description",
            "constitutional_classification", "constitutional_stability",
            "risk_diagnostics", "recommendations", "human_override_constitution",
            "audit_entry", "audit_ledger_depth", "audit_ledger_integrity",
        ):
            assert k in r, f"Missing key: {k}"

    def test_scope_note_mentions_gadd(self):
        r = self._r()
        assert "FTD-GADD" in r["scope_note"]

    def test_governance_state_is_valid(self):
        valid = {
            OBSERVATION_ONLY, SANDBOX_REPLAY, HUMAN_REVIEW_REQUIRED,
            GUARDED_EXPERIMENT, AUTO_DISABLED, CONSTITUTION_LOCKDOWN,
        }
        assert self._r()["governance_state"] in valid

    def test_constitutional_classification_is_valid(self):
        valid = {
            CONSTITUTIONALLY_STABLE, OVERSIGHT_DEPENDENT, ADAPTIVE_DRIFT_RISK,
            RECOMMENDATION_OVERREACH, GOVERNANCE_FRAGMENTATION, LOCKDOWN_RECOMMENDED,
        }
        assert self._r()["constitutional_classification"] in valid

    def test_constitutional_stability_has_score_and_tier(self):
        cs = self._r()["constitutional_stability"]
        assert "score" in cs and "tier" in cs
        assert 0.0 <= cs["score"] <= 100.0

    def test_risk_diagnostics_has_six_metrics(self):
        rd = self._r()["risk_diagnostics"]
        assert len(rd) == 6

    def test_recommendations_is_list(self):
        assert isinstance(self._r()["recommendations"], list)

    def test_audit_entry_is_dict_with_entry_id(self):
        ae = self._r()["audit_entry"]
        assert isinstance(ae, dict)
        assert "entry_id" in ae

    def test_no_error_key_on_valid_input(self):
        assert "error" not in self._r()

    def test_governance_state_description_is_non_empty(self):
        r = self._r()
        assert len(r["governance_state_description"]) > 0


# ══════════════════════════════════════════════════════════════════════════════
# TestProductionIsolation
# ══════════════════════════════════════════════════════════════════════════════

class TestProductionIsolation:

    def test_module_has_no_main_import(self):
        import core.deployment_doctrine as dd
        src = __import__("inspect").getsource(dd)
        assert "import main" not in src
        assert "from main" not in src

    def test_module_has_no_pnl_calc(self):
        import core.deployment_doctrine as dd
        src = __import__("inspect").getsource(dd)
        assert "pnl_calc" not in src

    def test_module_has_no_rl_engine(self):
        import core.deployment_doctrine as dd
        src = __import__("inspect").getsource(dd)
        assert "rl_engine" not in src

    def test_module_has_no_data_lake(self):
        import core.deployment_doctrine as dd
        src = __import__("inspect").getsource(dd)
        assert "data_lake" not in src

    def test_compute_never_raises_on_any_input(self):
        compute_governed_adaptive_doctrine(None)
        compute_governed_adaptive_doctrine({})
        compute_governed_adaptive_doctrine({"garbage": [1, 2, 3]})
        compute_governed_adaptive_doctrine(_s())

    def test_input_not_mutated(self):
        s = _s()
        original_trades = s["counterfactual"]["total_trades"]
        compute_governed_adaptive_doctrine(s)
        assert s["counterfactual"]["total_trades"] == original_trades


# ══════════════════════════════════════════════════════════════════════════════
# TestEdgeCases
# ══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:

    def test_none_input_returns_valid_dict(self):
        r = compute_governed_adaptive_doctrine(None)
        assert isinstance(r, dict)
        assert "scope_note" in r

    def test_empty_dict_returns_valid_dict(self):
        r = compute_governed_adaptive_doctrine({})
        assert isinstance(r, dict)
        assert "governance_state" in r

    def test_all_flags_true_is_auto_disabled(self):
        r = compute_governed_adaptive_doctrine(_s(
            cog_overfit=True, opp_collapse=True, beneficial=True,
            conflict_count=3,
        ))
        assert r["governance_state"] == AUTO_DISABLED

    def test_zero_trades_has_low_recommendation_confidence(self):
        s = _s(total_trades=0)
        r = compute_governed_adaptive_doctrine(s)
        rc = r["risk_diagnostics"]["recommendation_confidence"]
        assert rc["score"] <= 25.0


# ══════════════════════════════════════════════════════════════════════════════
# TestBackwardCompatibility
# ══════════════════════════════════════════════════════════════════════════════

class TestBackwardCompatibility:

    def test_missing_counterfactual_key(self):
        s = _s()
        del s["counterfactual"]
        r = compute_governed_adaptive_doctrine(s)
        assert isinstance(r, dict)
        assert "error" not in r

    def test_none_values_in_state(self):
        s = {
            "counterfactual":  None,
            "governance":      None,
            "memory_pressure": None,
            "rl":              None,
            "audit_ledger":    None,
        }
        r = compute_governed_adaptive_doctrine(s)
        assert isinstance(r, dict)
        assert "governance_state" in r

    def test_extra_unknown_keys_ignored(self):
        s = _s()
        s["unknown_future_key"] = {"some": "data"}
        r = compute_governed_adaptive_doctrine(s)
        assert "error" not in r

    def test_audit_ledger_none_treated_as_empty(self):
        s = _s()
        s["audit_ledger"] = None
        r = compute_governed_adaptive_doctrine(s)
        assert r["audit_ledger_depth"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# TestGovernanceStateDescriptions
# ══════════════════════════════════════════════════════════════════════════════

class TestGovernanceStateDescriptions:

    def test_all_six_states_have_descriptions(self):
        for state in (
            OBSERVATION_ONLY, SANDBOX_REPLAY, HUMAN_REVIEW_REQUIRED,
            GUARDED_EXPERIMENT, AUTO_DISABLED, CONSTITUTION_LOCKDOWN,
        ):
            assert state in GOVERNANCE_STATE_DESCRIPTIONS
            assert len(GOVERNANCE_STATE_DESCRIPTIONS[state]) > 0

    def test_hard_principles_has_eleven_keys(self):
        assert len(HARD_PRINCIPLES) == 11

    def test_negative_principles_are_false(self):
        for key in ("self_authorization_possible", "autonomous_deployment_possible",
                    "recursive_self_governance", "self_persisting_adaptation"):
            assert HARD_PRINCIPLES[key] is False

    def test_positive_principles_are_true(self):
        for key in ("human_supremacy", "explicit_approval_required", "rollback_capable",
                    "audit_history_immutable", "policy_transparent",
                    "sandbox_first_doctrine", "production_isolation"):
            assert HARD_PRINCIPLES[key] is True
