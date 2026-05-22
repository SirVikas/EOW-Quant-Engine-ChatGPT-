"""
FTD-UDCA: Institutional Archive Browser.

Chronological snapshot browsing, filtering, manifest preview,
and archive timeline navigation for PHOENIX institutional memory.

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.snapshot_manager import SNAPSHOT_TYPE_DESCRIPTIONS
from core.report_registry import REPORT_REGISTRY
from core.reconstruction_hashing import is_valid_sha256


def browse_snapshots(
    snapshots: List[dict],
    filters:   Optional[Dict[str, Any]] = None,
    page:      int = 1,
    page_size: int = 20,
) -> dict:
    """
    Browse snapshots chronologically with optional filters and pagination.

    Filter keys: snapshot_type, app_version, from_ts, to_ts, triggered_by.
    """
    try:
        filtered = list(snapshots)
        f = filters or {}

        if f.get("snapshot_type"):
            t = f["snapshot_type"].upper()
            filtered = [s for s in filtered if s.get("snapshot_type", "").upper() == t]
        if f.get("app_version"):
            filtered = [s for s in filtered if s.get("app_version") == f["app_version"]]
        if f.get("from_ts"):
            filtered = [s for s in filtered if s.get("timestamp_ms", 0) >= f["from_ts"]]
        if f.get("to_ts"):
            filtered = [s for s in filtered if s.get("timestamp_ms", 0) <= f["to_ts"]]
        if f.get("triggered_by"):
            tb = f["triggered_by"].upper()
            filtered = [s for s in filtered if s.get("triggered_by", "").upper() == tb]

        filtered.sort(key=lambda s: s.get("timestamp_ms", 0))

        total      = len(filtered)
        offset     = (page - 1) * page_size
        page_items = filtered[offset: offset + page_size]

        return {
            "total_snapshots": total,
            "page":            page,
            "page_size":       page_size,
            "total_pages":     max(1, (total + page_size - 1) // page_size),
            "filters_applied": {k: v for k, v in f.items() if v is not None},
            "snapshots":       page_items,
            "has_next":        offset + page_size < total,
            "has_prev":        page > 1,
            "browse_healthy":  True,
        }
    except Exception as exc:
        return {"browse_healthy": False, "error": str(exc), "snapshots": []}


def get_archive_timeline(snapshots: List[dict]) -> dict:
    """
    Build a chronological archive timeline from snapshot records.
    Each entry includes type, timestamp, version, and integrity indicator.
    """
    try:
        sorted_snaps = sorted(snapshots, key=lambda s: s.get("timestamp_ms", 0))
        timeline = []

        for i, snap in enumerate(sorted_snaps):
            fp = snap.get("reconstruction_hash", "")
            timeline.append({
                "index":             i + 1,
                "snapshot_id":       snap.get("snapshot_id", ""),
                "snapshot_type":     snap.get("snapshot_type", "UNKNOWN"),
                "type_description":  SNAPSHOT_TYPE_DESCRIPTIONS.get(
                    snap.get("snapshot_type", ""), ""
                ),
                "timestamp_ms":      snap.get("timestamp_ms", 0),
                "app_version":       snap.get("app_version", ""),
                "trade_count":       snap.get("trade_count", 0),
                "label":             snap.get("label", ""),
                "triggered_by":      snap.get("triggered_by", ""),
                "reconstruction_hash_prefix": fp[:16] if fp else "",
                "hash_valid":        is_valid_sha256(fp) if fp else False,
                "lineage_preserved": snap.get("lineage_preserved", True),
                "immutable":         snap.get("immutable", False),
            })

        versions  = sorted({e["app_version"] for e in timeline if e["app_version"]})
        types_seen = sorted({e["snapshot_type"] for e in timeline})

        return {
            "timeline_length":   len(timeline),
            "timeline":          timeline,
            "versions_covered":  versions,
            "types_seen":        types_seen,
            "earliest_timestamp": timeline[0]["timestamp_ms"] if timeline else None,
            "latest_timestamp":   timeline[-1]["timestamp_ms"] if timeline else None,
            "timeline_healthy":  True,
        }
    except Exception as exc:
        return {"timeline_healthy": False, "error": str(exc), "timeline": []}


def get_snapshot_manifest_preview(snapshot: dict) -> dict:
    """Human-readable manifest preview for a single snapshot."""
    try:
        fp = snapshot.get("reconstruction_hash", "")
        return {
            "snapshot_id":           snapshot.get("snapshot_id", "UNKNOWN"),
            "snapshot_type":         snapshot.get("snapshot_type", ""),
            "type_description":      SNAPSHOT_TYPE_DESCRIPTIONS.get(
                snapshot.get("snapshot_type", ""), ""
            ),
            "timestamp_ms":          snapshot.get("timestamp_ms", 0),
            "app_version":           snapshot.get("app_version", ""),
            "trade_count":           snapshot.get("trade_count", 0),
            "label":                 snapshot.get("label", ""),
            "triggered_by":          snapshot.get("triggered_by", ""),
            "total_registered_reports": snapshot.get(
                "total_registered_reports", len(REPORT_REGISTRY)
            ),
            "reconstruction_hash":   fp,
            "hash_valid":            is_valid_sha256(fp) if fp else False,
            "lineage_preserved":     snapshot.get("lineage_preserved", True),
            "auto_authorized":       snapshot.get("auto_authorized", False),
            "immutable":             snapshot.get("immutable", False),
            "preview_healthy":       True,
        }
    except Exception as exc:
        return {"preview_healthy": False, "error": str(exc)}


def get_browser_health(snapshots: List[dict]) -> dict:
    """Archive browser health summary."""
    try:
        timeline = get_archive_timeline(snapshots)
        return {
            "browser_operational": True,
            "total_snapshots":     len(snapshots),
            "timeline_length":     timeline.get("timeline_length", 0),
            "versions_covered":    timeline.get("versions_covered", []),
            "types_seen":          timeline.get("types_seen", []),
            "browser_healthy":     True,
        }
    except Exception as exc:
        return {
            "browser_operational": False,
            "error":               str(exc),
            "browser_healthy":     False,
        }
