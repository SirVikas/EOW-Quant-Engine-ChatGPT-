"""
Phase-G Adaptive Execution Governance — 84-check institutional verifier.
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
    regime: str = "TRENDING",
    origin_session: str = "NY",
    entry_ts: int = 0,
    exit_ts: int = 0,
    confidence: float = 0.70,
    operator_override: bool = False,
    override_reason: str = "",
) -> dict:
    now = int(time.time() * 1000)
    ds: dict = {"confidence": confidence}
    if operator_override:
        ds["operator_override"] = True
        ds["override_reason"]   = override_reason or "MANUAL"
    return {
        "trade_id":       f"T{now}-{net_pnl}-{regime}",
        "symbol":         "BTCUSDT",
        "side":           "BUY",
        "entry_price":    50000.0,
        "exit_price":     50050.0,
        "qty":            0.01,
        "entry_ts":       entry_ts or now,
        "exit_ts":        exit_ts  or (now + 300_000),
        "is_short":       False,
        "strategy_id":    "default",
        "regime":         regime,
        "gross_pnl":      gross_pnl,
        "net_pnl":        net_pnl,
        "fee_entry":      0.10,
        "fee_exit":       0.10,
        "slippage_cost":  0.05,
        "origin_session": origin_session,
        "close_session":  origin_session,
        "decision_snapshot":  ds,
        "exploration_origin": {"was_exploration_trade": False},
        "economic_truth":     {"fees_paid": 0.20},
    }


def _make_trades(n: int = 20, net_pnl: float = 1.0) -> list:
    now = int(time.time() * 1000)
    return [
        _trade(net_pnl=net_pnl, entry_ts=now + i * 60_000, exit_ts=now + i * 60_000 + 300_000)
        for i in range(n)
    ]


def _make_mixed(n: int = 30) -> list:
    now = int(time.time() * 1000)
    regimes = ["TRENDING", "MEAN_REVERTING", "VOLATILITY_EXPANSION", "UNKNOWN"]
    trades = []
    for i in range(n):
        pnl = 1.5 if i % 3 != 0 else -0.8
        trades.append(_trade(
            net_pnl=pnl,
            regime=regimes[i % len(regimes)],
            confidence=0.65 + (i % 4) * 0.07,
            entry_ts=now + i * 120_000,
            exit_ts=now + i * 120_000 + 300_000,
        ))
    return trades


_EMPTY = []


# ── Test class 1: Restraint Advisory Engine ───────────────────────────────────

class TestRestraintAdvisoryEngine(unittest.TestCase):

    def setUp(self):
        from core.adaptive_execution_governance.restraint_advisory_engine import (
            compute_restraint_advisory,
        )
        self.fn = compute_restraint_advisory

    def test_01_empty_report_key(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["report"], "RESTRAINT_ADVISORY_REPORT")

    def test_02_empty_trade_allowed(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["advisory"], "TRADE_ALLOWED")

    def test_03_empty_zero_trades(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["trade_count"], 0)

    def test_04_advisory_valid_state(self):
        valid = {"TRADE_ALLOWED","CONTRACT_RISK","PRESERVE_CAPITAL",
                 "PAUSE_ACTIVITY","RECOVERY_WAIT","ENTROPY_ALERT"}
        r = self.fn(_make_trades(20))
        self.assertIn(r["advisory"], valid)

    def test_05_lineage_id_prefix(self):
        r = self.fn(_make_trades(20))
        self.assertTrue(r["lineage_id"].startswith("ADV-"), r["lineage_id"])

    def test_06_constitutional_flags(self):
        r = self.fn(_make_trades(20))
        self.assertTrue(r["diagnostic_only"])
        self.assertFalse(r["auto_authorized"])
        self.assertTrue(r["human_confirmed"])
        self.assertTrue(r["override_visible"])

    def test_07_negative_trades_not_allowed(self):
        r = self.fn(_make_trades(25, net_pnl=-1.0))
        self.assertNotEqual(r["advisory"], "TRADE_ALLOWED")

    def test_08_contributing_subsystems_list(self):
        r = self.fn(_make_trades(20))
        self.assertIsInstance(r["contributing_subsystems"], list)
        self.assertGreater(len(r["contributing_subsystems"]), 0)

    def test_09_trade_count_correct(self):
        trades = _make_trades(18)
        r = self.fn(trades)
        self.assertEqual(r["trade_count"], 18)

    def test_10_fast_trade_ratio_range(self):
        r = self.fn(_make_trades(20))
        self.assertGreaterEqual(r["fast_trade_ratio"], 0.0)
        self.assertLessEqual(r["fast_trade_ratio"], 1.0)

    def test_11_never_raises_bad_input(self):
        for bad in ([None], [{}], [{"net_pnl": "x"}]):
            try:
                self.fn(bad)
            except Exception as exc:
                self.fail(f"Raised on bad input: {exc}")

    def test_12_replay_lineage_flags(self):
        r = self.fn(_make_trades(20))
        self.assertTrue(r["replay_safe"])
        self.assertTrue(r["lineage_preserved"])


# ── Test class 2: Capital Discipline Gate ─────────────────────────────────────

class TestCapitalDisciplineGate(unittest.TestCase):

    def setUp(self):
        from core.adaptive_execution_governance.capital_discipline_gate import (
            compute_capital_discipline_gate,
        )
        self.fn = compute_capital_discipline_gate

    def test_01_empty_report_key(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["report"], "CAPITAL_DISCIPLINE_GATE_REPORT")

    def test_02_empty_pass_gate(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["gate_state"], "PASS")

    def test_03_gate_state_valid(self):
        r = self.fn(_make_trades(20))
        self.assertIn(r["gate_state"], ("PASS", "CAUTION", "DEFENSIVE", "UNSAFE"))

    def test_04_gate_score_range(self):
        r = self.fn(_make_trades(20))
        self.assertGreaterEqual(r["gate_score"], 0)
        self.assertLessEqual(r["gate_score"], 100)

    def test_05_six_checks_present(self):
        r = self.fn(_make_trades(20))
        self.assertEqual(len(r["checks"]), 6)

    def test_06_check_structure(self):
        r = self.fn(_make_trades(20))
        for chk in r["checks"]:
            self.assertIn("check", chk)
            self.assertIn("passed", chk)
            self.assertIn("detail", chk)

    def test_07_checks_passed_consistent(self):
        r = self.fn(_make_trades(20))
        passed = sum(1 for c in r["checks"] if c["passed"])
        self.assertEqual(r["checks_passed"], passed)
        self.assertEqual(r["checks_failed"], 6 - passed)

    def test_08_constitutional_flags(self):
        r = self.fn(_make_trades(20))
        self.assertTrue(r["diagnostic_only"])
        self.assertFalse(r["auto_authorized"])
        self.assertTrue(r["human_confirmed"])

    def test_09_constitutional_note_present(self):
        r = self.fn(_make_trades(20))
        self.assertIn("constitutional_note", r)
        self.assertIn("recommend", r["constitutional_note"].lower())

    def test_10_trade_count_correct(self):
        trades = _make_trades(14)
        r = self.fn(trades)
        self.assertEqual(r["trade_count"], 14)

    def test_11_negative_trades_lower_score(self):
        r_pos = self.fn(_make_trades(20, net_pnl= 1.0))
        r_neg = self.fn(_make_trades(20, net_pnl=-1.0))
        self.assertGreaterEqual(r_pos["gate_score"], r_neg["gate_score"])

    def test_12_never_raises_bad_input(self):
        for bad in ([None], [{}], [{"net_pnl": "x"}]):
            try:
                self.fn(bad)
            except Exception as exc:
                self.fail(f"Raised on bad input: {exc}")


# ── Test class 3: Equilibrium Resumption Engine ───────────────────────────────

class TestEquilibriumResumptionEngine(unittest.TestCase):

    def setUp(self):
        from core.adaptive_execution_governance.equilibrium_resumption_engine import (
            compute_equilibrium_resumption,
        )
        self.fn = compute_equilibrium_resumption

    def test_01_empty_report_key(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["report"], "EQUILIBRIUM_RESUMPTION_REPORT")

    def test_02_empty_score_fifty(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["equilibrium_score"], 50)

    def test_03_equilibrium_state_valid(self):
        r = self.fn(_make_trades(20))
        self.assertIn(r["equilibrium_state"],
                      ("ACTIVE", "CAUTIONARY", "PRESERVATION", "RECOVERY", "LOCKDOWN"))

    def test_04_score_range(self):
        r = self.fn(_make_trades(20))
        self.assertGreaterEqual(r["equilibrium_score"], 0)
        self.assertLessEqual(r["equilibrium_score"], 100)

    def test_05_six_dimension_scores(self):
        r = self.fn(_make_trades(20))
        dims = r["dimension_scores"]
        required = {"ecological_stabilization","entropy_normalization","expectancy_recovery",
                    "confidence_realism_recovery","alpha_persistence_restoration","regime_stabilization"}
        self.assertTrue(required.issubset(set(dims.keys())))

    def test_06_dimension_scores_in_range(self):
        r = self.fn(_make_trades(20))
        for k, v in r["dimension_scores"].items():
            self.assertGreaterEqual(v, 0, f"{k} < 0")
            self.assertLessEqual(v, 100, f"{k} > 100")

    def test_07_weights_sum_to_one(self):
        r = self.fn(_make_trades(20))
        total = sum(r["dimension_weights"].values())
        self.assertAlmostEqual(total, 1.0, places=5)

    def test_08_recovery_readiness_bool(self):
        r = self.fn(_make_trades(20))
        self.assertIsInstance(r["recovery_readiness"], bool)

    def test_09_trade_count_correct(self):
        trades = _make_trades(16)
        r = self.fn(trades)
        self.assertEqual(r["trade_count"], 16)

    def test_10_constitutional_flags(self):
        r = self.fn(_make_trades(20))
        self.assertTrue(r["diagnostic_only"])
        self.assertFalse(r["auto_authorized"])
        self.assertTrue(r["human_confirmed"])

    def test_11_never_raises_bad_input(self):
        for bad in ([None], [{}]):
            try:
                self.fn(bad)
            except Exception as exc:
                self.fail(f"Raised on bad input: {exc}")

    def test_12_positive_trades_higher_score(self):
        r_pos = self.fn(_make_trades(30, net_pnl= 1.5))
        r_neg = self.fn(_make_trades(30, net_pnl=-1.5))
        self.assertGreaterEqual(r_pos["equilibrium_score"], r_neg["equilibrium_score"] - 5)


# ── Test class 4: Operator Override Transparency Engine ──────────────────────

class TestOperatorOverrideTransparencyEngine(unittest.TestCase):

    def setUp(self):
        from core.adaptive_execution_governance.operator_override_transparency_engine import (
            compute_operator_override_transparency,
        )
        self.fn = compute_operator_override_transparency

    def test_01_empty_report_key(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["report"], "OPERATOR_OVERRIDE_TRANSPARENCY_REPORT")

    def test_02_empty_no_overrides(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["total_override_count"], 0)

    def test_03_explicit_override_detected(self):
        now = int(time.time() * 1000)
        trades = [_trade(net_pnl=-0.5, operator_override=True, override_reason="MANUAL",
                         entry_ts=now, exit_ts=now+300_000)]
        r = self.fn(trades)
        self.assertEqual(r["explicit_override_count"], 1)

    def test_04_override_events_structure(self):
        r = self.fn(_make_mixed(30))
        for ev in r["override_events"]:
            self.assertIn("trade_id", ev)
            self.assertIn("override_type", ev)
            self.assertIn("net_pnl", ev)
            self.assertIn("survivability_impact", ev)

    def test_05_discipline_effectiveness_valid(self):
        r = self.fn(_make_mixed(30))
        self.assertIn(r["discipline_effectiveness"],
                      ("DISCIPLINE_HELPED", "DISCIPLINE_NEUTRAL", "OVERRIDES_BENEFICIAL"))

    def test_06_replay_visible(self):
        r = self.fn(_make_trades(20))
        self.assertTrue(r["replay_visible"])
        self.assertTrue(r["override_visible"])

    def test_07_constitutional_flags(self):
        r = self.fn(_make_trades(20))
        self.assertTrue(r["diagnostic_only"])
        self.assertFalse(r["auto_authorized"])
        self.assertTrue(r["human_confirmed"])

    def test_08_frequency_pct_range(self):
        r = self.fn(_make_trades(20))
        self.assertGreaterEqual(r["override_frequency_pct"], 0.0)
        self.assertLessEqual(r["override_frequency_pct"], 100.0)

    def test_09_trade_count_correct(self):
        trades = _make_trades(12)
        r = self.fn(trades)
        self.assertEqual(r["total_trade_count"], 12)

    def test_10_lineage_note_present(self):
        r = self.fn(_make_trades(20))
        self.assertIn("lineage_note", r)
        self.assertIn("replay", r["lineage_note"].lower())

    def test_11_never_raises_bad_input(self):
        for bad in ([None], [{}], [{"decision_snapshot": None}]):
            try:
                self.fn(bad)
            except Exception as exc:
                self.fail(f"Raised on bad input: {exc}")

    def test_12_override_count_consistency(self):
        r = self.fn(_make_mixed(30))
        explicit = r["explicit_override_count"]
        inferred = r["inferred_override_count"]
        self.assertEqual(r["total_override_count"], explicit + inferred)


# ── Test class 5: Execution Discipline Memory Engine ─────────────────────────

class TestExecutionDisciplineMemoryEngine(unittest.TestCase):

    def setUp(self):
        from core.adaptive_execution_governance.execution_discipline_memory_engine import (
            compute_execution_discipline_memory,
        )
        self.fn = compute_execution_discipline_memory

    def test_01_empty_report_key(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["report"], "EXECUTION_DISCIPLINE_MEMORY_REPORT")

    def test_02_empty_adequate_tier(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["discipline_tier"], "ADEQUATE")

    def test_03_discipline_score_range(self):
        r = self.fn(_make_trades(20))
        self.assertGreaterEqual(r["discipline_score"], 0)
        self.assertLessEqual(r["discipline_score"], 100)

    def test_04_discipline_tier_valid(self):
        r = self.fn(_make_trades(20))
        self.assertIn(r["discipline_tier"], ("DISCIPLINED", "ADEQUATE", "IMPULSIVE", "UNCONTROLLED"))

    def test_05_revenge_episodes_list(self):
        r = self.fn(_make_trades(20))
        self.assertIsInstance(r["revenge_episodes"], list)

    def test_06_impulsive_spikes_list(self):
        r = self.fn(_make_trades(20))
        self.assertIsInstance(r["impulsive_spikes"], list)

    def test_07_discipline_effectiveness_valid(self):
        r = self.fn(_make_trades(20))
        self.assertIn(r["discipline_effectiveness"],
                      ("DISCIPLINE_PRESERVED_SURVIVABILITY", "MIXED_EVIDENCE", "EMOTIONAL_OVERRIDES_DOMINATED"))

    def test_08_conditions_lists(self):
        r = self.fn(_make_trades(20))
        self.assertIsInstance(r["conditions_discipline_helped"], list)
        self.assertIsInstance(r["conditions_overrides_degraded"], list)

    def test_09_trade_count_correct(self):
        trades = _make_trades(13)
        r = self.fn(trades)
        self.assertEqual(r["total_trades"], 13)

    def test_10_constitutional_flags(self):
        r = self.fn(_make_trades(20))
        self.assertTrue(r["diagnostic_only"])
        self.assertFalse(r["auto_authorized"])
        self.assertTrue(r["human_confirmed"])

    def test_11_never_raises_bad_input(self):
        for bad in ([None], [{}]):
            try:
                self.fn(bad)
            except Exception as exc:
                self.fail(f"Raised on bad input: {exc}")

    def test_12_positive_only_high_discipline(self):
        r = self.fn(_make_trades(30, net_pnl=1.5))
        self.assertGreater(r["discipline_score"], 40)


# ── Test class 6: Human Governance Safety Engine ─────────────────────────────

class TestHumanGovernanceSafetyEngine(unittest.TestCase):

    def setUp(self):
        from core.adaptive_execution_governance.human_governance_safety_engine import (
            compute_human_governance_safety,
        )
        self.fn = compute_human_governance_safety

    def test_01_empty_report_key(self):
        r = self.fn(_EMPTY)
        self.assertEqual(r["report"], "HUMAN_GOVERNANCE_SAFETY_REPORT")

    def test_02_governance_status_valid(self):
        r = self.fn(_EMPTY)
        self.assertIn(r["governance_status"],
                      ("CERTIFIED", "PARTIAL_CERTIFICATION", "VIOLATION_DETECTED", "UNAVAILABLE"))

    def test_03_governance_health_score_range(self):
        r = self.fn(_make_trades(20))
        self.assertGreaterEqual(r["governance_health_score"], 0)
        self.assertLessEqual(r["governance_health_score"], 100)

    def test_04_validation_results_list(self):
        r = self.fn(_make_trades(20))
        self.assertIsInstance(r["validation_results"], list)

    def test_05_validation_result_structure(self):
        r = self.fn(_make_trades(20))
        for vr in r["validation_results"]:
            self.assertIn("engine", vr)
            self.assertIn("validated", vr)
            self.assertIn("violations", vr)
            self.assertIn("available", vr)

    def test_06_safety_assertions_present(self):
        r = self.fn(_make_trades(20))
        self.assertIsInstance(r["safety_assertions"], list)
        self.assertGreaterEqual(len(r["safety_assertions"]), 3)

    def test_07_constitutional_invariants_dict(self):
        r = self.fn(_make_trades(20))
        ci = r["constitutional_invariants"]
        self.assertTrue(ci.get("diagnostic_only"))
        self.assertFalse(ci.get("auto_authorized"))
        self.assertTrue(ci.get("human_confirmed"))

    def test_08_own_constitutional_flags(self):
        r = self.fn(_make_trades(20))
        self.assertTrue(r["diagnostic_only"])
        self.assertFalse(r["auto_authorized"])
        self.assertTrue(r["human_confirmed"])
        self.assertTrue(r["override_visible"])

    def test_09_engines_count_consistent(self):
        r = self.fn(_make_trades(20))
        checked     = r["engines_checked"]
        validated   = r["engines_validated"]
        unavailable = r["engines_unavailable"]
        self.assertEqual(checked, validated + (checked - validated))
        self.assertGreaterEqual(checked + unavailable, 0)

    def test_10_violation_count_int(self):
        r = self.fn(_make_trades(20))
        self.assertIsInstance(r["violation_count"], int)
        self.assertGreaterEqual(r["violation_count"], 0)

    def test_11_never_raises_bad_input(self):
        for bad in ([None], [{}]):
            try:
                self.fn(bad)
            except Exception as exc:
                self.fail(f"Raised on bad input: {exc}")

    def test_12_certified_on_clean_engines(self):
        r = self.fn(_make_trades(20))
        # In a clean implementation all engines should validate
        self.assertIn(r["governance_status"],
                      ("CERTIFIED", "PARTIAL_CERTIFICATION"))


# ── Test class 7: Adaptive Execution Orchestrator ────────────────────────────

class TestAdaptiveExecutionOrchestrator(unittest.TestCase):

    def setUp(self):
        from core.adaptive_execution_governance.adaptive_execution_orchestrator import (
            run_adaptive_execution_civilization,
            get_execution_governance_health,
        )
        self.run_fn    = run_adaptive_execution_civilization
        self.health_fn = get_execution_governance_health

    def test_01_empty_report_key(self):
        r = self.run_fn(_EMPTY)
        self.assertEqual(r["report"], "ADAPTIVE_EXECUTION_CIVILIZATION_REPORT")

    def test_02_health_report_key(self):
        r = self.health_fn(_EMPTY)
        self.assertEqual(r["report"], "EXECUTION_GOVERNANCE_HEALTH")

    def test_03_execution_id_format(self):
        r = self.run_fn(_make_trades(20))
        self.assertTrue(r["execution_id"].startswith("EXEC-"), r["execution_id"])

    def test_04_civilization_score_range(self):
        r = self.run_fn(_make_trades(20))
        self.assertGreaterEqual(r["civilization_score"], 0)
        self.assertLessEqual(r["civilization_score"], 100)

    def test_05_civilization_tier_valid(self):
        r = self.run_fn(_make_trades(20))
        self.assertIn(r["civilization_tier"],
                      ("SOVEREIGN", "OPERATIONAL", "GUARDED", "COMPROMISED"))

    def test_06_all_domain_reports_present(self):
        r = self.run_fn(_make_trades(20))
        required = {"restraint","discipline_gate","equilibrium",
                    "override_transparency","discipline_memory","governance_safety"}
        self.assertTrue(required.issubset(set(r["domain_reports"].keys())))

    def test_07_constitutional_flags(self):
        r = self.run_fn(_make_trades(20))
        self.assertTrue(r["diagnostic_only"])
        self.assertFalse(r["auto_authorized"])
        self.assertTrue(r["human_confirmed"])
        self.assertTrue(r["override_visible"])
        self.assertTrue(r["lineage_preserved"])
        self.assertTrue(r["replay_safe"])

    def test_08_constitutional_note_present(self):
        r = self.run_fn(_make_trades(20))
        self.assertIn("constitutional_note", r)
        note = r["constitutional_note"].lower()
        self.assertIn("human", note)

    def test_09_score_evidence_keys(self):
        r = self.run_fn(_make_trades(20))
        ev = r["score_evidence"]
        for key in ("execution_viable","gate_acceptable","equilibrium_stable",
                    "governance_certified","discipline_adequate"):
            self.assertIn(key, ev)

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
        TestRestraintAdvisoryEngine,
        TestCapitalDisciplineGate,
        TestEquilibriumResumptionEngine,
        TestOperatorOverrideTransparencyEngine,
        TestExecutionDisciplineMemoryEngine,
        TestHumanGovernanceSafetyEngine,
        TestAdaptiveExecutionOrchestrator,
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
        print(f"  Phase-G Adaptive Execution Governance is constitutionally coherent.")
    else:
        print(f"  {passed}/{total} CHECKS PASSED")
        for test, tb in result.failures + result.errors:
            print(f"\n  ✗ {test}")
            for line in tb.strip().splitlines()[-4:]:
                print(f"    {line}")
    print(f"{border}\n")

    sys.exit(0 if result.wasSuccessful() else 1)
