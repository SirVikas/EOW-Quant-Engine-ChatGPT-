"""Layer Dependency Engine — maps inter-layer dependencies and failure impact."""
import threading
from collections import deque


class LayerDependencyEngine:
    DEPENDENCY_MAP = {
        "NEXUS":          ["IMRAF", "TRUST_ENGINE"],
        "OBSERVATORY-X":  ["NEXUS"],
        "CORTEX":         ["NEXUS", "TRUST_ENGINE"],
        "AEG":            ["TRUST_ENGINE", "OBSERVATORY-X"],
        "PCAO":           ["AEG", "CORTEX", "NEXUS"],
        "PCCP":           ["NEXUS", "OBSERVATORY-X", "CORTEX", "AEG", "PCAO"],
        "CTAO":           ["PCCP", "OBSERVATORY-X"],
        "DIGITAL_TWIN":   ["NEXUS", "AEG"],
        "TRUST_ENGINE":   ["NEXUS"],
        "RISK_ENGINE":    ["TRUST_ENGINE", "PCAO"],
    }

    def __init__(self):
        self._lock = threading.RLock()
        # Build reverse map
        self._reverse: dict[str, list] = {}
        for layer, deps in self.DEPENDENCY_MAP.items():
            for dep in deps:
                self._reverse.setdefault(dep, []).append(layer)

    def impact_of_failure(self, layer_id: str) -> dict:
        with self._lock:
            visited = set()
            queue = deque([(layer_id, 0)])
            directly_affected = []
            transitively_affected = []

            while queue:
                current, depth = queue.popleft()
                if current in visited:
                    continue
                visited.add(current)
                dependents = self._reverse.get(current, [])
                for dep in dependents:
                    if dep not in visited:
                        if depth == 0:
                            directly_affected.append(dep)
                        else:
                            transitively_affected.append(dep)
                        queue.append((dep, depth + 1))

            all_affected = set(directly_affected + transitively_affected)
            if "PCAO" in all_affected or "TRUST_ENGINE" in all_affected:
                severity = "CRITICAL"
            elif "CORTEX" in all_affected or "AEG" in all_affected:
                severity = "HIGH"
            elif "OBSERVATORY-X" in all_affected:
                severity = "MEDIUM"
            else:
                severity = "LOW"

            recovery = self.recovery_sequence(layer_id)
            return {
                "failed_layer": layer_id,
                "directly_affected": directly_affected,
                "transitively_affected": transitively_affected,
                "severity": severity,
                "recovery_sequence": recovery,
            }

    def recovery_sequence(self, layer_id: str) -> list:
        # Topological sort of affected layers innermost-first (dependencies before dependents)
        affected = set()
        queue = deque([layer_id])
        visited = set()
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            affected.add(current)
            for dep in self._reverse.get(current, []):
                queue.append(dep)

        # Topological order: sort by number of dependencies (inner layers first)
        def dep_count(l):
            return len(self.DEPENDENCY_MAP.get(l, []))

        return sorted(affected, key=dep_count)

    def dependency_report(self) -> dict:
        with self._lock:
            report = {}
            for layer in self.DEPENDENCY_MAP:
                impact = self.impact_of_failure(layer)
                report[layer] = {
                    "depends_on": self.DEPENDENCY_MAP[layer],
                    "impact_if_failed": impact,
                }
            return report

    def most_critical_layer(self) -> str:
        with self._lock:
            max_impact = -1
            most_critical = None
            for layer in self.DEPENDENCY_MAP:
                impact = self.impact_of_failure(layer)
                total = len(impact["directly_affected"]) + len(impact["transitively_affected"])
                if total > max_impact:
                    max_impact = total
                    most_critical = layer
            return most_critical


layer_dependency_engine = LayerDependencyEngine()
