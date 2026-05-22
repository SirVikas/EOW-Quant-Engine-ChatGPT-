"""
FTD-UDCA: Export Preview Infrastructure.

Preview-before-download: shows manifests, included reports, dependency chains,
reconstruction hashes, and archive size estimates before a human commits to
an export operation.

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from core.report_registry import REPORT_REGISTRY
from core.report_taxonomy import BUNDLE_MEMBERSHIP, get_reports_in_bundle
from core.report_dependency_graph import topological_sort, get_dependencies
from core.reconstruction_hashing import is_valid_sha256
from core.export_manifest import generate_manifest

# Estimated average bytes per report in a JSON export (order-of-magnitude)
_BYTES_PER_REPORT = 4_096


def preview_bundle(
    bundle_type:      str,
    app_version:      str = "1.0",
    doctrine_version: str = "1.0",
    lineage_epoch:    str = "CURRENT",
) -> dict:
    """
    Preview what a bundle export would contain — without composing it.
    Includes report list, dependency topology, estimated size, and family breakdown.
    """
    try:
        if bundle_type not in BUNDLE_MEMBERSHIP:
            return {
                "preview_healthy": False,
                "error":           f"Unknown bundle_type: {bundle_type}",
            }

        report_ids = get_reports_in_bundle(bundle_type)
        topo       = topological_sort()
        id_set     = set(report_ids)
        exp_order  = [r for r in topo if r in id_set]

        primitives = [r for r in report_ids if not get_dependencies(r)]
        dependents = [r for r in report_ids if get_dependencies(r)]

        dep_map: Dict[str, List[str]] = {
            r_id: [d for d in get_dependencies(r_id) if d in id_set]
            for r_id in report_ids
        }

        family_breakdown: Dict[str, int] = {}
        for r_id in report_ids:
            fam = REPORT_REGISTRY.get(r_id, {}).get("report_family", "UNKNOWN")
            family_breakdown[fam] = family_breakdown.get(fam, 0) + 1

        n = len(report_ids)
        return {
            "bundle_type":          bundle_type,
            "report_count":         n,
            "report_ids":           report_ids,
            "export_order":         exp_order,
            "primitives":           primitives,
            "dependents":           dependents,
            "dependency_map":       dep_map,
            "family_breakdown":     family_breakdown,
            "estimated_json_bytes": n * _BYTES_PER_REPORT,
            "estimated_json_kb":    round(n * _BYTES_PER_REPORT / 1024, 1),
            "app_version":          app_version,
            "doctrine_version":     doctrine_version,
            "lineage_epoch":        lineage_epoch,
            "auto_authorized":      False,
            "preview_healthy":      True,
        }
    except Exception as exc:
        return {"preview_healthy": False, "error": str(exc)}


def preview_manifest(
    bundle_type: str,
    app_version: str = "1.0",
) -> dict:
    """
    Generate a manifest preview — shows what would be in the manifest
    without committing to a full export.
    """
    try:
        if bundle_type not in BUNDLE_MEMBERSHIP:
            return {"preview_healthy": False, "error": f"Unknown bundle_type: {bundle_type}"}

        report_ids = get_reports_in_bundle(bundle_type)
        meta = {
            "app_version":        app_version,
            "doctrine_version":   "1.0",
            "lineage_epoch":      "CURRENT",
            "export_bundle_type": bundle_type,
        }
        manifest = generate_manifest(bundle_type, report_ids, meta)

        m_hash = manifest.get("manifest_hash", "")
        return {
            "bundle_type":          bundle_type,
            "manifest_id_preview":  manifest.get("manifest_id", ""),
            "manifest_hash_prefix": m_hash[:16] if m_hash else "",
            "manifest_hash_valid":  is_valid_sha256(m_hash),
            "report_count":         manifest.get("report_count", 0),
            "export_order":         manifest.get("export_order", []),
            "bundle_topology":      manifest.get("bundle_topology", {}),
            "auto_authorized":      False,
            "preview_healthy":      True,
        }
    except Exception as exc:
        return {"preview_healthy": False, "error": str(exc)}


def preview_dependency_chain(report_id: str) -> dict:
    """
    Show the full dependency chain for a report.
    Useful for understanding what else must be exported alongside it.
    """
    try:
        if report_id not in REPORT_REGISTRY:
            return {"preview_healthy": False, "error": f"Unknown report_id: {report_id}"}

        direct_deps = get_dependencies(report_id)

        # Transitive closure via BFS
        all_deps: set = set()
        queue = list(direct_deps)
        while queue:
            dep = queue.pop()
            if dep not in all_deps:
                all_deps.add(dep)
                queue.extend(get_dependencies(dep))

        containing_bundles = sorted(
            bt for bt, ids in BUNDLE_MEMBERSHIP.items()
            if report_id in ids
        )

        meta = REPORT_REGISTRY[report_id]
        return {
            "report_id":               report_id,
            "report_name":             meta.get("name", report_id),
            "report_family":           meta.get("report_family", ""),
            "direct_dependencies":     direct_deps,
            "transitive_dependencies": sorted(all_deps),
            "total_dep_count":         len(all_deps),
            "is_primitive":            len(direct_deps) == 0,
            "containing_bundles":      containing_bundles,
            "preview_healthy":         True,
        }
    except Exception as exc:
        return {"preview_healthy": False, "error": str(exc)}


def preview_archive_size(bundle_type: str) -> dict:
    """Estimate the archive size for a bundle before export."""
    try:
        if bundle_type not in BUNDLE_MEMBERSHIP:
            return {"preview_healthy": False, "error": f"Unknown bundle_type: {bundle_type}"}

        n = len(get_reports_in_bundle(bundle_type))
        raw = n * _BYTES_PER_REPORT
        return {
            "bundle_type":          bundle_type,
            "report_count":         n,
            "estimated_json_bytes": raw,
            "estimated_json_kb":    round(raw / 1024, 1),
            "estimated_json_mb":    round(raw / (1024 * 1024), 3),
            "estimated_zip_kb":     round(raw * 0.3 / 1024, 1),
            "preview_healthy":      True,
        }
    except Exception as exc:
        return {"preview_healthy": False, "error": str(exc)}


def preview_continuity_scope(snapshots: List[dict]) -> dict:
    """
    Preview the continuity scope of a snapshot ledger — useful before
    committing to a lineage export or continuity archive.
    """
    try:
        if not snapshots:
            return {
                "snapshot_count":   0,
                "continuity_scope": "EMPTY",
                "preview_healthy":  True,
            }

        sorted_s  = sorted(snapshots, key=lambda s: s.get("timestamp_ms", 0))
        versions  = sorted({s.get("app_version", "") for s in snapshots
                            if s.get("app_version")})
        types_cnt: Dict[str, int] = {}
        for s in snapshots:
            t = s.get("snapshot_type", "UNKNOWN")
            types_cnt[t] = types_cnt.get(t, 0) + 1

        earliest = sorted_s[0].get("timestamp_ms", 0)
        latest   = sorted_s[-1].get("timestamp_ms", 0)
        span_ms  = latest - earliest

        return {
            "snapshot_count":    len(snapshots),
            "versions_covered":  versions,
            "types_breakdown":   types_cnt,
            "earliest_ts":       earliest,
            "latest_ts":         latest,
            "span_ms":           span_ms,
            "span_hours":        round(span_ms / 3_600_000, 2),
            "continuity_scope":  "MULTI_ERA" if len(versions) > 1 else "SINGLE_ERA",
            "has_catastrophic":  types_cnt.get("CATASTROPHIC_EVENT", 0) > 0,
            "has_governance":    types_cnt.get("GOVERNANCE_TRANSITION", 0) > 0,
            "preview_healthy":   True,
        }
    except Exception as exc:
        return {"preview_healthy": False, "error": str(exc)}


def get_preview_health() -> dict:
    """Export preview infrastructure health."""
    try:
        result = preview_bundle("EXECUTIVE")
        return {
            "preview_operational":      True,
            "sample_bundle_preview_ok": result.get("preview_healthy", False),
            "preview_healthy":          True,
        }
    except Exception as exc:
        return {
            "preview_operational": False,
            "error":               str(exc),
            "preview_healthy":     False,
        }
