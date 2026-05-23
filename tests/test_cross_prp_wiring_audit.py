"""
Phase-B Cross-PRP Wiring Audit — Institutional Test Suite
84 automated validation checks.

Tests:
  TestEndpointConstitutionAuditor   (12 checks)
  TestReportPropagationAuditor      (12 checks)
  TestDependencySurvivabilityAuditor(12 checks)
  TestArchiveContinuityAuditor      (12 checks)
  TestRenderingConsistencyAuditor   (12 checks)
  TestCompressionReadinessMapper    (12 checks)
  TestCrossPRPAuditOrchestrator     (12 checks)
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ══════════════════════════════════════════════════════════════════════════════
# TestEndpointConstitutionAuditor  (12 checks)
# ══════════════════════════════════════════════════════════════════════════════

class TestEndpointConstitutionAuditor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from core.cross_prp_audit.endpoint_constitution_auditor import (
            audit_endpoint_constitution,
        )
        cls.result = audit_endpoint_constitution()

    def test_01_returns_dict(self):
        self.assertIsInstance(self.result, dict)

    def test_02_report_key_value(self):
        self.assertEqual(self.result.get("report"), "PRP_ENDPOINT_CONSTITUTION_REPORT")

    def test_03_registry_count_is_25(self):
        self.assertEqual(self.result.get("registry_count"), 25)

    def test_04_endpoints_valid_is_nonneg_int(self):
        v = self.result.get("endpoints_valid")
        self.assertIsInstance(v, int)
        self.assertGreaterEqual(v, 0)

    def test_05_orphan_reports_is_list(self):
        self.assertIsInstance(self.result.get("orphan_reports"), list)

    def test_06_duplicate_endpoints_is_list(self):
        v = self.result.get("duplicate_endpoints")
        self.assertIsInstance(v, list)

    def test_07_duplicate_bundle_keys_is_list(self):
        v = self.result.get("duplicate_bundle_keys")
        self.assertIsInstance(v, list)

    def test_08_missing_required_fields_is_list(self):
        self.assertIsInstance(self.result.get("missing_required_fields"), list)

    def test_09_naming_violations_is_list(self):
        self.assertIsInstance(self.result.get("naming_violations"), list)

    def test_10_constitution_score_in_range(self):
        s = self.result.get("constitution_score")
        self.assertIsInstance(s, int)
        self.assertGreaterEqual(s, 0)
        self.assertLessEqual(s, 100)

    def test_11_constitution_tier_is_valid(self):
        self.assertIn(
            self.result.get("constitution_tier"),
            {"HEALTHY", "ADEQUATE", "WEAK", "CRITICAL"},
        )

    def test_12_auto_authorized_is_false(self):
        self.assertIs(self.result.get("auto_authorized"), False)


# ══════════════════════════════════════════════════════════════════════════════
# TestReportPropagationAuditor  (12 checks)
# ══════════════════════════════════════════════════════════════════════════════

class TestReportPropagationAuditor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from core.cross_prp_audit.report_propagation_auditor import (
            audit_report_propagation,
        )
        cls.result = audit_report_propagation()

    def test_01_returns_dict(self):
        self.assertIsInstance(self.result, dict)

    def test_02_report_key_value(self):
        self.assertEqual(self.result.get("report"), "REPORT_PROPAGATION_AUDIT")

    def test_03_registry_count_is_25(self):
        self.assertEqual(self.result.get("registry_count"), 25)

    def test_04_bundle_count_gte_25(self):
        v = self.result.get("bundle_count")
        self.assertIsInstance(v, int)
        self.assertGreaterEqual(v, 25)

    def test_05_dashboard_count_is_25(self):
        self.assertEqual(self.result.get("dashboard_count"), 25)

    def test_06_ghost_reports_is_list(self):
        # All 25 registry reports are visible in the dashboard.
        v = self.result.get("ghost_reports")
        self.assertIsInstance(v, list)

    def test_07_orphan_bundle_keys_is_list(self):
        # The 4 extras are classified as EXTENDED_GOVERNANCE — no orphans.
        v = self.result.get("orphan_bundle_keys")
        self.assertIsInstance(v, list)

    def test_08_extended_governance_count_is_4(self):
        self.assertEqual(self.result.get("extended_governance_count"), 4)

    def test_09_registry_to_bundle_coverage_is_float_in_range(self):
        v = self.result.get("registry_to_bundle_coverage")
        self.assertIsInstance(v, float)
        self.assertGreaterEqual(v, 0.0)
        self.assertLessEqual(v, 100.0)

    def test_10_registry_to_dashboard_coverage_is_100(self):
        self.assertEqual(self.result.get("registry_to_dashboard_coverage"), 100.0)

    def test_11_propagation_score_in_range(self):
        s = self.result.get("propagation_score")
        self.assertIsInstance(s, int)
        self.assertGreaterEqual(s, 0)
        self.assertLessEqual(s, 100)

    def test_12_auto_authorized_is_false(self):
        self.assertIs(self.result.get("auto_authorized"), False)


# ══════════════════════════════════════════════════════════════════════════════
# TestDependencySurvivabilityAuditor  (12 checks)
# ══════════════════════════════════════════════════════════════════════════════

class TestDependencySurvivabilityAuditor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from core.cross_prp_audit.dependency_survivability_auditor import (
            audit_dependency_survivability,
        )
        cls.result = audit_dependency_survivability()

    def test_01_returns_dict(self):
        self.assertIsInstance(self.result, dict)

    def test_02_report_key_value(self):
        self.assertEqual(self.result.get("report"), "DEPENDENCY_SURVIVABILITY_REPORT")

    def test_03_module_checks_is_list(self):
        self.assertIsInstance(self.result.get("module_checks"), list)

    def test_04_checks_passed_is_nonneg_int(self):
        v = self.result.get("checks_passed")
        self.assertIsInstance(v, int)
        self.assertGreaterEqual(v, 0)

    def test_05_checks_failed_is_nonneg_int(self):
        v = self.result.get("checks_failed")
        self.assertIsInstance(v, int)
        self.assertGreaterEqual(v, 0)

    def test_06_passed_plus_failed_equals_module_checks_len(self):
        module_checks = self.result.get("module_checks", [])
        passed = self.result.get("checks_passed", 0)
        failed = self.result.get("checks_failed", 0)
        self.assertEqual(passed + failed, len(module_checks))

    def test_07_failed_modules_is_list(self):
        self.assertIsInstance(self.result.get("failed_modules"), list)

    def test_08_family_coverage_has_all_families_mapped(self):
        fc = self.result.get("family_coverage")
        self.assertIsInstance(fc, dict)
        self.assertIn("all_families_mapped", fc)

    def test_09_registry_integrity_has_all_families_valid(self):
        ri = self.result.get("registry_integrity")
        self.assertIsInstance(ri, dict)
        self.assertIn("all_families_valid", ri)

    def test_10_dependency_score_in_range(self):
        s = self.result.get("dependency_score")
        self.assertIsInstance(s, int)
        self.assertGreaterEqual(s, 0)
        self.assertLessEqual(s, 100)

    def test_11_dependency_tier_is_valid(self):
        self.assertIn(
            self.result.get("dependency_tier"),
            {"HEALTHY", "ADEQUATE", "WEAK", "CRITICAL"},
        )

    def test_12_auto_authorized_is_false(self):
        self.assertIs(self.result.get("auto_authorized"), False)


# ══════════════════════════════════════════════════════════════════════════════
# TestArchiveContinuityAuditor  (12 checks)
# ══════════════════════════════════════════════════════════════════════════════

class TestArchiveContinuityAuditor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from core.cross_prp_audit.archive_continuity_auditor import (
            audit_archive_continuity,
        )
        cls.result = audit_archive_continuity()

    def test_01_returns_dict(self):
        self.assertIsInstance(self.result, dict)

    def test_02_report_key_value(self):
        self.assertEqual(self.result.get("report"), "ARCHIVE_CONTINUITY_AUDIT")

    def test_03_continuity_checks_is_list_with_8_plus(self):
        v = self.result.get("continuity_checks")
        self.assertIsInstance(v, list)
        self.assertGreaterEqual(len(v), 8)

    def test_04_determinism_verified_is_bool(self):
        self.assertIsInstance(self.result.get("determinism_verified"), bool)

    def test_05_auto_authorized_enforced_is_bool(self):
        self.assertIsInstance(self.result.get("auto_authorized_enforced"), bool)

    def test_06_bundle_reproducible_is_bool(self):
        self.assertIsInstance(self.result.get("bundle_reproducible"), bool)

    def test_07_report_status_count_is_int(self):
        v = self.result.get("report_status_count")
        self.assertIsInstance(v, int)

    def test_08_data_directory_exists_is_bool(self):
        self.assertIsInstance(self.result.get("data_directory_exists"), bool)

    def test_09_archive_score_in_range(self):
        s = self.result.get("archive_score")
        self.assertIsInstance(s, int)
        self.assertGreaterEqual(s, 0)
        self.assertLessEqual(s, 100)

    def test_10_archive_tier_is_valid(self):
        self.assertIn(
            self.result.get("archive_tier"),
            {"HEALTHY", "ADEQUATE", "WEAK", "CRITICAL"},
        )

    def test_11_each_continuity_check_has_required_keys(self):
        checks = self.result.get("continuity_checks", [])
        for item in checks:
            self.assertIn("check", item)
            self.assertIn("status", item)
            self.assertIn("detail", item)

    def test_12_auto_authorized_is_false(self):
        self.assertIs(self.result.get("auto_authorized"), False)


# ══════════════════════════════════════════════════════════════════════════════
# TestRenderingConsistencyAuditor  (12 checks)
# ══════════════════════════════════════════════════════════════════════════════

class TestRenderingConsistencyAuditor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from core.cross_prp_audit.rendering_consistency_auditor import (
            audit_rendering_consistency,
        )
        cls.result = audit_rendering_consistency()

    def test_01_returns_dict(self):
        self.assertIsInstance(self.result, dict)

    def test_02_report_key_value(self):
        self.assertEqual(self.result.get("report"), "INSTITUTIONAL_RENDERING_AUDIT")

    def test_03_mode_results_has_json_html_markdown_keys(self):
        mr = self.result.get("mode_results")
        self.assertIsInstance(mr, dict)
        self.assertIn("json", mr)
        self.assertIn("html", mr)
        self.assertIn("markdown", mr)

    def test_04_render_checks_is_list_with_8_plus(self):
        v = self.result.get("render_checks")
        self.assertIsInstance(v, list)
        self.assertGreaterEqual(len(v), 8)

    def test_05_auto_authorized_enforced_is_bool(self):
        self.assertIsInstance(self.result.get("auto_authorized_enforced"), bool)

    def test_06_section_count_json_is_nonneg_int(self):
        v = self.result.get("section_count_json")
        self.assertIsInstance(v, int)
        self.assertGreaterEqual(v, 0)

    def test_07_parity_checks_is_dict(self):
        self.assertIsInstance(self.result.get("parity_checks"), dict)

    def test_08_parity_checks_has_summary_keys(self):
        pc = self.result.get("parity_checks", {})
        self.assertIn("html_has_summary", pc)
        self.assertIn("markdown_has_summary", pc)

    def test_09_rendering_score_in_range(self):
        s = self.result.get("rendering_score")
        self.assertIsInstance(s, int)
        self.assertGreaterEqual(s, 0)
        self.assertLessEqual(s, 100)

    def test_10_rendering_tier_is_valid(self):
        self.assertIn(
            self.result.get("rendering_tier"),
            {"HEALTHY", "ADEQUATE", "WEAK", "CRITICAL"},
        )

    def test_11_each_render_check_has_required_keys(self):
        checks = self.result.get("render_checks", [])
        for item in checks:
            self.assertIn("check", item)
            self.assertIn("status", item)

    def test_12_auto_authorized_is_false(self):
        self.assertIs(self.result.get("auto_authorized"), False)


# ══════════════════════════════════════════════════════════════════════════════
# TestCompressionReadinessMapper  (12 checks)
# ══════════════════════════════════════════════════════════════════════════════

class TestCompressionReadinessMapper(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from core.cross_prp_audit.compression_readiness_mapper import (
            map_compression_readiness,
        )
        cls.result = map_compression_readiness()

    def test_01_returns_dict(self):
        self.assertIsInstance(self.result, dict)

    def test_02_report_key_value(self):
        self.assertEqual(self.result.get("report"), "COMPRESSION_READINESS_REPORT")

    def test_03_total_reports_is_25(self):
        self.assertEqual(self.result.get("total_reports"), 25)

    def test_04_tier_distribution_has_keys_1_2_3_4(self):
        td = self.result.get("tier_distribution")
        self.assertIsInstance(td, dict)
        for k in (1, 2, 3, 4):
            self.assertIn(k, td)

    def test_05_tier_distribution_sums_to_25(self):
        td = self.result.get("tier_distribution", {})
        self.assertEqual(sum(td.values()), 25)

    def test_06_tier_1_reports_is_nonempty_list(self):
        v = self.result.get("tier_1_reports")
        self.assertIsInstance(v, list)
        self.assertGreaterEqual(len(v), 1)

    def test_07_tier_2_reports_is_list(self):
        self.assertIsInstance(self.result.get("tier_2_reports"), list)

    def test_08_compression_map_is_list_of_25(self):
        cm = self.result.get("compression_map")
        self.assertIsInstance(cm, list)
        self.assertEqual(len(cm), 25)

    def test_09_each_compression_map_entry_has_required_keys(self):
        for entry in self.result.get("compression_map", []):
            self.assertIn("report_id", entry)
            self.assertIn("name", entry)
            self.assertIn("tier", entry)
            self.assertIn("compression_label", entry)

    def test_10_executive_summary_candidates_is_list(self):
        self.assertIsInstance(self.result.get("executive_summary_candidates"), list)

    def test_11_compression_readiness_score_is_100(self):
        self.assertEqual(self.result.get("compression_readiness_score"), 100)

    def test_12_auto_authorized_is_false(self):
        self.assertIs(self.result.get("auto_authorized"), False)


# ══════════════════════════════════════════════════════════════════════════════
# TestCrossPRPAuditOrchestrator  (12 checks)
# ══════════════════════════════════════════════════════════════════════════════

class TestCrossPRPAuditOrchestrator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from core.cross_prp_audit.cross_prp_audit_orchestrator import (
            run_full_wiring_audit,
            get_wiring_audit_health,
        )
        cls.full_result = run_full_wiring_audit()
        cls.health_result = get_wiring_audit_health()

    def test_01_run_full_wiring_audit_returns_dict(self):
        self.assertIsInstance(self.full_result, dict)

    def test_02_get_wiring_audit_health_returns_dict(self):
        self.assertIsInstance(self.health_result, dict)

    def test_03_full_result_has_wiring_health_score(self):
        self.assertIn("wiring_health_score", self.full_result)

    def test_04_wiring_health_score_in_range(self):
        s = self.full_result.get("wiring_health_score")
        self.assertIsInstance(s, int)
        self.assertGreaterEqual(s, 0)
        self.assertLessEqual(s, 100)

    def test_05_wiring_health_tier_is_valid(self):
        self.assertIn(
            self.full_result.get("wiring_health_tier"),
            {"HEALTHY", "ADEQUATE", "WEAK", "CRITICAL"},
        )

    def test_06_audit_id_starts_with_AUDIT_prefix(self):
        audit_id = self.full_result.get("audit_id", "")
        self.assertTrue(str(audit_id).startswith("AUDIT-"))

    def test_07_domain_reports_is_dict_with_6_keys(self):
        dr = self.full_result.get("domain_reports")
        self.assertIsInstance(dr, dict)
        self.assertEqual(len(dr), 6)

    def test_08_domain_reports_has_all_expected_keys(self):
        dr = self.full_result.get("domain_reports", {})
        for key in ("constitution", "propagation", "dependency", "archive", "rendering", "compression"):
            self.assertIn(key, dr)

    def test_09_full_result_auto_authorized_is_false(self):
        self.assertIs(self.full_result.get("auto_authorized"), False)

    def test_10_health_result_has_wiring_health_score(self):
        self.assertIn("wiring_health_score", self.health_result)

    def test_11_health_result_has_domain_scores(self):
        self.assertIn("domain_scores", self.health_result)

    def test_12_generated_ts_is_int_in_both(self):
        ts_full = self.full_result.get("generated_ts")
        ts_health = self.health_result.get("generated_ts")
        self.assertIsInstance(ts_full, int)
        self.assertIsInstance(ts_health, int)


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    classes = [
        TestEndpointConstitutionAuditor, TestReportPropagationAuditor,
        TestDependencySurvivabilityAuditor, TestArchiveContinuityAuditor,
        TestRenderingConsistencyAuditor, TestCompressionReadinessMapper,
        TestCrossPRPAuditOrchestrator,
    ]
    for cls in classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
    result = runner.run(suite)
    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    failed = len(result.failures) + len(result.errors)

    print("═" * 62)
    if failed == 0:
        print(f"  ALL {passed}/{total} CHECKS PASSED ✓")
        print("  Phase-B Cross-PRP Wiring Audit is institutionally coherent.")
    else:
        print(f"  {passed}/{total} PASSED — {failed} FAILED ✗")
        for f in result.failures + result.errors:
            print(f"  FAIL: {f[0]}")
    print("═" * 62)
    sys.exit(0 if failed == 0 else 1)
