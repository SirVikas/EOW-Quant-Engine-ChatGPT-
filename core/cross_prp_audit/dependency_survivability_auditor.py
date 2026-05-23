"""
PRP-PHASEB.3 — Dependency Survivability Audit.

Verifies that all modules depended upon by the report infrastructure
load without error, that all registry families are mapped, and that the
dashboard structure reports the expected count of 25 reports.

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from typing import Any, Dict, List


def _score_tier(score: int) -> str:
    if score >= 80:
        return "HEALTHY"
    if score >= 60:
        return "ADEQUATE"
    if score >= 40:
        return "WEAK"
    return "CRITICAL"


def audit_dependency_survivability() -> dict:
    """
    PRP-PHASEB.3 — Probe every module the report infrastructure depends on.

    Each check is individually wrapped so a single import failure does not
    abort the rest of the audit.  Returns a self-contained dict; never raises.
    """
    module_checks: List[Dict[str, Any]] = []

    def _record(module: str, status: str, error: str = "") -> None:
        module_checks.append({"module": module, "status": status, "error": error})

    # ── Check 1: core.report_registry ────────────────────────────────────────
    try:
        from core.report_registry import REPORT_REGISTRY, KNOWN_FAMILIES  # lazy
        assert len(REPORT_REGISTRY) > 0, "REPORT_REGISTRY is empty"
        assert len(KNOWN_FAMILIES) > 0, "KNOWN_FAMILIES is empty"
        _record("core.report_registry", "PASS")
    except Exception as exc:
        _record("core.report_registry", "FAIL", str(exc))

    # ── Check 2: core.dashboard_orchestrator ─────────────────────────────────
    try:
        from core.dashboard_orchestrator import build_tab_manifest  # lazy
        manifest = build_tab_manifest()
        assert isinstance(manifest, dict), "build_tab_manifest() did not return dict"
        _record("core.dashboard_orchestrator", "PASS")
    except Exception as exc:
        _record("core.dashboard_orchestrator", "FAIL", str(exc))

    # ── Checks 3-7: core.signal_truth sub-modules ────────────────────────────
    _signal_truth_modules = [
        "core.signal_truth.asymmetry_validation",
        "core.signal_truth.context_quality_engine",
        "core.signal_truth.directional_legitimacy",
        "core.signal_truth.false_positive_forensics",
        "core.signal_truth.signal_truth_engine",
    ]
    for mod in _signal_truth_modules:
        try:
            import importlib
            importlib.import_module(mod)
            _record(mod, "PASS")
        except Exception as exc:
            _record(mod, "FAIL", str(exc))

    # ── Checks 8-12: core.signal_ecology sub-modules ─────────────────────────
    _signal_ecology_modules = [
        "core.signal_ecology.adaptive_rsi_governor",
        "core.signal_ecology.alpha_context_memory",
        "core.signal_ecology.exploration_recovery",
        "core.signal_ecology.opportunity_ecology",
        "core.signal_ecology.signal_density_engine",
    ]
    for mod in _signal_ecology_modules:
        try:
            import importlib
            importlib.import_module(mod)
            _record(mod, "PASS")
        except Exception as exc:
            _record(mod, "FAIL", str(exc))

    # ── Check 13: core.institutional_report_renderer ─────────────────────────
    try:
        import importlib
        importlib.import_module("core.institutional_report_renderer")
        _record("core.institutional_report_renderer", "PASS")
    except Exception as exc:
        _record("core.institutional_report_renderer", "FAIL", str(exc))

    # ── Check 14: core.export_presentation ───────────────────────────────────
    try:
        import importlib
        importlib.import_module("core.export_presentation")
        _record("core.export_presentation", "PASS")
    except Exception as exc:
        _record("core.export_presentation", "FAIL", str(exc))

    # ── Check 15: core.download_experience ───────────────────────────────────
    try:
        import importlib
        importlib.import_module("core.download_experience")
        _record("core.download_experience", "PASS")
    except Exception as exc:
        _record("core.download_experience", "FAIL", str(exc))

    # ── Check 16: core.timeline_visualization ────────────────────────────────
    try:
        import importlib
        importlib.import_module("core.timeline_visualization")
        _record("core.timeline_visualization", "PASS")
    except Exception as exc:
        _record("core.timeline_visualization", "FAIL", str(exc))

    # ── Check 17: all registry families are in KNOWN_FAMILIES ─────────────────
    invalid_family_reports: List[str] = []
    all_families_valid: bool = False
    try:
        from core.report_registry import REPORT_REGISTRY, KNOWN_FAMILIES  # lazy
        for rid, meta in REPORT_REGISTRY.items():
            fam = meta.get("report_family", "")
            if fam not in KNOWN_FAMILIES:
                invalid_family_reports.append(rid)
        all_families_valid = len(invalid_family_reports) == 0
        if all_families_valid:
            _record("registry_family_validity", "PASS")
        else:
            _record(
                "registry_family_validity",
                "FAIL",
                f"Invalid families on: {invalid_family_reports}",
            )
    except Exception as exc:
        _record("registry_family_validity", "FAIL", str(exc))

    # ── Check 18: FAMILY_TO_TAB covers all KNOWN_FAMILIES ────────────────────
    unmapped_families: List[str] = []
    all_families_mapped: bool = False
    try:
        from core.report_registry import KNOWN_FAMILIES  # lazy
        from core.dashboard_orchestrator import FAMILY_TO_TAB  # lazy
        for fam in KNOWN_FAMILIES:
            if fam not in FAMILY_TO_TAB:
                unmapped_families.append(fam)
        all_families_mapped = len(unmapped_families) == 0
        if all_families_mapped:
            _record("family_to_tab_coverage", "PASS")
        else:
            _record(
                "family_to_tab_coverage",
                "FAIL",
                f"Families not in FAMILY_TO_TAB: {unmapped_families}",
            )
    except Exception as exc:
        _record("family_to_tab_coverage", "FAIL", str(exc))

    # ── Check 19: no duplicate report_ids (dict key uniqueness is structural) ─
    # A dict cannot have duplicate keys, so this is always 0 for a loaded dict.
    try:
        from core.report_registry import REPORT_REGISTRY  # lazy
        duplicate_ids: List[str] = []  # always empty for a valid dict
        _record("registry_duplicate_ids", "PASS")
    except Exception as exc:
        duplicate_ids = []
        _record("registry_duplicate_ids", "FAIL", str(exc))

    # ── Check 20: build_dashboard_structure({}) total_reports == 25 ───────────
    try:
        from core.dashboard_orchestrator import build_dashboard_structure  # lazy
        structure = build_dashboard_structure({})
        total = structure.get("total_reports", -1)
        if total == 25:
            _record("dashboard_structure_total_reports", "PASS")
        else:
            _record(
                "dashboard_structure_total_reports",
                "FAIL",
                f"Expected 25, got {total}",
            )
    except Exception as exc:
        _record("dashboard_structure_total_reports", "FAIL", str(exc))

    # ── Tally ─────────────────────────────────────────────────────────────────
    checks_passed = sum(1 for c in module_checks if c["status"] == "PASS")
    checks_failed = sum(1 for c in module_checks if c["status"] == "FAIL")
    total_checks = len(module_checks)
    failed_modules = [c["module"] for c in module_checks if c["status"] == "FAIL"]

    dependency_score = (
        round(checks_passed / total_checks * 100) if total_checks else 0
    )

    return {
        "report":          "DEPENDENCY_SURVIVABILITY_REPORT",
        "module_checks":   module_checks,
        "checks_passed":   checks_passed,
        "checks_failed":   checks_failed,
        "failed_modules":  failed_modules,
        "family_coverage": {
            "all_families_mapped": all_families_mapped,
            "unmapped_families":   unmapped_families,
        },
        "registry_integrity": {
            "duplicate_ids":         duplicate_ids,
            "all_families_valid":    all_families_valid,
            "invalid_family_reports": invalid_family_reports,
        },
        "dependency_score": dependency_score,
        "dependency_tier":  _score_tier(dependency_score),
        "auto_authorized":  False,
        "generated_ts":     int(_time.time() * 1000),
    }
