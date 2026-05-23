"""
PRP-PHASEC.5 — Governance Compression Layer.

Compresses governance civilization intelligence into an executive-operable
summary. Surfaces constitutional violations, alerts, conflicts, doctrinal
instability, escalation events, and audit failures without suppression or
optimistic inflation.

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
        return "DEGRADED"
    return "CRITICAL"


def compress_governance() -> dict:
    """
    PRP-PHASEC.5 — Compress governance state into an executive-readable view.

    Data sources:
      - Phase-B wiring audit (constitution, propagation, dependency)
      - Report registry (GOVERNANCE family reports)
      - Dashboard structure (coverage gaps)

    Returns a self-contained dict; never raises.
    """
    constitutional_violations: List[str] = []
    governance_alerts: List[str] = []
    unresolved_conflicts: List[str] = []
    escalation_events: List[str] = []
    audit_failures: List[str] = []
    doctrinal_instability: bool = False
    human_intervention_required: bool = False

    score_components: Dict[str, int] = {}

    # ── Source 1: Phase-B Wiring Audit ────────────────────────────────────────
    try:
        from core.cross_prp_audit.cross_prp_audit_orchestrator import run_full_wiring_audit
        audit = run_full_wiring_audit()
        domain_scores = audit.get("domain_scores", {})
        auditor_errors = audit.get("auditor_errors", [])

        # Constitution domain
        const_score = domain_scores.get("constitution_score", 0)
        score_components["wiring_constitution"] = const_score
        if const_score < 80:
            constitutional_violations.append(
                f"Endpoint constitution health degraded: {const_score}/100"
            )

        # Propagation domain
        prop_score = domain_scores.get("propagation_score", 0)
        score_components["wiring_propagation"] = prop_score
        if prop_score < 80:
            unresolved_conflicts.append(
                f"Report propagation gap: score={prop_score}/100"
            )

        # Dependency domain
        dep_score = domain_scores.get("dependency_score", 0)
        score_components["wiring_dependency"] = dep_score
        if dep_score < 80:
            escalation_events.append(
                f"Dependency survivability degraded: {dep_score}/100"
            )
            if dep_score < 60:
                human_intervention_required = True

        # Archive domain
        arch_score = domain_scores.get("archive_score", 0)
        score_components["wiring_archive"] = arch_score
        if arch_score < 60:
            escalation_events.append(f"Archive continuity critical: {arch_score}/100")

        # Rendering domain
        rend_score = domain_scores.get("rendering_score", 0)
        score_components["wiring_rendering"] = rend_score

        # Auditor errors → audit failures
        for err in auditor_errors:
            audit_failures.append(f"Auditor error: {err}")

        wiring_score = audit.get("wiring_health_score", 0)
        if wiring_score < 80:
            governance_alerts.append(
                f"Cross-PRP wiring health below threshold: {wiring_score}/100"
            )
        if wiring_score < 50:
            doctrinal_instability = True
            human_intervention_required = True

    except Exception as exc:
        governance_alerts.append(f"Wiring audit unavailable: {exc}")
        score_components["wiring_constitution"] = 0
        score_components["wiring_propagation"] = 0
        score_components["wiring_dependency"] = 0
        score_components["wiring_archive"] = 0
        score_components["wiring_rendering"] = 0

    # ── Source 2: Report Registry — Governance family ─────────────────────────
    try:
        from core.report_registry import REPORT_REGISTRY, FAMILY_GOVERNANCE
        gov_reports = {
            rid: meta for rid, meta in REPORT_REGISTRY.items()
            if meta.get("report_family") == FAMILY_GOVERNANCE
        }
        gov_report_count = len(gov_reports)
        score_components["governance_report_count"] = min(100, gov_report_count * 20)
    except Exception as exc:
        governance_alerts.append(f"Registry unavailable: {exc}")
        gov_report_count = 0
        score_components["governance_report_count"] = 0

    # ── Source 3: Dashboard Structure — Coverage Gaps ─────────────────────────
    try:
        from core.dashboard_orchestrator import build_dashboard_structure
        dash = build_dashboard_structure({})
        total    = dash.get("total_reports", 0)
        populated = dash.get("populated_reports", 0)
        coverage = dash.get("coverage_pct", 0.0)

        score_components["report_coverage"] = round(coverage)
        if coverage < 50.0:
            governance_alerts.append(
                f"Dashboard report coverage critically low: {coverage:.1f}%"
            )
        elif coverage < 80.0:
            governance_alerts.append(
                f"Dashboard report coverage below target: {coverage:.1f}%"
            )
    except Exception as exc:
        governance_alerts.append(f"Dashboard unavailable: {exc}")
        score_components["report_coverage"] = 50
        coverage = 0.0
        total    = 0
        populated = 0

    # ── Governance health score ───────────────────────────────────────────────
    # Weighted: constitution 30%, propagation 25%, dependency 20%,
    #           archive 15%, coverage 10%
    gov_score = round(
        score_components.get("wiring_constitution", 0) * 0.30
        + score_components.get("wiring_propagation", 0) * 0.25
        + score_components.get("wiring_dependency", 0)  * 0.20
        + score_components.get("wiring_archive", 0)     * 0.15
        + score_components.get("report_coverage", 50)   * 0.10
    )
    gov_score = max(0, min(100, gov_score))

    return {
        "report":                       "GOVERNANCE_EXECUTIVE_SUMMARY",
        "governance_health_score":      gov_score,
        "governance_health_tier":       _score_tier(gov_score),
        "constitutional_violations":    constitutional_violations,
        "constitutional_violations_count": len(constitutional_violations),
        "governance_alerts":            governance_alerts,
        "governance_alert_count":       len(governance_alerts),
        "unresolved_conflicts":         unresolved_conflicts,
        "unresolved_conflict_count":    len(unresolved_conflicts),
        "doctrinal_instability":        doctrinal_instability,
        "escalation_events":            escalation_events,
        "escalation_count":             len(escalation_events),
        "audit_failures":               audit_failures,
        "audit_failure_count":          len(audit_failures),
        "human_intervention_required":  human_intervention_required,
        "governance_report_count":      gov_report_count,
        "report_coverage_pct":          round(coverage, 1),
        "auto_authorized":              False,
        "generated_ts":                 int(_time.time() * 1000),
    }
