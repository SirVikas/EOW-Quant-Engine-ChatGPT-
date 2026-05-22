"""
FTD-UEI: Archive Integrity Validation.

Validates that composed export bundles and their manifests have
not been tampered with, corrupted, or structurally degraded.

Provides: bundle integrity verification, manifest integrity verification,
corruption detection, and overall archive health assessment.

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

from typing import Dict, List

from core.reconstruction_hashing import (
    verify_bundle_hash,
    verify_manifest_hash,
    is_valid_sha256,
)
from core.export_composer import EXPORT_METADATA_REQUIRED_FIELDS


# ── Bundle integrity ──────────────────────────────────────────────────────────

def verify_bundle_integrity(bundle: dict) -> dict:
    """
    Full integrity check on a composed bundle.
    Verifies reconstruction_hash, manifest_hash, and structural completeness.
    """
    issues: List[str] = []

    # Hash verification
    hash_result = verify_bundle_hash(bundle)
    if not hash_result["valid"]:
        issues.append(f"reconstruction_hash: {hash_result['reason']}")

    # Manifest hash verification
    manifest = bundle.get("manifest", {})
    if manifest:
        m_result = verify_manifest_hash(manifest)
        if not m_result["valid"]:
            issues.append(f"manifest_hash: {m_result['reason']}")
    else:
        issues.append("manifest missing")

    # Metadata field check
    meta = bundle.get("metadata", {})
    for field in EXPORT_METADATA_REQUIRED_FIELDS:
        if field not in meta:
            issues.append(f"metadata.{field} missing")

    # Constitutional invariant
    if bundle.get("auto_authorized") is True:
        issues.append("auto_authorized must be False — constitutional violation")

    return {
        "bundle_type":   bundle.get("bundle_type", "UNKNOWN"),
        "valid":         len(issues) == 0,
        "issues":        issues,
        "issue_count":   len(issues),
        "hash_check":    hash_result,
    }


# ── Manifest integrity ────────────────────────────────────────────────────────

def verify_manifest_integrity(manifest: dict) -> dict:
    """
    Verify manifest structural integrity and hash correctness.
    """
    issues: List[str] = []

    required = (
        "manifest_id", "manifest_hash", "bundle_type", "generation_ts",
        "report_ids", "export_order", "lineage_graph", "dependency_map",
    )
    for f in required:
        if f not in manifest:
            issues.append(f"manifest.{f} missing")

    if "manifest_hash" in manifest:
        h_result = verify_manifest_hash(manifest)
        if not h_result["valid"]:
            issues.append(f"manifest_hash: {h_result['reason']}")

    if manifest.get("auto_authorized") is True:
        issues.append("auto_authorized must be False")

    return {
        "manifest_id":  manifest.get("manifest_id", "UNKNOWN"),
        "valid":        len(issues) == 0,
        "issues":       issues,
        "issue_count":  len(issues),
    }


# ── Corruption detection ──────────────────────────────────────────────────────

def detect_corruption(bundle: dict) -> List[str]:
    """
    Returns a list of corruption signals in the bundle.
    Empty list = no corruption detected.
    """
    signals: List[str] = []
    meta = bundle.get("metadata", {})

    stored_hash = meta.get("reconstruction_hash", "")
    if stored_hash and not is_valid_sha256(stored_hash):
        signals.append(f"malformed reconstruction_hash: '{stored_hash[:16]}...'")

    manifest = bundle.get("manifest", {})
    m_hash = manifest.get("manifest_hash", "")
    if m_hash and not is_valid_sha256(m_hash):
        signals.append(f"malformed manifest_hash: '{m_hash[:16]}...'")

    stored_m_hash = meta.get("manifest_hash", "")
    if stored_m_hash and m_hash and stored_m_hash != m_hash:
        signals.append("metadata.manifest_hash ≠ manifest.manifest_hash")

    if bundle.get("auto_authorized") is True:
        signals.append("constitutional violation: auto_authorized=True")

    return signals


# ── Health assessment ─────────────────────────────────────────────────────────

def assess_bundle_health(bundle: dict) -> dict:
    """
    Comprehensive health assessment of a single composed bundle.
    """
    integrity  = verify_bundle_integrity(bundle)
    corruption = detect_corruption(bundle)
    report_ids = bundle.get("report_ids", [])
    exp_order  = bundle.get("export_order", [])

    return {
        "bundle_type":        bundle.get("bundle_type", "UNKNOWN"),
        "integrity_valid":    integrity["valid"],
        "integrity_issues":   integrity["issues"],
        "corruption_signals": corruption,
        "report_count":       len(report_ids),
        "ordering_present":   len(exp_order) > 0,
        "manifest_present":   bool(bundle.get("manifest")),
        "healthy":            integrity["valid"] and len(corruption) == 0,
    }


def assess_archive_health(bundles: List[dict]) -> dict:
    """
    Overall archive health for a list of bundles.
    """
    if not bundles:
        return {
            "total_bundles":    0,
            "healthy_bundles":  0,
            "failed_bundles":   [],
            "archive_healthy":  True,
            "corruption_detected": False,
        }

    results   = [assess_bundle_health(b) for b in bundles]
    healthy   = [r["bundle_type"] for r in results if r["healthy"]]
    failed    = [r["bundle_type"] for r in results if not r["healthy"]]
    corrupted = [r["bundle_type"] for r in results if r["corruption_signals"]]

    return {
        "total_bundles":       len(bundles),
        "healthy_bundles":     len(healthy),
        "failed_bundles":      failed,
        "corrupted_bundles":   corrupted,
        "archive_healthy":     len(failed) == 0,
        "corruption_detected": len(corrupted) > 0,
    }
