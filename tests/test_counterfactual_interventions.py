"""
Tests for FTD-CIL: core/counterfactual_lab.py

All tests use synthetic trade dicts — no live engine required.
Covers: filter functions, metrics, deltas, classification, full compute,
production isolation, edge cases, ranking, backward compatibility.
"""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.counterfactual_lab import (
    BENEFICIAL_ADAPTATION,
    COGNITIVE_OVERFITTING,
    COSMETIC_STABILITY,
    FRAGILE_OPTIMIZATION,
    INSUFFICIENT_DATA,
    INTERVENTION_PROFILES,
    MIN_REPLAY_TRADES,
    ONTOLOGY_STABILIZATION,
    OPP_COLLAPSE_THRESHOLD,
    OPPORTUNITY_COLLAPSE,
    _apply_ecology_stricter,
    _apply_negmem_soft_decay,
    _apply_ny_only,
    _apply_ontology_weighting_rl_dominant,
    _apply_rl_reset_mean_reverting,
    _apply_rule4_high_explore,
    _apply_session_suppression_asia,
    _apply_tf5_projection,
    _classify_intervention,
    _compute_deltas,
    _compute_trade_metrics,
    _gross_fee_rate,
    _is_exploration,
    _ontology_drift_proxy,
    _plasticity_proxy,
    _rank_interventions,
    _replay_confidence,
    compute_counterfactual_interventions,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _t(
    net_pnl:         float = 1.0,
    gross_pnl:       float = 2.0,
    regime:          str   = "TRENDING",
    session:         str   = "NY",
    was_exploration: bool  = False,
    explore_type:    str   = "EXPLOIT",
    fee_entry:       float = 0.5,
    fee_exit:        float = 0.5,
) -> dict:
    return {
        "trade_id":        f"t{id(object())}",
        "net_pnl":         net_pnl,
        "gross_pnl":       gross_pnl,
        "regime":          regime,
        "origin_session":  session,
        "entry_ts":        1_000_000,
        "exit_ts":         1_001_000,
        "fee_entry":       fee_entry,
        "fee_exit":        fee_exit,
        "slippage_cost":   0.0,
        "borrow_cost":     0.0,
        "r_multiple":      1.0,
        "exploration_origin": {
            "was_exploration_trade": was_exploration,
            "explore_type":          explore_type,
        },
    }


def _trades(n: int = 10, **kwargs) -> list:
    return [_t(**kwargs) for _ in range(n)]


def _mixed_trades(n_explore: int = 3, n_exploit: int = 7) -> list:
    return (
        [_t(was_exploration=True,  explore_type="RULE4_MIN_EXPLORE") for _ in range(n_explore)]
        + [_t(was_exploration=False, explore_type="EXPLOIT")         for _ in range(n_exploit)]
    )


def _session_mix(ny: int = 5, asia: int = 3, london: int = 2) -> list:
    return (
        [_t(session="NY")     for _ in range(ny)]
        + [_t(session="ASIA") for _ in range(asia)]
        + [_t(session="LONDON") for _ in range(london)]
    )


# ── TestInterventionFilters ───────────────────────────────────────────────────

class TestInterventionFilters(unittest.TestCase):

    def test_negmem_soft_decay_keeps_profitable_exploit(self):
        trades = [_t(net_pnl=1.0, was_exploration=False)]
        self.assertEqual(len(_apply_negmem_soft_decay(trades)), 1)

    def test_negmem_soft_decay_removes_losing_exploit(self):
        trades = [_t(net_pnl=-1.0, was_exploration=False)]
        self.assertEqual(len(_apply_negmem_soft_decay(trades)), 0)

    def test_negmem_soft_decay_keeps_exploration_even_losing(self):
        trades = [_t(net_pnl=-2.0, was_exploration=True)]
        self.assertEqual(len(_apply_negmem_soft_decay(trades)), 1)

    def test_rule4_high_explore_keeps_only_exploration(self):
        trades = [
            _t(was_exploration=True),
            _t(was_exploration=False),
            _t(was_exploration=True),
        ]
        result = _apply_rule4_high_explore(trades)
        self.assertEqual(len(result), 2)
        self.assertTrue(all(_is_exploration(t) for t in result))

    def test_rule4_high_explore_removes_all_exploit(self):
        trades = [_t(was_exploration=False) for _ in range(5)]
        self.assertEqual(len(_apply_rule4_high_explore(trades)), 0)

    def test_ny_only_filters_correctly(self):
        trades = _session_mix(ny=4, asia=3, london=2)
        result = _apply_ny_only(trades)
        self.assertEqual(len(result), 4)
        self.assertTrue(all(t["origin_session"] == "NY" for t in result))

    def test_tf5_projection_scales_gross_pnl(self):
        t = _t(net_pnl=1.0, gross_pnl=2.0, fee_entry=0.5, fee_exit=0.5)
        result = _apply_tf5_projection([t])
        self.assertAlmostEqual(result[0]["gross_pnl"], 10.0, places=5)

    def test_tf5_projection_keeps_fees_constant(self):
        t = _t(net_pnl=1.0, gross_pnl=2.0, fee_entry=0.3, fee_exit=0.4)
        result = _apply_tf5_projection([t])
        # fees unchanged: net = gross*5 - (0.3+0.4+0+0) = 10.0 - 0.7 = 9.3
        self.assertAlmostEqual(result[0]["net_pnl"], 10.0 - 0.7, places=5)

    def test_tf5_projection_doesnt_mutate_original(self):
        t = _t(gross_pnl=2.0)
        original_gross = t["gross_pnl"]
        _apply_tf5_projection([t])
        self.assertEqual(t["gross_pnl"], original_gross)

    def test_rl_reset_mean_reverting_excludes_regime(self):
        trades = [
            _t(regime="TRENDING"),
            _t(regime="MEAN_REVERTING"),
            _t(regime="MEAN_REVERTING"),
            _t(regime="TRENDING"),
        ]
        result = _apply_rl_reset_mean_reverting(trades)
        self.assertEqual(len(result), 2)
        self.assertTrue(all(t["regime"] != "MEAN_REVERTING" for t in result))

    def test_session_suppression_asia_removes_asia(self):
        trades = _session_mix(ny=5, asia=3, london=2)
        result = _apply_session_suppression_asia(trades)
        self.assertEqual(len(result), 7)
        self.assertTrue(all(t["origin_session"] != "ASIA" for t in result))

    def test_ontology_weighting_keeps_exploit_only(self):
        trades = _mixed_trades(n_explore=4, n_exploit=6)
        result = _apply_ontology_weighting_rl_dominant(trades)
        self.assertEqual(len(result), 6)
        self.assertTrue(all(not _is_exploration(t) for t in result))

    def test_ecology_stricter_passes_low_fee_rate(self):
        # gross=10, fee=2 → rate=0.2 ≤ 0.5
        t = _t(gross_pnl=10.0, net_pnl=8.0, fee_entry=1.0, fee_exit=1.0)
        result = _apply_ecology_stricter([t])
        self.assertEqual(len(result), 1)

    def test_ecology_stricter_blocks_high_fee_rate(self):
        # gross=2, fee=1.5 → rate=0.75 > 0.5
        t = _t(gross_pnl=2.0, net_pnl=0.5, fee_entry=0.75, fee_exit=0.75)
        result = _apply_ecology_stricter([t])
        self.assertEqual(len(result), 0)

    def test_ecology_stricter_passes_zero_gross(self):
        # zero gross → rate=0.0 ≤ 0.5 (passes by default)
        t = _t(gross_pnl=0.0, net_pnl=0.0, fee_entry=0.0, fee_exit=0.0)
        result = _apply_ecology_stricter([t])
        self.assertEqual(len(result), 1)

    def test_all_filters_are_deterministic(self):
        trades = _mixed_trades() + _session_mix()
        for name, profile in INTERVENTION_PROFILES.items():
            r1 = profile["fn"](trades)
            r2 = profile["fn"](trades)
            self.assertEqual(len(r1), len(r2), f"{name} is non-deterministic")

    def test_all_filters_dont_mutate_input(self):
        trades = _mixed_trades()
        for name, profile in INTERVENTION_PROFILES.items():
            before = [t["net_pnl"] for t in trades]
            profile["fn"](trades)
            after  = [t["net_pnl"] for t in trades]
            self.assertEqual(before, after, f"{name} mutated input")

    def test_empty_trades_handled_by_all_filters(self):
        for name, profile in INTERVENTION_PROFILES.items():
            result = profile["fn"]([])
            self.assertIsInstance(result, list, f"{name} failed on empty input")


# ── TestReplayConfidence ──────────────────────────────────────────────────────

class TestReplayConfidence(unittest.TestCase):

    def test_high_confidence_80_pct(self):
        r = _replay_confidence(100, 85)
        self.assertEqual(r["tier"], "HIGH")

    def test_moderate_confidence(self):
        r = _replay_confidence(100, 60)
        self.assertEqual(r["tier"], "MODERATE")

    def test_low_confidence(self):
        r = _replay_confidence(100, 30)
        self.assertEqual(r["tier"], "LOW")

    def test_insufficient_confidence(self):
        r = _replay_confidence(100, 10)
        self.assertEqual(r["tier"], "INSUFFICIENT")

    def test_zero_original_returns_insufficient(self):
        r = _replay_confidence(0, 5)
        self.assertEqual(r["tier"], "INSUFFICIENT")
        self.assertEqual(r["score"], 0.0)

    def test_score_reflects_retention_ratio(self):
        r = _replay_confidence(200, 100)
        self.assertAlmostEqual(r["score"], 50.0, places=1)


# ── TestDeltaComputation ──────────────────────────────────────────────────────

class TestDeltaComputation(unittest.TestCase):

    def _m(self, ne, surv, drag, wr, plast, drift, expl, count):
        return {
            "net_expectancy": ne, "survivability_score": surv,
            "fee_drag_mean_pct": drag, "win_rate_pct": wr,
            "plasticity_proxy": plast, "ontology_drift_proxy": drift,
            "exploration_dependence_pct": expl, "trade_count": count,
        }

    def test_positive_ne_delta(self):
        b = self._m(1.0, 50, 5.0, 60.0, 1.0, 10.0, 30.0, 10)
        i = self._m(2.0, 55, 4.0, 65.0, 1.5, 8.0,  35.0, 10)
        d = _compute_deltas(b, i, 10)
        self.assertAlmostEqual(d["net_expectancy_delta"], 1.0, places=5)

    def test_negative_ne_delta(self):
        b = self._m(2.0, 50, 5.0, 60.0, 1.0, 10.0, 30.0, 10)
        i = self._m(1.0, 50, 5.0, 60.0, 1.0, 10.0, 30.0, 10)
        d = _compute_deltas(b, i, 10)
        self.assertAlmostEqual(d["net_expectancy_delta"], -1.0, places=5)

    def test_zero_delta_same_metrics(self):
        m = self._m(1.0, 50, 5.0, 60.0, 1.0, 10.0, 30.0, 10)
        d = _compute_deltas(m, m, 10)
        self.assertAlmostEqual(d["net_expectancy_delta"], 0.0, places=5)

    def test_opportunity_density_delta_computed(self):
        b = self._m(1.0, 50, 5.0, 60.0, 1.0, 10.0, 30.0, 10)
        i = self._m(1.0, 50, 5.0, 60.0, 1.0, 10.0, 30.0, 6)
        d = _compute_deltas(b, i, 10)
        self.assertAlmostEqual(d["opportunity_density_delta_pct"], -40.0, places=1)

    def test_delta_dict_has_all_keys(self):
        m = self._m(1.0, 50, 5.0, 60.0, 1.0, 10.0, 30.0, 10)
        d = _compute_deltas(m, m, 10)
        for k in ("net_expectancy_delta", "survivability_delta", "fee_drag_delta",
                  "win_rate_delta", "plasticity_delta", "ontology_drift_delta",
                  "exploration_dependence_delta", "opportunity_density_delta_pct"):
            self.assertIn(k, d)

    def test_none_in_baseline_produces_none_delta(self):
        b = {"trade_count": 10, "net_expectancy": None}
        i = {"trade_count": 10, "net_expectancy": 1.0}
        d = _compute_deltas(b, i, 10)
        self.assertIsNone(d["net_expectancy_delta"])

    def test_none_in_intervention_produces_none_delta(self):
        b = {"trade_count": 10, "net_expectancy": 1.0}
        i = {"trade_count": 10, "net_expectancy": None}
        d = _compute_deltas(b, i, 10)
        self.assertIsNone(d["net_expectancy_delta"])


# ── TestClassification ────────────────────────────────────────────────────────

class TestClassification(unittest.TestCase):

    def _d(self, ne=0.0, surv=0.0, drag=0.0, wr=0.0, plast=0.0, drift=0.0, expl=0.0, opp=0.0):
        return {
            "net_expectancy_delta":           ne,
            "survivability_delta":            surv,
            "fee_drag_delta":                 drag,
            "win_rate_delta":                 wr,
            "plasticity_delta":               plast,
            "ontology_drift_delta":           drift,
            "exploration_dependence_delta":   expl,
            "opportunity_density_delta_pct":  opp,
        }

    def test_insufficient_data_on_few_trades(self):
        r = _classify_intervention(self._d(ne=1.0, surv=5.0), i_count=2, b_count=10)
        self.assertEqual(r, INSUFFICIENT_DATA)

    def test_opportunity_collapse_threshold(self):
        r = _classify_intervention(self._d(opp=OPP_COLLAPSE_THRESHOLD - 1), 6, 10)
        self.assertEqual(r, OPPORTUNITY_COLLAPSE)

    def test_cognitive_overfitting_threshold(self):
        r = _classify_intervention(self._d(plast=-25.0), 8, 10)
        self.assertEqual(r, COGNITIVE_OVERFITTING)

    def test_beneficial_adaptation(self):
        r = _classify_intervention(self._d(ne=0.01, surv=5.0, opp=-5.0), 9, 10)
        self.assertEqual(r, BENEFICIAL_ADAPTATION)

    def test_beneficial_requires_positive_surv(self):
        # NE positive but surv negative → not BENEFICIAL
        r = _classify_intervention(self._d(ne=0.01, surv=-5.0, opp=-5.0), 9, 10)
        self.assertNotEqual(r, BENEFICIAL_ADAPTATION)

    def test_beneficial_requires_opp_above_warn(self):
        # NE and surv good but opportunity dropped below warn threshold
        r = _classify_intervention(self._d(ne=0.01, surv=5.0, opp=-25.0), 9, 10)
        self.assertNotEqual(r, BENEFICIAL_ADAPTATION)

    def test_ontology_stabilization_drift_reduction(self):
        r = _classify_intervention(self._d(drift=-20.0), 8, 10)
        self.assertEqual(r, ONTOLOGY_STABILIZATION)

    def test_cosmetic_stability_flat_ne_positive_surv(self):
        r = _classify_intervention(self._d(ne=0.00005, surv=3.0), 10, 10)
        self.assertEqual(r, COSMETIC_STABILITY)

    def test_fragile_optimization_ne_positive_surv_negative(self):
        r = _classify_intervention(self._d(ne=0.5, surv=-3.0, opp=-5.0), 9, 10)
        self.assertEqual(r, FRAGILE_OPTIMIZATION)

    def test_opportunity_collapse_beats_beneficial(self):
        # Opp collapses even though NE and surv look good
        r = _classify_intervention(self._d(ne=0.5, surv=10.0, opp=-45.0), 8, 10)
        self.assertEqual(r, OPPORTUNITY_COLLAPSE)

    def test_cognitive_overfitting_beats_beneficial(self):
        r = _classify_intervention(self._d(ne=0.5, surv=10.0, plast=-25.0), 8, 10)
        self.assertEqual(r, COGNITIVE_OVERFITTING)

    def test_classification_returns_known_label(self):
        known = {BENEFICIAL_ADAPTATION, COSMETIC_STABILITY, OPPORTUNITY_COLLAPSE,
                 FRAGILE_OPTIMIZATION, ONTOLOGY_STABILIZATION, COGNITIVE_OVERFITTING,
                 INSUFFICIENT_DATA}
        for deltas in [
            self._d(ne=0.01, surv=5.0, opp=-5.0),
            self._d(opp=-50.0),
            self._d(plast=-30.0),
            self._d(drift=-20.0),
            self._d(ne=0.00001, surv=1.0),
            self._d(ne=0.5, surv=-1.0),
        ]:
            r = _classify_intervention(deltas, 8, 10)
            self.assertIn(r, known)


# ── TestComputeStructure ──────────────────────────────────────────────────────

class TestComputeStructure(unittest.TestCase):

    def setUp(self):
        # Enough trades to exceed MIN_REPLAY_TRADES for most interventions
        self.trades = (
            [_t(was_exploration=True,  session="NY",     regime="TRENDING")     for _ in range(5)]
            + [_t(was_exploration=False, session="NY",   regime="MEAN_REVERTING") for _ in range(5)]
            + [_t(was_exploration=False, session="ASIA",  regime="TRENDING",
                  net_pnl=-0.5, gross_pnl=1.0, fee_entry=0.75, fee_exit=0.75)    for _ in range(3)]
        )
        self.result = compute_counterfactual_interventions(self.trades)

    def test_top_level_keys_present(self):
        for k in ("scope_note", "total_trades", "baseline", "interventions",
                  "intervention_ranking", "top_intervention"):
            self.assertIn(k, self.result)

    def test_baseline_has_required_keys(self):
        b = self.result["baseline"]
        for k in ("trade_count", "net_expectancy", "survivability_score",
                  "plasticity_proxy", "ontology_drift_proxy"):
            self.assertIn(k, b)

    def test_all_profiles_in_interventions(self):
        for name in INTERVENTION_PROFILES:
            self.assertIn(name, self.result["interventions"])

    def test_each_intervention_has_required_keys(self):
        for name, data in self.result["interventions"].items():
            self.assertIn("classification", data, f"{name} missing classification")
            self.assertIn("description",    data, f"{name} missing description")

    def test_intervention_ranking_is_list(self):
        self.assertIsInstance(self.result["intervention_ranking"], list)

    def test_intervention_ranking_sorted_descending(self):
        ranked = self.result["intervention_ranking"]
        scores = [r["net_expectancy_delta"] for r in ranked if r["net_expectancy_delta"] is not None]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_top_intervention_is_string_or_none(self):
        ti = self.result["top_intervention"]
        self.assertTrue(ti is None or isinstance(ti, str))

    def test_detection_flags_are_bool(self):
        for k in ("beneficial_adaptation_detected", "opportunity_collapse_detected",
                  "ontology_stabilization_detected", "cognitive_overfitting_detected"):
            self.assertIn(k, self.result)
            self.assertIsInstance(self.result[k], bool, f"{k} is not bool")

    def test_scope_note_present(self):
        self.assertTrue(len(self.result["scope_note"]) > 20)

    def test_total_trades_correct(self):
        self.assertEqual(self.result["total_trades"], len(self.trades))


# ── TestProductionIsolation ───────────────────────────────────────────────────

class TestProductionIsolation(unittest.TestCase):

    def test_input_trades_not_mutated(self):
        trades = _trades(10)
        before = copy.deepcopy(trades)
        compute_counterfactual_interventions(trades)
        self.assertEqual([t["net_pnl"] for t in trades],
                         [t["net_pnl"] for t in before])

    def test_repeated_calls_identical(self):
        trades = _mixed_trades(4, 8)
        r1 = compute_counterfactual_interventions(trades)
        r2 = compute_counterfactual_interventions(trades)
        self.assertEqual(r1["total_trades"], r2["total_trades"])
        for name in INTERVENTION_PROFILES:
            c1 = r1["interventions"].get(name, {}).get("classification")
            c2 = r2["interventions"].get(name, {}).get("classification")
            self.assertEqual(c1, c2, f"{name} non-deterministic")

    def test_different_inputs_give_different_results(self):
        trades_a = [_t(net_pnl=2.0, gross_pnl=3.0)  for _ in range(10)]
        trades_b = [_t(net_pnl=-1.0, gross_pnl=1.0) for _ in range(10)]
        ra = compute_counterfactual_interventions(trades_a)
        rb = compute_counterfactual_interventions(trades_b)
        ne_a = ra["baseline"].get("net_expectancy")
        ne_b = rb["baseline"].get("net_expectancy")
        # Different inputs should yield different baseline NE
        if ne_a is not None and ne_b is not None:
            self.assertNotAlmostEqual(ne_a, ne_b, places=3)

    def test_tf5_doesnt_mutate_source_trades(self):
        trades = [_t(gross_pnl=2.0) for _ in range(5)]
        originals = [t["gross_pnl"] for t in trades]
        _apply_tf5_projection(trades)
        self.assertEqual([t["gross_pnl"] for t in trades], originals)

    def test_fail_open_on_exception(self):
        for bad in [None, "bad", 42, 3.14]:
            r = compute_counterfactual_interventions(bad)
            self.assertIn("scope_note", r)

    def test_no_shared_state_between_calls(self):
        # Verify that modifying the result of one call doesn't affect another
        trades = _trades(10)
        r1 = compute_counterfactual_interventions(trades)
        r1["total_trades"] = 9999  # mutate result
        r2 = compute_counterfactual_interventions(trades)
        self.assertEqual(r2["total_trades"], 10)

    def test_intervention_profiles_registry_immutability(self):
        # All profiles must still be present after compute
        trades = _trades(10)
        compute_counterfactual_interventions(trades)
        self.assertEqual(len(INTERVENTION_PROFILES), 8)


# ── TestEdgeCases ─────────────────────────────────────────────────────────────

class TestEdgeCases(unittest.TestCase):

    def test_empty_trades_returns_note(self):
        r = compute_counterfactual_interventions([])
        self.assertIn("scope_note", r)
        self.assertEqual(r["total_trades"], 0)

    def test_too_few_trades_returns_note(self):
        r = compute_counterfactual_interventions([_t()] * (MIN_REPLAY_TRADES - 1))
        self.assertIn("note", r)

    def test_never_raises_on_bad_input(self):
        for bad in [None, [], {}, "string", 0, [None, None]]:
            try:
                r = compute_counterfactual_interventions(bad)
                self.assertIn("scope_note", r)
            except Exception as e:
                self.fail(f"raised {e!r} for input {bad!r}")

    def test_no_exploration_trades_rule4_insufficient(self):
        # All exploit → RULE4_HIGH_EXPLORE should be INSUFFICIENT_DATA
        trades = [_t(was_exploration=False) for _ in range(10)]
        r = compute_counterfactual_interventions(trades)
        rule4 = r["interventions"]["RULE4_HIGH_EXPLORE"]
        self.assertEqual(rule4["classification"], INSUFFICIENT_DATA)

    def test_all_trades_asia_session_suppression_insufficient(self):
        trades = [_t(session="ASIA") for _ in range(10)]
        r = compute_counterfactual_interventions(trades)
        asia = r["interventions"]["SESSION_SUPPRESSION_ASIA"]
        self.assertEqual(asia["classification"], INSUFFICIENT_DATA)

    def test_missing_exploration_origin_handled(self):
        trades = [{"trade_id": f"t{i}", "net_pnl": 1.0, "gross_pnl": 2.0,
                   "regime": "TRENDING", "origin_session": "NY",
                   "entry_ts": 1000000, "exit_ts": 1001000}
                  for i in range(10)]
        r = compute_counterfactual_interventions(trades)
        self.assertIn("scope_note", r)

    def test_zero_gross_pnl_ecology_handled(self):
        trades = [_t(gross_pnl=0.0, net_pnl=0.0, fee_entry=0.0, fee_exit=0.0)
                  for _ in range(10)]
        r = compute_counterfactual_interventions(trades)
        eco = r["interventions"]["ECOLOGY_STRICTER"]
        self.assertIn("classification", eco)

    def test_all_mean_reverting_rl_reset_insufficient(self):
        trades = [_t(regime="MEAN_REVERTING") for _ in range(10)]
        r = compute_counterfactual_interventions(trades)
        rr = r["interventions"]["RL_RESET_MEAN_REVERTING"]
        self.assertEqual(rr["classification"], INSUFFICIENT_DATA)


# ── TestRankingAndDetection ───────────────────────────────────────────────────

class TestRankingAndDetection(unittest.TestCase):

    def test_ranking_highest_ne_delta_first(self):
        interventions = {
            "A": {"deltas": {"net_expectancy_delta": 1.0}, "classification": BENEFICIAL_ADAPTATION},
            "B": {"deltas": {"net_expectancy_delta": 0.5}, "classification": FRAGILE_OPTIMIZATION},
            "C": {"deltas": {"net_expectancy_delta": 2.0}, "classification": BENEFICIAL_ADAPTATION},
        }
        ranked = _rank_interventions(interventions)
        self.assertEqual(ranked[0]["intervention"], "C")
        self.assertEqual(ranked[1]["intervention"], "A")

    def test_none_ne_delta_ranked_last(self):
        interventions = {
            "GOOD": {"deltas": {"net_expectancy_delta": 0.5}, "classification": FRAGILE_OPTIMIZATION},
            "BAD":  {"deltas": {"net_expectancy_delta": None}, "classification": INSUFFICIENT_DATA},
        }
        ranked = _rank_interventions(interventions)
        self.assertEqual(ranked[-1]["intervention"], "BAD")

    def test_opportunity_collapse_detected_flag(self):
        # Create a scenario where ASIA suppression removes almost all trades
        trades = (
            [_t(session="ASIA") for _ in range(45)]
            + [_t(session="NY")  for _ in range(10)]
        )
        r = compute_counterfactual_interventions(trades)
        # ASIA suppression removes 45/55 = ~82% of trades → OPPORTUNITY_COLLAPSE
        self.assertTrue(r["opportunity_collapse_detected"])

    def test_beneficial_detected_flag_present(self):
        r = compute_counterfactual_interventions(_trades(20))
        self.assertIsInstance(r["beneficial_adaptation_detected"], bool)

    def test_all_detection_flags_consistent_with_interventions(self):
        r = compute_counterfactual_interventions(
            [_t(was_exploration=True,  session="NY",   regime="TRENDING") for _ in range(8)]
            + [_t(was_exploration=False, session="ASIA", regime="MEAN_REVERTING",
                  net_pnl=-1.0, gross_pnl=2.0) for _ in range(5)]
        )
        # If any intervention has the label, the flag should be True
        any_opp = any(
            v.get("classification") == OPPORTUNITY_COLLAPSE
            for v in r["interventions"].values()
        )
        self.assertEqual(r["opportunity_collapse_detected"], any_opp)


# ── TestProxyMetrics ──────────────────────────────────────────────────────────

class TestProxyMetrics(unittest.TestCase):

    def test_plasticity_proxy_higher_for_diverse_pnl(self):
        uniform = [_t(gross_pnl=1.0) for _ in range(10)]
        diverse = [_t(gross_pnl=float(i)) for i in range(10)]
        self.assertGreater(_plasticity_proxy(diverse), _plasticity_proxy(uniform))

    def test_plasticity_proxy_zero_for_identical(self):
        trades = [_t(gross_pnl=5.0) for _ in range(5)]
        self.assertEqual(_plasticity_proxy(trades), 0.0)

    def test_ontology_drift_proxy_zero_when_equal_wr(self):
        # Explore and exploit have same win-rate
        trades = (
            [_t(net_pnl=1.0, was_exploration=True)  for _ in range(5)]
            + [_t(net_pnl=1.0, was_exploration=False) for _ in range(5)]
        )
        self.assertAlmostEqual(_ontology_drift_proxy(trades), 0.0, places=1)

    def test_ontology_drift_proxy_max_when_fully_diverged(self):
        # Explore: all win; Exploit: all lose
        trades = (
            [_t(net_pnl=1.0,  was_exploration=True)  for _ in range(5)]
            + [_t(net_pnl=-1.0, was_exploration=False) for _ in range(5)]
        )
        self.assertAlmostEqual(_ontology_drift_proxy(trades), 100.0, places=1)


# ── TestBackwardCompatibility ─────────────────────────────────────────────────

class TestBackwardCompatibility(unittest.TestCase):

    def test_missing_gross_pnl_handled(self):
        trades = [{"trade_id": f"t{i}", "net_pnl": 1.0, "regime": "TRENDING",
                   "origin_session": "NY", "entry_ts": 1000000, "exit_ts": 1001000}
                  for i in range(10)]
        r = compute_counterfactual_interventions(trades)
        self.assertIn("scope_note", r)

    def test_missing_regime_field(self):
        trades = [{"trade_id": f"t{i}", "net_pnl": 1.0, "gross_pnl": 2.0,
                   "origin_session": "NY", "entry_ts": 1000000, "exit_ts": 1001000}
                  for i in range(10)]
        r = compute_counterfactual_interventions(trades)
        self.assertIn("scope_note", r)

    def test_missing_session_field(self):
        trades = [{"trade_id": f"t{i}", "net_pnl": 1.0, "gross_pnl": 2.0,
                   "regime": "TRENDING", "entry_ts": 1000000, "exit_ts": 1001000}
                  for i in range(10)]
        r = compute_counterfactual_interventions(trades)
        self.assertIn("scope_note", r)

    def test_none_net_pnl_handled(self):
        trades = [_t(net_pnl=None) for _ in range(10)]
        r = compute_counterfactual_interventions(trades)
        self.assertIn("scope_note", r)

    def test_extra_trade_fields_ignored(self):
        trades = [dict(**_t(), extra_field="ignored", another=42) for _ in range(10)]
        r = compute_counterfactual_interventions(trades)
        self.assertIn("scope_note", r)

    def test_none_exploration_origin_handled(self):
        def _no_eo():
            t = _t()
            t["exploration_origin"] = None
            return t
        trades = [_no_eo() for _ in range(10)]
        r = compute_counterfactual_interventions(trades)
        self.assertIn("scope_note", r)


if __name__ == "__main__":
    unittest.main()
