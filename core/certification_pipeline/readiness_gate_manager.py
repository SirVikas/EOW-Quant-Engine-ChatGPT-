"""
Readiness gate manager — threshold gates a certification run must clear.
Pre-seeded with the four institutional readiness gates.
"""
import threading
from dataclasses import dataclass
from typing import Dict

_SEED_GATES = [
    ("MATURITY", 60.0),
    ("READINESS", 50.0),
    ("EVIDENCE", 40.0),
    ("PROOF", 50.0),
]


@dataclass
class ReadinessGate:
    gate_id: str
    dimension: str
    threshold: float   # 0–100
    pass_count: int
    fail_count: int


class ReadinessGateManager:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._gates: Dict[str, ReadinessGate] = {}
        self._counter = 0
        for dimension, threshold in _SEED_GATES:
            self._counter += 1
            self._gates[dimension] = ReadinessGate(
                gate_id=f"CPG-{self._counter:03d}",
                dimension=dimension,
                threshold=threshold,
                pass_count=0,
                fail_count=0,
            )

    def set_threshold(self, dimension: str, threshold: float) -> dict:
        with self._lock:
            gate = self._gates.get(dimension)
            if gate is None:
                self._counter += 1
                gate = ReadinessGate(
                    gate_id=f"CPG-{self._counter:03d}",
                    dimension=dimension,
                    threshold=0.0,
                    pass_count=0,
                    fail_count=0,
                )
                self._gates[dimension] = gate
            gate.threshold = max(0.0, min(100.0, threshold))
            return vars(gate)

    def evaluate(self, scores: Dict[str, float]) -> dict:
        with self._lock:
            results = {}
            for dimension, gate in self._gates.items():
                score = float(scores.get(dimension, 0.0))
                passed = score >= gate.threshold
                if passed:
                    gate.pass_count += 1
                else:
                    gate.fail_count += 1
                results[dimension] = {
                    "score": round(score, 2),
                    "threshold": gate.threshold,
                    "passed": passed,
                }
            passed_n = sum(1 for r in results.values() if r["passed"])
            return {
                "gates": results,
                "passed": passed_n,
                "total": len(results),
                "all_passed": passed_n == len(results),
            }

    def gate_summary(self) -> dict:
        with self._lock:
            return {
                "total": len(self._gates),
                "gates": [vars(g) for g in self._gates.values()],
            }


readiness_gate_manager = ReadinessGateManager()
