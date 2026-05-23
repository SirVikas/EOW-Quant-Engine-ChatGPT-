"""
Phase-H Institutional Continuity & Multi-Cycle Evolution — 84-check verifier.
7 classes × 12 checks each = 84 total.
"""
from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Synthetic trade factory ───────────────────────────────────────────────────

def _trade(net_pnl=1.0, gross_pnl=1.5, regime="TRENDING", origin_session="NY",
           entry_ts=0, exit_ts=0, confidence=0.70) -> dict:
    now = int(time.time() * 1000)
    return {
        "trade_id":       f"T{now}-{net_pnl}-{regime}",
        "symbol":         "BTCUSDT",
        "side":           "BUY",
        "entry_price":    50000.0, "exit_price": 50050.0, "qty": 0.01,
        "entry_ts":       entry_ts or now,
        "exit_ts":        exit_ts  or (now + 300_000),
        "is_short":       False,
        "strategy_id":    "default",
        "regime":         regime,
        "gross_pnl":      gross_pnl,
        "net_pnl":        net_pnl,
        "fee_entry":      0.10, "fee_exit": 0.10, "slippage_cost": 0.05,
        "origin_session": origin_session,
        "close_session":  origin_session,
        "decision_snapshot":  {"confidence": confidence},
        "exploration_origin": {"was_exploration_trade": False},
        "economic_truth":     {"fees_paid": 0.20},
    }


def _make_trades(n=20, net_pnl=1.0) -> list:
    now = int(time.time() * 1000)
    return [_trade(net_pnl=net_pnl, entry_ts=now + i * 60_000,
                   exit_ts=now + i * 60_000 + 300_000) for i in range(n)]


def _make_mixed(n=40) -> list:
    now = int(time.time() * 1000)
    regimes  = ["TRENDING", "MEAN_REVERTING", "VOLATILITY_EXPANSION", "UNKNOWN"]
    sessions = ["NY", "LONDON", "ASIA"]
    trades = []
    for i in range(n):
        pnl = 1.5 if i % 3 != 0 else -0.8
        trades.append(_trade(
            net_pnl=pnl, regime=regimes[i % 4],
            origin_session=sessions[i % 3],
            confidence=0.65 + (i % 4) * 0.07,
            entry_ts=now + i * 120_000,
            exit_ts=now + i * 120_000 + 300_000,
        ))
    return trades


_EMPTY = []


# ── Test class 1: Multi-Cycle Survivability Memory ────────────────────────────

class TestMultiCycleSurvivabilityMemory(unittest.TestCase):

    def setUp(self):
        from core.institutional_continuity.multi_cycle_survivability_memory import (
            compute_multi_cycle_survivability_memory,
        )
        self.fn = compute_multi_cycle_survivability_memory

    def test_01_empty_report_key(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["report"], "MULTI_CYCLE_SURVIVABILITY_REPORT")

    def test_02_empty_no_data_verdict(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["multi_cycle_verdict"], "NO_DATA")

    def test_03_empty_zero_cycles(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["cycle_count"], 0)

    def test_04_populated_report_key(self):
        r = self.fn(_make_trades(30))
        self.assertEqual(r["report"], "MULTI_CYCLE_SURVIVABILITY_REPORT")

    def test_05_verdict_valid(self):
        r = self.fn(_make_trades(30))
        self.assertIn(r["multi_cycle_verdict"],
                      ("DURABLE", "CYCLICAL", "DETERIORATING", "NO_DATA"))

    def test_06_continuity_valid(self):
        r = self.fn(_make_trades(30))
        self.assertIn(r["survivability_continuity"],
                      ("PERSISTENT_SURVIVABILITY", "TEMPORARY_ADAPTATION", "INSUFFICIENT_DATA"))

    def test_07_cycles_is_list(self):
        r = self.fn(_make_trades(30))
        self.assertIsInstance(r["cycles"], list)

    def test_08_longest_eras_non_negative(self):
        r = self.fn(_make_trades(30))
        self.assertGreaterEqual(r["longest_positive_era"], 0)
        self.assertGreaterEqual(r["longest_negative_era"], 0)

    def test_09_trade_count_correct(self):
        trades = _make_trades(22)
        r = self.fn(trades)
        self.assertEqual(r["total_trades"], 22)

    def test_10_constitutional_flags(self):
        r = self.fn(_make_trades(20))
        self.assertTrue(r["diagnostic_only"])
        self.assertFalse(r["auto_authorized"])

    def test_11_never_raises_bad_input(self):
        for bad in ([None], [{}], [{"net_pnl": "x"}]):
            try:
                self.fn(bad)
            except Exception as exc:
                self.fail(f"Raised: {exc}")

    def test_12_positive_trades_durable_or_cyclical(self):
        r = self.fn(_make_trades(30, net_pnl=1.5))
        self.assertIn(r["multi_cycle_verdict"], ("DURABLE", "CYCLICAL", "NO_DATA"))


# ── Test class 2: Evolutionary Doctrine Memory ───────────────────────────────

class TestEvolutionaryDoctrineMemory(unittest.TestCase):

    def setUp(self):
        from core.institutional_continuity.evolutionary_doctrine_memory import (
            compute_evolutionary_doctrine_memory,
        )
        self.fn = compute_evolutionary_doctrine_memory

    def test_01_empty_report_key(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["report"], "EVOLUTIONARY_DOCTRINE_REPORT")

    def test_02_small_insufficient_data(self):
        r = self.fn(_make_trades(5))
        self.assertEqual(r["doctrine_state"], "INSUFFICIENT_DATA")

    def test_03_populated_report_key(self):
        r = self.fn(_make_trades(20))
        self.assertEqual(r["report"], "EVOLUTIONARY_DOCTRINE_REPORT")

    def test_04_doctrine_state_valid(self):
        r = self.fn(_make_mixed(40))
        self.assertIn(r["doctrine_state"],
                      ("DOCTRINE_STABLE", "DOCTRINE_DRIFTING", "DOCTRINE_REGRESSED",
                       "DOCTRINE_EVOLVING_POSITIVELY", "INSUFFICIENT_DATA"))

    def test_05_quartile_doctrines_present(self):
        r = self.fn(_make_trades(20))
        qd = r.get("quartile_doctrines", {})
        self.assertTrue(len(qd) >= 2)

    def test_06_drift_signals_list(self):
        r = self.fn(_make_trades(20))
        self.assertIsInstance(r["drift_signals"], list)

    def test_07_contradictions_list(self):
        r = self.fn(_make_trades(20))
        self.assertIsInstance(r["contradictions"], list)

    def test_08_drift_count_consistent(self):
        r = self.fn(_make_trades(20))
        self.assertEqual(r["drift_count"], len(r["drift_signals"]))

    def test_09_trade_count_correct(self):
        trades = _make_trades(16)
        r = self.fn(trades)
        self.assertEqual(r["total_trades"], 16)

    def test_10_constitutional_flags(self):
        r = self.fn(_make_trades(20))
        self.assertTrue(r["diagnostic_only"])
        self.assertFalse(r["auto_authorized"])

    def test_11_never_raises_bad_input(self):
        for bad in ([None], [{}]):
            try:
                self.fn(bad)
            except Exception as exc:
                self.fail(f"Raised: {exc}")

    def test_12_stable_on_uniform_positive(self):
        r = self.fn(_make_trades(32, net_pnl=1.0))
        self.assertIn(r["doctrine_state"],
                      ("DOCTRINE_STABLE", "DOCTRINE_EVOLVING_POSITIVELY", "INSUFFICIENT_DATA"))


# ── Test class 3: Long-Horizon Entropy Engine ────────────────────────────────

class TestLongHorizonEntropyEngine(unittest.TestCase):

    def setUp(self):
        from core.institutional_continuity.long_horizon_entropy_engine import (
            compute_long_horizon_entropy,
        )
        self.fn = compute_long_horizon_entropy

    def test_01_empty_report_key(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["report"], "LONG_HORIZON_ENTROPY_REPORT")

    def test_02_empty_durable(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["entropy_state"], "DURABLE")

    def test_03_populated_report_key(self):
        r = self.fn(_make_trades(20))
        self.assertEqual(r["report"], "LONG_HORIZON_ENTROPY_REPORT")

    def test_04_state_valid(self):
        r = self.fn(_make_trades(20))
        self.assertIn(r["entropy_state"], ("DURABLE", "AGING", "FRAGILE", "EXHAUSTED"))

    def test_05_degradation_signals_list(self):
        r = self.fn(_make_trades(20))
        self.assertIsInstance(r["degradation_signals"], list)

    def test_06_signal_count_consistent(self):
        r = self.fn(_make_trades(20))
        self.assertEqual(r["degradation_signal_count"], len(r["degradation_signals"]))

    def test_07_bool_fields(self):
        r = self.fn(_make_trades(20))
        for key in ("slow_survivability_erosion", "adaptive_instability_accumulation",
                    "long_cycle_entropy_growth", "hidden_degradation_momentum",
                    "persistence_weakening", "structural_exhaustion"):
            self.assertIsInstance(r[key], bool, f"{key} not bool")

    def test_08_segment_analysis_present(self):
        r = self.fn(_make_trades(20))
        self.assertIsInstance(r["segment_analysis"], dict)

    def test_09_trade_count_correct(self):
        trades = _make_trades(24)
        r = self.fn(trades)
        self.assertEqual(r["total_trades"], 24)

    def test_10_constitutional_flags(self):
        r = self.fn(_make_trades(20))
        self.assertTrue(r["diagnostic_only"])
        self.assertFalse(r["auto_authorized"])

    def test_11_never_raises_bad_input(self):
        for bad in ([None], [{}]):
            try:
                self.fn(bad)
            except Exception as exc:
                self.fail(f"Raised: {exc}")

    def test_12_uniform_positive_durable(self):
        r = self.fn(_make_trades(32, net_pnl=1.5))
        self.assertIn(r["entropy_state"], ("DURABLE", "AGING"))


# ── Test class 4: Institutional Recovery Inheritance ─────────────────────────

class TestInstitutionalRecoveryInheritance(unittest.TestCase):

    def setUp(self):
        from core.institutional_continuity.institutional_recovery_inheritance import (
            compute_institutional_recovery_inheritance,
        )
        self.fn = compute_institutional_recovery_inheritance

    def test_01_empty_report_key(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["report"], "RECOVERY_INHERITANCE_REPORT")

    def test_02_empty_no_inheritance(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["inheritance_state"], "NO_INHERITANCE")

    def test_03_populated_report_key(self):
        r = self.fn(_make_mixed(40))
        self.assertEqual(r["report"], "RECOVERY_INHERITANCE_REPORT")

    def test_04_inheritance_state_valid(self):
        r = self.fn(_make_mixed(40))
        self.assertIn(r["inheritance_state"],
                      ("RICH_INHERITANCE", "MODERATE_INHERITANCE", "SPARSE_INHERITANCE", "NO_INHERITANCE"))

    def test_05_recovery_pathways_list(self):
        r = self.fn(_make_mixed(40))
        self.assertIsInstance(r["recovery_pathways"], list)

    def test_06_pathway_count_consistent(self):
        r = self.fn(_make_mixed(40))
        self.assertEqual(r["pathway_count"], len(r["recovery_pathways"]))

    def test_07_pathway_structure(self):
        r = self.fn(_make_mixed(40))
        for p in r["recovery_pathways"]:
            self.assertIn("dominant_regime", p)
            self.assertIn("recovery_strength", p)

    def test_08_repeatability_valid(self):
        r = self.fn(_make_mixed(40))
        self.assertIn(r["repeatability"], ("REPEATABLE", "SINGLE_EVENT", "NO_INHERITANCE"))

    def test_09_trade_count_correct(self):
        trades = _make_trades(20)
        r = self.fn(trades)
        self.assertEqual(r["total_trades"], 20)

    def test_10_constitutional_flags(self):
        r = self.fn(_make_trades(20))
        self.assertTrue(r["diagnostic_only"])
        self.assertFalse(r["auto_authorized"])

    def test_11_never_raises_bad_input(self):
        for bad in ([None], [{}]):
            try:
                self.fn(bad)
            except Exception as exc:
                self.fail(f"Raised: {exc}")

    def test_12_behaviors_list(self):
        r = self.fn(_make_mixed(40))
        self.assertIsInstance(r["behaviors_restored"], list)


# ── Test class 5: Cross-Regime Continuity Engine ─────────────────────────────

class TestCrossRegimeContinuityEngine(unittest.TestCase):

    def setUp(self):
        from core.institutional_continuity.cross_regime_continuity_engine import (
            compute_cross_regime_continuity,
        )
        self.fn = compute_cross_regime_continuity

    def test_01_empty_report_key(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["report"], "CROSS_REGIME_CONTINUITY_REPORT")

    def test_02_empty_no_data(self):
        r = self.fn(_EMPTY)
        self.assertIn(r["continuity_verdict"], ("NO_DATA", "ENVIRONMENT_SPECIFIC"))

    def test_03_populated_report_key(self):
        r = self.fn(_make_mixed(40))
        self.assertEqual(r["report"], "CROSS_REGIME_CONTINUITY_REPORT")

    def test_04_verdict_valid(self):
        r = self.fn(_make_mixed(40))
        self.assertIn(r["continuity_verdict"],
                      ("UNIVERSAL", "BROAD", "NARROW", "FRAGILE", "NO_DATA", "NOT_SURVIVABLE_ANY"))

    def test_05_continuity_score_range(self):
        r = self.fn(_make_mixed(40))
        self.assertGreaterEqual(r["continuity_score"], 0)
        self.assertLessEqual(r["continuity_score"], 100)

    def test_06_environment_analysis_structure(self):
        r = self.fn(_make_mixed(40))
        ea = r["environment_analysis"]
        for env in ("TRENDING", "RANGING", "VOLATILITY_EXPANSION",
                    "COMPRESSION", "LIQUIDITY_SHIFT", "STRUCTURAL_INSTABILITY"):
            self.assertIn(env, ea)

    def test_07_survivable_list(self):
        r = self.fn(_make_trades(30))
        self.assertIsInstance(r["survivable_environments"], list)

    def test_08_continuity_type_valid(self):
        r = self.fn(_make_trades(30))
        self.assertIn(r["continuity_type"],
                      ("CROSS_REGIME_CONTINUITY", "ENVIRONMENT_SPECIFIC"))

    def test_09_trade_count_correct(self):
        trades = _make_trades(18)
        r = self.fn(trades)
        self.assertEqual(r["total_trades"], 18)

    def test_10_constitutional_flags(self):
        r = self.fn(_make_trades(20))
        self.assertTrue(r["diagnostic_only"])
        self.assertFalse(r["auto_authorized"])

    def test_11_never_raises_bad_input(self):
        for bad in ([None], [{}]):
            try:
                self.fn(bad)
            except Exception as exc:
                self.fail(f"Raised: {exc}")

    def test_12_non_survivable_list(self):
        r = self.fn(_make_mixed(40))
        self.assertIsInstance(r["non_survivable_environments"], list)


# ── Test class 6: Institutional Identity Stability ───────────────────────────

class TestInstitutionalIdentityStabilityEngine(unittest.TestCase):

    def setUp(self):
        from core.institutional_continuity.institutional_identity_stability_engine import (
            compute_institutional_identity_stability,
        )
        self.fn = compute_institutional_identity_stability

    def test_01_empty_report_key(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["report"], "INSTITUTIONAL_IDENTITY_REPORT")

    def test_02_empty_stable(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["identity_status"], "STABLE")

    def test_03_identity_status_valid(self):
        r = self.fn(_make_mixed(40))
        self.assertIn(r["identity_status"],
                      ("STABLE", "CAUTIONARY", "DRIFTING", "COMPROMISED"))

    def test_04_identity_score_range(self):
        r = self.fn(_make_trades(20))
        self.assertGreaterEqual(r["identity_score"], 0)
        self.assertLessEqual(r["identity_score"], 100)

    def test_05_dimension_results_dict(self):
        r = self.fn(_make_trades(20))
        dims = r["dimension_results"]
        for key in ("constitutional_continuity", "governance_continuity", "replay_continuity",
                    "survivability_continuity", "anti_sovereignty_continuity",
                    "operator_transparency_continuity"):
            self.assertIn(key, dims)

    def test_06_dimension_values_bool(self):
        r = self.fn(_make_trades(20))
        for k, v in r["dimension_results"].items():
            self.assertIsInstance(v, bool, f"{k} not bool")

    def test_07_drift_signals_list(self):
        r = self.fn(_make_trades(20))
        self.assertIsInstance(r["drift_signals"], list)

    def test_08_drift_count_consistent(self):
        r = self.fn(_make_trades(20))
        self.assertEqual(r["drift_count"], len(r["drift_signals"]))

    def test_09_trade_count_correct(self):
        trades = _make_trades(16)
        r = self.fn(trades)
        self.assertEqual(r["total_trades"], 16)

    def test_10_constitutional_flags(self):
        r = self.fn(_make_trades(20))
        self.assertTrue(r["diagnostic_only"])
        self.assertFalse(r["auto_authorized"])

    def test_11_never_raises_bad_input(self):
        for bad in ([None], [{}]):
            try:
                self.fn(bad)
            except Exception as exc:
                self.fail(f"Raised: {exc}")

    def test_12_stable_on_uniform_positive(self):
        r = self.fn(_make_trades(30, net_pnl=1.0))
        self.assertIn(r["identity_status"], ("STABLE", "CAUTIONARY"))


# ── Test class 7: Continuity Evolution Orchestrator ──────────────────────────

class TestContinuityEvolutionOrchestrator(unittest.TestCase):

    def setUp(self):
        from core.institutional_continuity.continuity_evolution_orchestrator import (
            run_institutional_continuity,
            get_continuity_health,
        )
        self.run_fn    = run_institutional_continuity
        self.health_fn = get_continuity_health

    def test_01_empty_report_key(self):
        r = self.run_fn(_EMPTY)
        self.assertEqual(r["report"], "INSTITUTIONAL_CONTINUITY_REPORT")

    def test_02_health_report_key(self):
        r = self.health_fn(_EMPTY)
        self.assertEqual(r["report"], "CONTINUITY_HEALTH")

    def test_03_continuity_id_format(self):
        r = self.run_fn(_make_trades(20))
        self.assertTrue(r["continuity_id"].startswith("CONT-"), r["continuity_id"])

    def test_04_score_range(self):
        r = self.run_fn(_make_trades(20))
        self.assertGreaterEqual(r["continuity_score"], 0)
        self.assertLessEqual(r["continuity_score"], 100)

    def test_05_tier_valid(self):
        r = self.run_fn(_make_trades(20))
        self.assertIn(r["continuity_tier"], ("ENDURING", "PERSISTENT", "FRAGILE", "DECAYING"))

    def test_06_all_domain_reports_present(self):
        r = self.run_fn(_make_trades(20))
        required = {"survivability_memory", "doctrine", "entropy",
                    "recovery", "cross_regime", "identity"}
        self.assertTrue(required.issubset(set(r["domain_reports"].keys())))

    def test_07_constitutional_flags(self):
        r = self.run_fn(_make_trades(20))
        self.assertTrue(r["diagnostic_only"])
        self.assertFalse(r["auto_authorized"])
        self.assertTrue(r["lineage_preserved"])
        self.assertTrue(r["replay_safe"])

    def test_08_score_evidence_keys(self):
        r = self.run_fn(_make_trades(20))
        ev = r["score_evidence"]
        for key in ("cycles_stable", "entropy_managed", "cross_regime_viable",
                    "identity_preserved", "recovery_inherited"):
            self.assertIn(key, ev)

    def test_09_health_fields(self):
        r = self.health_fn(_make_trades(20))
        for key in ("continuity_score", "continuity_tier", "entropy_state",
                    "identity_status", "domain_errors"):
            self.assertIn(key, r)

    def test_10_trade_count_correct(self):
        trades = _make_trades(19)
        r = self.run_fn(trades)
        self.assertEqual(r["trade_count"], 19)

    def test_11_never_raises_bad_input(self):
        for bad in ([None], [{}], _EMPTY):
            try:
                self.run_fn(bad)
                self.health_fn(bad)
            except Exception as exc:
                self.fail(f"Raised: {exc}")

    def test_12_domain_errors_list(self):
        r = self.run_fn(_make_trades(20))
        self.assertIsInstance(r["domain_errors"], list)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    classes = [
        TestMultiCycleSurvivabilityMemory,
        TestEvolutionaryDoctrineMemory,
        TestLongHorizonEntropyEngine,
        TestInstitutionalRecoveryInheritance,
        TestCrossRegimeContinuityEngine,
        TestInstitutionalIdentityStabilityEngine,
        TestContinuityEvolutionOrchestrator,
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
        print(f"  Phase-H Institutional Continuity is institutionally coherent.")
    else:
        print(f"  {passed}/{total} CHECKS PASSED")
        for test, tb in result.failures + result.errors:
            print(f"\n  ✗ {test}")
            for line in tb.strip().splitlines()[-4:]:
                print(f"    {line}")
    print(f"{border}\n")
    sys.exit(0 if result.wasSuccessful() else 1)
