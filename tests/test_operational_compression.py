"""
Phase-C Operational Compression Layer — Institutional Test Suite
84 automated validation checks.

Tests:
  TestSignalEcologyCompressionLayer      (12 checks)
  TestGovernanceCompressionLayer         (12 checks)
  TestAnomalyClusteringEngine            (12 checks)
  TestInstitutionalHealthScoreEngine     (12 checks)
  TestMultiTierVisibilityArchitecture    (12 checks)
  TestExecutiveCompressionEngine         (12 checks)
  TestCompressionOrchestrator            (12 checks)
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ══════════════════════════════════════════════════════════════════════════════
# TestSignalEcologyCompressionLayer  (12 checks)
# ══════════════════════════════════════════════════════════════════════════════

class TestSignalEcologyCompressionLayer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from core.operational_compression.signal_ecology_compression_layer import (
            compress_signal_ecology,
        )
        cls.result = compress_signal_ecology()

    def test_01_returns_dict(self):
        self.assertIsInstance(self.result, dict)

    def test_02_report_key_value(self):
        self.assertEqual(self.result.get("report"), "SIGNAL_ECOLOGY_SUMMARY_REPORT")

    def test_03_ecology_score_in_range(self):
        s = self.result.get("ecology_score")
        self.assertIsInstance(s, int)
        self.assertGreaterEqual(s, 0)
        self.assertLessEqual(s, 100)

    def test_04_ecology_tier_is_valid(self):
        self.assertIn(
            self.result.get("ecology_tier"),
            {"HEALTHY", "ADEQUATE", "DEGRADED", "CRITICAL"},
        )

    def test_05_domains_is_dict(self):
        self.assertIsInstance(self.result.get("domains"), dict)

    def test_06_domain_count_is_8(self):
        self.assertEqual(self.result.get("domain_count"), 8)

    def test_07_all_8_domains_present(self):
        domains = self.result.get("domains", {})
        expected = {
            "signal_survivability", "expectancy_condition", "fee_drag_state",
            "ecological_collapse_risk", "session_viability", "strategy_density",
            "alpha_concentration", "regime_instability",
        }
        self.assertTrue(expected.issubset(domains.keys()))

    def test_08_each_domain_has_state_and_score(self):
        for name, domain in self.result.get("domains", {}).items():
            self.assertIn("state", domain, msg=f"Domain {name} missing 'state'")
            self.assertIn("score", domain, msg=f"Domain {name} missing 'score'")

    def test_09_alerts_is_list(self):
        self.assertIsInstance(self.result.get("alerts"), list)

    def test_10_alert_count_matches_alerts_length(self):
        alerts = self.result.get("alerts", [])
        self.assertEqual(self.result.get("alert_count"), len(alerts))

    def test_11_auto_authorized_is_false(self):
        self.assertIs(self.result.get("auto_authorized"), False)

    def test_12_generated_ts_is_int(self):
        self.assertIsInstance(self.result.get("generated_ts"), int)


# ══════════════════════════════════════════════════════════════════════════════
# TestGovernanceCompressionLayer  (12 checks)
# ══════════════════════════════════════════════════════════════════════════════

class TestGovernanceCompressionLayer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from core.operational_compression.governance_compression_layer import (
            compress_governance,
        )
        cls.result = compress_governance()

    def test_01_returns_dict(self):
        self.assertIsInstance(self.result, dict)

    def test_02_report_key_value(self):
        self.assertEqual(self.result.get("report"), "GOVERNANCE_EXECUTIVE_SUMMARY")

    def test_03_governance_health_score_in_range(self):
        s = self.result.get("governance_health_score")
        self.assertIsInstance(s, int)
        self.assertGreaterEqual(s, 0)
        self.assertLessEqual(s, 100)

    def test_04_governance_health_tier_is_valid(self):
        self.assertIn(
            self.result.get("governance_health_tier"),
            {"HEALTHY", "ADEQUATE", "DEGRADED", "CRITICAL"},
        )

    def test_05_constitutional_violations_is_list(self):
        self.assertIsInstance(self.result.get("constitutional_violations"), list)

    def test_06_constitutional_violations_count_matches(self):
        violations = self.result.get("constitutional_violations", [])
        self.assertEqual(
            self.result.get("constitutional_violations_count"), len(violations)
        )

    def test_07_governance_alerts_is_list(self):
        self.assertIsInstance(self.result.get("governance_alerts"), list)

    def test_08_governance_alert_count_matches(self):
        alerts = self.result.get("governance_alerts", [])
        self.assertEqual(self.result.get("governance_alert_count"), len(alerts))

    def test_09_human_intervention_required_is_bool(self):
        self.assertIsInstance(self.result.get("human_intervention_required"), bool)

    def test_10_doctrinal_instability_is_bool(self):
        self.assertIsInstance(self.result.get("doctrinal_instability"), bool)

    def test_11_auto_authorized_is_false(self):
        self.assertIs(self.result.get("auto_authorized"), False)

    def test_12_generated_ts_is_int(self):
        self.assertIsInstance(self.result.get("generated_ts"), int)


# ══════════════════════════════════════════════════════════════════════════════
# TestAnomalyClusteringEngine  (12 checks)
# ══════════════════════════════════════════════════════════════════════════════

class TestAnomalyClusteringEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from core.operational_compression.anomaly_clustering_engine import (
            cluster_anomalies,
        )
        cls.result = cluster_anomalies()

    def test_01_returns_dict(self):
        self.assertIsInstance(self.result, dict)

    def test_02_report_key_value(self):
        self.assertEqual(self.result.get("report"), "ANOMALY_CLUSTER_REPORT")

    def test_03_total_anomalies_is_nonneg_int(self):
        v = self.result.get("total_anomalies")
        self.assertIsInstance(v, int)
        self.assertGreaterEqual(v, 0)

    def test_04_critical_count_is_nonneg_int(self):
        v = self.result.get("critical_count")
        self.assertIsInstance(v, int)
        self.assertGreaterEqual(v, 0)

    def test_05_overall_tier_is_valid(self):
        self.assertIn(
            self.result.get("overall_tier"),
            {"NONE", "LOW", "MODERATE", "HIGH", "CRITICAL", "UNKNOWN"},
        )

    def test_06_cluster_count_is_7(self):
        self.assertEqual(self.result.get("cluster_count"), 7)

    def test_07_clusters_is_list_of_7(self):
        c = self.result.get("clusters")
        self.assertIsInstance(c, list)
        self.assertEqual(len(c), 7)

    def test_08_all_cluster_names_present(self):
        names = {c["cluster"] for c in self.result.get("clusters", [])}
        expected = {"GOVERNANCE", "ARCHIVE", "RENDERING",
                    "SURVIVABILITY", "ALPHA", "PROPAGATION", "ECOLOGICAL"}
        self.assertEqual(names, expected)

    def test_09_each_cluster_has_required_keys(self):
        for cluster in self.result.get("clusters", []):
            self.assertIn("cluster", cluster)
            self.assertIn("anomaly_count", cluster)
            self.assertIn("severity_tier", cluster)
            self.assertIn("anomalies", cluster)

    def test_10_each_anomaly_has_required_keys(self):
        for cluster in self.result.get("clusters", []):
            for anomaly in cluster.get("anomalies", []):
                self.assertIn("severity",    anomaly)
                self.assertIn("domain",      anomaly)
                self.assertIn("description", anomaly)
                self.assertIn("source",      anomaly)

    def test_11_auto_authorized_is_false(self):
        self.assertIs(self.result.get("auto_authorized"), False)

    def test_12_generated_ts_is_int(self):
        self.assertIsInstance(self.result.get("generated_ts"), int)


# ══════════════════════════════════════════════════════════════════════════════
# TestInstitutionalHealthScoreEngine  (12 checks)
# ══════════════════════════════════════════════════════════════════════════════

class TestInstitutionalHealthScoreEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from core.operational_compression.institutional_health_score_engine import (
            compute_institutional_health,
        )
        cls.result = compute_institutional_health()

    def test_01_returns_dict(self):
        self.assertIsInstance(self.result, dict)

    def test_02_report_key_value(self):
        self.assertEqual(self.result.get("report"), "INSTITUTIONAL_HEALTH_REPORT")

    def test_03_composite_score_in_range(self):
        s = self.result.get("composite_score")
        self.assertIsInstance(s, int)
        self.assertGreaterEqual(s, 0)
        self.assertLessEqual(s, 100)

    def test_04_composite_tier_is_valid(self):
        self.assertIn(
            self.result.get("composite_tier"),
            {"HEALTHY", "ADEQUATE", "DEGRADED", "CRITICAL"},
        )

    def test_05_domain_scores_is_dict_with_8_domains(self):
        ds = self.result.get("domain_scores")
        self.assertIsInstance(ds, dict)
        self.assertEqual(len(ds), 8)

    def test_06_all_8_domains_present_in_scores(self):
        ds = self.result.get("domain_scores", {})
        expected = {
            "economic_survivability", "governance_integrity", "archive_continuity",
            "signal_ecology", "alpha_density", "propagation_integrity",
            "replay_survivability", "rendering_integrity",
        }
        self.assertTrue(expected.issubset(ds.keys()))

    def test_07_all_domain_scores_in_range(self):
        for domain, score in self.result.get("domain_scores", {}).items():
            self.assertIsInstance(score, int, msg=f"{domain} score not int")
            self.assertGreaterEqual(score, 0, msg=f"{domain} score < 0")
            self.assertLessEqual(score, 100, msg=f"{domain} score > 100")

    def test_08_weights_is_dict_summing_to_1(self):
        weights = self.result.get("weights", {})
        self.assertIsInstance(weights, dict)
        total = sum(weights.values())
        self.assertAlmostEqual(total, 1.0, places=5)

    def test_09_assessment_only_is_true(self):
        self.assertIs(self.result.get("assessment_only"), True)

    def test_10_domain_notes_is_dict(self):
        self.assertIsInstance(self.result.get("domain_notes"), dict)

    def test_11_auto_authorized_is_false(self):
        self.assertIs(self.result.get("auto_authorized"), False)

    def test_12_generated_ts_is_int(self):
        self.assertIsInstance(self.result.get("generated_ts"), int)


# ══════════════════════════════════════════════════════════════════════════════
# TestMultiTierVisibilityArchitecture  (12 checks)
# ══════════════════════════════════════════════════════════════════════════════

class TestMultiTierVisibilityArchitecture(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from core.operational_compression.multi_tier_visibility_architecture import (
            build_visibility_tier_map,
        )
        cls.result = build_visibility_tier_map()

    def test_01_returns_dict(self):
        self.assertIsInstance(self.result, dict)

    def test_02_report_key_value(self):
        self.assertEqual(self.result.get("report"), "VISIBILITY_TIER_MAP")

    def test_03_total_reports_is_25(self):
        self.assertEqual(self.result.get("total_reports"), 25)

    def test_04_tier_summaries_is_list_of_4(self):
        ts = self.result.get("tier_summaries")
        self.assertIsInstance(ts, list)
        self.assertEqual(len(ts), 4)

    def test_05_tier_distribution_sums_to_25(self):
        td = self.result.get("tier_distribution", {})
        self.assertEqual(sum(td.values()), 25)

    def test_06_tier_1_reports_is_nonempty_list(self):
        t1 = self.result.get("tier_1_reports")
        self.assertIsInstance(t1, list)
        self.assertGreaterEqual(len(t1), 1)

    def test_07_all_tier_report_lists_present(self):
        for key in ("tier_1_reports", "tier_2_reports", "tier_3_reports", "tier_4_reports"):
            self.assertIsInstance(self.result.get(key), list)

    def test_08_each_tier_entry_has_required_keys(self):
        for tier_key in ("tier_1_reports", "tier_2_reports",
                         "tier_3_reports", "tier_4_reports"):
            for entry in self.result.get(tier_key, []):
                self.assertIn("report_id",        entry)
                self.assertIn("tier",             entry)
                self.assertIn("lineage_preserved", entry)
                self.assertIn("replay_safe",       entry)

    def test_09_lineage_preserved_is_true(self):
        self.assertIs(self.result.get("lineage_preserved"), True)

    def test_10_replay_safe_is_true(self):
        self.assertIs(self.result.get("replay_safe"), True)

    def test_11_auto_authorized_is_false(self):
        self.assertIs(self.result.get("auto_authorized"), False)

    def test_12_generated_ts_is_int(self):
        self.assertIsInstance(self.result.get("generated_ts"), int)


# ══════════════════════════════════════════════════════════════════════════════
# TestExecutiveCompressionEngine  (12 checks)
# ══════════════════════════════════════════════════════════════════════════════

class TestExecutiveCompressionEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from core.operational_compression.executive_compression_engine import (
            generate_executive_compression,
        )
        cls.result = generate_executive_compression()

    def test_01_returns_dict(self):
        self.assertIsInstance(self.result, dict)

    def test_02_report_key_value(self):
        self.assertEqual(self.result.get("report"), "EXECUTIVE_COMPRESSION_REPORT")

    def test_03_ecosystem_health_score_in_range(self):
        s = self.result.get("ecosystem_health_score")
        self.assertIsInstance(s, int)
        self.assertGreaterEqual(s, 0)
        self.assertLessEqual(s, 100)

    def test_04_ecosystem_health_tier_is_valid(self):
        self.assertIn(
            self.result.get("ecosystem_health_tier"),
            {"HEALTHY", "ADEQUATE", "DEGRADED", "CRITICAL", "UNKNOWN"},
        )

    def test_05_top_risks_is_list_capped_at_5(self):
        tr = self.result.get("top_risks")
        self.assertIsInstance(tr, list)
        self.assertLessEqual(len(tr), 5)

    def test_06_top_risk_count_matches_top_risks(self):
        tr = self.result.get("top_risks", [])
        self.assertEqual(self.result.get("top_risk_count"), len(tr))

    def test_07_alpha_condition_is_str(self):
        self.assertIsInstance(self.result.get("alpha_condition"), str)

    def test_08_governance_state_is_str(self):
        self.assertIsInstance(self.result.get("governance_state"), str)

    def test_09_summary_lines_is_nonempty_list(self):
        sl = self.result.get("summary_lines")
        self.assertIsInstance(sl, list)
        self.assertGreaterEqual(len(sl), 1)

    def test_10_assessment_only_is_true(self):
        self.assertIs(self.result.get("assessment_only"), True)

    def test_11_auto_authorized_is_false(self):
        self.assertIs(self.result.get("auto_authorized"), False)

    def test_12_generated_ts_is_int(self):
        self.assertIsInstance(self.result.get("generated_ts"), int)


# ══════════════════════════════════════════════════════════════════════════════
# TestCompressionOrchestrator  (12 checks)
# ══════════════════════════════════════════════════════════════════════════════

class TestCompressionOrchestrator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from core.operational_compression.compression_orchestrator import (
            run_full_compression,
            get_compression_health,
        )
        cls.full_result   = run_full_compression()
        cls.health_result = get_compression_health()

    def test_01_run_full_compression_returns_dict(self):
        self.assertIsInstance(self.full_result, dict)

    def test_02_get_compression_health_returns_dict(self):
        self.assertIsInstance(self.health_result, dict)

    def test_03_full_report_key_value(self):
        self.assertEqual(self.full_result.get("report"), "OPERATIONAL_COMPRESSION_REPORT")

    def test_04_compression_id_starts_with_COMP(self):
        cid = self.full_result.get("compression_id", "")
        self.assertTrue(str(cid).startswith("COMP-"))

    def test_05_composite_score_in_range(self):
        s = self.full_result.get("composite_score")
        self.assertIsInstance(s, int)
        self.assertGreaterEqual(s, 0)
        self.assertLessEqual(s, 100)

    def test_06_composite_tier_is_valid(self):
        self.assertIn(
            self.full_result.get("composite_tier"),
            {"HEALTHY", "ADEQUATE", "DEGRADED", "CRITICAL"},
        )

    def test_07_domain_reports_has_6_keys(self):
        dr = self.full_result.get("domain_reports")
        self.assertIsInstance(dr, dict)
        self.assertEqual(len(dr), 6)

    def test_08_domain_reports_has_all_expected_keys(self):
        dr = self.full_result.get("domain_reports", {})
        for key in ("signal_ecology", "governance", "anomalies",
                    "health", "visibility", "executive"):
            self.assertIn(key, dr)

    def test_09_lineage_preserved_is_true(self):
        self.assertIs(self.full_result.get("lineage_preserved"), True)

    def test_10_replay_safe_is_true(self):
        self.assertIs(self.full_result.get("replay_safe"), True)

    def test_11_auto_authorized_is_false_in_both(self):
        self.assertIs(self.full_result.get("auto_authorized"),   False)
        self.assertIs(self.health_result.get("auto_authorized"), False)

    def test_12_generated_ts_is_int_in_both(self):
        self.assertIsInstance(self.full_result.get("generated_ts"),   int)
        self.assertIsInstance(self.health_result.get("generated_ts"), int)


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    classes = [
        TestSignalEcologyCompressionLayer,
        TestGovernanceCompressionLayer,
        TestAnomalyClusteringEngine,
        TestInstitutionalHealthScoreEngine,
        TestMultiTierVisibilityArchitecture,
        TestExecutiveCompressionEngine,
        TestCompressionOrchestrator,
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
        print("  Phase-C Operational Compression is institutionally coherent.")
    else:
        print(f"  {passed}/{total} PASSED — {failed} FAILED ✗")
        for f in result.failures + result.errors:
            print(f"  FAIL: {f[0]}")
    print("═" * 62)
    sys.exit(0 if failed == 0 else 1)
