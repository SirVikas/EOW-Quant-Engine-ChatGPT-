"""
PHOENIX CORTEX — Dependency Mapper  [CX-2]

Builds and maintains the complete dependency graph for all registered CORTEX
modules.  A dependency graph edge  A → B  means:
  "Module A must be running / healthy before Module B can operate correctly."

Sources of dependency information (in precedence order):
  1. Explicit dependencies in ModuleDefinition.dependencies
  2. consumes/produces contract matching (module A produces X, module B consumes X)
  3. Tier-based implicit rules (all Tier-A modules depend on global_gate_controller)

The mapper provides:
  - dependency_chain(module_key)  : all transitive dependencies of a module
  - dependents(module_key)        : all modules that depend on this one
  - impact_radius(module_key)     : how many modules are affected if this one fails
  - shared_inputs()               : modules sharing the same input streams (conflict risk)
  - boot_order()                  : safe startup sequence
  - health_impact(module_key)     : severity if this module goes down
"""
from __future__ import annotations

import threading
from collections import deque
from typing import Dict, List, Set, Tuple


class CortexDependencyMapper:

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # forward: A → set of modules A depends on
        self._deps:  Dict[str, Set[str]] = {}
        # reverse: A → set of modules that depend on A
        self._rdeps: Dict[str, Set[str]] = {}
        self._built = False

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self) -> None:
        """Construct dependency graph from the module registry."""
        from core.cortex.module_registry import cortex_module_registry
        modules = cortex_module_registry.all()

        with self._lock:
            self._deps  = {m.key: set() for m in modules}
            self._rdeps = {m.key: set() for m in modules}

            # 1. Explicit dependencies
            for m in modules:
                for dep in m.dependencies:
                    if dep in self._deps:
                        self._deps[m.key].add(dep)
                        self._rdeps[dep].add(m.key)

            # 2. consumes/produces contract matching
            produces_map: Dict[str, List[str]] = {}  # output → list of producer keys
            for m in modules:
                for output in m.produces:
                    produces_map.setdefault(output, []).append(m.key)
            for m in modules:
                for inp in m.consumes:
                    for producer_key in produces_map.get(inp, []):
                        if producer_key != m.key and producer_key in self._deps:
                            self._deps[m.key].add(producer_key)
                            self._rdeps[producer_key].add(m.key)

            # 3. Tier-A implicit dependency on global_gate_controller
            gate_key = "global_gate_controller"
            if gate_key in self._deps:
                for m in modules:
                    if m.tier == "A" and m.key != gate_key:
                        self._deps[m.key].add(gate_key)
                        self._rdeps[gate_key].add(m.key)

            self._built = True

    def _ensure_built(self) -> None:
        if not self._built:
            self.build()

    # ── Query ─────────────────────────────────────────────────────────────────

    def dependency_chain(self, module_key: str) -> List[str]:
        """All transitive dependencies of module_key (BFS)."""
        self._ensure_built()
        with self._lock:
            if module_key not in self._deps:
                return []
            visited: Set[str] = set()
            queue = deque(self._deps[module_key])
            while queue:
                node = queue.popleft()
                if node in visited:
                    continue
                visited.add(node)
                queue.extend(self._deps.get(node, set()) - visited)
        return sorted(visited)

    def dependents(self, module_key: str) -> List[str]:
        """All modules that directly depend on module_key."""
        self._ensure_built()
        with self._lock:
            return sorted(self._rdeps.get(module_key, set()))

    def transitive_dependents(self, module_key: str) -> List[str]:
        """All modules that would be impacted if module_key fails (BFS)."""
        self._ensure_built()
        with self._lock:
            visited: Set[str] = set()
            queue = deque(self._rdeps.get(module_key, set()))
            while queue:
                node = queue.popleft()
                if node in visited:
                    continue
                visited.add(node)
                queue.extend(self._rdeps.get(node, set()) - visited)
        return sorted(visited)

    def impact_radius(self, module_key: str) -> dict:
        """How many modules are transitively impacted if module_key fails."""
        affected = self.transitive_dependents(module_key)
        from core.cortex.module_registry import cortex_module_registry
        critical_affected = [
            k for k in affected
            if (m := cortex_module_registry.get(k)) and m.critical
        ]
        return {
            "module_key":       module_key,
            "total_impacted":   len(affected),
            "critical_impacted": len(critical_affected),
            "impacted_modules": affected,
            "critical_modules": critical_affected,
            "severity": (
                "CRITICAL" if critical_affected else
                "HIGH"     if len(affected) >= 10 else
                "MEDIUM"   if len(affected) >= 5  else
                "LOW"
            ),
        }

    def shared_inputs(self) -> List[dict]:
        """
        Pairs of modules that consume the same input stream.
        High-conflict risk if their logic contradicts.
        """
        self._ensure_built()
        from core.cortex.module_registry import cortex_module_registry
        modules = cortex_module_registry.all()
        input_owners: Dict[str, List[str]] = {}
        for m in modules:
            for inp in m.consumes:
                input_owners.setdefault(inp, []).append(m.key)
        result = []
        for inp, owners in input_owners.items():
            if len(owners) >= 2:
                result.append({
                    "shared_input": inp,
                    "consumers":    sorted(owners),
                    "consumer_count": len(owners),
                    "conflict_risk": len(owners) >= 3,
                })
        result.sort(key=lambda x: x["consumer_count"], reverse=True)
        return result

    def boot_order(self) -> List[str]:
        """
        Safe module startup sequence — topological sort of the dependency graph.
        Modules with no dependencies come first.
        """
        self._ensure_built()
        with self._lock:
            all_keys = set(self._deps.keys())
            in_degree = {k: len(self._deps[k]) for k in all_keys}
            queue = deque(sorted(k for k, d in in_degree.items() if d == 0))
            order: List[str] = []
            while queue:
                node = queue.popleft()
                order.append(node)
                for dependent in sorted(self._rdeps.get(node, set())):
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
            # Append any remaining (cycle nodes)
            remaining = sorted(all_keys - set(order))
            order.extend(remaining)
        return order

    def graph_summary(self) -> dict:
        self._ensure_built()
        with self._lock:
            total_edges = sum(len(v) for v in self._deps.values())
            nodes = len(self._deps)
        return {
            "total_nodes": nodes,
            "total_edges": total_edges,
            "built":       self._built,
        }

    def full_graph(self) -> dict:
        """Serialisable adjacency list for the dependency graph."""
        self._ensure_built()
        with self._lock:
            return {
                k: sorted(v)
                for k, v in self._deps.items()
                if v  # omit isolated nodes for brevity
            }


# Singleton
cortex_dependency_mapper = CortexDependencyMapper()
