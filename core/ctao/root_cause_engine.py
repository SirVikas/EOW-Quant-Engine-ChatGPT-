"""CTAO — Root Cause Engine: identifies root causes behind CT Scan findings."""
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional


SYMPTOM_CAUSE_MAP = [
    (["unstable", "sizing"],        "Volatility regime changes not propagated",      ["regime detector lag", "position sizer not updated"]),
    (["signal quality"],            "Upstream data quality degradation",             ["data feed issues", "indicator warmup incomplete"]),
    (["trust", "calibration"],      "Insufficient evidence accumulation",            ["insufficient trades", "calibration not run"]),
    (["cascade", "propagation"],    "Cross-layer dependency failure",                ["layer ordering issue", "event bus miss"]),
    (["risk", "exposure"],          "Position sizing model drift",                   ["risk parameters stale", "equity reference stale"]),
    (["latency", "delay"],          "I/O bottleneck or blocking call in event loop", ["synchronous call in async context", "DB contention"]),
]


@dataclass
class RootCause:
    cause_id: str
    finding_id: str
    symptom: str
    root_cause: str
    contributing_factors: List[str]
    confidence: float
    causal_chain: List[str]
    analyzed_at: float


class RootCauseEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._analyses: List[RootCause] = []

    def analyze(self, finding_id: str, symptom: str, context_data: dict = None) -> dict:
        with self._lock:
            symptom_lower = symptom.lower()
            root_cause = "Unknown root cause — manual investigation required"
            contributing_factors = []
            confidence = 0.4

            for keywords, cause, factors in SYMPTOM_CAUSE_MAP:
                if any(kw in symptom_lower for kw in keywords):
                    root_cause = cause
                    contributing_factors = factors
                    confidence = 0.75
                    break

            causal_chain = [f"Symptom: {symptom}", f"Root Cause: {root_cause}"]
            if contributing_factors:
                causal_chain.append(f"Contributing: {', '.join(contributing_factors)}")

            rc = RootCause(
                cause_id=str(uuid.uuid4()),
                finding_id=finding_id,
                symptom=symptom,
                root_cause=root_cause,
                contributing_factors=contributing_factors,
                confidence=confidence,
                causal_chain=causal_chain,
                analyzed_at=time.time(),
            )
            self._analyses.append(rc)
            if len(self._analyses) > 500:
                self._analyses = self._analyses[-500:]
            return asdict(rc)

    def all_analyses(self, limit: int = 50) -> List[dict]:
        with self._lock:
            return [asdict(a) for a in self._analyses[-limit:]]

    def cause_frequency(self) -> Dict[str, int]:
        with self._lock:
            freq: Dict[str, int] = {}
            for a in self._analyses:
                freq[a.root_cause] = freq.get(a.root_cause, 0) + 1
            return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True))


root_cause_engine = RootCauseEngine()
