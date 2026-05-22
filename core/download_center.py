"""
FTD-UEI: Unified Download Center & Export Infrastructure Governance.

Orchestrates PHOENIX's institutional export infrastructure and produces
a constitutional export infrastructure governance assessment.

Capabilities assessed:
  - Bundle composer health (all 6 canonical bundles composable)
  - Manifest generation health
  - Reconstruction hash infrastructure
  - Archive integrity validation
  - Snapshot continuity health
  - Export ordering (topological sort validity)
  - Export metadata compliance

Constitutional guarantee:
  All recommendations have auto_authorized=False.
  Export governance remains permanently under human authority.

Pure analytics — no I/O, no live engine imports, fail-open.
"""
from __future__ import annotations

import hashlib
import time as _time
from typing import Dict, List, Optional

from core.export_composer import (
    compose_bundle, compose_all_bundles, get_composer_health,
    EXPORT_METADATA_REQUIRED_FIELDS,
)
from core.export_manifest import generate_manifest, validate_manifest
from core.reconstruction_hashing import (
    bundle_hash, content_hash, is_valid_sha256,
)
from core.archive_integrity import (
    verify_bundle_integrity, assess_archive_health,
)
from core.snapshot_manager import get_snapshot_health, SNAPSHOT_TYPES
from core.report_dependency_graph import topological_sort
from core.report_registry import REPORT_REGISTRY
from core.report_taxonomy import BUNDLE_MEMBERSHIP

# ── Hard constitutional export principles (immutable) ─────────────────────────
EXPORT_HARD_PRINCIPLES: Dict[str, bool] = {
    "human_authority_over_export_governance":  True,
    "explicit_export_approval_required":       True,
    "immutable_archive_lineage_guaranteed":    True,
    "all_archives_human_controlled":           True,
    "reconstruction_continuity_preserved":     True,
    "manifest_integrity_enforced":             True,
    "autonomous_archive_deletion":             False,
    "self_authorized_export_generation":       False,
    "autonomous_lineage_mutation":             False,
    "silent_manifest_alteration":             False,
    "autonomous_snapshot_governance":          False,
}


# ── Sub-assessments ───────────────────────────────────────────────────────────

def _bundle_composer_health() -> dict:
    try:
        return get_composer_health()
    except Exception:
        return {
            "all_bundles_composable": False,
            "bundle_count": 0,
            "succeeded_bundles": [],
            "failed_bundles": ["ALL"],
            "composer_healthy": False,
        }


def _manifest_generation_health() -> dict:
    try:
        # Spot-check: generate a manifest for EXECUTIVE bundle
        from core.report_taxonomy import get_reports_in_bundle, BUNDLE_EXECUTIVE
        report_ids = get_reports_in_bundle(BUNDLE_EXECUTIVE)
        meta = {"app_version": "test", "doctrine_version": "1.0",
                "lineage_epoch": "CURRENT", "export_bundle_type": BUNDLE_EXECUTIVE}
        manifest  = generate_manifest(BUNDLE_EXECUTIVE, report_ids, meta)
        is_valid, issues = validate_manifest(manifest)
        return {
            "manifest_generation_healthy": is_valid,
            "sample_bundle":              BUNDLE_EXECUTIVE,
            "manifest_id_format_ok":      manifest.get("manifest_id", "").startswith("MNF-"),
            "manifest_hash_valid":        is_valid_sha256(manifest.get("manifest_hash", "")),
            "issues":                     issues,
        }
    except Exception as exc:
        return {"manifest_generation_healthy": False, "error": str(exc)}


def _hash_infrastructure_health() -> dict:
    try:
        # Verify determinism and basic operation
        h1 = bundle_hash("TEST", ["A", "B"], 1_000_000)
        h2 = bundle_hash("TEST", ["B", "A"], 1_000_000)  # order-insensitive
        h3 = bundle_hash("TEST", ["A", "B"], 1_000_000)
        return {
            "hashing_operational":   True,
            "deterministic":         h1 == h3,
            "order_insensitive":     h1 == h2,
            "hash_format_valid":     is_valid_sha256(h1),
        }
    except Exception as exc:
        return {"hashing_operational": False, "error": str(exc)}


def _archive_integrity_health() -> dict:
    try:
        bundle  = compose_bundle("EXECUTIVE", app_version="test")
        result  = verify_bundle_integrity(bundle)
        return {
            "integrity_checks_operational": True,
            "sample_bundle_valid":          result["valid"],
            "sample_issues":                result["issues"],
        }
    except Exception as exc:
        return {"integrity_checks_operational": False, "error": str(exc)}


def _export_ordering_health() -> dict:
    try:
        topo = topological_sort()
        return {
            "topological_sort_valid":  len(topo) == len(REPORT_REGISTRY),
            "export_order_length":     len(topo),
            "first_primitives":        topo[:3],
            "ordering_healthy":        len(topo) > 0,
        }
    except Exception as exc:
        return {"topological_sort_valid": False, "error": str(exc)}


def _export_metadata_compliance() -> dict:
    return {
        "required_fields":         list(EXPORT_METADATA_REQUIRED_FIELDS),
        "required_field_count":    len(EXPORT_METADATA_REQUIRED_FIELDS),
        "compliance_schema_defined": True,
    }


def _generate_export_recommendations(
    composer_h: dict,
    manifest_h: dict,
    hash_h: dict,
    integrity_h: dict,
    snap_h: dict,
    ordering_h: dict,
) -> List[dict]:
    recs: List[dict] = []

    if not composer_h.get("composer_healthy"):
        recs.append({
            "priority":        "CRITICAL",
            "type":            "BUNDLE_COMPOSER_FAILURE",
            "summary":         (
                f"Bundle composer failing for: "
                f"{composer_h.get('failed_bundles', [])}. "
                "Institutional export continuity at risk."
            ),
            "action_required": "HUMAN_REVIEW_EXPORT_INFRASTRUCTURE",
            "auto_authorized": False,
        })

    if not manifest_h.get("manifest_generation_healthy"):
        recs.append({
            "priority":        "CRITICAL",
            "type":            "MANIFEST_GENERATION_FAILURE",
            "summary":         "Manifest generation failing — archive forensic index at risk.",
            "action_required": "HUMAN_REVIEW_MANIFEST_INFRASTRUCTURE",
            "auto_authorized": False,
        })

    if not hash_h.get("hashing_operational"):
        recs.append({
            "priority":        "HIGH",
            "type":            "HASH_INFRASTRUCTURE_FAILURE",
            "summary":         "Reconstruction hashing infrastructure failing — integrity guarantees degraded.",
            "action_required": "HUMAN_REVIEW_HASH_INFRASTRUCTURE",
            "auto_authorized": False,
        })

    if not integrity_h.get("integrity_checks_operational"):
        recs.append({
            "priority":        "HIGH",
            "type":            "INTEGRITY_CHECK_FAILURE",
            "summary":         "Archive integrity checks failing — corruption detection unavailable.",
            "action_required": "HUMAN_REVIEW_INTEGRITY_INFRASTRUCTURE",
            "auto_authorized": False,
        })

    if not ordering_h.get("topological_sort_valid"):
        recs.append({
            "priority":        "MEDIUM",
            "type":            "EXPORT_ORDERING_INVALID",
            "summary":         "Topological export ordering invalid — dependency-aware export unavailable.",
            "action_required": "HUMAN_REVIEW_DEPENDENCY_GRAPH",
            "auto_authorized": False,
        })

    if not recs:
        recs.append({
            "priority":        "LOW",
            "type":            "EXPORT_INFRASTRUCTURE_HEALTHY",
            "summary": (
                "All export infrastructure components operational — bundle composition, "
                "manifest generation, reconstruction hashing, and archive integrity healthy."
            ),
            "action_required": "CONTINUE_MONITORING",
            "auto_authorized": False,
        })

    return recs


# ── Public entry point ────────────────────────────────────────────────────────

def compute_export_infrastructure_governance(
    snapshots: Optional[List[dict]] = None,
) -> dict:
    """
    Produce a constitutional export infrastructure governance assessment.

    Args:
        snapshots: Optional list of snapshot records from the session ledger.

    Returns a research-only dict. Never raises. Never modifies input.
    All recommendations have auto_authorized=False.
    """
    try:
        snap_list   = list(snapshots or [])
        composer_h  = _bundle_composer_health()
        manifest_h  = _manifest_generation_health()
        hash_h      = _hash_infrastructure_health()
        integrity_h = _archive_integrity_health()
        ordering_h  = _export_ordering_health()
        snap_h      = get_snapshot_health(snap_list)
        meta_comp   = _export_metadata_compliance()
        recs        = _generate_export_recommendations(
            composer_h, manifest_h, hash_h, integrity_h, snap_h, ordering_h
        )

        # Infrastructure health score (0–100)
        score = 0.0
        if composer_h.get("composer_healthy"):     score += 30.0
        if manifest_h.get("manifest_generation_healthy"): score += 20.0
        if hash_h.get("hashing_operational"):      score += 20.0
        if integrity_h.get("integrity_checks_operational"): score += 15.0
        if ordering_h.get("topological_sort_valid"): score += 10.0
        if meta_comp.get("compliance_schema_defined"):  score += 5.0

        if   score >= 80.0: health_tier = "HEALTHY"
        elif score >= 60.0: health_tier = "ADEQUATE"
        elif score >= 40.0: health_tier = "VULNERABLE"
        else:               health_tier = "CRITICAL"

        ts      = int(_time.time() * 1000)
        payload = f"UEI|{ts}|{score}|{len(REPORT_REGISTRY)}"
        fp      = hashlib.sha256(payload.encode()).hexdigest()

        return {
            "scope_note": (
                "FTD-UEI constitutional unified export & download infrastructure governance — "
                "research instrumentation only. Assesses whether PHOENIX's institutional export "
                "infrastructure is operational, integrity-preserving, lineage-continuous, and "
                "constitutionally auditable. "
                "All export governance remains permanently subordinate to human authority."
            ),
            "infrastructure_health_score": round(score, 2),
            "infrastructure_health_tier":  health_tier,
            "bundle_composer_health":      composer_h,
            "manifest_generation_health":  manifest_h,
            "hash_infrastructure_health":  hash_h,
            "archive_integrity_health":    integrity_h,
            "export_ordering_health":      ordering_h,
            "snapshot_health":             snap_h,
            "export_metadata_compliance":  meta_comp,
            "available_bundles":           sorted(BUNDLE_MEMBERSHIP.keys()),
            "available_snapshot_types":    sorted(SNAPSHOT_TYPES),
            "recommendations":             recs,
            "export_hard_principles":      EXPORT_HARD_PRINCIPLES,
            "audit_entry": {
                "entry_id":                   f"UEI-{ts}-{fp[:16]}",
                "timestamp_ms":               ts,
                "entry_type":                 "INFRASTRUCTURE_ASSESSMENT",
                "infrastructure_health_score": round(score, 2),
                "health_tier":                health_tier,
                "snapshots_assessed":         len(snap_list),
                "human_approval_required":    True,
                "auto_authorized":            False,
                "immutable":                  True,
            },
        }
    except Exception:
        ts = int(_time.time() * 1000)
        return {
            "scope_note":  "FTD-UEI research instrumentation — analysis error.",
            "error":       "analysis failed",
            "export_hard_principles": EXPORT_HARD_PRINCIPLES,
            "audit_entry": {
                "entry_id":        f"UEI-{ts}-error",
                "timestamp_ms":    ts,
                "entry_type":      "INFRASTRUCTURE_ASSESSMENT",
                "auto_authorized": False,
                "immutable":       True,
            },
        }
