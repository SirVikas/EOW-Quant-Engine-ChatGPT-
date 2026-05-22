"""
FTD-UDCA: Archive Visualization Layer.

Machine-readable visualization structures for dependency graphs, bundle topology,
snapshot lineage trees, archive continuity flows, and export relationship maps.

Structures are designed for consumption by frontend visualization libraries
(D3.js, Mermaid, Graphviz, etc.) or rendered as text diagrams.

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from core.report_registry import REPORT_REGISTRY
from core.report_taxonomy import BUNDLE_MEMBERSHIP, get_reports_in_bundle
from core.report_dependency_graph import topological_sort, get_dependencies
from core.snapshot_manager import SNAPSHOT_TYPE_DESCRIPTIONS


def build_dependency_graph(report_ids: Optional[List[str]] = None) -> dict:
    """
    Build a dependency graph for a set of reports (or all 25 reports).
    Returns {nodes, edges} suitable for graph visualization.
    Edges point from dependency → dependent (source provides data to target).
    """
    try:
        ids    = report_ids if report_ids is not None else list(REPORT_REGISTRY.keys())
        id_set = set(ids)

        nodes = []
        for r_id in sorted(ids):
            meta = REPORT_REGISTRY.get(r_id, {})
            deps = get_dependencies(r_id)
            nodes.append({
                "id":           r_id,
                "label":        meta.get("name", r_id),
                "family":       meta.get("report_family", ""),
                "tier":         meta.get("export_tier", ""),
                "priority":     meta.get("archive_priority", "STANDARD"),
                "is_primitive": len(deps) == 0,
                "dep_count":    len([d for d in deps if d in id_set]),
            })

        edges = []
        for r_id in sorted(ids):
            for dep in sorted(get_dependencies(r_id)):
                if dep in id_set:
                    edges.append({
                        "source": dep,
                        "target": r_id,
                        "type":   "DEPENDENCY",
                    })

        topo = [r for r in topological_sort() if r in id_set]

        return {
            "node_count":        len(nodes),
            "edge_count":        len(edges),
            "nodes":             nodes,
            "edges":             edges,
            "topological_order": topo,
            "primitives":        [n["id"] for n in nodes if n["is_primitive"]],
            "visualization_type": "DEPENDENCY_GRAPH",
            "graph_healthy":     True,
        }
    except Exception as exc:
        return {"graph_healthy": False, "error": str(exc)}


def build_bundle_topology(bundle_type: str) -> dict:
    """
    Visualize the topology of a specific bundle — primitives, dependents,
    family groupings, and export ordering.
    """
    try:
        if bundle_type not in BUNDLE_MEMBERSHIP:
            return {"graph_healthy": False, "error": f"Unknown bundle_type: {bundle_type}"}

        report_ids = get_reports_in_bundle(bundle_type)
        graph      = build_dependency_graph(report_ids)

        family_groups: Dict[str, List[str]] = {}
        for r_id in report_ids:
            fam = REPORT_REGISTRY.get(r_id, {}).get("report_family", "UNKNOWN")
            family_groups.setdefault(fam, []).append(r_id)

        return {
            "bundle_type":        bundle_type,
            "report_count":       len(report_ids),
            "nodes":              graph.get("nodes", []),
            "edges":              graph.get("edges", []),
            "topological_order":  graph.get("topological_order", []),
            "primitives":         graph.get("primitives", []),
            "family_groups":      family_groups,
            "visualization_type": "BUNDLE_TOPOLOGY",
            "graph_healthy":      True,
        }
    except Exception as exc:
        return {"graph_healthy": False, "error": str(exc)}


def build_lineage_tree(snapshots: List[dict]) -> dict:
    """
    Build a lineage tree from snapshot records.
    Nodes are snapshots; edges represent temporal succession.
    """
    try:
        sorted_snaps = sorted(snapshots, key=lambda s: s.get("timestamp_ms", 0))
        nodes: List[dict] = []
        edges: List[dict] = []

        for i, snap in enumerate(sorted_snaps):
            fp = snap.get("reconstruction_hash", "") or ""
            nodes.append({
                "id":           snap.get("snapshot_id", f"SNP-{i}"),
                "type":         snap.get("snapshot_type", "UNKNOWN"),
                "type_desc":    SNAPSHOT_TYPE_DESCRIPTIONS.get(
                    snap.get("snapshot_type", ""), ""
                ),
                "timestamp_ms": snap.get("timestamp_ms", 0),
                "app_version":  snap.get("app_version", ""),
                "label":        snap.get("label", ""),
                "hash_prefix":  fp[:12],
                "immutable":    snap.get("immutable", False),
            })
            if i > 0:
                edges.append({
                    "source": sorted_snaps[i - 1].get("snapshot_id", f"SNP-{i-1}"),
                    "target": snap.get("snapshot_id", f"SNP-{i}"),
                    "type":   "TEMPORAL_SUCCESSION",
                })

        version_transitions: List[dict] = []
        prev_ver = None
        for node in nodes:
            ver = node["app_version"]
            if prev_ver and ver != prev_ver:
                version_transitions.append({
                    "at_node":   node["id"],
                    "from_ver":  prev_ver,
                    "to_ver":    ver,
                    "edge_type": "VERSION_TRANSITION",
                })
            prev_ver = ver

        return {
            "node_count":          len(nodes),
            "edge_count":          len(edges),
            "nodes":               nodes,
            "edges":               edges,
            "version_transitions": version_transitions,
            "visualization_type":  "LINEAGE_TREE",
            "graph_healthy":       True,
        }
    except Exception as exc:
        return {"graph_healthy": False, "error": str(exc)}


def build_continuity_flow(snapshots: List[dict]) -> dict:
    """
    Build an archive continuity flow diagram — shows how snapshots chain
    across versions, governance epochs, and milestone events.
    """
    try:
        sorted_snaps = sorted(snapshots, key=lambda s: s.get("timestamp_ms", 0))
        flow_nodes: List[dict] = []
        flow_edges: List[dict] = []

        for i, snap in enumerate(sorted_snaps):
            stype = snap.get("snapshot_type", "UNKNOWN")
            flow_nodes.append({
                "id":           snap.get("snapshot_id", f"SNP-{i}"),
                "type":         stype,
                "timestamp_ms": snap.get("timestamp_ms", 0),
                "app_version":  snap.get("app_version", ""),
                "is_milestone": stype in {
                    "MILESTONE", "VERSION_TRANSITION",
                    "GOVERNANCE_TRANSITION", "CATASTROPHIC_EVENT",
                },
                "is_critical":  stype == "CATASTROPHIC_EVENT",
            })
            if i > 0:
                flow_edges.append({
                    "source": sorted_snaps[i - 1].get("snapshot_id", f"SNP-{i-1}"),
                    "target": snap.get("snapshot_id", f"SNP-{i}"),
                    "type":   "CONTINUITY_LINK",
                })

        milestones = [n for n in flow_nodes if n["is_milestone"]]
        criticals  = [n for n in flow_nodes if n["is_critical"]]

        return {
            "node_count":         len(flow_nodes),
            "edge_count":         len(flow_edges),
            "nodes":              flow_nodes,
            "edges":              flow_edges,
            "milestone_count":    len(milestones),
            "critical_events":    len(criticals),
            "milestone_nodes":    milestones,
            "visualization_type": "CONTINUITY_FLOW",
            "graph_healthy":      True,
        }
    except Exception as exc:
        return {"graph_healthy": False, "error": str(exc)}


def build_export_relationship_map() -> dict:
    """
    Map of how bundles relate to reports and to each other
    (report overlap, shared primitives, bundle-contains edges).
    """
    try:
        bundle_reports: Dict[str, set] = {
            bt: set(get_reports_in_bundle(bt))
            for bt in BUNDLE_MEMBERSHIP
        }

        nodes: List[dict] = []
        for bt, ids in sorted(bundle_reports.items()):
            nodes.append({
                "id":           bt,
                "node_type":    "BUNDLE",
                "report_count": len(ids),
            })
        for r_id in sorted(REPORT_REGISTRY.keys()):
            meta = REPORT_REGISTRY[r_id]
            nodes.append({
                "id":        r_id,
                "node_type": "REPORT",
                "family":    meta.get("report_family", ""),
                "tier":      meta.get("export_tier", ""),
            })

        edges: List[dict] = []
        for bt, ids in sorted(bundle_reports.items()):
            for r_id in sorted(ids):
                edges.append({
                    "source": bt,
                    "target": r_id,
                    "type":   "BUNDLE_CONTAINS",
                })

        # Bundle pairwise overlap
        bundle_names = sorted(bundle_reports.keys())
        overlaps: List[dict] = []
        for i, bt_a in enumerate(bundle_names):
            for bt_b in bundle_names[i + 1:]:
                common = bundle_reports[bt_a] & bundle_reports[bt_b]
                if common:
                    overlaps.append({
                        "bundle_a":       bt_a,
                        "bundle_b":       bt_b,
                        "shared_count":   len(common),
                        "shared_reports": sorted(common),
                    })

        return {
            "node_count":         len(nodes),
            "edge_count":         len(edges),
            "nodes":              nodes,
            "edges":              edges,
            "bundle_overlaps":    overlaps,
            "visualization_type": "EXPORT_RELATIONSHIP_MAP",
            "graph_healthy":      True,
        }
    except Exception as exc:
        return {"graph_healthy": False, "error": str(exc)}


def get_visualization_health() -> dict:
    """Visualization infrastructure health."""
    try:
        graph = build_dependency_graph()
        return {
            "visualization_operational": True,
            "node_count":                graph.get("node_count", 0),
            "edge_count":                graph.get("edge_count", 0),
            "primitives":                len(graph.get("primitives", [])),
            "visualization_healthy":     graph.get("graph_healthy", False),
        }
    except Exception as exc:
        return {
            "visualization_operational": False,
            "error":                     str(exc),
            "visualization_healthy":     False,
        }
