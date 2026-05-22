"""
FTD-UDCA: Institutional Archive Search Infrastructure.

Provides searchable access to the PHOENIX report registry, bundle taxonomy,
and snapshot ledger. Searchable by report family, tier, priority, bundle type,
doctrine version, dependency presence, and free-text query.

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.report_registry import REPORT_REGISTRY
from core.report_taxonomy import BUNDLE_MEMBERSHIP, get_reports_in_bundle
from core.snapshot_manager import SNAPSHOT_TYPES


def build_search_index() -> Dict[str, Any]:
    """Build a full searchable index of the report registry and bundle taxonomy."""
    by_family:   Dict[str, List[str]] = {}
    by_tier:     Dict[str, List[str]] = {}
    by_priority: Dict[str, List[str]] = {}

    for r_id, meta in REPORT_REGISTRY.items():
        family = meta.get("report_family", "UNKNOWN")
        tier   = meta.get("export_tier",   "UNKNOWN")
        prio   = meta.get("archive_priority", "STANDARD")
        by_family.setdefault(family, []).append(r_id)
        by_tier.setdefault(tier,     []).append(r_id)
        by_priority.setdefault(prio, []).append(r_id)

    bundle_index = {
        bt: get_reports_in_bundle(bt)
        for bt in BUNDLE_MEMBERSHIP
    }

    return {
        "total_reports":     len(REPORT_REGISTRY),
        "by_family":         by_family,
        "by_tier":           by_tier,
        "by_priority":       by_priority,
        "bundle_index":      bundle_index,
        "all_report_ids":    sorted(REPORT_REGISTRY.keys()),
        "all_families":      sorted(by_family.keys()),
        "all_tiers":         sorted(by_tier.keys()),
        "all_priorities":    sorted(by_priority.keys()),
        "all_bundle_types":  sorted(BUNDLE_MEMBERSHIP.keys()),
        "all_snapshot_types": sorted(SNAPSHOT_TYPES),
    }


def search_reports(
    query:            Optional[str]  = None,
    family:           Optional[str]  = None,
    tier:             Optional[str]  = None,
    priority:         Optional[str]  = None,
    bundle_type:      Optional[str]  = None,
    doctrine_version: Optional[str]  = None,
    has_dependencies: Optional[bool] = None,
) -> dict:
    """
    Search the report registry with optional filters.
    All parameters optional — no filters returns every report.
    """
    try:
        candidates = list(REPORT_REGISTRY.keys())

        if bundle_type and bundle_type in BUNDLE_MEMBERSHIP:
            bundle_ids = set(get_reports_in_bundle(bundle_type))
            candidates = [r for r in candidates if r in bundle_ids]

        results = []
        for r_id in candidates:
            meta = REPORT_REGISTRY[r_id]

            if family and meta.get("report_family", "").upper() != family.upper():
                continue
            if tier and meta.get("export_tier", "").upper() != tier.upper():
                continue
            if priority and meta.get("archive_priority", "").upper() != priority.upper():
                continue
            if doctrine_version and str(meta.get("doctrine_version", "")) != str(doctrine_version):
                continue
            if has_dependencies is True and not meta.get("dependencies"):
                continue
            if has_dependencies is False and meta.get("dependencies"):
                continue

            if query:
                q = query.lower()
                searchable = " ".join([
                    r_id,
                    meta.get("name", ""),
                    meta.get("description", ""),
                    meta.get("report_family", ""),
                    meta.get("constitutional_scope", ""),
                ]).lower()
                if q not in searchable:
                    continue

            results.append({
                "report_id":        r_id,
                "name":             meta.get("name", r_id),
                "report_family":    meta.get("report_family", ""),
                "export_tier":      meta.get("export_tier", ""),
                "archive_priority": meta.get("archive_priority", "STANDARD"),
                "doctrine_version": meta.get("doctrine_version", "1.0"),
                "dependencies":     meta.get("dependencies", []),
                "endpoint":         meta.get("endpoint", ""),
                "description":      meta.get("description", ""),
            })

        return {
            "query":           query,
            "filters_applied": {k: v for k, v in {
                "family": family, "tier": tier, "priority": priority,
                "bundle_type": bundle_type, "doctrine_version": doctrine_version,
                "has_dependencies": has_dependencies,
            }.items() if v is not None},
            "result_count":   len(results),
            "results":        results,
            "search_healthy": True,
        }
    except Exception as exc:
        return {"search_healthy": False, "error": str(exc), "results": []}


def search_snapshots(
    snapshots:     List[dict],
    query:         Optional[str] = None,
    snapshot_type: Optional[str] = None,
    app_version:   Optional[str] = None,
    from_ts:       Optional[int] = None,
    to_ts:         Optional[int] = None,
    triggered_by:  Optional[str] = None,
) -> dict:
    """
    Search/filter a snapshot ledger. Returns matching snapshots in
    chronological order.
    """
    try:
        results = []
        for snap in snapshots:
            if snapshot_type and snap.get("snapshot_type", "").upper() != snapshot_type.upper():
                continue
            if app_version and snap.get("app_version", "") != app_version:
                continue
            if from_ts and snap.get("timestamp_ms", 0) < from_ts:
                continue
            if to_ts and snap.get("timestamp_ms", 0) > to_ts:
                continue
            if triggered_by and snap.get("triggered_by", "").upper() != triggered_by.upper():
                continue
            if query:
                q = query.lower()
                searchable = " ".join([
                    snap.get("snapshot_id", ""),
                    snap.get("snapshot_type", ""),
                    snap.get("label", ""),
                    snap.get("app_version", ""),
                    snap.get("triggered_by", ""),
                ]).lower()
                if q not in searchable:
                    continue
            results.append(snap)

        return {
            "query":           query,
            "filters_applied": {k: v for k, v in {
                "snapshot_type": snapshot_type, "app_version": app_version,
                "from_ts": from_ts, "to_ts": to_ts, "triggered_by": triggered_by,
            }.items() if v is not None},
            "total_searched":  len(snapshots),
            "result_count":    len(results),
            "results":         results,
            "search_healthy":  True,
        }
    except Exception as exc:
        return {"search_healthy": False, "error": str(exc), "results": []}


def search_bundles(
    query:             Optional[str] = None,
    min_report_count:  Optional[int] = None,
    contains_report:   Optional[str] = None,
) -> dict:
    """Search bundle taxonomy by name, size, or report membership."""
    try:
        results = []
        for bt in sorted(BUNDLE_MEMBERSHIP.keys()):
            ids = get_reports_in_bundle(bt)

            if min_report_count is not None and len(ids) < min_report_count:
                continue
            if contains_report and contains_report not in ids:
                continue
            if query and query.lower() not in bt.lower():
                continue

            results.append({
                "bundle_type":  bt,
                "report_count": len(ids),
                "report_ids":   ids,
            })

        return {
            "query":          query,
            "result_count":   len(results),
            "results":        results,
            "search_healthy": True,
        }
    except Exception as exc:
        return {"search_healthy": False, "error": str(exc), "results": []}


def get_search_health() -> dict:
    """Overall institutional search infrastructure health."""
    try:
        index = build_search_index()
        return {
            "search_operational":   True,
            "indexed_reports":      index["total_reports"],
            "indexed_bundles":      len(index["all_bundle_types"]),
            "indexed_families":     len(index["all_families"]),
            "search_index_healthy": index["total_reports"] > 0,
            "search_healthy":       True,
        }
    except Exception as exc:
        return {"search_operational": False, "error": str(exc), "search_healthy": False}
