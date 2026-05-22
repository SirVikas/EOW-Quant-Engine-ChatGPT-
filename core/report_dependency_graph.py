"""
FTD-RTAG: Report Dependency Graph.

Tracks conceptual dependency relationships between PHOENIX LIO reports.
An edge A → B means "report A conceptually depends on primitives from B"
(B should be computed / archived before A for full interpretability).

Provides: cycle detection, dangling-reference detection, topological sort
(primitives-first), and overlap-risk analysis.

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations
from typing import Dict, List, Set, Tuple

from core.report_registry import REPORT_REGISTRY


# ── Graph construction ────────────────────────────────────────────────────────

def _build_adjacency() -> Dict[str, List[str]]:
    """
    graph[A] = [B, C] means A depends on B and C.
    Only includes edges where both endpoints are in the registry.
    """
    return {
        r_id: [d for d in spec.get("dependencies", []) if d in REPORT_REGISTRY]
        for r_id, spec in REPORT_REGISTRY.items()
    }


# ── Dependency / dependent lookup ─────────────────────────────────────────────

def get_dependencies(report_id: str) -> List[str]:
    """Reports that report_id depends on (direct only)."""
    return list(REPORT_REGISTRY.get(report_id, {}).get("dependencies", []))


def get_dependents(report_id: str) -> List[str]:
    """Reports that directly depend on report_id."""
    return sorted(
        r_id for r_id, spec in REPORT_REGISTRY.items()
        if report_id in spec.get("dependencies", [])
    )


def get_all_ancestors(report_id: str) -> Set[str]:
    """Transitive closure: all reports that report_id transitively depends on."""
    graph = _build_adjacency()
    visited: Set[str] = set()
    stack = list(graph.get(report_id, []))
    while stack:
        node = stack.pop()
        if node not in visited:
            visited.add(node)
            stack.extend(graph.get(node, []))
    return visited


# ── Dangling reference detection ──────────────────────────────────────────────

def get_dangling_dependencies() -> List[Tuple[str, str]]:
    """
    (report_id, dep_id) pairs where dep_id is declared but not in the registry.
    Indicates an incomplete or stale registry entry.
    """
    dangling = []
    for r_id, spec in REPORT_REGISTRY.items():
        for dep in spec.get("dependencies", []):
            if dep not in REPORT_REGISTRY:
                dangling.append((r_id, dep))
    return dangling


# ── Cycle detection (DFS) ─────────────────────────────────────────────────────

def _has_cycle(graph: Dict[str, List[str]]) -> bool:
    """DFS-based cycle detection on the dependency graph."""
    visited: Set[str]   = set()
    rec_stack: Set[str] = set()

    def _dfs(node: str) -> bool:
        visited.add(node)
        rec_stack.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if _dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
        rec_stack.discard(node)
        return False

    for node in graph:
        if node not in visited:
            if _dfs(node):
                return True
    return False


def detect_cycles() -> bool:
    """True if the dependency graph contains a cycle."""
    return _has_cycle(_build_adjacency())


# ── Topological sort (Kahn's algorithm) ───────────────────────────────────────

def topological_sort() -> List[str]:
    """
    Returns all registered reports in dependency order (primitives first).
    Returns [] if a cycle is detected.
    """
    graph = _build_adjacency()
    if _has_cycle(graph):
        return []

    all_nodes = list(graph.keys())

    # in_deg[A] = number of known dependencies A has
    in_deg: Dict[str, int] = {
        n: len([d for d in graph[n] if d in graph])
        for n in all_nodes
    }

    # dependents_of[B] = nodes that list B as a dependency
    dependents_of: Dict[str, List[str]] = {n: [] for n in all_nodes}
    for node in all_nodes:
        for dep in graph[node]:
            if dep in dependents_of:
                dependents_of[dep].append(node)

    queue = sorted(n for n in all_nodes if in_deg[n] == 0)
    result: List[str] = []

    while queue:
        node = queue.pop(0)
        result.append(node)
        for dependent in sorted(dependents_of.get(node, [])):
            if dependent in in_deg:
                in_deg[dependent] -= 1
                if in_deg[dependent] == 0:
                    queue.append(dependent)
                    queue.sort()

    return result


# ── Overlap analysis ──────────────────────────────────────────────────────────

def get_overlap_map() -> Dict[str, List[str]]:
    """Each report's declared overlapping_reports list."""
    return {
        r_id: list(spec.get("overlapping_reports", []))
        for r_id, spec in REPORT_REGISTRY.items()
    }


def get_high_overlap_reports(threshold: int = 2) -> List[str]:
    """Reports declaring >= threshold overlapping reports."""
    return sorted(
        r_id for r_id, overlaps in get_overlap_map().items()
        if len(overlaps) >= threshold
    )


def get_primitive_reports() -> List[str]:
    """Reports with no dependencies — the foundation of the ecosystem."""
    return sorted(
        r_id for r_id, spec in REPORT_REGISTRY.items()
        if not spec.get("dependencies", [])
    )


# ── Health summary ────────────────────────────────────────────────────────────

def get_dependency_graph_health() -> dict:
    has_cycle = detect_cycles()
    dangling  = get_dangling_dependencies()
    topo      = topological_sort()
    high_ov   = get_high_overlap_reports()
    prim      = get_primitive_reports()
    return {
        "has_cycle":              has_cycle,
        "cycle_free":             not has_cycle,
        "dangling_dependencies":  dangling,
        "dangling_count":         len(dangling),
        "topological_order":      topo,
        "topological_count":      len(topo),
        "primitive_reports":      prim,
        "primitive_count":        len(prim),
        "high_overlap_reports":   high_ov,
        "high_overlap_count":     len(high_ov),
        "graph_healthy":          not has_cycle and len(dangling) == 0,
    }
