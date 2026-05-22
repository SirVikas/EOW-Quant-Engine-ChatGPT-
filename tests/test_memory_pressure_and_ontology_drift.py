"""
Tests for FTD-ONTOLOGY-DRIFT: core/memory_pressure_analytics.py

All tests use synthetic state dicts — no live engine required.
"""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.memory_pressure_analytics import (
    ADAPTIVE_CONVERGENCE,
    DRIFT_HIGH,
    DRIFT_LOW,
    DRIFT_MODERATE,
    ECOLOGICAL_AMNESIA,
    HEALTHY_PLASTICITY,
    MEMORY_SATURATION,
    ONTOLOGY_FRAGMENTATION,
    PREMATURE_FOSSILIZATION,
    Q_ENTROPY_HIGH,
    Q_ENTROPY_LOW,
    _classify_cognitive_state,
    _drift_alpha_context_rl,
    _drift_pattern_negmem,
    _drift_rl_ecology,
    _drift_rl_negmem,
    _drift_rl_pattern,
    _drift_tier,
    _fossilization_risk,
    _plasticity_score,
    _q_entropy,
    compute_memory_pressure_dynamics,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_state(
    rl_profitable_pct: float = 0.6,
    rl_total_contexts: int   = 50,
    q_values:    list | None = None,
    q_velocities:list | None = None,
    toxic_count: int         = 2,
    explore_ratio: float     = 0.20,
    regime_avg_q: dict | None = None,
    nm_permanent: int        = 3,
    nm_total:     int        = 10,
    nm_entries:   list | None = None,
    pat_total:    int        = 20,
    pat_formed:   int        = 5,
    formed_dicts: list | None = None,
    eco_regimes:  dict | None = None,
    ac_profitable:int        = 30,
    ac_toxic:     int        = 5,
    ac_total:     int        = 50,
) -> dict:
    if q_values is None:
        q_values = [0.1 * i - 0.5 for i in range(12)]
    if q_velocities is None:
        q_velocities = [0.01] * 10
    if regime_avg_q is None:
        regime_avg_q = {"TRENDING": 0.2, "MEAN_REVERTING": -0.1}
    if nm_entries is None:
        nm_entries = [
            {"key_str": f"TRENDING|LOW|ES|rsi|LONG_{i}", "permanent": i < nm_permanent, "rollbacks": 1, "score": 0.9}
            for i in range(nm_total)
        ]
    if formed_dicts is None:
        formed_dicts = [
            {
                "pattern_id": f"p{i}",
                "key": {"regime": "TRENDING", "volatility": "LOW",
                        "instrument": "ES", "parameter": "rsi", "direction": "LONG"},
                "samples": 25, "success": 15, "confidence": 72.0,
                "contexts": ["c1", "c2", "c3"], "last_seen": 10, "created_at": 1000.0,
            }
            for i in range(pat_formed)
        ]
    if eco_regimes is None:
        eco_regimes = {
            "TRENDING":      {"n_trades": 20, "win_rate": 0.6, "weight": 1.1},
            "MEAN_REVERTING": {"n_trades": 15, "win_rate": 0.45, "weight": 0.9},
        }

    return {
        "rl": {
            "profitable_pct":  rl_profitable_pct,
            "total_contexts":  rl_total_contexts,
            "q_values":        q_values,
            "q_velocities":    q_velocities,
            "toxic_count":     toxic_count,
            "explore_ratio":   explore_ratio,
            "regime_avg_q":    regime_avg_q,
        },
        "negmem": {
            "count":   {"permanent": nm_permanent, "temporary": nm_total - nm_permanent, "total": nm_total},
            "entries": nm_entries,
        },
        "patterns": {
            "total_patterns":      pat_total,
            "formed_patterns":     pat_formed,
            "formed_pattern_dicts": formed_dicts,
        },
        "ecology": {"regimes": eco_regimes},
        "alpha_context": {
            "profitable_count": ac_profitable,
            "toxic_count":      ac_toxic,
            "total_contexts":   ac_total,
        },
    }


# ── TestQEntropy ──────────────────────────────────────────────────────────────

class TestQEntropy(unittest.TestCase):

    def test_empty_returns_zero(self):
        self.assertEqual(_q_entropy([]), 0.0)

    def test_single_value_returns_zero(self):
        self.assertEqual(_q_entropy([0.5]), 0.0)

    def test_two_identical_returns_zero(self):
        self.assertEqual(_q_entropy([1.0, 1.0]), 0.0)

    def test_uniform_distribution_max_entropy(self):
        # 10 values each in a different bin → max entropy
        q = [float(i) for i in range(10)]
        e = _q_entropy(q)
        self.assertGreater(e, 2.0)

    def test_concentrated_values_low_entropy(self):
        # All in same bin
        q = [0.0] * 8 + [10.0]
        e = _q_entropy(q)
        self.assertLess(e, 1.5)

    def test_two_extreme_values_returns_one_bit(self):
        q = [0.0, 1.0]
        e = _q_entropy(q)
        self.assertAlmostEqual(e, 1.0, places=3)

    def test_result_is_non_negative(self):
        q = [0.1, 0.5, -0.3, 0.7, 0.2]
        self.assertGreaterEqual(_q_entropy(q), 0.0)


# ── TestDriftTier ─────────────────────────────────────────────────────────────

class TestDriftTier(unittest.TestCase):

    def test_high_drift(self):
        self.assertEqual(_drift_tier(DRIFT_HIGH),        "HIGH_DRIFT")
        self.assertEqual(_drift_tier(DRIFT_HIGH + 10),   "HIGH_DRIFT")

    def test_moderate_drift(self):
        self.assertEqual(_drift_tier(DRIFT_MODERATE),        "MODERATE_DRIFT")
        self.assertEqual(_drift_tier(DRIFT_HIGH - 1),        "MODERATE_DRIFT")

    def test_low_drift(self):
        self.assertEqual(_drift_tier(DRIFT_LOW),          "LOW_DRIFT")
        self.assertEqual(_drift_tier(DRIFT_MODERATE - 1), "LOW_DRIFT")

    def test_aligned(self):
        self.assertEqual(_drift_tier(0.0),            "ALIGNED")
        self.assertEqual(_drift_tier(DRIFT_LOW - 1),  "ALIGNED")


# ── TestPlasticityScore ───────────────────────────────────────────────────────

class TestPlasticityScore(unittest.TestCase):

    def test_max_score_all_factors_met(self):
        r = _plasticity_score(
            q_entropy=3.0, negmem_density=20.0, avg_q_velocity=0.01, explore_rate=0.20
        )
        self.assertEqual(r["score"], 100)
        self.assertEqual(r["tier"], "HIGH")

    def test_min_score_no_factors_met(self):
        r = _plasticity_score(
            q_entropy=0.5, negmem_density=60.0, avg_q_velocity=0.001, explore_rate=0.01
        )
        self.assertEqual(r["score"], 0)
        self.assertEqual(r["tier"], "CRITICAL")

    def test_q_entropy_factor(self):
        r_low  = _plasticity_score(1.0, 60.0, 0.001, 0.01)
        r_high = _plasticity_score(Q_ENTROPY_HIGH, 60.0, 0.001, 0.01)
        self.assertEqual(r_high["score"] - r_low["score"], 25)

    def test_negmem_headroom_factor(self):
        r_low  = _plasticity_score(1.0, 60.0, 0.001, 0.01)
        r_high = _plasticity_score(1.0, 20.0, 0.001, 0.01)
        self.assertEqual(r_high["score"] - r_low["score"], 25)

    def test_q_velocity_factor(self):
        r_low  = _plasticity_score(1.0, 60.0, 0.001, 0.01)
        r_high = _plasticity_score(1.0, 60.0, 0.01,  0.01)
        self.assertEqual(r_high["score"] - r_low["score"], 25)

    def test_explore_balance_factor(self):
        r_low  = _plasticity_score(1.0, 60.0, 0.001, 0.01)
        r_high = _plasticity_score(1.0, 60.0, 0.001, 0.25)
        self.assertEqual(r_high["score"] - r_low["score"], 25)

    def test_moderate_tier(self):
        # 2 factors met → 50
        r = _plasticity_score(Q_ENTROPY_HIGH, 20.0, 0.001, 0.01)
        self.assertEqual(r["score"], 50)
        self.assertEqual(r["tier"], "MODERATE")

    def test_low_tier(self):
        # 1 factor met → 25
        r = _plasticity_score(Q_ENTROPY_HIGH, 60.0, 0.001, 0.01)
        self.assertEqual(r["score"], 25)
        self.assertEqual(r["tier"], "LOW")

    def test_components_sum_matches_score(self):
        r = _plasticity_score(3.0, 20.0, 0.01, 0.20)
        total = sum(r["components"].values())
        self.assertEqual(total, r["score"])


# ── TestFossilizationRisk ─────────────────────────────────────────────────────

class TestFossilizationRisk(unittest.TestCase):

    def test_max_risk_all_factors(self):
        r = _fossilization_risk(
            negmem_density=60.0, q_entropy=1.0, avg_q_velocity=0.001, explore_rate=0.02
        )
        self.assertEqual(r["score"], 100)
        self.assertEqual(r["tier"], "HIGH")

    def test_min_risk_no_factors(self):
        r = _fossilization_risk(
            negmem_density=20.0, q_entropy=2.5, avg_q_velocity=0.01, explore_rate=0.20
        )
        self.assertEqual(r["score"], 0)
        self.assertEqual(r["tier"], "MINIMAL")

    def test_negmem_overload_factor(self):
        r_low  = _fossilization_risk(20.0, 2.5, 0.01, 0.20)
        r_high = _fossilization_risk(60.0, 2.5, 0.01, 0.20)
        self.assertEqual(r_high["score"] - r_low["score"], 30)

    def test_medium_tier_threshold(self):
        # negmem(30) + q_entropy(25) = 55 → MEDIUM (35-59)
        r = _fossilization_risk(60.0, 1.0, 0.01, 0.20)
        self.assertEqual(r["score"], 55)
        self.assertEqual(r["tier"], "MEDIUM")

    def test_components_sum_matches_score(self):
        r = _fossilization_risk(60.0, 1.0, 0.001, 0.02)
        total = sum(r["components"].values())
        self.assertEqual(total, r["score"])


# ── TestDriftRlNegmem ─────────────────────────────────────────────────────────

class TestDriftRlNegmem(unittest.TestCase):

    def _rl(self, pct): return {"profitable_pct": pct}
    def _nm(self, perm, total): return {"count": {"permanent": perm, "temporary": total - perm, "total": total}}

    def test_perfect_alignment(self):
        # RL failure 40% vs negmem density 40%
        r = _drift_rl_negmem(self._rl(0.6), self._nm(4, 10))
        self.assertAlmostEqual(r["drift_score"], 0.0, places=1)
        self.assertEqual(r["tier"], "ALIGNED")

    def test_high_drift(self):
        # RL failure 10% vs negmem density 90%
        r = _drift_rl_negmem(self._rl(0.9), self._nm(9, 10))
        self.assertGreaterEqual(r["drift_score"], DRIFT_HIGH)

    def test_zero_negmem(self):
        r = _drift_rl_negmem(self._rl(0.6), self._nm(0, 0))
        # total becomes max(0,1)=1; permanent=0 → density=0
        self.assertIsInstance(r["drift_score"], float)

    def test_required_keys(self):
        r = _drift_rl_negmem(self._rl(0.5), self._nm(2, 5))
        for key in ("drift_score", "tier", "rl_failure_rate_pct", "negmem_perm_density_pct"):
            self.assertIn(key, r)

    def test_drift_score_bounded_0_100(self):
        r = _drift_rl_negmem(self._rl(0.0), self._nm(0, 10))
        self.assertLessEqual(r["drift_score"], 100.0)
        self.assertGreaterEqual(r["drift_score"], 0.0)


# ── TestDriftRlPattern ────────────────────────────────────────────────────────

class TestDriftRlPattern(unittest.TestCase):

    def _pattern(self, samples, success):
        return {
            "pattern_id": "x", "samples": samples, "success": success,
            "confidence": 75.0,
            "key": {"regime": "TRENDING", "volatility": "LOW",
                    "instrument": "ES", "parameter": "rsi", "direction": "LONG"},
            "contexts": ["c1", "c2", "c3"], "last_seen": 1, "created_at": 1.0,
        }

    def test_no_formed_patterns_returns_aligned(self):
        rl = {"profitable_pct": 0.6}
        r  = _drift_rl_pattern(rl, {"formed_pattern_dicts": []})
        self.assertEqual(r["tier"], "ALIGNED")
        self.assertIn("note", r)

    def test_perfect_alignment(self):
        rl = {"profitable_pct": 0.6}
        pats = {"formed_pattern_dicts": [self._pattern(10, 6)]}
        r = _drift_rl_pattern(rl, pats)
        self.assertAlmostEqual(r["drift_score"], 0.0, places=1)

    def test_high_drift(self):
        rl = {"profitable_pct": 0.9}
        pats = {"formed_pattern_dicts": [self._pattern(10, 1)]}  # 10% success
        r = _drift_rl_pattern(rl, pats)
        self.assertGreaterEqual(r["drift_score"], DRIFT_HIGH)

    def test_required_keys_when_patterns_present(self):
        rl = {"profitable_pct": 0.6}
        pats = {"formed_pattern_dicts": [self._pattern(10, 6)]}
        r = _drift_rl_pattern(rl, pats)
        for key in ("drift_score", "tier", "rl_profitable_pct", "pattern_mean_success_pct"):
            self.assertIn(key, r)

    def test_zero_samples_excluded(self):
        rl = {"profitable_pct": 0.6}
        p  = self._pattern(0, 0)  # will be excluded
        r  = _drift_rl_pattern(rl, {"formed_pattern_dicts": [p]})
        self.assertIn("note", r)


# ── TestDriftRlEcology ────────────────────────────────────────────────────────

class TestDriftRlEcology(unittest.TestCase):

    def test_no_regime_avg_q_returns_aligned(self):
        rl = {"profitable_pct": 0.6, "regime_avg_q": {}}
        r  = _drift_rl_ecology(rl, {"regimes": {"TRENDING": {"weight": 1.1}}}, {})
        self.assertEqual(r["tier"], "ALIGNED")
        self.assertIn("note", r)

    def test_no_shared_regimes_returns_aligned(self):
        rl = {"profitable_pct": 0.6}
        r  = _drift_rl_ecology(
            rl,
            {"regimes": {"TRENDING": {"weight": 1.1}}},
            {"MEAN_REVERTING": 0.5},
        )
        self.assertEqual(r["tier"], "ALIGNED")

    def test_full_agreement(self):
        rl = {"profitable_pct": 0.6}
        ecology = {"regimes": {
            "TRENDING":      {"weight": 1.2},  # bullish
            "MEAN_REVERTING": {"weight": 0.8}, # bearish
        }}
        regime_avg_q = {"TRENDING": 0.3, "MEAN_REVERTING": -0.1}
        r = _drift_rl_ecology(rl, ecology, regime_avg_q)
        self.assertEqual(r["drift_score"], 0.0)

    def test_full_conflict(self):
        rl = {"profitable_pct": 0.6}
        ecology = {"regimes": {
            "TRENDING":      {"weight": 1.2},  # bullish
            "MEAN_REVERTING": {"weight": 1.5}, # bullish
        }}
        regime_avg_q = {"TRENDING": -0.1, "MEAN_REVERTING": -0.2}  # both bearish
        r = _drift_rl_ecology(rl, ecology, regime_avg_q)
        self.assertEqual(r["drift_score"], 100.0)

    def test_partial_conflict(self):
        rl = {"profitable_pct": 0.6}
        ecology = {"regimes": {
            "TRENDING":      {"weight": 1.2},  # bullish
            "MEAN_REVERTING": {"weight": 0.5}, # bearish
        }}
        regime_avg_q = {"TRENDING": -0.1, "MEAN_REVERTING": -0.2}  # TRENDING disagrees
        r = _drift_rl_ecology(rl, ecology, regime_avg_q)
        self.assertAlmostEqual(r["drift_score"], 50.0, places=1)


# ── TestDriftPatternNegmem ────────────────────────────────────────────────────

class TestDriftPatternNegmem(unittest.TestCase):

    def _pat(self, regime, samples, success):
        return {
            "pattern_id": "x",
            "key": {"regime": regime, "volatility": "LOW",
                    "instrument": "ES", "parameter": "rsi", "direction": "LONG"},
            "samples": samples, "success": success, "confidence": 75.0,
            "contexts": ["c1", "c2", "c3"], "last_seen": 1, "created_at": 1.0,
        }

    def _nm_entry(self, regime, permanent):
        return {"key_str": f"{regime}|LOW|ES|rsi|LONG", "permanent": permanent, "rollbacks": 1, "score": 0.9}

    def test_no_formed_returns_aligned(self):
        r = _drift_pattern_negmem({"formed_pattern_dicts": []}, {"entries": [self._nm_entry("TRENDING", False)]})
        self.assertEqual(r["tier"], "ALIGNED")

    def test_no_entries_returns_aligned(self):
        r = _drift_pattern_negmem({"formed_pattern_dicts": [self._pat("TRENDING", 10, 6)]}, {"entries": []})
        self.assertEqual(r["tier"], "ALIGNED")

    def test_no_shared_regimes_returns_aligned(self):
        pats = {"formed_pattern_dicts": [self._pat("TRENDING", 10, 6)]}
        nms  = {"entries": [self._nm_entry("MEAN_REVERTING", False)]}
        r = _drift_pattern_negmem(pats, nms)
        self.assertIn("note", r)

    def test_perfect_alignment(self):
        # Pattern: 60% success; NegMem: 40% permanent (complement=60%)
        pats = {"formed_pattern_dicts": [self._pat("TRENDING", 10, 6)]}
        nms  = {"entries": [
            self._nm_entry("TRENDING", True),
            self._nm_entry("TRENDING", True),
            self._nm_entry("TRENDING", False),
            self._nm_entry("TRENDING", False),
            self._nm_entry("TRENDING", False),
        ]}
        r = _drift_pattern_negmem(pats, nms)
        self.assertAlmostEqual(r["drift_score"], 0.0, places=1)

    def test_high_disagreement(self):
        # Pattern: 100% success; NegMem: 100% permanent (complement=0%)
        pats = {"formed_pattern_dicts": [self._pat("TRENDING", 10, 10)]}
        nms  = {"entries": [self._nm_entry("TRENDING", True) for _ in range(5)]}
        r = _drift_pattern_negmem(pats, nms)
        self.assertAlmostEqual(r["drift_score"], 100.0, places=1)

    def test_per_regime_present(self):
        pats = {"formed_pattern_dicts": [self._pat("TRENDING", 10, 6)]}
        nms  = {"entries": [self._nm_entry("TRENDING", False)] * 5}
        r = _drift_pattern_negmem(pats, nms)
        self.assertIn("per_regime", r)


# ── TestDriftAlphaContextRl ───────────────────────────────────────────────────

class TestDriftAlphaContextRl(unittest.TestCase):

    def test_perfect_alignment(self):
        ac = {"profitable_count": 6, "total_contexts": 10}
        rl = {"profitable_pct": 0.6}
        r  = _drift_alpha_context_rl(ac, rl)
        self.assertAlmostEqual(r["drift_score"], 0.0, places=1)

    def test_high_drift(self):
        ac = {"profitable_count": 9, "total_contexts": 10}  # 90%
        rl = {"profitable_pct": 0.1}                         # 10%
        r  = _drift_alpha_context_rl(ac, rl)
        self.assertGreaterEqual(r["drift_score"], DRIFT_HIGH)

    def test_zero_ac_contexts(self):
        ac = {"profitable_count": 0, "total_contexts": 0}
        rl = {"profitable_pct": 0.5}
        r  = _drift_alpha_context_rl(ac, rl)
        self.assertIsInstance(r["drift_score"], float)

    def test_required_keys(self):
        ac = {"profitable_count": 5, "total_contexts": 10}
        rl = {"profitable_pct": 0.6}
        r  = _drift_alpha_context_rl(ac, rl)
        for key in ("drift_score", "tier", "alpha_context_pct", "rl_profitable_pct"):
            self.assertIn(key, r)


# ── TestClassifyCognitiveState ────────────────────────────────────────────────

class TestClassifyCognitiveState(unittest.TestCase):

    def _classify(self, **kwargs):
        # avg_q_velocity=0.003 is below AVG_VELOCITY_ACTIVE so ADAPTIVE_CONVERGENCE
        # doesn't fire and the default falls through to HEALTHY_PLASTICITY.
        defaults = dict(
            negmem_density=20.0, pattern_formation_rate=30.0,
            max_drift=20.0, avg_drift=15.0,
            fossilization_score=10, plasticity_score=75,
            negmem_total=5, rl_total_contexts=50,
            explore_rate=0.20, avg_q_velocity=0.003,
        )
        defaults.update(kwargs)
        return _classify_cognitive_state(**defaults)

    def test_healthy_plasticity_default(self):
        self.assertEqual(self._classify(), HEALTHY_PLASTICITY)

    def test_memory_saturation_priority(self):
        r = self._classify(
            negmem_density=70.0, pattern_formation_rate=70.0,
            max_drift=80.0, avg_drift=60.0,
            fossilization_score=80, plasticity_score=10,
        )
        self.assertEqual(r, MEMORY_SATURATION)

    def test_ontology_fragmentation_max_drift(self):
        r = self._classify(max_drift=75.0)
        self.assertEqual(r, ONTOLOGY_FRAGMENTATION)

    def test_ontology_fragmentation_avg_drift(self):
        r = self._classify(avg_drift=55.0)
        self.assertEqual(r, ONTOLOGY_FRAGMENTATION)

    def test_premature_fossilization(self):
        r = self._classify(fossilization_score=70, plasticity_score=20)
        self.assertEqual(r, PREMATURE_FOSSILIZATION)

    def test_ecological_amnesia(self):
        r = self._classify(negmem_total=0, rl_total_contexts=50, explore_rate=0.5)
        self.assertEqual(r, ECOLOGICAL_AMNESIA)

    def test_adaptive_convergence(self):
        # Must explicitly set avg_q_velocity above AVG_VELOCITY_ACTIVE to trigger
        r = self._classify(
            avg_q_velocity=0.01, explore_rate=0.20,
            max_drift=30.0, plasticity_score=75,
        )
        self.assertEqual(r, ADAPTIVE_CONVERGENCE)

    def test_memory_saturation_beats_fragmentation(self):
        # Both conditions met — MEMORY_SATURATION has priority
        r = self._classify(
            negmem_density=70.0, pattern_formation_rate=70.0,
            max_drift=75.0, avg_drift=55.0,
        )
        self.assertEqual(r, MEMORY_SATURATION)


# ── TestComputeStructure ──────────────────────────────────────────────────────

class TestComputeStructure(unittest.TestCase):

    def setUp(self):
        self.result = compute_memory_pressure_dynamics(_make_state())

    def test_top_level_keys_present(self):
        for key in ("scope_note", "cognitive_state", "memory_pressure",
                    "ontology_drift", "drift_heatmap", "summary_stats"):
            self.assertIn(key, self.result, f"Missing key: {key}")

    def test_scope_note_non_empty(self):
        self.assertTrue(len(self.result["scope_note"]) > 10)

    def test_memory_pressure_keys(self):
        mp = self.result["memory_pressure"]
        for key in ("negmem_density_pct", "pattern_formation_rate_pct", "q_entropy_bits",
                    "avg_q_velocity", "exploration_rate_pct", "plasticity", "fossilization_risk"):
            self.assertIn(key, mp)

    def test_ontology_drift_five_pairs(self):
        od = self.result["ontology_drift"]
        for pair in ("RL_vs_NegMem", "RL_vs_Pattern", "RL_vs_Ecology",
                     "Pattern_vs_NegMem", "AlphaContext_vs_RL"):
            self.assertIn(pair, od)

    def test_drift_heatmap_is_list(self):
        self.assertIsInstance(self.result["drift_heatmap"], list)

    def test_drift_heatmap_sorted_descending(self):
        scores = [h["drift_score"] for h in self.result["drift_heatmap"]]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_summary_stats_keys(self):
        ss = self.result["summary_stats"]
        for key in ("total_pairs", "avg_drift", "max_drift", "min_drift"):
            self.assertIn(key, ss)

    def test_cognitive_state_is_known_label(self):
        known = {HEALTHY_PLASTICITY, PREMATURE_FOSSILIZATION, ONTOLOGY_FRAGMENTATION,
                 ADAPTIVE_CONVERGENCE, MEMORY_SATURATION, ECOLOGICAL_AMNESIA}
        self.assertIn(self.result["cognitive_state"], known)

    def test_plasticity_has_score_and_tier(self):
        p = self.result["memory_pressure"]["plasticity"]
        self.assertIn("score", p)
        self.assertIn("tier", p)

    def test_fossilization_risk_has_score_and_tier(self):
        fr = self.result["memory_pressure"]["fossilization_risk"]
        self.assertIn("score", fr)
        self.assertIn("tier", fr)


# ── TestEmptyAndEdgeCases ─────────────────────────────────────────────────────

class TestEmptyAndEdgeCases(unittest.TestCase):

    def test_empty_state_returns_scope_note(self):
        r = compute_memory_pressure_dynamics({})
        self.assertIn("scope_note", r)
        self.assertNotIn("error", r)

    def test_none_values_dont_crash(self):
        state = {
            "rl": {"profitable_pct": None, "total_contexts": None,
                   "q_values": None, "q_velocities": None,
                   "toxic_count": None, "explore_ratio": None, "regime_avg_q": None},
            "negmem": {"count": None, "entries": None},
            "patterns": {"total_patterns": None, "formed_patterns": None, "formed_pattern_dicts": None},
            "ecology": {"regimes": None},
            "alpha_context": {"profitable_count": None, "toxic_count": None, "total_contexts": None},
        }
        r = compute_memory_pressure_dynamics(state)
        self.assertIn("scope_note", r)

    def test_zero_negmem_no_crash(self):
        state = _make_state(nm_permanent=0, nm_total=0, nm_entries=[])
        r = compute_memory_pressure_dynamics(state)
        self.assertAlmostEqual(r["memory_pressure"]["negmem_density_pct"], 0.0)

    def test_zero_patterns_no_crash(self):
        state = _make_state(pat_total=0, pat_formed=0, formed_dicts=[])
        r = compute_memory_pressure_dynamics(state)
        self.assertAlmostEqual(r["memory_pressure"]["pattern_formation_rate_pct"], 0.0)

    def test_never_raises_on_bad_input(self):
        for bad in [None, "string", 42, [], 3.14]:
            try:
                r = compute_memory_pressure_dynamics(bad)
                self.assertIn("scope_note", r)
            except Exception as e:
                self.fail(f"compute_memory_pressure_dynamics raised {e} for input {bad!r}")


# ── TestDriftHeatmapIntegrity ─────────────────────────────────────────────────

class TestDriftHeatmapIntegrity(unittest.TestCase):

    def test_all_pairs_represented(self):
        r = compute_memory_pressure_dynamics(_make_state())
        pair_names = {h["pair"] for h in r["drift_heatmap"]}
        expected = {"RL_vs_NegMem", "RL_vs_Pattern", "RL_vs_Ecology",
                    "Pattern_vs_NegMem", "AlphaContext_vs_RL"}
        self.assertEqual(pair_names, expected)

    def test_heatmap_entries_have_tier(self):
        r = compute_memory_pressure_dynamics(_make_state())
        for h in r["drift_heatmap"]:
            self.assertIn("tier", h)

    def test_summary_max_matches_heatmap_max(self):
        r = compute_memory_pressure_dynamics(_make_state())
        heatmap_max = r["drift_heatmap"][0]["drift_score"] if r["drift_heatmap"] else 0.0
        self.assertAlmostEqual(r["summary_stats"]["max_drift"], heatmap_max, places=1)

    def test_total_pairs_matches_heatmap_length(self):
        r = compute_memory_pressure_dynamics(_make_state())
        self.assertEqual(r["summary_stats"]["total_pairs"], len(r["drift_heatmap"]))


# ── TestNoExecutionMutation ───────────────────────────────────────────────────

class TestNoExecutionMutation(unittest.TestCase):

    def test_state_dict_not_mutated(self):
        state = _make_state()
        import copy
        original = copy.deepcopy(state)
        compute_memory_pressure_dynamics(state)
        self.assertEqual(state["rl"]["profitable_pct"], original["rl"]["profitable_pct"])
        self.assertEqual(state["negmem"]["count"]["permanent"],
                         original["negmem"]["count"]["permanent"])

    def test_repeated_calls_same_result(self):
        state = _make_state()
        r1 = compute_memory_pressure_dynamics(state)
        r2 = compute_memory_pressure_dynamics(state)
        self.assertEqual(r1["cognitive_state"], r2["cognitive_state"])
        self.assertEqual(r1["summary_stats"]["max_drift"], r2["summary_stats"]["max_drift"])

    def test_function_is_pure(self):
        # Calling with different states returns different results
        state_high = _make_state(nm_permanent=9, nm_total=10, rl_profitable_pct=0.9)
        state_low  = _make_state(nm_permanent=1, nm_total=10, rl_profitable_pct=0.5)
        r_high = compute_memory_pressure_dynamics(state_high)
        r_low  = compute_memory_pressure_dynamics(state_low)
        drift_high = r_high["ontology_drift"]["RL_vs_NegMem"]["drift_score"]
        drift_low  = r_low["ontology_drift"]["RL_vs_NegMem"]["drift_score"]
        self.assertGreater(drift_high, drift_low)


# ── TestBackwardCompatibility ─────────────────────────────────────────────────

class TestBackwardCompatibility(unittest.TestCase):

    def test_missing_regime_avg_q_key(self):
        state = _make_state()
        del state["rl"]["regime_avg_q"]
        r = compute_memory_pressure_dynamics(state)
        self.assertIn("scope_note", r)

    def test_missing_formed_pattern_dicts(self):
        state = _make_state()
        del state["patterns"]["formed_pattern_dicts"]
        r = compute_memory_pressure_dynamics(state)
        self.assertIn("scope_note", r)

    def test_missing_ecology_regimes(self):
        state = _make_state()
        del state["ecology"]["regimes"]
        r = compute_memory_pressure_dynamics(state)
        self.assertIn("scope_note", r)

    def test_extra_unknown_keys_ignored(self):
        state = _make_state()
        state["rl"]["unknown_future_field"] = "value"
        state["negmem"]["another_field"]    = 999
        r = compute_memory_pressure_dynamics(state)
        self.assertIn("cognitive_state", r)


if __name__ == "__main__":
    unittest.main()
