"""
FTD-IREL: Timeline Visualization Layer.

Generates structured replay visualizations for evolution timelines,
doctrine emergence, version transitions, governance drift, and regime transitions.
All outputs are machine-readable for frontend UI evolution.

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

from typing import List, Optional

from core.snapshot_manager import SNAPSHOT_TYPE_DESCRIPTIONS
from core.reconstruction_hashing import is_valid_sha256

# Snapshot types that carry governance significance
_GOVERNANCE_TYPES = frozenset({"GOVERNANCE_TRANSITION", "EPISTEMIC_SHIFT"})
# Snapshot types that count as milestones
_MILESTONE_TYPES  = frozenset({"MILESTONE", "VERSION_TRANSITION", "CATASTROPHIC_EVENT"})
# Version transition type
_VERSION_TYPE     = "VERSION_TRANSITION"


def build_evolution_timeline(snapshots: list) -> dict:
    """
    Annotated timeline with version transitions, governance events, and milestones.

    Each event carries enough metadata for a frontend timeline UI to render
    colour-coded dots, version epoch separators, and governance markers without
    additional data fetches.
    """
    try:
        sorted_snaps = sorted(snapshots or [], key=lambda s: s.get("timestamp_ms", 0))
        events: list = []
        version_transitions: list = []
        governance_events: list   = []
        milestone_events: list    = []

        prev_version = None

        for i, snap in enumerate(sorted_snaps):
            s_type   = snap.get("snapshot_type", "UNKNOWN")
            version  = snap.get("app_version", "")
            ts       = snap.get("timestamp_ms", 0)
            snap_id  = snap.get("snapshot_id", f"SNP-{i}")
            fp       = snap.get("reconstruction_hash", "")

            is_ver_trans  = (s_type == _VERSION_TYPE) or (
                version and prev_version and version != prev_version
            )
            is_gov_event  = s_type in _GOVERNANCE_TYPES
            is_milestone  = s_type in _MILESTONE_TYPES
            is_critical   = s_type == "CATASTROPHIC_EVENT"

            event = {
                "index":                i + 1,
                "snapshot_id":          snap_id,
                "snapshot_type":        s_type,
                "type_description":     SNAPSHOT_TYPE_DESCRIPTIONS.get(s_type, ""),
                "timestamp_ms":         ts,
                "app_version":          version,
                "trade_count":          snap.get("trade_count", 0),
                "is_version_transition": bool(is_ver_trans),
                "is_governance_event":  bool(is_gov_event),
                "is_milestone":         bool(is_milestone),
                "is_critical":          bool(is_critical),
                "hash_prefix":          fp[:16] if is_valid_sha256(fp) else fp[:16] if fp else "",
            }
            events.append(event)

            if is_ver_trans and prev_version != version:
                version_transitions.append({
                    "from_version":  prev_version or "INITIAL",
                    "to_version":    version,
                    "at_snapshot_id": snap_id,
                    "timestamp_ms":  ts,
                    "index":         i + 1,
                })

            if is_gov_event:
                governance_events.append({
                    "snapshot_id":  snap_id,
                    "event_type":   s_type,
                    "timestamp_ms": ts,
                    "app_version":  version,
                    "index":        i + 1,
                })

            if is_milestone:
                milestone_events.append({
                    "snapshot_id":  snap_id,
                    "event_type":   s_type,
                    "timestamp_ms": ts,
                    "app_version":  version,
                    "is_critical":  bool(is_critical),
                    "index":        i + 1,
                })

            prev_version = version

        return {
            "events":             events,
            "event_count":        len(events),
            "version_transitions": version_transitions,
            "governance_events":  governance_events,
            "milestone_events":   milestone_events,
            "timeline_healthy":   True,
        }
    except Exception as exc:
        return {
            "events":             [],
            "version_transitions": [],
            "governance_events":  [],
            "milestone_events":   [],
            "timeline_healthy":   False,
            "error":              str(exc),
        }


def build_snapshot_lineage_graph(snapshots: list) -> dict:
    """
    Node-edge graph of the snapshot lineage — richer metadata than
    archive_visualization.build_lineage_tree.

    Nodes are snapshots; edges connect temporally adjacent snapshots with
    same or transitioning version epochs.  Version epochs are extracted so
    the UI can collapse groups.
    """
    try:
        sorted_snaps = sorted(snapshots or [], key=lambda s: s.get("timestamp_ms", 0))
        nodes: list = []
        edges: list = []
        version_epochs: dict = {}  # version → list of snapshot_ids

        for i, snap in enumerate(sorted_snaps):
            snap_id = snap.get("snapshot_id", f"SNP-{i}")
            s_type  = snap.get("snapshot_type", "UNKNOWN")
            version = snap.get("app_version", "")
            fp      = snap.get("reconstruction_hash", "")

            nodes.append({
                "id":               snap_id,
                "index":            i + 1,
                "snapshot_type":    s_type,
                "app_version":      version,
                "timestamp_ms":     snap.get("timestamp_ms", 0),
                "trade_count":      snap.get("trade_count", 0),
                "label":            snap.get("label", s_type),
                "hash_valid":       is_valid_sha256(fp) if fp else False,
                "hash_prefix":      fp[:12] if fp else "",
                "is_root":          i == 0,
                "is_leaf":          i == len(sorted_snaps) - 1,
                "is_version_epoch": s_type == _VERSION_TYPE,
            })

            if i > 0:
                prev_id = sorted_snaps[i - 1].get("snapshot_id", f"SNP-{i-1}")
                prev_version = sorted_snaps[i - 1].get("app_version", "")
                edges.append({
                    "source":           prev_id,
                    "target":           snap_id,
                    "edge_type":        "VERSION_TRANSITION" if version != prev_version else "LINEAGE",
                    "timestamp_delta":  snap.get("timestamp_ms", 0) - sorted_snaps[i - 1].get("timestamp_ms", 0),
                })

            if version:
                version_epochs.setdefault(version, []).append(snap_id)

        root_node = nodes[0]["id"] if nodes else ""
        leaf_node = nodes[-1]["id"] if nodes else ""

        return {
            "nodes":              nodes,
            "edges":              edges,
            "node_count":         len(nodes),
            "edge_count":         len(edges),
            "root_node":          root_node,
            "leaf_node":          leaf_node,
            "version_epochs":     version_epochs,
            "visualization_type": "SNAPSHOT_LINEAGE_GRAPH",
            "graph_healthy":      True,
        }
    except Exception as exc:
        return {
            "nodes":              [],
            "edges":              [],
            "root_node":          "",
            "leaf_node":          "",
            "version_epochs":     {},
            "visualization_type": "SNAPSHOT_LINEAGE_GRAPH",
            "graph_healthy":      False,
            "error":              str(exc),
        }


def build_regime_transition_map(snapshots: list) -> dict:
    """
    Extract version and type transition events — a regime-level view
    of how the engine has moved between operational states over time.
    """
    try:
        sorted_snaps = sorted(snapshots or [], key=lambda s: s.get("timestamp_ms", 0))
        transitions: list = []
        unique_versions: list = []
        unique_types: list    = []
        seen_versions: set    = set()
        seen_types: set       = set()

        prev = None
        for i, snap in enumerate(sorted_snaps):
            s_type  = snap.get("snapshot_type", "UNKNOWN")
            version = snap.get("app_version", "")
            ts      = snap.get("timestamp_ms", 0)
            snap_id = snap.get("snapshot_id", f"SNP-{i}")

            if version not in seen_versions:
                seen_versions.add(version)
                unique_versions.append(version)
            if s_type not in seen_types:
                seen_types.add(s_type)
                unique_types.append(s_type)

            if prev is not None:
                prev_version = prev.get("app_version", "")
                prev_type    = prev.get("snapshot_type", "UNKNOWN")
                if version != prev_version or s_type != prev_type:
                    transitions.append({
                        "from_version":    prev_version,
                        "to_version":      version,
                        "from_type":       prev_type,
                        "to_type":         s_type,
                        "at_snapshot_id":  snap_id,
                        "timestamp_ms":    ts,
                        "index":           i + 1,
                    })
            prev = snap

        return {
            "transitions":        transitions,
            "total_transitions":  len(transitions),
            "unique_versions":    unique_versions,
            "unique_types":       unique_types,
            "visualization_type": "REGIME_TRANSITION_MAP",
            "map_healthy":        True,
        }
    except Exception as exc:
        return {
            "transitions":        [],
            "total_transitions":  0,
            "unique_versions":    [],
            "unique_types":       [],
            "visualization_type": "REGIME_TRANSITION_MAP",
            "map_healthy":        False,
            "error":              str(exc),
        }


def build_governance_drift_flow(snapshots: list) -> dict:
    """
    Focus specifically on governance transition events.

    Drift is detected when multiple GOVERNANCE_TRANSITION or EPISTEMIC_SHIFT
    events cluster within a short time window, indicating the constitutional
    state is not settling.  The threshold is three or more governance events
    across the entire timeline — a heuristic, not a hard gate.
    """
    try:
        sorted_snaps  = sorted(snapshots or [], key=lambda s: s.get("timestamp_ms", 0))
        flow_nodes: list = []
        flow_edges: list = []
        governance_events = 0
        drift_signals: list = []

        prev_gov_node = None

        for i, snap in enumerate(sorted_snaps):
            s_type  = snap.get("snapshot_type", "UNKNOWN")
            snap_id = snap.get("snapshot_id", f"SNP-{i}")
            ts      = snap.get("timestamp_ms", 0)
            version = snap.get("app_version", "")

            if s_type in _GOVERNANCE_TYPES:
                governance_events += 1
                node = {
                    "id":            snap_id,
                    "index":         i + 1,
                    "event_type":    s_type,
                    "app_version":   version,
                    "timestamp_ms":  ts,
                    "governance_seq": governance_events,
                }
                flow_nodes.append(node)

                if prev_gov_node is not None:
                    delta_ms = ts - prev_gov_node["timestamp_ms"]
                    flow_edges.append({
                        "source":       prev_gov_node["id"],
                        "target":       snap_id,
                        "delta_ms":     delta_ms,
                        "edge_type":    "GOVERNANCE_SEQUENCE",
                    })
                    # Rapid succession (<60 s between governance events) is a drift signal
                    if delta_ms < 60_000:
                        drift_signals.append({
                            "signal_type": "RAPID_GOVERNANCE_SUCCESSION",
                            "from_id":     prev_gov_node["id"],
                            "to_id":       snap_id,
                            "delta_ms":    delta_ms,
                        })

                prev_gov_node = node

        # Three or more governance events total is also flagged as potential drift
        if governance_events >= 3:
            drift_signals.append({
                "signal_type":       "HIGH_GOVERNANCE_EVENT_DENSITY",
                "governance_events": governance_events,
                "total_snapshots":   len(sorted_snaps),
            })

        drift_detected = len(drift_signals) > 0

        return {
            "flow_nodes":         flow_nodes,
            "flow_edges":         flow_edges,
            "governance_events":  governance_events,
            "drift_detected":     drift_detected,
            "drift_signals":      drift_signals,
            "visualization_type": "GOVERNANCE_DRIFT_FLOW",
            "flow_healthy":       True,
        }
    except Exception as exc:
        return {
            "flow_nodes":         [],
            "flow_edges":         [],
            "governance_events":  0,
            "drift_detected":     False,
            "drift_signals":      [],
            "visualization_type": "GOVERNANCE_DRIFT_FLOW",
            "flow_healthy":       False,
            "error":              str(exc),
        }


def get_timeline_health(snapshots: Optional[list] = None) -> dict:
    """
    Spot-check all four visualization builders.
    Returns health summary without raising.
    """
    try:
        snap_list = list(snapshots or [])
        evo   = build_evolution_timeline(snap_list)
        lin   = build_snapshot_lineage_graph(snap_list)
        reg   = build_regime_transition_map(snap_list)
        gov   = build_governance_drift_flow(snap_list)

        timeline_healthy = all([
            evo.get("timeline_healthy", False),
            lin.get("graph_healthy", False),
            reg.get("map_healthy", False),
            gov.get("flow_healthy", False),
        ])

        return {
            "timeline_operational":  True,
            "snapshot_count":        len(snap_list),
            "visualization_count":   4,
            "evolution_timeline_ok": evo.get("timeline_healthy", False),
            "lineage_graph_ok":      lin.get("graph_healthy", False),
            "regime_map_ok":         reg.get("map_healthy", False),
            "governance_flow_ok":    gov.get("flow_healthy", False),
            "timeline_healthy":      timeline_healthy,
        }
    except Exception as exc:
        return {
            "timeline_operational": False,
            "snapshot_count":       0,
            "visualization_count":  4,
            "timeline_healthy":     False,
            "error":                str(exc),
        }
