"""Verifier: FTD PHX-INSTITUTIONAL-VERIFICATION-PROGRAM-001"""
import sys, importlib, time
sys.path.insert(0, "/home/user/EOW-Quant-Engine-ChatGPT-")

MODULES = [
    "core.disaster_recovery.backup_engine",
    "core.disaster_recovery.restore_engine",
    "core.disaster_recovery.recovery_validator",
    "core.disaster_recovery.failover_manager",
    "core.maturity_scorecard.maturity_engine",
    "core.maturity_scorecard.readiness_calculator",
    "core.maturity_scorecard.institutional_dashboard",
]

TEST_SCRIPTS = [
    "tests.integration_audit.integration_dependency_mapper",
    "tests.integration_audit.integration_gap_detector",
    "tests.end_to_end.lifecycle_trace_engine",
    "tests.stress_testing.stress_test_engine",
    "tests.safety_certification.constitution_bypass_test",
    "tests.safety_certification.trust_bypass_test",
    "tests.safety_certification.autonomy_boundary_test",
    "tests.economic_validation.economic_reality_validator",
    "tests.reporting_audit.report_consistency_checker",
    "tests.production_certification.readiness_auditor",
    "tests.production_certification.final_certification_report",
]

passed = 0
total = len(MODULES) + len(TEST_SCRIPTS)
for mod in MODULES + TEST_SCRIPTS:
    try:
        importlib.import_module(mod)
        print(f"  OK  {mod}")
        passed += 1
    except Exception as e:
        print(f"  FAIL {mod}: {e}")

print(f"\n{passed}/{total} modules/scripts verified")
sys.exit(0 if passed == total else 1)
