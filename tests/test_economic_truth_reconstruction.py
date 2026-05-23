"""
Phase-D Economic Truth Reconstruction — Institutional Test Suite
84 automated validation checks.

Tests run with ZERO trades (paper-trading startup) and with SYNTHETIC trades
to verify both empty-state safety and analytical correctness.

Tests:
  TestExpectancyReconstruction       (12 checks)
  TestFeeDragIntelligence            (12 checks)
  TestSurvivableAlphaDetector        (12 checks)
  TestEcologicalCollapseDetector     (12 checks)
  TestRegimeSurvivabilityEngine      (12 checks)
  TestAdaptiveSignalFiltration       (12 checks)
  TestEconomicTruthOrchestrator      (12 checks)
"""
from __future__ import annotations

import os
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ── Synthetic trade factory ──────────────────────────────────────────────────

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
    exit_ts: int = 300_000,   # 5 min hold
    side: str = "BUY",
) -> dict:
    now = int(time.time() * 1000)
    return {
        "trade_id":       f"T{now}",
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
        "decision_snapshot": {"confidence": 0.70},
        "exploration_origin": {"was_exploration_trade": False},
        "economic_truth": {
            "fees_paid": fee_entry + fee_exit,
            "fee_drag_pct": round((fee_entry + fee_exit) / gross_pnl * 100, 2) if gross_pnl > 0 else None,
        },
    }


def _make_trades(n: int = 20) -> list:
    trades = []
    for i in range(n):
        t = _trade(
            net_pnl=1.0 if i % 3 != 0 else -0.5,
            gross_pnl=1.2,
            regime="TRENDING" if i % 2 == 0 else "MEAN_REVERTING",
            origin_session="NY" if i % 3 == 0 else "LONDON",
            entry_ts=int(time.time() * 1000) + i * 60_000,
            exit_ts=int(time.time() * 1000) + i * 60_000 + 300_000,
        )
        trades.append(t)
    return trades


_EMPTY_TRADES  = []
_SAMPLE_TRADES = _make_trades(20)


# ══════════════════════════════════════════════════════════════════════════════
# TestExpectancyReconstruction  (12 checks)
# ══════════════════════════════════════════════════════════════════════════════

class TestExpectancyReconstruction(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from core.economic_truth_reconstruction.expectancy_reconstruction import (
            compute_expectancy_reconstruction,
        )
        cls.empty  = compute_expectancy_reconstruction(_EMPTY_TRADES)
        cls.result = compute_expectancy_reconstruction(_SAMPLE_TRADES)

    def test_01_empty_trades_returns_dict(self):
        self.assertIsInstance(self.empty, dict)

    def test_02_report_key_value(self):
        self.assertEqual(self.result.get("report"), "EXPECTANCY_RECONSTRUCTION_REPORT")

    def test_03_empty_report_key_value(self):
        self.assertEqual(self.empty.get("report"), "EXPECTANCY_RECONSTRUCTION_REPORT")

    def test_04_total_trades_correct(self):
        self.assertEqual(self.result.get("total_trades"), len(_SAMPLE_TRADES))

    def test_05_decomposition_is_dict(self):
        self.assertIsInstance(self.result.get("decomposition"), dict)

    def test_06_decomposition_has_required_axes(self):
        d = self.result.get("decomposition", {})
        for axis in ("session", "regime", "strategy", "hold_bucket", "fee_adjusted"):
            self.assertIn(axis, d, msg=f"Axis '{axis}' missing from decomposition")

    def test_07_false_expectancy_groups_is_list(self):
        self.assertIsInstance(self.result.get("false_expectancy_groups"), list)

    def test_08_fee_collapsed_groups_is_list(self):
        self.assertIsInstance(self.result.get("fee_collapsed_groups"), list)

    def test_09_survivable_regions_is_list(self):
        self.assertIsInstance(self.result.get("survivable_regions"), list)

    def test_10_expectancy_decay_has_required_keys(self):
        ed = self.result.get("expectancy_decay", {})
        self.assertIn("early_half", ed)
        self.assertIn("late_half",  ed)
        self.assertIn("trend",      ed)

    def test_11_auto_authorized_is_false(self):
        self.assertIs(self.result.get("auto_authorized"), False)

    def test_12_diagnostic_only_is_true(self):
        self.assertIs(self.result.get("diagnostic_only"), True)


# ══════════════════════════════════════════════════════════════════════════════
# TestFeeDragIntelligence  (12 checks)
# ══════════════════════════════════════════════════════════════════════════════

class TestFeeDragIntelligence(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from core.economic_truth_reconstruction.fee_drag_intelligence import (
            compute_fee_drag_intelligence,
        )
        cls.empty  = compute_fee_drag_intelligence(_EMPTY_TRADES)
        cls.result = compute_fee_drag_intelligence(_SAMPLE_TRADES)

    def test_01_empty_returns_dict(self):
        self.assertIsInstance(self.empty, dict)

    def test_02_report_key_value(self):
        self.assertEqual(self.result.get("report"), "FEE_DRAG_INTELLIGENCE_REPORT")

    def test_03_gross_expectancy_is_float_or_none(self):
        v = self.result.get("gross_expectancy")
        self.assertTrue(v is None or isinstance(v, float))

    def test_04_net_expectancy_is_float_or_none(self):
        v = self.result.get("net_expectancy")
        self.assertTrue(v is None or isinstance(v, float))

    def test_05_fee_collapsed_count_is_nonneg_int(self):
        v = self.result.get("fee_collapsed_trade_count")
        self.assertIsInstance(v, int)
        self.assertGreaterEqual(v, 0)

    def test_06_cost_adjusted_survivability_is_str(self):
        self.assertIsInstance(self.result.get("cost_adjusted_survivability"), str)

    def test_07_trade_frequency_toxicity_is_str(self):
        self.assertIsInstance(self.result.get("trade_frequency_toxicity"), str)

    def test_08_session_fee_analysis_is_dict(self):
        self.assertIsInstance(self.result.get("session_fee_analysis"), dict)

    def test_09_regime_fee_analysis_is_dict(self):
        self.assertIsInstance(self.result.get("regime_fee_analysis"), dict)

    def test_10_worst_fee_patterns_is_list(self):
        self.assertIsInstance(self.result.get("worst_fee_patterns"), list)

    def test_11_auto_authorized_is_false(self):
        self.assertIs(self.result.get("auto_authorized"), False)

    def test_12_diagnostic_only_is_true(self):
        self.assertIs(self.result.get("diagnostic_only"), True)


# ══════════════════════════════════════════════════════════════════════════════
# TestSurvivableAlphaDetector  (12 checks)
# ══════════════════════════════════════════════════════════════════════════════

class TestSurvivableAlphaDetector(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from core.economic_truth_reconstruction.survivable_alpha_detector import (
            detect_survivable_alpha,
        )
        cls.empty  = detect_survivable_alpha(_EMPTY_TRADES)
        cls.result = detect_survivable_alpha(_SAMPLE_TRADES)

    def test_01_empty_returns_dict(self):
        self.assertIsInstance(self.empty, dict)

    def test_02_report_key_value(self):
        self.assertEqual(self.result.get("report"), "SURVIVABLE_ALPHA_REPORT")

    def test_03_alpha_pockets_is_list(self):
        self.assertIsInstance(self.result.get("alpha_pockets"), list)

    def test_04_pocket_count_matches_alpha_pockets(self):
        pockets = self.result.get("alpha_pockets", [])
        self.assertEqual(self.result.get("pocket_count"), len(pockets))

    def test_05_dimension_coverage_is_dict_with_8_keys(self):
        dc = self.result.get("dimension_coverage", {})
        self.assertIsInstance(dc, dict)
        self.assertEqual(len(dc), 8)

    def test_06_all_8_dimensions_present(self):
        dc = self.result.get("dimension_coverage", {})
        expected = {
            "session", "timeframe", "volatility", "market_structure",
            "confidence_regime", "directional_state", "trade_density",
            "ecological_context",
        }
        self.assertTrue(expected.issubset(dc.keys()))

    def test_07_global_alpha_state_is_str(self):
        self.assertIsInstance(self.result.get("global_alpha_state"), str)

    def test_08_survivability_index_in_range(self):
        si = self.result.get("survivability_index")
        self.assertIsInstance(si, int)
        self.assertGreaterEqual(si, 0)
        self.assertLessEqual(si, 100)

    def test_09_each_pocket_has_required_keys(self):
        for pocket in self.result.get("alpha_pockets", []):
            self.assertIn("dimension",      pocket)
            self.assertIn("group",          pocket)
            self.assertIn("net_expectancy", pocket)
            self.assertIn("trade_count",    pocket)

    def test_10_empty_pocket_count_is_zero(self):
        self.assertEqual(self.empty.get("pocket_count"), 0)

    def test_11_auto_authorized_is_false(self):
        self.assertIs(self.result.get("auto_authorized"), False)

    def test_12_diagnostic_only_is_true(self):
        self.assertIs(self.result.get("diagnostic_only"), True)


# ══════════════════════════════════════════════════════════════════════════════
# TestEcologicalCollapseDetector  (12 checks)
# ══════════════════════════════════════════════════════════════════════════════

class TestEcologicalCollapseDetector(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from core.economic_truth_reconstruction.ecological_collapse_detector import (
            detect_ecological_collapse,
        )
        cls.empty  = detect_ecological_collapse(_EMPTY_TRADES)
        cls.result = detect_ecological_collapse(_SAMPLE_TRADES)

    def test_01_empty_returns_dict(self):
        self.assertIsInstance(self.empty, dict)

    def test_02_report_key_value(self):
        self.assertEqual(self.result.get("report"), "ECOLOGICAL_COLLAPSE_REPORT")

    def test_03_collapse_severity_is_valid(self):
        self.assertIn(
            self.result.get("collapse_severity"),
            {"NONE", "LOW", "MODERATE", "HIGH", "CRITICAL"},
        )

    def test_04_collapse_signals_is_list(self):
        self.assertIsInstance(self.result.get("collapse_signals"), list)

    def test_05_signal_count_matches_collapse_signals(self):
        signals = self.result.get("collapse_signals", [])
        self.assertEqual(self.result.get("signal_count"), len(signals))

    def test_06_recovery_zones_is_list(self):
        self.assertIsInstance(self.result.get("recovery_zones"), list)

    def test_07_ecology_state_is_dict(self):
        self.assertIsInstance(self.result.get("ecology_state"), dict)

    def test_08_trade_analysis_is_dict(self):
        self.assertIsInstance(self.result.get("trade_analysis"), dict)

    def test_09_each_signal_has_required_keys(self):
        for sig in self.result.get("collapse_signals", []):
            self.assertIn("signal",   sig)
            self.assertIn("severity", sig)
            self.assertIn("source",   sig)

    def test_10_severity_values_are_valid(self):
        valid = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
        for sig in self.result.get("collapse_signals", []):
            self.assertIn(sig.get("severity"), valid)

    def test_11_auto_authorized_is_false(self):
        self.assertIs(self.result.get("auto_authorized"), False)

    def test_12_diagnostic_only_is_true(self):
        self.assertIs(self.result.get("diagnostic_only"), True)


# ══════════════════════════════════════════════════════════════════════════════
# TestRegimeSurvivabilityEngine  (12 checks)
# ══════════════════════════════════════════════════════════════════════════════

class TestRegimeSurvivabilityEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from core.economic_truth_reconstruction.regime_survivability_engine import (
            compute_regime_survivability,
        )
        cls.empty  = compute_regime_survivability(_EMPTY_TRADES)
        cls.result = compute_regime_survivability(_SAMPLE_TRADES)

    def test_01_empty_returns_dict(self):
        self.assertIsInstance(self.empty, dict)

    def test_02_report_key_value(self):
        self.assertEqual(self.result.get("report"), "REGIME_SURVIVABILITY_REPORT")

    def test_03_regime_analysis_is_dict(self):
        self.assertIsInstance(self.result.get("regime_analysis"), dict)

    def test_04_survivable_regimes_is_list(self):
        self.assertIsInstance(self.result.get("survivable_regimes"), list)

    def test_05_collapsed_regimes_is_list(self):
        self.assertIsInstance(self.result.get("collapsed_regimes"), list)

    def test_06_regime_count_is_nonneg_int(self):
        v = self.result.get("regime_count")
        self.assertIsInstance(v, int)
        self.assertGreaterEqual(v, 0)

    def test_07_each_regime_has_required_keys(self):
        for regime, metrics in self.result.get("regime_analysis", {}).items():
            self.assertIn("trade_count",   metrics)
            self.assertIn("survivability", metrics)
            self.assertIn("net_expectancy", metrics)

    def test_08_overall_regime_health_is_str(self):
        self.assertIsInstance(self.result.get("overall_regime_health"), str)

    def test_09_transition_fragility_is_dict(self):
        self.assertIsInstance(self.result.get("transition_fragility"), dict)

    def test_10_empty_regime_count_is_zero(self):
        self.assertEqual(self.empty.get("regime_count", 0), 0)

    def test_11_auto_authorized_is_false(self):
        self.assertIs(self.result.get("auto_authorized"), False)

    def test_12_diagnostic_only_is_true(self):
        self.assertIs(self.result.get("diagnostic_only"), True)


# ══════════════════════════════════════════════════════════════════════════════
# TestAdaptiveSignalFiltration  (12 checks)
# ══════════════════════════════════════════════════════════════════════════════

class TestAdaptiveSignalFiltration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from core.economic_truth_reconstruction.adaptive_signal_filtration import (
            compute_adaptive_filtration,
        )
        cls.empty  = compute_adaptive_filtration(_EMPTY_TRADES)
        cls.result = compute_adaptive_filtration(_SAMPLE_TRADES)

    def test_01_empty_returns_dict(self):
        self.assertIsInstance(self.empty, dict)

    def test_02_report_key_value(self):
        self.assertEqual(self.result.get("report"), "ADAPTIVE_SIGNAL_FILTRATION_REPORT")

    def test_03_filtration_candidates_is_list(self):
        self.assertIsInstance(self.result.get("filtration_candidates"), list)

    def test_04_candidate_count_matches_filtration_candidates(self):
        candidates = self.result.get("filtration_candidates", [])
        self.assertEqual(self.result.get("candidate_count"), len(candidates))

    def test_05_contradictory_evidence_is_list(self):
        self.assertIsInstance(self.result.get("contradictory_evidence"), list)

    def test_06_filtration_score_in_range(self):
        s = self.result.get("filtration_score")
        self.assertIsInstance(s, int)
        self.assertGreaterEqual(s, 0)
        self.assertLessEqual(s, 100)

    def test_07_filtration_verdict_is_str(self):
        self.assertIsInstance(self.result.get("filtration_verdict"), str)

    def test_08_cluster_analysis_is_dict(self):
        self.assertIsInstance(self.result.get("cluster_analysis"), dict)

    def test_09_each_candidate_has_filter_key(self):
        for c in self.result.get("filtration_candidates", []):
            self.assertIn("filter", c)
            self.assertIn("cluster", c)

    def test_10_empty_candidate_count_is_zero(self):
        self.assertEqual(self.empty.get("candidate_count"), 0)

    def test_11_auto_authorized_is_false(self):
        self.assertIs(self.result.get("auto_authorized"), False)

    def test_12_diagnostic_only_is_true(self):
        self.assertIs(self.result.get("diagnostic_only"), True)


# ══════════════════════════════════════════════════════════════════════════════
# TestEconomicTruthOrchestrator  (12 checks)
# ══════════════════════════════════════════════════════════════════════════════

class TestEconomicTruthOrchestrator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from core.economic_truth_reconstruction.economic_truth_orchestrator import (
            run_economic_truth,
            get_economic_health,
        )
        cls.full_empty  = run_economic_truth(_EMPTY_TRADES)
        cls.full_result = run_economic_truth(_SAMPLE_TRADES)
        cls.health      = get_economic_health(_SAMPLE_TRADES)

    def test_01_run_full_returns_dict(self):
        self.assertIsInstance(self.full_result, dict)

    def test_02_report_key_value(self):
        self.assertEqual(self.full_result.get("report"), "ECONOMIC_TRUTH_REPORT")

    def test_03_economic_id_starts_with_ECO(self):
        eid = self.full_result.get("economic_id", "")
        self.assertTrue(str(eid).startswith("ECO-"))

    def test_04_survivability_score_in_range(self):
        s = self.full_result.get("survivability_score")
        self.assertIsInstance(s, int)
        self.assertGreaterEqual(s, 0)
        self.assertLessEqual(s, 100)

    def test_05_survivability_tier_is_valid(self):
        self.assertIn(
            self.full_result.get("survivability_tier"),
            {"VIABLE", "MARGINAL", "WEAK", "CRITICAL"},
        )

    def test_06_domain_reports_has_6_keys(self):
        dr = self.full_result.get("domain_reports")
        self.assertIsInstance(dr, dict)
        self.assertEqual(len(dr), 6)

    def test_07_domain_reports_has_all_expected_keys(self):
        dr = self.full_result.get("domain_reports", {})
        for key in ("expectancy", "fee_drag", "alpha", "ecology", "regime", "filtration"):
            self.assertIn(key, dr)

    def test_08_get_health_returns_dict(self):
        self.assertIsInstance(self.health, dict)

    def test_09_health_has_survivability_score(self):
        self.assertIn("survivability_score", self.health)

    def test_10_lineage_preserved_is_true(self):
        self.assertIs(self.full_result.get("lineage_preserved"), True)

    def test_11_auto_authorized_is_false_in_both(self):
        self.assertIs(self.full_result.get("auto_authorized"), False)
        self.assertIs(self.health.get("auto_authorized"), False)

    def test_12_diagnostic_only_is_true_in_both(self):
        self.assertIs(self.full_result.get("diagnostic_only"), True)
        self.assertIs(self.health.get("diagnostic_only"), True)


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    classes = [
        TestExpectancyReconstruction,
        TestFeeDragIntelligence,
        TestSurvivableAlphaDetector,
        TestEcologicalCollapseDetector,
        TestRegimeSurvivabilityEngine,
        TestAdaptiveSignalFiltration,
        TestEconomicTruthOrchestrator,
    ]
    for cls in classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, "w"))
    result = runner.run(suite)
    total  = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    failed = len(result.failures) + len(result.errors)

    print("═" * 62)
    if failed == 0:
        print(f"  ALL {passed}/{total} CHECKS PASSED ✓")
        print("  Phase-D Economic Truth Reconstruction is institutionally coherent.")
    else:
        print(f"  {passed}/{total} PASSED — {failed} FAILED ✗")
        for f in result.failures + result.errors:
            print(f"  FAIL: {f[0]}")
    print("═" * 62)
    sys.exit(0 if failed == 0 else 1)
