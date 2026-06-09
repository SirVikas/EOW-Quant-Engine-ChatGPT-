"""
Verification script for v1.83.0 reality-proof gap closure.
Imports all 20 new core modules and reports OK/FAIL per module.
"""
import importlib
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

MODULES = [
    "core.data_assurance.market_data_auditor",
    "core.data_assurance.data_gap_detector",
    "core.data_assurance.data_integrity_validator",
    "core.data_assurance.feed_health_monitor",
    "core.signal_certification.signal_certifier",
    "core.signal_certification.signal_decay_tracker",
    "core.signal_certification.false_positive_tracker",
    "core.signal_certification.false_negative_tracker",
    "core.drift_detection.drift_engine",
    "core.drift_detection.behavior_drift_tracker",
    "core.drift_detection.performance_drift_detector",
    "core.drift_detection.alert_generator",
    "core.postmortem.postmortem_engine",
    "core.postmortem.incident_reconstructor",
    "core.postmortem.lesson_extractor",
    "core.postmortem.corrective_action_tracker",
    "core.readiness_v2.continuous_readiness_engine",
    "core.readiness_v2.readiness_trend_tracker",
    "core.readiness_v2.certification_monitor",
    "core.readiness_v2.compliance_dashboard",
]


def main():
    failures = []
    for mod in MODULES:
        try:
            importlib.import_module(mod)
            print(f"  OK  {mod}")
        except Exception as exc:
            print(f"  FAIL  {mod}  —  {exc}")
            failures.append(mod)

    print()
    if failures:
        print(f"FAILED: {len(failures)}/{len(MODULES)} modules")
        sys.exit(1)
    else:
        print(f"ALL PASS: {len(MODULES)}/{len(MODULES)} modules verified")
        sys.exit(0)


if __name__ == "__main__":
    main()
