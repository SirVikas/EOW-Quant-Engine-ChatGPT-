"""
PHOENIX OBSERVATORY-X — Report Relationship Engine  [OX-2A]

Reports in PHOENIX are not isolated islands.  A Risk Report is related to the
Trades that triggered the risk event; those trades are related to the Signals
that generated them; those signals belong to a Regime; that regime influenced
Capital sizing.  The Relationship Engine makes these connections explicit so
that clicking on any report surfaces its full ecosystem context.

Architecture
────────────
  ReportRelationshipEngine maintains a directed relationship graph:
    source_report_key  ──[relationship_type]──▶  target_report_key

  Relationship types:
    INFORMS   source provides data that target consumes
    DEPENDS   source must run before target (hard dependency)
    OVERLAPS  both reports present the same underlying data
    EXPLAINS  target provides root-cause analysis for source events
    ARCHIVES  target is the long-term archive of source output

  Bootstrap logic builds edges from:
    1. Registry dependency lists (hard DEPENDS edges)
    2. Category/tier heuristics (soft INFORMS / OVERLAPS edges)
    3. Manual registration (report generators call relate() at boot)

  Thread-safe singleton.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


# ── Data Model ────────────────────────────────────────────────────────────────

INFORMS  = "INFORMS"
DEPENDS  = "DEPENDS"
OVERLAPS = "OVERLAPS"
EXPLAINS = "EXPLAINS"
ARCHIVES = "ARCHIVES"

_VALID_TYPES = {INFORMS, DEPENDS, OVERLAPS, EXPLAINS, ARCHIVES}


@dataclass
class ReportRelationship:
    source: str
    target: str
    rel_type: str
    description: str = ""


# ── Engine ────────────────────────────────────────────────────────────────────

class ReportRelationshipEngine:
    """
    Directed relationship graph over the report catalog.
    Nodes = report keys.  Edges = typed relationships.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # adjacency: source → list of (target, rel_type, description)
        self._edges: Dict[str, List[ReportRelationship]] = {}
        # reverse adjacency for fast "who points to me" lookups
        self._reverse: Dict[str, List[ReportRelationship]] = {}
        self._bootstrap_from_registry()

    # ── Registration ─────────────────────────────────────────────────────────

    def relate(
        self,
        source: str,
        target: str,
        rel_type: str = INFORMS,
        description: str = "",
    ) -> None:
        """Add a directed relationship edge.  Idempotent."""
        if rel_type not in _VALID_TYPES:
            raise ValueError(f"Unknown relationship type: {rel_type}")
        edge = ReportRelationship(source=source, target=target,
                                  rel_type=rel_type, description=description)
        with self._lock:
            fwd = self._edges.setdefault(source, [])
            if not any(e.target == target and e.rel_type == rel_type for e in fwd):
                fwd.append(edge)
            rev = self._reverse.setdefault(target, [])
            if not any(e.source == source and e.rel_type == rel_type for e in rev):
                rev.append(edge)

    # ── Query ─────────────────────────────────────────────────────────────────

    def context_for(self, report_key: str) -> dict:
        """
        Return the full relationship context for one report:
          - reports this one informs / depends on / overlaps (outbound)
          - reports that inform / depend on / explain this one (inbound)
        """
        with self._lock:
            outbound = list(self._edges.get(report_key, []))
            inbound  = list(self._reverse.get(report_key, []))

        def _fmt(edges: List[ReportRelationship]) -> List[dict]:
            return [
                {"report_key": e.target if e.source == report_key else e.source,
                 "rel_type": e.rel_type,
                 "direction": "outbound" if e.source == report_key else "inbound",
                 "description": e.description}
                for e in edges
            ]

        return {
            "report_key": report_key,
            "outbound":   _fmt(outbound),
            "inbound":    _fmt(inbound),
            "total_connections": len(outbound) + len(inbound),
        }

    def neighbors(self, report_key: str, rel_type: Optional[str] = None) -> List[str]:
        """Keys of all reports directly connected to report_key."""
        with self._lock:
            fwd = self._edges.get(report_key, [])
            rev = self._reverse.get(report_key, [])
        result: Set[str] = set()
        for e in fwd:
            if rel_type is None or e.rel_type == rel_type:
                result.add(e.target)
        for e in rev:
            if rel_type is None or e.rel_type == rel_type:
                result.add(e.source)
        return sorted(result)

    def dependency_order(self) -> List[str]:
        """
        Topological sort of all registered reports respecting DEPENDS edges.
        Reports with no dependencies come first.
        Returns a flat list; cycles are broken by omitting the back-edge report.
        """
        with self._lock:
            all_keys: Set[str] = set(self._edges.keys()) | set(self._reverse.keys())
            dep_map: Dict[str, Set[str]] = {k: set() for k in all_keys}
            for src, edges in self._edges.items():
                for e in edges:
                    if e.rel_type == DEPENDS:
                        dep_map.setdefault(e.target, set()).add(src)

        visited: Set[str] = set()
        order: List[str] = []

        def _visit(key: str, path: Set[str]) -> None:
            if key in visited:
                return
            if key in path:
                return  # cycle guard
            path.add(key)
            for dep in dep_map.get(key, set()):
                _visit(dep, path)
            path.discard(key)
            visited.add(key)
            order.append(key)

        for k in sorted(all_keys):
            _visit(k, set())

        return order

    def graph_summary(self) -> dict:
        with self._lock:
            total_edges = sum(len(v) for v in self._edges.values())
            nodes = set(self._edges.keys()) | set(self._reverse.keys())
            by_type: Dict[str, int] = {}
            for edges in self._edges.values():
                for e in edges:
                    by_type[e.rel_type] = by_type.get(e.rel_type, 0) + 1
        return {
            "total_nodes":  len(nodes),
            "total_edges":  total_edges,
            "edges_by_type": by_type,
            "nodes": sorted(nodes),
        }

    def all_relationships(self) -> List[dict]:
        with self._lock:
            result = []
            for edges in self._edges.values():
                for e in edges:
                    result.append({
                        "source":      e.source,
                        "target":      e.target,
                        "rel_type":    e.rel_type,
                        "description": e.description,
                    })
        return result

    # ── Bootstrap ─────────────────────────────────────────────────────────────

    def _bootstrap_from_registry(self) -> None:
        """
        Build initial edges from:
          1. Registry explicit dependency lists → DEPENDS
          2. Category-based heuristics → INFORMS / OVERLAPS
          3. Hard-coded institutional relationships → EXPLAINS / ARCHIVES
        """
        try:
            from core.observatory.registry import report_registry
        except Exception:
            return

        defs = report_registry.all()

        # 1. Registry dependencies → DEPENDS
        for defn in defs:
            for dep_key in defn.dependencies:
                self.relate(dep_key, defn.key, DEPENDS,
                            f"{dep_key} must complete before {defn.key}")

        # 2. Performance reports inform the board summary
        for defn in defs:
            if defn.category == "performance" and defn.key != "dashboard_summary":
                self.relate(defn.key, "dashboard_summary", INFORMS,
                            "performance data feeds dashboard")

        # 3. Signal reports inform performance reports
        for defn in defs:
            if defn.category == "signal":
                self.relate(defn.key, "perf_report_1d", INFORMS,
                            "signal quality influences win rate")

        # 4. Risk reports inform governance reports
        for defn in defs:
            if defn.category == "risk":
                self.relate(defn.key, "adaptive_decision_audit", INFORMS,
                            "risk state influences adaptive decisions")

        # 5. Intelligence reports explain performance outcomes
        for defn in defs:
            if defn.category == "intelligence" and defn.key not in ("ct_scan", "ai_brain"):
                self.relate(defn.key, "intelligence_maturity_report", INFORMS,
                            "intelligence module feeds maturity score")

        # 6. The bundle archives everything
        for defn in defs:
            if defn.key not in ("all_reports_bundle", "metadata"):
                self.relate(defn.key, "all_reports_bundle", ARCHIVES,
                            "session archive captures all reports")

        # 7. Hard-coded institutional relationships
        _institutional = [
            ("signal_truth_matrix",    "signal_funnel",           EXPLAINS,
             "truth matrix explains funnel losses"),
            ("false_positive_clusters","signal_truth_matrix",     EXPLAINS,
             "FP clusters explain low truth scores"),
            ("regime_performance_matrix", "perf_report_1d",       EXPLAINS,
             "regime breakdown explains overall PnL"),
            ("consistency",            "perf_report_1d",          EXPLAINS,
             "consistency failures explain PnL variance"),
            ("negative_memory",        "failed_patterns",         INFORMS,
             "negative memory seeds failed-pattern library"),
            ("anomalies",              "escalations",             INFORMS,
             "detected anomalies trigger escalations"),
            ("audit_log",              "adaptive_decision_audit", INFORMS,
             "raw audit events feed adaptive audit"),
            ("rl_intelligence",        "strategy_evolution_report", INFORMS,
             "RL rewards guide genome evolution"),
            ("edge_validation_report", "capital_efficiency",      INFORMS,
             "edge strength determines capital deployment"),
            ("exit_analysis",          "perf_report_1d",          INFORMS,
             "exit quality is a primary PnL driver"),
            ("fee_drag_analysis",      "capital_efficiency",      INFORMS,
             "fee drag reduces capital efficiency"),
            ("confidence_calibration_report", "signal_truth_matrix", OVERLAPS,
             "both measure signal confidence quality"),
            ("confidence_reality_divergence", "confidence_calibration_report", EXPLAINS,
             "divergence explains calibration errors"),
        ]
        for src, tgt, rtype, desc in _institutional:
            self.relate(src, tgt, rtype, desc)


# Singleton
report_relationship_engine = ReportRelationshipEngine()
