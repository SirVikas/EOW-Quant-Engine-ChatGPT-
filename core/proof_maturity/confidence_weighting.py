"""
Confidence weighting — dimension weights for the Proof Maturity Index.
Weights are normalized at computation time so adjustments cannot break
the 0–100 scale.
"""
import threading

_DEFAULT_WEIGHTS = {
    "VALIDATION": 0.30,
    "RUNTIME": 0.25,
    "EVIDENCE": 0.25,
    "CERTIFICATION": 0.20,
}


class ConfidenceWeighting:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._weights = dict(_DEFAULT_WEIGHTS)

    def weights(self) -> dict:
        with self._lock:
            return dict(self._weights)

    def set_weight(self, dimension: str, weight: float) -> dict:
        with self._lock:
            if dimension in self._weights:
                self._weights[dimension] = max(0.0, float(weight))
            return dict(self._weights)

    def weighted_score(self, scores: dict) -> float:
        with self._lock:
            total_weight = sum(self._weights.values()) or 1.0
            weighted = sum(
                float(scores.get(dim, 0.0)) * w
                for dim, w in self._weights.items()
            )
            return round(weighted / total_weight, 2)


confidence_weighting = ConfidenceWeighting()
