"""
FTD-RTAG: Export Bundle Manager & Report Ecosystem Governance.

Provides:
  - Bundle composition queries
  - Registry health validation
  - Bundle coverage analysis
  - Overlap risk assessment
  - Archive survivability assessment
  - compute_report_ecosystem_governance() — the constitutional governance entry point

Constitutional guarantee:
  All recommendations have auto_authorized=False.
  Reporting governance remains permanently under human authority.

Pure analytics — no I/O, no live engine imports, fail-open.
"""
from __future__ import annotations

import hashlib
import time as _time
from typing import Any, Dict, List

from core.report_registry import (
    REPORT_REGISTRY,
    REGISTRY_REQUIRED_FIELDS,
    PRIORITY_CRITICAL, PRIORITY_HIGH,
)
from core.report_taxonomy import (
    BUNDLE_MEMBERSHIP, BUNDLE_MASTER_ARCHIVE,
    get_orphaned_reports, get_coverage_summary,
)
from core.report_dependency_graph import (
    get_dependency_graph_health,
    get_overlap_map,
    get_high_overlap_reports,
)
from core.report_metadata_schema import (
    REQUIRED_METADATA_FIELDS, SCHEMA_VERSION,
)

# ── Hard constitutional reporting principles (immutable) ──────────────────────
REPORTING_HARD_PRINCIPLES: Dict[str, bool] = {
    "human_authority_over_reporting_governance": True,
    "explicit_archive_approval_required":        True,
    "immutable_lineage_guaranteed":              True,
    "all_exports_human_controlled":              True,
    "audit_continuity_preserved":               True,
    "canonical_taxonomy_enforced":              True,
    "autonomous_lineage_mutation":               False,
    "self_authorized_export":                    False,
    "autonomous_archive_rewriting":              False,
    "undocumented_report_proliferation":         False,
    "autonomous_governance_modification":        False,
}


# ── Bundle composition ────────────────────────────────────────────────────────

def get_bundle_composition(bundle_name: str) -> Dict[str, Any]:
    """Full metadata for a named export bundle."""
    members = sorted(BUNDLE_MEMBERSHIP.get(bundle_name, set()))
    specs   = [REPORT_REGISTRY[r] for r in members if r in REPORT_REGISTRY]
    return {
        "bundle_name":    bundle_name,
        "report_count":   len(members),
        "report_ids":     members,
        "families":       sorted({s["report_family"] for s in specs}),
        "tiers":          sorted({s["export_tier"] for s in specs}),
        "critical_count": sum(1 for s in specs if s.get("archive_priority") == PRIORITY_CRITICAL),
        "high_count":     sum(1 for s in specs if s.get("archive_priority") == PRIORITY_HIGH),
    }


def get_all_bundle_compositions() -> Dict[str, Dict]:
    return {b: get_bundle_composition(b) for b in sorted(BUNDLE_MEMBERSHIP)}


# ── Sub-assessments ───────────────────────────────────────────────────────────

def _registry_health() -> dict:
    violations: List[str] = []
    for r_id, spec in REPORT_REGISTRY.items():
        for f in REGISTRY_REQUIRED_FIELDS:
            if f not in spec:
                violations.append(f"{r_id}: missing field '{f}'")
        fam  = spec.get("report_family", "")
        tier = spec.get("archive_priority", "")
        if not fam:
            violations.append(f"{r_id}: empty report_family")
        if not tier:
            violations.append(f"{r_id}: empty archive_priority")

    families_represented = sorted({s["report_family"] for s in REPORT_REGISTRY.values()})
    critical_reports     = sorted(
        r for r, s in REPORT_REGISTRY.items()
        if s.get("archive_priority") == PRIORITY_CRITICAL
    )
    return {
        "total_reports":         len(REPORT_REGISTRY),
        "schema_violations":     violations,
        "violations_count":      len(violations),
        "families_represented":  families_represented,
        "family_count":          len(families_represented),
        "critical_reports":      critical_reports,
        "critical_count":        len(critical_reports),
        "registry_healthy":      len(violations) == 0,
    }


def _bundle_coverage_health() -> dict:
    orphaned   = get_orphaned_reports()
    all_bund   = get_all_bundle_compositions()
    return {
        "orphaned_reports": orphaned,
        "orphaned_count":   len(orphaned),
        "bundle_summary":   {b: c["report_count"] for b, c in all_bund.items()},
        "coverage_healthy": len(orphaned) == 0,
    }


def _overlap_risk_assessment() -> dict:
    overlap_map = get_overlap_map()
    high_risk   = [(r_id, ovs) for r_id, ovs in overlap_map.items() if len(ovs) >= 2]
    total_decl  = sum(len(v) for v in overlap_map.values())
    return {
        "total_overlap_declarations": total_decl,
        "high_overlap_reports":       sorted(r for r, _ in high_risk),
        "high_overlap_count":         len(high_risk),
        "overlap_risk_tier": (
            "HIGH"     if len(high_risk) > 5 else
            "MODERATE" if len(high_risk) > 2 else
            "LOW"
        ),
    }


def _metadata_compliance_summary() -> dict:
    return {
        "schema_version":           SCHEMA_VERSION,
        "required_fields":          list(REQUIRED_METADATA_FIELDS),
        "required_field_count":     len(REQUIRED_METADATA_FIELDS),
        "compliance_schema_defined": True,
    }


def _archive_survivability() -> dict:
    high_prio = sorted(
        r_id for r_id, s in REPORT_REGISTRY.items()
        if s.get("archive_priority") in (PRIORITY_CRITICAL, PRIORITY_HIGH)
    )
    return {
        "high_priority_reports": high_prio,
        "high_priority_count":   len(high_prio),
        "survivability_tier": (
            "STRONG"   if len(high_prio) >= 10 else
            "ADEQUATE" if len(high_prio) >= 5  else
            "WEAK"
        ),
    }


def _generate_ecosystem_recommendations(
    registry_h: dict,
    dep_h: dict,
    bundle_h: dict,
    overlap_h: dict,
) -> List[dict]:
    recs: List[dict] = []

    if registry_h["violations_count"] > 0:
        recs.append({
            "priority":        "CRITICAL",
            "type":            "REGISTRY_SCHEMA_VIOLATION",
            "summary":         (
                f"{registry_h['violations_count']} registry schema violation(s) — "
                "report metadata incomplete."
            ),
            "action_required": "FIX_REGISTRY_SCHEMA",
            "auto_authorized": False,
        })

    if not dep_h["cycle_free"]:
        recs.append({
            "priority":        "CRITICAL",
            "type":            "DEPENDENCY_CYCLE",
            "summary":         "Circular dependency detected — dependency graph corrupted.",
            "action_required": "HUMAN_REVIEW_DEPENDENCY_GRAPH",
            "auto_authorized": False,
        })

    if dep_h["dangling_count"] > 0:
        recs.append({
            "priority":        "HIGH",
            "type":            "DANGLING_DEPENDENCIES",
            "summary":         (
                f"{dep_h['dangling_count']} dangling dependency reference(s) — "
                "reports reference unregistered reports."
            ),
            "action_required": "REGISTER_MISSING_REPORTS",
            "auto_authorized": False,
        })

    if bundle_h["orphaned_count"] > 0:
        recs.append({
            "priority":        "MEDIUM",
            "type":            "ORPHANED_REPORTS",
            "summary":         (
                f"{bundle_h['orphaned_count']} report(s) not assigned to any export bundle."
            ),
            "action_required": "ASSIGN_TO_BUNDLE",
            "auto_authorized": False,
        })

    if overlap_h["overlap_risk_tier"] in ("HIGH", "MODERATE"):
        recs.append({
            "priority":        "MEDIUM",
            "type":            "METRIC_OVERLAP_RISK",
            "summary":         (
                f"Overlap risk {overlap_h['overlap_risk_tier']} — "
                f"{overlap_h['high_overlap_count']} reports declare ≥2 overlapping reports."
            ),
            "action_required": "CONSIDER_CANONICAL_METRIC_CONSOLIDATION",
            "auto_authorized": False,
        })

    if not recs:
        recs.append({
            "priority":        "LOW",
            "type":            "ECOSYSTEM_HEALTHY",
            "summary":         (
                "Report ecosystem governance healthy — registry complete, "
                "dependencies clean, all reports assigned to export bundles."
            ),
            "action_required": "CONTINUE_MONITORING",
            "auto_authorized": False,
        })

    return recs


# ── Public entry point ────────────────────────────────────────────────────────

def compute_report_ecosystem_governance() -> dict:
    """
    Produce a constitutional report taxonomy alignment & export governance assessment.

    Returns a research-only dict. Never raises. Never modifies input.
    All recommendations have auto_authorized=False.
    """
    try:
        registry_h = _registry_health()
        dep_h      = get_dependency_graph_health()
        bundle_h   = _bundle_coverage_health()
        overlap_h  = _overlap_risk_assessment()
        meta_h     = _metadata_compliance_summary()
        archive_h  = _archive_survivability()
        coverage   = get_coverage_summary()
        recs       = _generate_ecosystem_recommendations(
            registry_h, dep_h, bundle_h, overlap_h
        )

        # Ecosystem health score (0–100, higher = better governed)
        penalty = 0.0
        if not registry_h["registry_healthy"]:
            penalty += 30.0
        if not dep_h["cycle_free"]:
            penalty += 30.0
        if dep_h["dangling_count"] > 0:
            penalty += 15.0
        if bundle_h["orphaned_count"] > 0:
            penalty += 10.0
        if   overlap_h["overlap_risk_tier"] == "HIGH":
            penalty += 15.0
        elif overlap_h["overlap_risk_tier"] == "MODERATE":
            penalty += 7.0
        score = max(0.0, min(100.0, 100.0 - penalty))

        if   score >= 80.0: health_tier = "HEALTHY"
        elif score >= 60.0: health_tier = "ADEQUATE"
        elif score >= 40.0: health_tier = "VULNERABLE"
        else:               health_tier = "CRITICAL"

        ts      = int(_time.time() * 1000)
        payload = f"RTAG|{ts}|{len(REPORT_REGISTRY)}|{score}"
        fp      = hashlib.sha256(payload.encode()).hexdigest()

        return {
            "scope_note": (
                "FTD-RTAG constitutional report taxonomy alignment & export governance — "
                "research instrumentation only. Assesses whether the PHOENIX reporting "
                "ecosystem is canonical, composable, auditable, and institutionally governed. "
                "PHOENIX reporting must remain permanently subordinate to explicit human governance."
            ),
            "total_reports_registered":  len(REPORT_REGISTRY),
            "ecosystem_health_score":    round(score, 2),
            "ecosystem_health_tier":     health_tier,
            "registry_health":           registry_h,
            "dependency_health":         dep_h,
            "bundle_coverage":           bundle_h,
            "overlap_risk":              overlap_h,
            "metadata_compliance":       meta_h,
            "archive_survivability":     archive_h,
            "coverage_summary":          coverage,
            "bundle_compositions":       get_all_bundle_compositions(),
            "recommendations":           recs,
            "reporting_hard_principles": REPORTING_HARD_PRINCIPLES,
            "audit_entry": {
                "entry_id":               f"RTAG-{ts}-{fp[:16]}",
                "timestamp_ms":           ts,
                "entry_type":             "GOVERNANCE_ASSESSMENT",
                "total_reports_assessed": len(REPORT_REGISTRY),
                "health_score":           round(score, 2),
                "health_tier":            health_tier,
                "human_approval_required": True,
                "auto_authorized":        False,
                "immutable":              True,
            },
        }
    except Exception:
        ts = int(_time.time() * 1000)
        return {
            "scope_note":  "FTD-RTAG research instrumentation — analysis error.",
            "error":       "analysis failed",
            "reporting_hard_principles": REPORTING_HARD_PRINCIPLES,
            "audit_entry": {
                "entry_id":          f"RTAG-{ts}-error",
                "timestamp_ms":      ts,
                "entry_type":        "GOVERNANCE_ASSESSMENT",
                "auto_authorized":   False,
                "immutable":         True,
            },
        }
