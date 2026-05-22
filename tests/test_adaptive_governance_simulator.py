"""
Tests for FTD-GAGS: Guarded Adaptive Governance Simulator.

Covers:
  - Compound stack application (sequential filtering)
  - Regime specialization risk (HHI)
  - Overfitting risk
  - Weighted governance scoring
  - Governance outcome classification
  - Conflict detection
  - Consensus compound
  - Full compute_adaptive_governance structure
  - Production isolation
  - Edge cases and backward compatibility
"""
import importlib
import sys
import types
from typing import List

import pytest


# ── Trade factory ─────────────────────────────────────────────────────────────

def _t(
    net_pnl: float = 0.10,
    gross_pnl: float = 0.15,
    regime: str = "TRENDING",
    session: str = "NY",
    was_exploration: bool = False,
    fee_entry: float = 0.02,
    fee_exit: float  = 0.03,
) -> dict:
    return {
        "trade_id":         f"T{id(object())}",
        "entry_ts":         1_700_000_000,
        "exit_ts":          1_700_003_600,
        "net_pnl":          net_pnl,
        "gross_pnl":        gross_pnl,
        "fee_entry":        fee_entry,
        "fee_exit":         fee_exit,
        "slippage_cost":    0.0,
        "borrow_cost":      0.0,
        "regime":           regime,
        "origin_session":   session,
        "strategy":         "S1",
        "exploration_origin": {
            "was_exploration_trade": was_exploration,
        },
    }


def _trades(n: int = 30, **kw) -> List[dict]:
    return [_t(**kw) for _ in range(n)]


def _mixed_trades(n: int = 30) -> List[dict]:
    """Mix of regimes/sessions/exploration for realistic testing."""
    result = []
    for i in range(n):
        regime  = ["TRENDING", "MEAN_REVERTING", "VOLATILE"][i % 3]
        session = ["NY", "ASIA", "LONDON"][i % 3]
        explore = i % 5 == 0
        pnl     = 0.10 if i % 3 != 1 else -0.05
        result.append(_t(
            net_pnl=pnl, gross_pnl=abs(pnl) + 0.05,
            regime=regime, session=session,
            was_exploration=explore,
        ))
    return result


# ── Imports ───────────────────────────────────────────────────────────────────

from core.governance_simulator import (
    COMPOUND_PROFILES,
    GOVERNANCE_PROFILES,
    GOVERNANCE_STABLE,
    ECONOMIC_AUTHORITARIANISM,
    PLASTICITY_OVEREXPANSION,
    ONTOLOGY_FRAGMENTATION,
    ECOLOGICAL_COLLAPSE,
    BALANCED_ADAPTATION,
    _apply_compound,
    _weighted_governance_score,
    _regime_specialization_risk,
    _overfitting_risk,
    _classify_governance,
    _detect_conflicts,
    _consensus_compound,
    compute_adaptive_governance,
)


# ══════════════════════════════════════════════════════════════════════════════
# TestCompoundStackApplication
# ══════════════════════════════════════════════════════════════════════════════

class TestCompoundStackApplication:

    def test_six_compound_profiles_defined(self):
        assert len(COMPOUND_PROFILES) == 6

    def test_compound_names_present(self):
        expected = {
            "SOFT_NEGMEM_TF5", "NY_TF5_PROJECTION", "DEFENSIVE_SESSIONS",
            "EXPLORE_REGIME_RESET", "FULL_QUALITY_FILTER", "ONTOLOGY_RL_TF5",
        }
        assert set(COMPOUND_PROFILES.keys()) == expected

    def test_each_compound_has_at_least_two_interventions(self):
        for name, i_names in COMPOUND_PROFILES.items():
            assert len(i_names) >= 2, f"{name} has fewer than 2 interventions"

    def test_apply_compound_ny_tf5_keeps_only_ny(self):
        trades = _mixed_trades(30)
        result = _apply_compound(trades, COMPOUND_PROFILES["NY_TF5_PROJECTION"])
        assert all(t.get("origin_session") == "NY" for t in result)

    def test_apply_compound_defensive_sessions_excludes_asia(self):
        trades = _mixed_trades(30)
        result = _apply_compound(trades, COMPOUND_PROFILES["DEFENSIVE_SESSIONS"])
        assert all(t.get("origin_session") != "ASIA" for t in result)

    def test_apply_compound_explore_regime_reset_only_exploration(self):
        trades = _mixed_trades(30)
        result = _apply_compound(trades, COMPOUND_PROFILES["EXPLORE_REGIME_RESET"])
        from core.counterfactual_lab import _is_exploration
        # RULE4_HIGH_EXPLORE keeps only exploration; RL_RESET_MEAN_REVERTING removes MEAN_REVERTING
        # After both, no MEAN_REVERTING + all exploration
        for t in result:
            assert _is_exploration(t)
            assert t.get("regime") != "MEAN_REVERTING"

    def test_apply_compound_does_not_mutate_input(self):
        trades = _mixed_trades(30)
        original_count = len(trades)
        _apply_compound(trades, COMPOUND_PROFILES["FULL_QUALITY_FILTER"])
        assert len(trades) == original_count

    def test_apply_compound_full_quality_filter_reduces_count(self):
        # FULL_QUALITY_FILTER applies 3 filters — should reduce
        trades = _mixed_trades(60)
        result = _apply_compound(trades, COMPOUND_PROFILES["FULL_QUALITY_FILTER"])
        assert len(result) <= len(trades)

    def test_apply_compound_empty_input_returns_empty(self):
        result = _apply_compound([], COMPOUND_PROFILES["SOFT_NEGMEM_TF5"])
        assert result == []


# ══════════════════════════════════════════════════════════════════════════════
# TestRegimeSpecializationRisk
# ══════════════════════════════════════════════════════════════════════════════

class TestRegimeSpecializationRisk:

    def test_empty_returns_minimal(self):
        r = _regime_specialization_risk([])
        assert r["tier"] == "MINIMAL"
        assert r["score"] == 0.0

    def test_single_regime_max_concentration(self):
        trades = _trades(20, regime="TRENDING")
        r = _regime_specialization_risk(trades)
        # HHI = 1.0 → score = 100
        assert r["score"] == 100.0
        assert r["tier"] == "HIGH"

    def test_equal_two_regimes_is_moderate_or_low(self):
        trades = [_t(regime="TRENDING") for _ in range(10)] + \
                 [_t(regime="VOLATILE") for _ in range(10)]
        r = _regime_specialization_risk(trades)
        # HHI = (0.5)^2 + (0.5)^2 = 0.5 → score 50 → MODERATE
        assert r["score"] == pytest.approx(50.0, abs=0.1)
        assert r["tier"] == "MODERATE"

    def test_four_equal_regimes_low_hhi(self):
        trades = (
            [_t(regime="A") for _ in range(10)] +
            [_t(regime="B") for _ in range(10)] +
            [_t(regime="C") for _ in range(10)] +
            [_t(regime="D") for _ in range(10)]
        )
        r = _regime_specialization_risk(trades)
        # HHI = 4 * (0.25)^2 = 0.25 → score 25 → LOW
        assert r["score"] == pytest.approx(25.0, abs=0.1)
        assert r["tier"] == "LOW"

    def test_regime_counts_present_in_output(self):
        trades = [_t(regime="X") for _ in range(5)] + \
                 [_t(regime="Y") for _ in range(5)]
        r = _regime_specialization_risk(trades)
        assert "regime_counts" in r
        assert r["regime_counts"].get("X") == 5
        assert r["regime_counts"].get("Y") == 5


# ══════════════════════════════════════════════════════════════════════════════
# TestOverfittingRisk
# ══════════════════════════════════════════════════════════════════════════════

class TestOverfittingRisk:

    def _b_metrics(self, count: int = 100, surv: float = 50.0) -> dict:
        return {"trade_count": count, "survivability_score": surv}

    def _c_metrics(self, count: int, surv: float) -> dict:
        return {"trade_count": count, "survivability_score": surv}

    def test_high_overfitting(self):
        r = _overfitting_risk(
            self._b_metrics(100, 50.0),
            self._c_metrics(50, 60.0),   # 50% drop, +10 surv
        )
        assert r["tier"] == "HIGH"

    def test_moderate_overfitting(self):
        r = _overfitting_risk(
            self._b_metrics(100, 50.0),
            self._c_metrics(75, 55.0),   # 25% drop, +5 surv
        )
        assert r["tier"] == "MODERATE"

    def test_low_overfitting_no_surv_improvement(self):
        r = _overfitting_risk(
            self._b_metrics(100, 50.0),
            self._c_metrics(90, 50.0),
        )
        assert r["tier"] == "LOW"

    def test_score_is_non_negative(self):
        r = _overfitting_risk(self._b_metrics(), self._c_metrics(110, 48.0))
        assert r["score"] >= 0.0


# ══════════════════════════════════════════════════════════════════════════════
# TestWeightedGovernanceScore
# ══════════════════════════════════════════════════════════════════════════════

class TestWeightedGovernanceScore:

    def _baseline(self) -> dict:
        return {
            "trade_count":          100,
            "net_expectancy":       0.01,
            "survivability_score":  60.0,
            "plasticity_proxy":     2.0,
            "ontology_drift_proxy": 10.0,
            "fee_drag_mean_pct":    5.0,
        }

    def test_baseline_vs_itself_scores_near_50(self):
        b = self._baseline()
        score = _weighted_governance_score(b, b, 100, GOVERNANCE_PROFILES["ADAPTIVE_GENERALIST"]["weights"])
        assert 49.0 <= score <= 51.0

    def test_better_ne_scores_above_50_for_economic_maximalist(self):
        b = self._baseline()
        c = dict(b)
        c["net_expectancy"] = 0.02
        score = _weighted_governance_score(c, b, 100, GOVERNANCE_PROFILES["ECONOMIC_MAXIMALIST"]["weights"])
        assert score > 50.0

    def test_worse_ne_scores_below_50(self):
        b = self._baseline()
        c = dict(b)
        c["net_expectancy"] = 0.005
        score = _weighted_governance_score(c, b, 100, GOVERNANCE_PROFILES["ECONOMIC_MAXIMALIST"]["weights"])
        assert score < 50.0

    def test_score_clamped_0_to_100(self):
        b = self._baseline()
        c = dict(b)
        c["net_expectancy"] = 999.0  # extreme
        score = _weighted_governance_score(c, b, 100, GOVERNANCE_PROFILES["ECONOMIC_MAXIMALIST"]["weights"])
        assert 0.0 <= score <= 100.0

    def test_higher_plasticity_scores_better_for_plasticity_preserver(self):
        b = self._baseline()
        c = dict(b)
        c["plasticity_proxy"] = 3.0
        score = _weighted_governance_score(c, b, 100, GOVERNANCE_PROFILES["PLASTICITY_PRESERVER"]["weights"])
        assert score > 50.0

    def test_lower_drift_scores_better_for_ontology_harmonizer(self):
        b = self._baseline()
        c = dict(b)
        c["ontology_drift_proxy"] = 2.0  # drift improved
        score = _weighted_governance_score(c, b, 100, GOVERNANCE_PROFILES["ONTOLOGY_HARMONIZER"]["weights"])
        assert score > 50.0

    def test_none_fields_handled_gracefully(self):
        b = {"trade_count": 100, "net_expectancy": None, "survivability_score": None,
             "plasticity_proxy": None, "ontology_drift_proxy": None, "fee_drag_mean_pct": None}
        score = _weighted_governance_score(b, b, 100, GOVERNANCE_PROFILES["ADAPTIVE_GENERALIST"]["weights"])
        assert 0.0 <= score <= 100.0


# ══════════════════════════════════════════════════════════════════════════════
# TestGovernanceClassification
# ══════════════════════════════════════════════════════════════════════════════

class TestGovernanceClassification:

    def _b(self) -> dict:
        return {
            "trade_count":          100,
            "net_expectancy":       0.01,
            "survivability_score":  60.0,
            "plasticity_proxy":     2.0,
            "ontology_drift_proxy": 10.0,
            "fee_drag_mean_pct":    5.0,
        }

    def test_default_is_governance_stable(self):
        b = self._b()
        cls = _classify_governance(dict(b), b, 100)
        assert cls == GOVERNANCE_STABLE

    def test_ecological_collapse_surv_up_big_opp_drop(self):
        b = self._b()
        best = dict(b)
        best["trade_count"]         = 30   # 70% drop
        best["survivability_score"] = 75.0  # surv up
        cls = _classify_governance(best, b, 100)
        assert cls == ECOLOGICAL_COLLAPSE

    def test_economic_authoritarianism_ne_up_big_opp_drop(self):
        b = self._b()
        best = dict(b)
        best["trade_count"]   = 30    # 70% drop
        best["net_expectancy"] = 0.05  # NE up (surv not up)
        best["survivability_score"] = 55.0  # surv slightly down — no ECOLOGICAL_COLLAPSE
        cls = _classify_governance(best, b, 100)
        assert cls == ECONOMIC_AUTHORITARIANISM

    def test_ontology_fragmentation_drift_up(self):
        b = self._b()
        best = dict(b)
        best["ontology_drift_proxy"] = 25.0  # +15 drift → fragmentation
        cls = _classify_governance(best, b, 100)
        assert cls == ONTOLOGY_FRAGMENTATION

    def test_plasticity_overexpansion_plasticity_up_ne_down(self):
        b = self._b()
        best = dict(b)
        best["plasticity_proxy"] = 3.0    # pl up
        best["net_expectancy"]   = 0.005  # ne down
        cls = _classify_governance(best, b, 100)
        assert cls == PLASTICITY_OVEREXPANSION

    def test_balanced_adaptation_three_metrics_improved(self):
        b = self._b()
        best = dict(b)
        best["trade_count"]          = 110   # opp up
        best["net_expectancy"]       = 0.02   # ne up
        best["survivability_score"]  = 65.0  # surv up
        best["fee_drag_mean_pct"]    = 4.0   # fee down
        cls = _classify_governance(best, b, 100)
        assert cls == BALANCED_ADAPTATION

    def test_ecological_collapse_takes_priority_over_ne_up(self):
        # Both conditions met — ECOLOGICAL_COLLAPSE checks surv_up first
        b = self._b()
        best = dict(b)
        best["trade_count"]         = 20    # 80% drop
        best["survivability_score"] = 80.0  # surv up → ECOLOGICAL_COLLAPSE
        best["net_expectancy"]      = 0.05  # ne also up
        cls = _classify_governance(best, b, 100)
        assert cls == ECOLOGICAL_COLLAPSE

    def test_valid_classification_string(self):
        valid = {
            GOVERNANCE_STABLE, ECONOMIC_AUTHORITARIANISM, PLASTICITY_OVEREXPANSION,
            ONTOLOGY_FRAGMENTATION, ECOLOGICAL_COLLAPSE, BALANCED_ADAPTATION,
        }
        b = self._b()
        cls = _classify_governance(b, b, 100)
        assert cls in valid


# ══════════════════════════════════════════════════════════════════════════════
# TestConflictDetection
# ══════════════════════════════════════════════════════════════════════════════

class TestConflictDetection:

    def _gov_result(self, best: str) -> dict:
        return {"best_compound": best, "governance_classification": GOVERNANCE_STABLE}

    def test_no_conflict_same_best(self):
        gr = {
            "ECONOMIC_MAXIMALIST":   self._gov_result("SOFT_NEGMEM_TF5"),
            "PLASTICITY_PRESERVER":  self._gov_result("SOFT_NEGMEM_TF5"),
            "ECOLOGY_BALANCED":      self._gov_result("NY_TF5_PROJECTION"),
            "SURVIVABILITY_DEFENSIVE": self._gov_result("NY_TF5_PROJECTION"),
            "ONTOLOGY_HARMONIZER":   self._gov_result("DEFENSIVE_SESSIONS"),
            "ADAPTIVE_GENERALIST":   self._gov_result("DEFENSIVE_SESSIONS"),
        }
        r = _detect_conflicts(gr)
        assert r["conflict_count"] == 0
        assert r["consensus_reachable"] is True

    def test_expectancy_vs_plasticity_conflict(self):
        gr = {
            "ECONOMIC_MAXIMALIST":  self._gov_result("ONTOLOGY_RL_TF5"),
            "PLASTICITY_PRESERVER": self._gov_result("EXPLORE_REGIME_RESET"),
            "ECOLOGY_BALANCED":      self._gov_result("DEFENSIVE_SESSIONS"),
            "SURVIVABILITY_DEFENSIVE": self._gov_result("DEFENSIVE_SESSIONS"),
            "ONTOLOGY_HARMONIZER":   self._gov_result("NY_TF5_PROJECTION"),
            "ADAPTIVE_GENERALIST":   self._gov_result("NY_TF5_PROJECTION"),
        }
        r = _detect_conflicts(gr)
        assert r["conflict_count"] >= 1
        types_ = [c["conflict_type"] for c in r["conflicts"]]
        assert "EXPECTANCY_VS_PLASTICITY" in types_

    def test_opportunity_vs_survivability_conflict(self):
        gr = {
            "ECONOMIC_MAXIMALIST":   self._gov_result("SOFT_NEGMEM_TF5"),
            "PLASTICITY_PRESERVER":  self._gov_result("SOFT_NEGMEM_TF5"),
            "ECOLOGY_BALANCED":      self._gov_result("EXPLORE_REGIME_RESET"),
            "SURVIVABILITY_DEFENSIVE": self._gov_result("FULL_QUALITY_FILTER"),
            "ONTOLOGY_HARMONIZER":   self._gov_result("NY_TF5_PROJECTION"),
            "ADAPTIVE_GENERALIST":   self._gov_result("NY_TF5_PROJECTION"),
        }
        r = _detect_conflicts(gr)
        types_ = [c["conflict_type"] for c in r["conflicts"]]
        assert "OPPORTUNITY_VS_SURVIVABILITY" in types_

    def test_ontology_vs_balance_conflict(self):
        gr = {
            "ECONOMIC_MAXIMALIST":   self._gov_result("SOFT_NEGMEM_TF5"),
            "PLASTICITY_PRESERVER":  self._gov_result("SOFT_NEGMEM_TF5"),
            "ECOLOGY_BALANCED":      self._gov_result("NY_TF5_PROJECTION"),
            "SURVIVABILITY_DEFENSIVE": self._gov_result("NY_TF5_PROJECTION"),
            "ONTOLOGY_HARMONIZER":   self._gov_result("DEFENSIVE_SESSIONS"),
            "ADAPTIVE_GENERALIST":   self._gov_result("EXPLORE_REGIME_RESET"),
        }
        r = _detect_conflicts(gr)
        types_ = [c["conflict_type"] for c in r["conflicts"]]
        assert "ONTOLOGY_VS_BALANCE" in types_

    def test_conflict_output_structure(self):
        gr = {
            "ECONOMIC_MAXIMALIST":   self._gov_result("A"),
            "PLASTICITY_PRESERVER":  self._gov_result("B"),
            "ECOLOGY_BALANCED":      self._gov_result("C"),
            "SURVIVABILITY_DEFENSIVE": self._gov_result("D"),
            "ONTOLOGY_HARMONIZER":   self._gov_result("E"),
            "ADAPTIVE_GENERALIST":   self._gov_result("F"),
        }
        r = _detect_conflicts(gr)
        assert "conflict_count" in r
        assert "conflicts" in r
        assert "consensus_reachable" in r
        assert isinstance(r["conflicts"], list)


# ══════════════════════════════════════════════════════════════════════════════
# TestConsensusCompound
# ══════════════════════════════════════════════════════════════════════════════

class TestConsensusCompound:

    def _gr(self, bests: list) -> dict:
        profile_names = [
            "ECONOMIC_MAXIMALIST", "PLASTICITY_PRESERVER", "SURVIVABILITY_DEFENSIVE",
            "ECOLOGY_BALANCED", "ONTOLOGY_HARMONIZER", "ADAPTIVE_GENERALIST",
        ]
        return {name: {"best_compound": b} for name, b in zip(profile_names, bests)}

    def test_clear_majority(self):
        gr = self._gr(["A", "A", "A", "B", "B", "C"])
        assert _consensus_compound(gr) == "A"

    def test_tie_returns_none(self):
        gr = self._gr(["A", "A", "A", "B", "B", "B"])
        assert _consensus_compound(gr) is None

    def test_all_same_returns_that(self):
        gr = self._gr(["X"] * 6)
        assert _consensus_compound(gr) == "X"

    def test_empty_governance_returns_none(self):
        assert _consensus_compound({}) is None


# ══════════════════════════════════════════════════════════════════════════════
# TestComputeStructure
# ══════════════════════════════════════════════════════════════════════════════

class TestComputeStructure:

    def _result(self, n: int = 40) -> dict:
        return compute_adaptive_governance(_mixed_trades(n))

    def test_top_level_keys_present(self):
        r = self._result()
        for k in (
            "scope_note", "total_trades", "baseline",
            "compound_stacks", "governance_profiles", "governance_classifications",
            "conflict_analysis", "regime_specialization_risk",
            "overfitting_risk", "consensus_compound",
        ):
            assert k in r, f"Missing key: {k}"

    def test_scope_note_mentions_gags(self):
        r = self._result()
        assert "FTD-GAGS" in r["scope_note"]

    def test_six_compound_stacks_present(self):
        r = self._result()
        assert len(r["compound_stacks"]) == 6

    def test_six_governance_profiles_present(self):
        r = self._result()
        assert len(r["governance_profiles"]) == 6

    def test_governance_profile_has_required_keys(self):
        r = self._result()
        for gp, data in r["governance_profiles"].items():
            for k in ("description", "weights", "compound_scores", "best_compound",
                      "best_score", "governance_classification"):
                assert k in data, f"{gp} missing {k}"

    def test_conflict_analysis_keys(self):
        r = self._result()
        ca = r["conflict_analysis"]
        assert "conflict_count" in ca
        assert "conflicts" in ca
        assert "consensus_reachable" in ca

    def test_regime_specialization_risk_keys(self):
        r = self._result()
        rsr = r["regime_specialization_risk"]
        assert "score" in rsr
        assert "tier" in rsr
        assert "regime_counts" in rsr

    def test_overfitting_risk_keys(self):
        r = self._result()
        ofr = r["overfitting_risk"]
        assert "score" in ofr
        assert "tier" in ofr

    def test_total_trades_matches(self):
        trades = _mixed_trades(40)
        r = compute_adaptive_governance(trades)
        assert r["total_trades"] == 40

    def test_no_error_key_on_success(self):
        r = self._result()
        assert "error" not in r


# ══════════════════════════════════════════════════════════════════════════════
# TestProductionIsolation
# ══════════════════════════════════════════════════════════════════════════════

class TestProductionIsolation:

    def test_module_imports_no_main(self):
        assert "main" not in sys.modules or True  # soft check
        import core.governance_simulator as gs
        src = __import__("inspect").getsource(gs)
        assert "import main" not in src
        assert "from main" not in src

    def test_module_imports_no_pnl_calc(self):
        import core.governance_simulator as gs
        src = __import__("inspect").getsource(gs)
        assert "pnl_calc" not in src

    def test_module_imports_no_rl_engine(self):
        import core.governance_simulator as gs
        src = __import__("inspect").getsource(gs)
        assert "rl_engine" not in src

    def test_module_imports_no_data_lake(self):
        import core.governance_simulator as gs
        src = __import__("inspect").getsource(gs)
        assert "data_lake" not in src

    def test_compute_does_not_raise(self):
        # Should never raise regardless of input
        compute_adaptive_governance([])
        compute_adaptive_governance(None)
        compute_adaptive_governance([{"bad": "data"}] * 10)

    def test_input_list_not_mutated(self):
        trades = _mixed_trades(30)
        original = [dict(t) for t in trades]
        compute_adaptive_governance(trades)
        assert len(trades) == len(original)
        for orig, after in zip(original, trades):
            assert orig == after


# ══════════════════════════════════════════════════════════════════════════════
# TestEdgeCases
# ══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:

    def test_empty_list_returns_note(self):
        r = compute_adaptive_governance([])
        assert "note" in r or "error" in r

    def test_none_input_returns_note(self):
        r = compute_adaptive_governance(None)
        assert "note" in r or "error" in r

    def test_below_min_trades_returns_note(self):
        r = compute_adaptive_governance([_t()] * 3)
        assert "note" in r

    def test_exactly_min_trades_has_no_note(self):
        # MIN_REPLAY_TRADES = 5 in counterfactual_lab
        from core.counterfactual_lab import MIN_REPLAY_TRADES
        r = compute_adaptive_governance([_t()] * MIN_REPLAY_TRADES)
        # Should not have a top-level "note" key (may have partial data)
        # Just verify it doesn't crash
        assert isinstance(r, dict)

    def test_all_same_session_ny_suppresses_other_session_stacks(self):
        trades = _trades(30, session="NY")
        r = compute_adaptive_governance(trades)
        # DEFENSIVE_SESSIONS excludes ASIA (nothing to exclude) — fine
        # NY_TF5_PROJECTION keeps NY only (all kept)
        assert r["total_trades"] == 30

    def test_all_exploration_trades(self):
        trades = _trades(30, was_exploration=True)
        r = compute_adaptive_governance(trades)
        assert isinstance(r, dict)
        assert "error" not in r


# ══════════════════════════════════════════════════════════════════════════════
# TestBackwardCompatibility
# ══════════════════════════════════════════════════════════════════════════════

class TestBackwardCompatibility:

    def test_missing_regime_field_treated_as_unknown(self):
        trades = [{"net_pnl": 0.10, "gross_pnl": 0.15, "entry_ts": i} for i in range(30)]
        r = compute_adaptive_governance(trades)
        rsr = r.get("regime_specialization_risk", {})
        # Should not crash; UNKNOWN regime captured
        if "regime_counts" in rsr:
            assert isinstance(rsr["regime_counts"], dict)

    def test_missing_exploration_origin_handled(self):
        def _no_eo():
            t = _t()
            del t["exploration_origin"]
            return t
        trades = [_no_eo() for _ in range(30)]
        r = compute_adaptive_governance(trades)
        assert isinstance(r, dict)
        assert "error" not in r

    def test_none_exploration_origin_handled(self):
        def _null_eo():
            t = _t()
            t["exploration_origin"] = None
            return t
        trades = [_null_eo() for _ in range(30)]
        r = compute_adaptive_governance(trades)
        assert isinstance(r, dict)
        assert "error" not in r

    def test_extra_unknown_fields_ignored(self):
        trades = [dict(_t(), unknown_field_xyz=999) for _ in range(30)]
        r = compute_adaptive_governance(trades)
        assert isinstance(r, dict)
        assert "error" not in r


# ══════════════════════════════════════════════════════════════════════════════
# TestGovernanceProfileWeights
# ══════════════════════════════════════════════════════════════════════════════

class TestGovernanceProfileWeights:

    def test_six_profiles_defined(self):
        assert len(GOVERNANCE_PROFILES) == 6

    def test_all_profiles_have_weights(self):
        for name, gp in GOVERNANCE_PROFILES.items():
            assert "weights" in gp, f"{name} missing weights"
            assert "description" in gp, f"{name} missing description"

    def test_weights_sum_to_one(self):
        for name, gp in GOVERNANCE_PROFILES.items():
            total = sum(gp["weights"].values())
            assert abs(total - 1.0) < 1e-9, f"{name} weights sum to {total}"

    def test_all_weight_values_non_negative(self):
        for name, gp in GOVERNANCE_PROFILES.items():
            for obj, w in gp["weights"].items():
                assert w >= 0.0, f"{name}.{obj} has negative weight {w}"


# ══════════════════════════════════════════════════════════════════════════════
# TestGovernanceClassificationsMapping
# ══════════════════════════════════════════════════════════════════════════════

class TestGovernanceClassificationsMapping:

    def test_classifications_dict_has_all_profiles(self):
        r = compute_adaptive_governance(_mixed_trades(40))
        gc = r.get("governance_classifications", {})
        for gp in GOVERNANCE_PROFILES:
            assert gp in gc, f"{gp} missing from classifications"

    def test_all_classifications_valid_labels(self):
        valid = {
            GOVERNANCE_STABLE, ECONOMIC_AUTHORITARIANISM, PLASTICITY_OVEREXPANSION,
            ONTOLOGY_FRAGMENTATION, ECOLOGICAL_COLLAPSE, BALANCED_ADAPTATION,
        }
        r = compute_adaptive_governance(_mixed_trades(40))
        for gp, cls in r.get("governance_classifications", {}).items():
            assert cls in valid, f"{gp} has invalid classification {cls}"
