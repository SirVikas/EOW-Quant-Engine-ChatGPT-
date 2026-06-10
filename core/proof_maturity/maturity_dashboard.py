"""
Maturity dashboard — PMI history and trend view for the Proof Maturity Index.
"""
import threading
from typing import List


class MaturityDashboard:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._history: List[dict] = []
        self._counter = 0

    def record(self, report: dict) -> str:
        with self._lock:
            self._counter += 1
            snapshot_id = f"PMI-{self._counter:03d}"
            self._history.append({
                "snapshot_id": snapshot_id,
                "proof_maturity_index": report.get("proof_maturity_index", 0.0),
                "proof_level": report.get("proof_level", "FOUNDATIONAL"),
                "dimension_scores": report.get("dimension_scores", {}),
                "generated_at": report.get("generated_at", 0.0),
            })
            # Cap history so a long-running engine doesn't grow unbounded
            if len(self._history) > 500:
                self._history = self._history[-500:]
            return snapshot_id

    def _trend(self) -> str:
        with self._lock:
            if len(self._history) < 2:
                return "STABLE"
            prev = self._history[-2]["proof_maturity_index"]
            curr = self._history[-1]["proof_maturity_index"]
        if curr > prev:
            return "IMPROVING"
        if curr < prev:
            return "DECLINING"
        return "STABLE"

    def dashboard(self) -> dict:
        with self._lock:
            history = list(self._history)
        latest = history[-1] if history else {}
        return {
            "latest": latest,
            "trend": self._trend(),
            "snapshots": len(history),
            "history": history[-20:],
        }


maturity_dashboard = MaturityDashboard()
