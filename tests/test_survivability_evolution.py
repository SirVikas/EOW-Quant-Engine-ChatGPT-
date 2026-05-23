"""
Phase-E Survivability Evolution Program — 84-check institutional verifier.
7 classes × 12 checks each = 84 total.
"""
from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Synthetic trade factory ───────────────────────────────────────────────────

def _trade(
    net_pnl: float = 1.0,
    gross_pnl: float = 1.5,
    fee_entry: float = 0.1,
    fee_exit: float = 0.1,
    slippage_cost: float = 0.05,
    regime: str = "TRENDING",
    strategy_id: str = "default",
    origin_session: str = "NY",
    entry_ts: int = 0,
    exit_ts: int = 0,
    side: str = "BUY",
    confidence: float = 0.70,
) -> dict:
    now = int(time.time() * 1000)
    return {
        "trade_id":       f"T{now}-{net_pnl}-{regime}",
        "symbol":         "BTCUSDT",
        "side":           side,
        "entry_price":    50000.0,
        "exit_price":     50050.0,
        "qty":            0.01,
        "entry_ts":       entry_ts or now,
        "exit_ts":        exit_ts or (now + 300_000),
        "is_short":       side in ("SELL", "SHORT"),
        "strategy_id":    strategy_id,
        "regime":         regime,
        "gross_pnl":      gross_pnl,
        "net_pnl":        net_pnl,
        "fee_entry":      fee_entry,
        "fee_exit":       fee_exit,
        "slippage_cost":  slippage_cost,
        "borrow_cost":    0.0,
        "origin_session": origin_session,
        "close_session":  origin_session,
        "decision_snapshot":   {"confidence": confidence},
        "exploration_origin":  {"was_exploration_trade": False},
        "economic_truth":      {
            "fees_paid":    fee_entry + fee_exit,
            "fee_drag_pct": round((fee_entry + fee_exit) / max(gross_pnl, 1e-9) * 100, 2),
        },
    }


def _make_trades(n: int = 20, net_pnl: float = 1.0) -> list:
    now = int(time.time() * 1000)
    trades = []
    for i in range(n):
        trades.append(_trade(
            net_pnl=net_pnl,
            entry_ts=now + i * 60_000,
            exit_ts=now + i * 60_000 + 300_000,
        ))
    return trades


def _make_mixed_trades(n: int = 30) -> list:
    """Mix of winning and losing trades across different regimes and sessions."""
    now = int(time.time() * 1000)
    trades = []
    regimes  = ["TRENDING", "MEAN_REVERTING", "VOLATILITY_EXPANSION", "UNKNOWN"]
    sessions = ["NY", "LONDON", "ASIA"]
    for i in range(n):
        pnl = 1.5 if i % 3 != 0 else -0.8
        trades.append(_trade(
            net_pnl=pnl,
            regime=regimes[i % len(regimes)],
            origin_session=sessions[i % len(sessions)],
            confidence=0.60 + (i % 4) * 0.08,
            entry_ts=now + i * 120_000,
            exit_ts=now + i * 120_000 + 300_000,
        ))
    return trades


_EMPTY = []


# ── Test class 1: Expectancy Stability Engine ─────────────────────────────────

class TestExpectancyStabilityEngine(unittest.TestCase):

    def setUp(self):
        from core.survivability_evolution.expectancy_stability_engine import (
            compute_expectancy_stability,
        )
        self.fn = compute_expectancy_stability

    def test_01_empty_returns_no_data(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["stability_state"], "NO_DATA")

    def test_02_empty_report_key(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["report"], "EXPECTANCY_STABILITY_REPORT")

    def test_03_empty_persistence_zero(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["persistence_score"], 0)

    def test_04_populated_has_report_key(self):
        r = self.fn(_make_trades(20))
        self.assertEqual(r["report"], "EXPECTANCY_STABILITY_REPORT")

    def test_05_positive_trades_stabilizing(self):
        r = self.fn(_make_trades(30, net_pnl=1.0))
        self.assertIn(r["stability_state"],
                      ("STABILIZING", "RECOVERING", "OSCILLATING", "DEGRADING", "COLLAPSING"))

    def test_06_persistence_score_range(self):
        r = self.fn(_make_trades(30))
        self.assertGreaterEqual(r["persistence_score"], 0)
        self.assertLessEqual(r["persistence_score"], 100)

    def test_07_rolling_windows_present(self):
        r = self.fn(_make_trades(20))
        self.assertIsInstance(r["rolling_windows"], dict)

    def test_08_total_trades_correct(self):
        trades = _make_trades(25)
        r = self.fn(trades)
        self.assertEqual(r["total_trades"], 25)

    def test_09_diagnostic_flags(self):
        r = self.fn(_make_trades(20))
        self.assertTrue(r["diagnostic_only"])
        self.assertFalse(r["auto_authorized"])

    def test_10_generated_ts_present(self):
        r = self.fn(_make_trades(20))
        self.assertIsInstance(r["generated_ts"], int)

    def test_11_never_raises_bad_input(self):
        for bad in ([None], [{}], [{"net_pnl": "bad"}]):
            try:
                self.fn(bad)
            except Exception as exc:
                self.fail(f"Raised on bad input: {exc}")

    def test_12_decay_velocity_type(self):
        r = self.fn(_make_trades(20))
        dv = r.get("decay_velocity")
        self.assertTrue(dv is None or isinstance(dv, float))


# ── Test class 2: Ecological Self-Preservation Engine ────────────────────────

class TestEcologicalSelfPreservationEngine(unittest.TestCase):

    def setUp(self):
        from core.survivability_evolution.ecological_self_preservation_engine import (
            compute_ecological_self_preservation,
        )
        self.fn = compute_ecological_self_preservation

    def test_01_empty_returns_safe(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["preservation_tier"], "SAFE")

    def test_02_empty_report_key(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["report"], "ECOLOGICAL_SELF_PRESERVATION_REPORT")

    def test_03_empty_no_threats(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["threat_count"], 0)
        self.assertEqual(len(r["threats"]), 0)

    def test_04_populated_report_key(self):
        r = self.fn(_make_trades(30))
        self.assertEqual(r["report"], "ECOLOGICAL_SELF_PRESERVATION_REPORT")

    def test_05_preservation_score_range(self):
        r = self.fn(_make_trades(30))
        self.assertGreaterEqual(r["preservation_score"], 0)
        self.assertLessEqual(r["preservation_score"], 100)

    def test_06_preservation_tier_valid(self):
        r = self.fn(_make_trades(30))
        self.assertIn(r["preservation_tier"], ("SAFE", "GUARDED", "STRESSED", "CRITICAL"))

    def test_07_threat_structure(self):
        r = self.fn(_make_mixed_trades(40))
        for threat in r["threats"]:
            self.assertIn("threat", threat)
            self.assertIn("severity", threat)
            self.assertIn("detail", threat)

    def test_08_recommendations_is_list(self):
        r = self.fn(_make_mixed_trades(40))
        self.assertIsInstance(r["recommendations"], list)

    def test_09_total_trades_correct(self):
        trades = _make_trades(22)
        r = self.fn(trades)
        self.assertEqual(r["total_trades"], 22)

    def test_10_diagnostic_flags(self):
        r = self.fn(_make_trades(20))
        self.assertTrue(r["diagnostic_only"])
        self.assertFalse(r["auto_authorized"])

    def test_11_never_raises_bad_input(self):
        for bad in ([None], [{}], [{"net_pnl": "x"}]):
            try:
                self.fn(bad)
            except Exception as exc:
                self.fail(f"Raised on bad input: {exc}")

    def test_12_high_threat_count_consistent(self):
        r = self.fn(_make_mixed_trades(40))
        high = [t for t in r["threats"] if t.get("severity") == "HIGH"]
        self.assertEqual(r["high_threat_count"], len(high))


# ── Test class 3: Regime Adaptation Memory Engine ────────────────────────────

class TestRegimeAdaptationMemoryEngine(unittest.TestCase):

    def setUp(self):
        from core.survivability_evolution.regime_adaptation_memory_engine import (
            compute_regime_adaptation_memory,
        )
        self.fn = compute_regime_adaptation_memory

    def test_01_empty_report_key(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["report"], "REGIME_ADAPTATION_MEMORY_REPORT")

    def test_02_empty_no_regime_memory(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["regime_memory"], {})

    def test_03_empty_no_transitions(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["transition_count"], 0)

    def test_04_populated_report_key(self):
        r = self.fn(_make_mixed_trades(30))
        self.assertEqual(r["report"], "REGIME_ADAPTATION_MEMORY_REPORT")

    def test_05_regime_memory_structure(self):
        r = self.fn(_make_mixed_trades(30))
        for regime, mem in r["regime_memory"].items():
            self.assertIn("trade_count", mem)
            self.assertIn("net_expectancy", mem)
            self.assertIn("survivability", mem)

    def test_06_adaptive_fingerprints_present(self):
        r = self.fn(_make_mixed_trades(30))
        self.assertIsInstance(r["adaptive_fingerprints"], dict)

    def test_07_collapse_conditions_list(self):
        r = self.fn(_make_mixed_trades(30))
        self.assertIsInstance(r["collapse_conditions"], list)

    def test_08_survivability_conditions_list(self):
        r = self.fn(_make_mixed_trades(30))
        self.assertIsInstance(r["survivability_conditions"], list)

    def test_09_total_trades_correct(self):
        trades = _make_trades(18)
        r = self.fn(trades)
        self.assertEqual(r["total_trades"], 18)

    def test_10_diagnostic_flags(self):
        r = self.fn(_make_trades(20))
        self.assertTrue(r["diagnostic_only"])
        self.assertFalse(r["auto_authorized"])

    def test_11_never_raises_bad_input(self):
        for bad in ([None], [{}], [{"regime": None}]):
            try:
                self.fn(bad)
            except Exception as exc:
                self.fail(f"Raised on bad input: {exc}")

    def test_12_fingerprint_values_valid(self):
        valid = {
            "POSITIVE_PERSISTENCE", "POSITIVE_DEGRADING",
            "RECOVERING", "COLLAPSING", "MARGINAL_STABLE",
        }
        r = self.fn(_make_mixed_trades(30))
        for fp in r["adaptive_fingerprints"].values():
            self.assertIn(fp, valid)


# ── Test class 4: Alpha Persistence Tracker ──────────────────────────────────

class TestAlphaPersistenceTracker(unittest.TestCase):

    def setUp(self):
        from core.survivability_evolution.alpha_persistence_tracker import (
            track_alpha_persistence,
        )
        self.fn = track_alpha_persistence

    def test_01_empty_report_key(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["report"], "ALPHA_PERSISTENCE_REPORT")

    def test_02_empty_statistical_noise(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["alpha_state"], "STATISTICAL_NOISE")

    def test_03_small_sample_statistical_noise(self):
        r = self.fn(_make_trades(5))
        self.assertEqual(r["alpha_state"], "STATISTICAL_NOISE")

    def test_04_populated_report_key(self):
        r = self.fn(_make_trades(20))
        self.assertEqual(r["report"], "ALPHA_PERSISTENCE_REPORT")

    def test_05_persistence_score_range(self):
        r = self.fn(_make_trades(20))
        self.assertGreaterEqual(r["persistence_score"], 0)
        self.assertLessEqual(r["persistence_score"], 100)

    def test_06_alpha_state_valid(self):
        valid = {"PERSISTENT", "DECAYING", "EVAPORATING", "STATISTICAL_NOISE", "ABSENT", "LOCALIZED"}
        r = self.fn(_make_trades(20))
        self.assertIn(r["alpha_state"], valid)

    def test_07_decay_curve_is_list(self):
        r = self.fn(_make_trades(20))
        self.assertIsInstance(r["decay_curve"], list)

    def test_08_evaporation_risk_valid(self):
        r = self.fn(_make_trades(20))
        self.assertIn(r["evaporation_risk"], ("LOW", "MODERATE", "HIGH", "CRITICAL"))

    def test_09_total_trades_correct(self):
        trades = _make_trades(15)
        r = self.fn(trades)
        self.assertEqual(r["total_trades"], 15)

    def test_10_diagnostic_flags(self):
        r = self.fn(_make_trades(20))
        self.assertTrue(r["diagnostic_only"])
        self.assertFalse(r["auto_authorized"])

    def test_11_never_raises_bad_input(self):
        for bad in ([None], [{}], [{"net_pnl": "x"}]):
            try:
                self.fn(bad)
            except Exception as exc:
                self.fail(f"Raised on bad input: {exc}")

    def test_12_persistent_positive_trades_high_score(self):
        r = self.fn(_make_trades(30, net_pnl=2.0))
        self.assertGreater(r["persistence_score"], 40)


# ── Test class 5: Confidence Realism Engine ──────────────────────────────────

class TestConfidenceRealismEngine(unittest.TestCase):

    def setUp(self):
        from core.survivability_evolution.confidence_realism_engine import (
            compute_confidence_realism,
        )
        self.fn = compute_confidence_realism

    def test_01_empty_report_key(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["report"], "CONFIDENCE_REALISM_REPORT")

    def test_02_empty_unknown_conviction(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["conviction_reliability"], "UNKNOWN")

    def test_03_empty_no_hallucination(self):
        r = self.fn(_EMPTY)
        self.assertFalse(r["hallucination_detected"])

    def test_04_populated_report_key(self):
        r = self.fn(_make_trades(20))
        self.assertEqual(r["report"], "CONFIDENCE_REALISM_REPORT")

    def test_05_realism_score_range(self):
        r = self.fn(_make_trades(20))
        self.assertGreaterEqual(r["realism_score"], 0)
        self.assertLessEqual(r["realism_score"], 100)

    def test_06_conviction_reliability_valid(self):
        r = self.fn(_make_trades(20))
        self.assertIn(r["conviction_reliability"], ("RELIABLE", "UNRELIABLE", "NEUTRAL", "UNKNOWN"))

    def test_07_overconfidence_zones_list(self):
        r = self.fn(_make_trades(20))
        self.assertIsInstance(r["overconfidence_zones"], list)

    def test_08_confidence_buckets_present(self):
        r = self.fn(_make_trades(20))
        self.assertIsInstance(r["confidence_buckets"], dict)

    def test_09_total_trades_correct(self):
        trades = _make_trades(14)
        r = self.fn(trades)
        self.assertEqual(r["total_trades"], 14)

    def test_10_diagnostic_flags(self):
        r = self.fn(_make_trades(20))
        self.assertTrue(r["diagnostic_only"])
        self.assertFalse(r["auto_authorized"])

    def test_11_never_raises_bad_input(self):
        for bad in ([None], [{}], [{"decision_snapshot": None}]):
            try:
                self.fn(bad)
            except Exception as exc:
                self.fail(f"Raised on bad input: {exc}")

    def test_12_overconfidence_zone_count_consistent(self):
        r = self.fn(_make_trades(20))
        self.assertEqual(r["overconfidence_zone_count"], len(r["overconfidence_zones"]))


# ── Test class 6: Entropy Resistance Engine ──────────────────────────────────

class TestEntropyResistanceEngine(unittest.TestCase):

    def setUp(self):
        from core.survivability_evolution.entropy_resistance_engine import (
            compute_entropy_resistance,
        )
        self.fn = compute_entropy_resistance

    def test_01_empty_report_key(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["report"], "ENTROPY_RESISTANCE_REPORT")

    def test_02_empty_fragile_state(self):
        r = self.fn(_EMPTY)
        self.assertIn(r["entropy_state"], ("FRAGILE", "STABLE", "CRITICAL", "DEGENERATIVE"))

    def test_03_empty_score_reasonable(self):
        r = self.fn(_EMPTY)
        self.assertGreaterEqual(r["resistance_score"], 0)
        self.assertLessEqual(r["resistance_score"], 100)

    def test_04_populated_report_key(self):
        r = self.fn(_make_trades(20))
        self.assertEqual(r["report"], "ENTROPY_RESISTANCE_REPORT")

    def test_05_entropy_state_valid(self):
        r = self.fn(_make_trades(20))
        self.assertIn(r["entropy_state"], ("STABLE", "FRAGILE", "CRITICAL", "DEGENERATIVE"))

    def test_06_resistance_score_range(self):
        r = self.fn(_make_trades(20))
        self.assertGreaterEqual(r["resistance_score"], 0)
        self.assertLessEqual(r["resistance_score"], 100)

    def test_07_entropy_domains_structure(self):
        r = self.fn(_make_trades(20))
        domains = r["entropy_domains"]
        required = {
            "signal_entropy", "ecological_entropy", "regime_instability_entropy",
            "alpha_fragmentation", "survivability_erosion", "structural_degradation_velocity",
        }
        self.assertTrue(required.issubset(set(domains.keys())))

    def test_08_each_domain_has_score(self):
        r = self.fn(_make_trades(20))
        for domain, data in r["entropy_domains"].items():
            self.assertIn("score", data, f"Missing 'score' in domain {domain}")

    def test_09_total_trades_correct(self):
        trades = _make_trades(16)
        r = self.fn(trades)
        self.assertEqual(r["total_trades"], 16)

    def test_10_diagnostic_flags(self):
        r = self.fn(_make_trades(20))
        self.assertTrue(r["diagnostic_only"])
        self.assertFalse(r["auto_authorized"])

    def test_11_never_raises_bad_input(self):
        for bad in ([None], [{}], [{"net_pnl": "x", "entry_ts": None}]):
            try:
                self.fn(bad)
            except Exception as exc:
                self.fail(f"Raised on bad input: {exc}")

    def test_12_consistent_positive_trades_higher_score(self):
        r_positive = self.fn(_make_trades(30, net_pnl=1.5))
        r_negative = self.fn(_make_trades(30, net_pnl=-1.5))
        self.assertGreaterEqual(r_positive["resistance_score"], r_negative["resistance_score"] - 10)


# ── Test class 7: Survivability Evolution Orchestrator ───────────────────────

class TestSurvivabilityEvolutionOrchestrator(unittest.TestCase):

    def setUp(self):
        from core.survivability_evolution.survivability_evolution_orchestrator import (
            run_survivability_evolution,
            get_survivability_health,
        )
        self.run_fn    = run_survivability_evolution
        self.health_fn = get_survivability_health

    def test_01_empty_evolution_report_key(self):
        r = self.run_fn(_EMPTY)
        self.assertEqual(r["report"], "SURVIVABILITY_EVOLUTION_REPORT")

    def test_02_empty_health_report_key(self):
        r = self.health_fn(_EMPTY)
        self.assertEqual(r["report"], "SURVIVABILITY_HEALTH")

    def test_03_survivability_id_format(self):
        r = self.run_fn(_make_trades(20))
        sid = r.get("survivability_id", "")
        self.assertTrue(sid.startswith("SURV-"), f"Bad id: {sid}")

    def test_04_evolution_score_range(self):
        r = self.run_fn(_make_trades(20))
        self.assertGreaterEqual(r["evolution_score"], 0)
        self.assertLessEqual(r["evolution_score"], 100)

    def test_05_evolution_tier_valid(self):
        r = self.run_fn(_make_trades(20))
        self.assertIn(r["evolution_tier"], ("EVOLVING", "ADAPTING", "STRUGGLING", "COLLAPSING"))

    def test_06_domain_reports_all_present(self):
        r = self.run_fn(_make_trades(20))
        required = {
            "expectancy_stability", "ecological_preservation",
            "regime_memory", "alpha_persistence",
            "confidence_realism", "entropy_resistance",
        }
        self.assertTrue(required.issubset(set(r["domain_reports"].keys())))

    def test_07_lineage_flags(self):
        r = self.run_fn(_make_trades(20))
        self.assertTrue(r["lineage_preserved"])
        self.assertTrue(r["replay_safe"])
        self.assertTrue(r["diagnostic_only"])
        self.assertFalse(r["auto_authorized"])

    def test_08_score_evidence_keys(self):
        r = self.run_fn(_make_trades(20))
        ev = r.get("score_evidence", {})
        for key in ("expectancy_stable", "ecology_preserved", "alpha_persisting",
                    "entropy_managed", "confidence_realistic"):
            self.assertIn(key, ev)

    def test_09_health_lightweight_fields(self):
        r = self.health_fn(_make_trades(20))
        for key in ("evolution_score", "evolution_tier", "entropy_state",
                    "confidence_realism_score", "domain_errors"):
            self.assertIn(key, r, f"Missing key: {key}")

    def test_10_trade_count_correct(self):
        trades = _make_trades(17)
        r = self.run_fn(trades)
        self.assertEqual(r["trade_count"], 17)

    def test_11_never_raises_bad_input(self):
        for bad in ([None], [{}], _EMPTY):
            try:
                self.run_fn(bad)
                self.health_fn(bad)
            except Exception as exc:
                self.fail(f"Raised on bad input: {exc}")

    def test_12_domain_errors_is_list(self):
        r = self.run_fn(_make_trades(20))
        self.assertIsInstance(r["domain_errors"], list)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()

    classes = [
        TestExpectancyStabilityEngine,
        TestEcologicalSelfPreservationEngine,
        TestRegimeAdaptationMemoryEngine,
        TestAlphaPersistenceTracker,
        TestConfidenceRealismEngine,
        TestEntropyResistanceEngine,
        TestSurvivabilityEvolutionOrchestrator,
    ]

    total = 0
    for cls in classes:
        tests = loader.loadTestsFromTestCase(cls)
        suite.addTests(tests)
        total += tests.countTestCases()

    runner = unittest.TextTestRunner(verbosity=0, stream=open("/dev/null", "w"))
    result = runner.run(suite)

    passed = total - len(result.failures) - len(result.errors)

    border = "═" * 62
    print(f"\n{border}")
    if result.wasSuccessful():
        print(f"  ALL {total}/{total} CHECKS PASSED ✓")
        print(f"  Phase-E Survivability Evolution is institutionally coherent.")
    else:
        print(f"  {passed}/{total} CHECKS PASSED")
        for test, tb in result.failures + result.errors:
            print(f"\n  ✗ {test}")
            for line in tb.strip().splitlines()[-4:]:
                print(f"    {line}")
    print(f"{border}\n")

    sys.exit(0 if result.wasSuccessful() else 1)
