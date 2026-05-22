"""
FTD-UDCA: Institutional Replay Explorer.

Timeline replay of PHOENIX institutional lineage — compare snapshots,
compare eras, compare governance states, replay catastrophic recovery.

Human-accessible institutional archaeology.

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from core.report_registry import REPORT_REGISTRY
from core.report_dependency_graph import get_dependencies
from core.snapshot_manager import SNAPSHOT_TYPE_DESCRIPTIONS


def replay_lineage(
    report_id: str,
    snapshots: List[dict],
) -> dict:
    """
    Replay the lineage of a specific report across available snapshots.
    Returns a chronological view of how the report's context evolved.
    """
    try:
        meta = REPORT_REGISTRY.get(report_id)
        if not meta:
            return {
                "replay_healthy": False,
                "error":          f"Unknown report_id: {report_id}",
            }

        deps         = get_dependencies(report_id)
        sorted_snaps = sorted(snapshots, key=lambda s: s.get("timestamp_ms", 0))

        replay_events = []
        for snap in sorted_snaps:
            fp = snap.get("reconstruction_hash", "") or ""
            replay_events.append({
                "snapshot_id":               snap.get("snapshot_id", ""),
                "snapshot_type":             snap.get("snapshot_type", ""),
                "type_description":          SNAPSHOT_TYPE_DESCRIPTIONS.get(
                    snap.get("snapshot_type", ""), ""
                ),
                "timestamp_ms":              snap.get("timestamp_ms", 0),
                "app_version":               snap.get("app_version", ""),
                "trade_count":               snap.get("trade_count", 0),
                "reconstruction_hash_prefix": fp[:16],
            })

        return {
            "report_id":          report_id,
            "report_name":        meta.get("name", report_id),
            "report_family":      meta.get("report_family", ""),
            "dependencies":       deps,
            "dependency_count":   len(deps),
            "replay_event_count": len(replay_events),
            "replay_events":      replay_events,
            "replay_healthy":     True,
        }
    except Exception as exc:
        return {"replay_healthy": False, "error": str(exc)}


def compare_snapshots(snap_a: dict, snap_b: dict) -> dict:
    """
    Diff two snapshot records — version drift, trade count delta,
    type change, hash change, lineage continuity.
    """
    try:
        ts_a = snap_a.get("timestamp_ms", 0)
        ts_b = snap_b.get("timestamp_ms", 0)
        older, newer = (snap_a, snap_b) if ts_a <= ts_b else (snap_b, snap_a)

        ver_a  = older.get("app_version", "")
        ver_b  = newer.get("app_version", "")
        tc_a   = older.get("trade_count", 0)
        tc_b   = newer.get("trade_count", 0)
        type_a = older.get("snapshot_type", "")
        type_b = newer.get("snapshot_type", "")
        hash_a = older.get("reconstruction_hash", "") or ""
        hash_b = newer.get("reconstruction_hash", "") or ""

        elapsed_ms = newer.get("timestamp_ms", 0) - older.get("timestamp_ms", 0)

        return {
            "snapshot_a_id":     older.get("snapshot_id", ""),
            "snapshot_b_id":     newer.get("snapshot_id", ""),
            "chronological":     ts_a <= ts_b,
            "elapsed_ms":        elapsed_ms,
            "version_changed":   ver_a != ver_b,
            "version_a":         ver_a,
            "version_b":         ver_b,
            "trade_count_delta": tc_b - tc_a,
            "trade_count_a":     tc_a,
            "trade_count_b":     tc_b,
            "type_changed":      type_a != type_b,
            "type_a":            type_a,
            "type_b":            type_b,
            "hash_changed":      hash_a != hash_b,
            "hash_a_prefix":     hash_a[:16],
            "hash_b_prefix":     hash_b[:16],
            "both_immutable":    bool(older.get("immutable") and newer.get("immutable")),
            "compare_healthy":   True,
        }
    except Exception as exc:
        return {"compare_healthy": False, "error": str(exc)}


def compare_eras(
    era_a:       List[dict],
    era_b:       List[dict],
    era_a_label: str = "ERA_A",
    era_b_label: str = "ERA_B",
) -> dict:
    """
    Compare two collections of snapshots (eras).
    Useful for comparing governance epochs, version eras, or recovery periods.
    """
    try:
        def _era_summary(snaps: list, label: str) -> dict:
            if not snaps:
                return {"label": label, "count": 0, "versions": [],
                        "snapshot_types": {}, "earliest_ts": 0,
                        "latest_ts": 0, "total_trades": 0}
            sorted_s = sorted(snaps, key=lambda s: s.get("timestamp_ms", 0))
            versions = sorted({s.get("app_version", "") for s in snaps
                               if s.get("app_version")})
            types: Dict[str, int] = {}
            for s in snaps:
                t = s.get("snapshot_type", "UNKNOWN")
                types[t] = types.get(t, 0) + 1
            return {
                "label":          label,
                "count":          len(snaps),
                "versions":       versions,
                "snapshot_types": types,
                "earliest_ts":    sorted_s[0].get("timestamp_ms", 0),
                "latest_ts":      sorted_s[-1].get("timestamp_ms", 0),
                "total_trades":   max((s.get("trade_count", 0) for s in snaps), default=0),
            }

        summary_a = _era_summary(era_a, era_a_label)
        summary_b = _era_summary(era_b, era_b_label)

        all_types_a = set(summary_a["snapshot_types"].keys())
        all_types_b = set(summary_b["snapshot_types"].keys())

        return {
            "era_a":           summary_a,
            "era_b":           summary_b,
            "era_a_label":     era_a_label,
            "era_b_label":     era_b_label,
            "version_overlap": sorted(
                set(summary_a["versions"]) & set(summary_b["versions"])
            ),
            "type_overlap":    sorted(all_types_a & all_types_b),
            "types_only_in_a": sorted(all_types_a - all_types_b),
            "types_only_in_b": sorted(all_types_b - all_types_a),
            "count_delta":     summary_b["count"] - summary_a["count"],
            "trade_delta":     summary_b["total_trades"] - summary_a["total_trades"],
            "compare_healthy": True,
        }
    except Exception as exc:
        return {"compare_healthy": False, "error": str(exc)}


def get_replay_timeline(snapshots: List[dict]) -> dict:
    """
    Build an ordered replay timeline from snapshots, annotated with
    type transitions and version transitions for institutional archaeology.
    """
    try:
        sorted_snaps = sorted(snapshots, key=lambda s: s.get("timestamp_ms", 0))
        events: List[dict] = []
        prev_ver  = None
        prev_type = None

        for i, snap in enumerate(sorted_snaps):
            ver   = snap.get("app_version", "")
            stype = snap.get("snapshot_type", "")
            fp    = snap.get("reconstruction_hash", "") or ""

            version_transition = prev_ver is not None and ver != prev_ver
            type_transition    = prev_type is not None and stype != prev_type

            events.append({
                "index":              i + 1,
                "snapshot_id":        snap.get("snapshot_id", ""),
                "snapshot_type":      stype,
                "type_description":   SNAPSHOT_TYPE_DESCRIPTIONS.get(stype, ""),
                "timestamp_ms":       snap.get("timestamp_ms", 0),
                "app_version":        ver,
                "trade_count":        snap.get("trade_count", 0),
                "version_transition": version_transition,
                "type_transition":    type_transition,
                "reconstruction_hash_prefix": fp[:16],
            })
            prev_ver  = ver
            prev_type = stype

        version_transition_events = [e for e in events if e["version_transition"]]

        return {
            "event_count":         len(events),
            "events":              events,
            "version_transitions": len(version_transition_events),
            "transition_events":   version_transition_events,
            "replay_healthy":      True,
        }
    except Exception as exc:
        return {"replay_healthy": False, "error": str(exc), "events": []}


def get_replay_health(snapshots: List[dict]) -> dict:
    """Replay explorer health summary."""
    try:
        timeline = get_replay_timeline(snapshots)
        return {
            "replay_operational":  True,
            "snapshot_count":      len(snapshots),
            "replay_event_count":  timeline.get("event_count", 0),
            "version_transitions": timeline.get("version_transitions", 0),
            "replay_healthy":      True,
        }
    except Exception as exc:
        return {
            "replay_operational": False,
            "error":              str(exc),
            "replay_healthy":     False,
        }
