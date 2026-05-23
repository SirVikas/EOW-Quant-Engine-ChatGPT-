"""
PRP-PHASEB.1 — Endpoint Constitutional Audit.

Verifies that every report in REPORT_REGISTRY carries a structurally valid,
non-duplicate endpoint and bundle_key and that naming conventions are met.

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from typing import Any, Dict, List


_REQUIRED_FIELDS: tuple = (
    "name",
    "report_family",
    "archive_priority",
    "bundle_key",
    "endpoint",
)


def _score_tier(score: int) -> str:
    if score >= 80:
        return "HEALTHY"
    if score >= 60:
        return "ADEQUATE"
    if score >= 40:
        return "WEAK"
    return "CRITICAL"


def audit_endpoint_constitution() -> dict:
    """
    PRP-PHASEB.1 — Inspect every registry report for endpoint/bundle_key
    structural integrity and constitutional naming conventions.

    Returns a self-contained audit dict; never raises.
    """
    try:
        from core.report_registry import REPORT_REGISTRY  # lazy

        registry: Dict[str, Dict[str, Any]] = REPORT_REGISTRY

        registry_count: int = len(registry)
        orphan_reports: List[str] = []
        duplicate_endpoints: List[str] = []
        duplicate_bundle_keys: List[str] = []
        missing_required_fields: List[dict] = []
        naming_violations: List[str] = []
        findings: List[str] = []

        seen_endpoints: Dict[str, str] = {}   # endpoint → first report_id
        seen_bundle_keys: Dict[str, str] = {} # bundle_key → first report_id
        dup_ep_set: set = set()
        dup_bk_set: set = set()
        endpoints_valid: int = 0

        for report_id, meta in registry.items():
            endpoint = meta.get("endpoint", "") or ""
            bundle_key = meta.get("bundle_key", "") or ""

            # ── Orphan check ──────────────────────────────────────────────────
            if not endpoint or not bundle_key:
                orphan_reports.append(report_id)
            else:
                endpoints_valid += 1

            # ── Duplicate endpoint detection ──────────────────────────────────
            if endpoint:
                if endpoint in seen_endpoints:
                    if endpoint not in dup_ep_set:
                        duplicate_endpoints.append(endpoint)
                        dup_ep_set.add(endpoint)
                else:
                    seen_endpoints[endpoint] = report_id

            # ── Duplicate bundle_key detection ────────────────────────────────
            if bundle_key:
                if bundle_key in seen_bundle_keys:
                    if bundle_key not in dup_bk_set:
                        duplicate_bundle_keys.append(bundle_key)
                        dup_bk_set.add(bundle_key)
                else:
                    seen_bundle_keys[bundle_key] = report_id

            # ── Required field presence ───────────────────────────────────────
            missing = [
                f for f in _REQUIRED_FIELDS
                if not meta.get(f)
            ]
            if missing:
                missing_required_fields.append({
                    "report_id": report_id,
                    "missing_fields": missing,
                })

            # ── Naming convention: endpoint must contain /learning-intelligence/
            if endpoint and "/learning-intelligence/" not in endpoint:
                naming_violations.append(report_id)

        # ── Scoring — deduct 15 per violated category ─────────────────────────
        constitution_score: int = 100
        if orphan_reports:
            constitution_score -= 15
            findings.append(
                f"ORPHAN_ENDPOINTS: {len(orphan_reports)} report(s) missing endpoint "
                f"or bundle_key — {orphan_reports}"
            )
        if duplicate_endpoints:
            constitution_score -= 15
            findings.append(
                f"DUPLICATE_ENDPOINTS: {len(duplicate_endpoints)} endpoint(s) reused — "
                f"{duplicate_endpoints}"
            )
        if duplicate_bundle_keys:
            constitution_score -= 15
            findings.append(
                f"DUPLICATE_BUNDLE_KEYS: {len(duplicate_bundle_keys)} key(s) reused — "
                f"{duplicate_bundle_keys}"
            )
        if missing_required_fields:
            constitution_score -= 15
            findings.append(
                f"MISSING_REQUIRED_FIELDS: {len(missing_required_fields)} report(s) "
                f"have incomplete field sets"
            )
        if naming_violations:
            constitution_score -= 15
            findings.append(
                f"NAMING_VIOLATIONS: {len(naming_violations)} endpoint(s) do not contain "
                f"/learning-intelligence/ — {naming_violations}"
            )

        constitution_score = max(0, constitution_score)

        if not findings:
            findings.append(
                f"ALL_CHECKS_PASSED: {registry_count} reports fully constitute-valid"
            )

        return {
            "report":                 "PRP_ENDPOINT_CONSTITUTION_REPORT",
            "registry_count":         registry_count,
            "endpoints_valid":        endpoints_valid,
            "orphan_reports":         orphan_reports,
            "duplicate_endpoints":    duplicate_endpoints,
            "duplicate_bundle_keys":  duplicate_bundle_keys,
            "missing_required_fields": missing_required_fields,
            "naming_violations":      naming_violations,
            "constitution_score":     constitution_score,
            "constitution_tier":      _score_tier(constitution_score),
            "findings":               findings,
            "auto_authorized":        False,
            "generated_ts":           int(_time.time() * 1000),
        }

    except Exception as exc:
        return {
            "report":                  "PRP_ENDPOINT_CONSTITUTION_REPORT",
            "error":                   str(exc),
            "registry_count":          0,
            "endpoints_valid":         0,
            "orphan_reports":          [],
            "duplicate_endpoints":     [],
            "duplicate_bundle_keys":   [],
            "missing_required_fields": [],
            "naming_violations":       [],
            "constitution_score":      0,
            "constitution_tier":       "CRITICAL",
            "findings":                [f"AUDIT_FAILED: {exc}"],
            "auto_authorized":         False,
            "generated_ts":            int(_time.time() * 1000),
        }
