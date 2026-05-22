"""
FTD-UEI: Export Bundle Composer.

Composes institutional export bundle descriptors from the canonical
report registry — dependency-aware, lineage-preserving, and
reconstruction-safe.

A composed bundle is a data descriptor (not a file). It contains:
  - the ordered list of reports to export
  - per-report registry metadata
  - a canonical manifest
  - reconstruction and manifest hashes
  - export metadata complying with the UEI standard

The actual live report data (from LIO endpoints) is injected separately
at the HTTP layer. The composer governs structure, ordering, and integrity.

Pure module — no I/O, no live engine imports, fail-open. Import-safe.
"""
from __future__ import annotations

import time as _time
from typing import Dict, List, Optional

from core.report_registry import REPORT_REGISTRY
from core.report_taxonomy import BUNDLE_MEMBERSHIP, get_reports_in_bundle
from core.report_dependency_graph import topological_sort, get_dependencies
from core.reconstruction_hashing import bundle_hash, dict_hash
from core.export_manifest import generate_manifest

# ── UEI export metadata required fields ──────────────────────────────────────
EXPORT_METADATA_REQUIRED_FIELDS: tuple = (
    "export_id",
    "bundle_type",
    "generation_ts",
    "app_version",
    "doctrine_version",
    "lineage_epoch",
    "reconstruction_hash",
    "manifest_hash",
    "constitutional_flags",
    "dependency_version_map",
)


def _compose_export_metadata(
    export_id: str,
    bundle_type: str,
    generation_ts: int,
    app_version: str,
    doctrine_version: str,
    lineage_epoch: str,
    report_ids: List[str],
    manifest: dict,
    constitutional_flags: dict,
) -> dict:
    """Build the canonical UEI export metadata block."""
    dep_version_map = {
        r_id: REPORT_REGISTRY.get(r_id, {}).get("doctrine_version", "1.0")
        for r_id in report_ids
    }
    r_hash  = bundle_hash(bundle_type, report_ids, generation_ts)
    m_hash  = manifest.get("manifest_hash", "")
    return {
        "export_id":             export_id,
        "bundle_type":           bundle_type,
        "generation_ts":         generation_ts,
        "app_version":           app_version,
        "doctrine_version":      doctrine_version,
        "lineage_epoch":         lineage_epoch,
        "reconstruction_hash":   r_hash,
        "manifest_hash":         m_hash,
        "constitutional_flags":  constitutional_flags,
        "dependency_version_map": dep_version_map,
    }


def compose_bundle(
    bundle_type: str,
    app_version: str = "1.0",
    doctrine_version: str = "1.0",
    trade_count: int = 0,
    lineage_epoch: str = "CURRENT",
    constitutional_flags: Optional[dict] = None,
    generation_ts: Optional[int] = None,
) -> dict:
    """
    Compose an institutional export bundle descriptor.

    Returns a fully-formed bundle dict with manifest, metadata, and
    reconstruction hashes. Never raises — returns an error bundle on failure.
    auto_authorized=False always.
    """
    try:
        if bundle_type not in BUNDLE_MEMBERSHIP:
            return {
                "export_id":   f"EXP-UNKNOWN-error",
                "bundle_type": bundle_type,
                "error":       f"unknown bundle_type: {bundle_type}",
                "auto_authorized": False,
            }

        ts          = generation_ts or int(_time.time() * 1000)
        report_ids  = get_reports_in_bundle(bundle_type)  # sorted
        flags       = constitutional_flags or {}

        # Generate manifest first (needed for manifest_hash)
        proto_meta  = {
            "app_version":       app_version,
            "doctrine_version":  doctrine_version,
            "lineage_epoch":     lineage_epoch,
            "export_bundle_type": bundle_type,
        }
        manifest    = generate_manifest(bundle_type, report_ids, proto_meta, ts)

        # Full export metadata
        r_hash  = bundle_hash(bundle_type, report_ids, ts)
        fp_short = r_hash[:14]
        export_id = f"EXP-{bundle_type}-{ts}-{fp_short}"

        metadata = _compose_export_metadata(
            export_id=export_id,
            bundle_type=bundle_type,
            generation_ts=ts,
            app_version=app_version,
            doctrine_version=doctrine_version,
            lineage_epoch=lineage_epoch,
            report_ids=report_ids,
            manifest=manifest,
            constitutional_flags=flags,
        )

        # Topological export order filtered to this bundle
        topo      = topological_sort()
        id_set    = set(report_ids)
        exp_order = [r for r in topo if r in id_set]

        # Per-report descriptors (from registry)
        report_descriptors = {
            r_id: REPORT_REGISTRY[r_id]
            for r_id in report_ids
            if r_id in REPORT_REGISTRY
        }

        return {
            "export_id":           export_id,
            "bundle_type":         bundle_type,
            "generation_ts":       ts,
            "report_count":        len(report_ids),
            "report_ids":          report_ids,
            "export_order":        exp_order,
            "report_descriptors":  report_descriptors,
            "metadata":            metadata,
            "manifest":            manifest,
            "trade_count":         trade_count,
            "auto_authorized":     False,
            "immutable":           True,
        }
    except Exception as exc:
        ts = int(_time.time() * 1000)
        return {
            "export_id":   f"EXP-{bundle_type}-{ts}-error",
            "bundle_type": bundle_type,
            "error":       f"composition failed: {exc}",
            "auto_authorized": False,
        }


def compose_all_bundles(
    app_version: str = "1.0",
    doctrine_version: str = "1.0",
    trade_count: int = 0,
) -> Dict[str, dict]:
    """Compose descriptors for all canonical bundles."""
    return {
        bundle_type: compose_bundle(
            bundle_type, app_version, doctrine_version, trade_count
        )
        for bundle_type in sorted(BUNDLE_MEMBERSHIP.keys())
    }


def get_composer_health(
    app_version: str = "1.0",
    doctrine_version: str = "1.0",
) -> dict:
    """
    Self-test: compose all bundles and report health.
    Returns a health dict — never raises.
    """
    try:
        all_bundles = compose_all_bundles(app_version, doctrine_version)
        failed      = [b for b, bd in all_bundles.items() if "error" in bd]
        succeeded   = [b for b in all_bundles if b not in failed]
        return {
            "all_bundles_composable": len(failed) == 0,
            "bundle_count":           len(all_bundles),
            "succeeded_bundles":      succeeded,
            "failed_bundles":         failed,
            "composer_healthy":       len(failed) == 0,
        }
    except Exception:
        return {
            "all_bundles_composable": False,
            "bundle_count":           0,
            "succeeded_bundles":      [],
            "failed_bundles":         ["ALL"],
            "composer_healthy":       False,
        }
