"""CTAO — Recommendation Intelligence Engine: generates structured recommendations from findings."""
import threading
import time
from dataclasses import dataclass, asdict
from typing import List


SEVERITY_PRIORITY = {"CRITICAL": 9.0, "HIGH": 7.0, "MEDIUM": 5.0, "LOW": 3.0, "INFO": 1.0}

KEYWORD_DEFAULTS = [
    (["volatility", "regime"],  "Recalibrate regime detector and propagate updates",    "HIGH",   "MEDIUM", "Improved trade quality, fewer false signals"),
    (["data", "quality"],       "Audit data feed pipeline and indicator warmup",         "HIGH",   "LOW",    "Stable signal foundation"),
    (["trust", "evidence"],     "Increase evidence accumulation window",                "MEDIUM", "LOW",    "More reliable trust scores"),
    (["risk", "exposure"],      "Recalibrate position sizing model",                    "HIGH",   "MEDIUM", "Controlled drawdown"),
    (["latency", "io"],         "Refactor blocking calls to async",                     "MEDIUM", "HIGH",   "Reduced event loop lag"),
    (["cascade", "dependency"], "Audit inter-layer dependency ordering",                "HIGH",   "HIGH",   "System stability"),
]


@dataclass
class CTRecommendation:
    rec_id: str
    finding_id: str
    recommended_fix: str
    expected_benefit: str
    risk_level: str
    complexity: str
    expected_roi: str
    priority_score: float
    status: str
    created_at: float


class CTAORecommendationEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._recs: List[CTRecommendation] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"REC-{self._counter:03d}"

    def generate(self, finding_id: str, finding_description: str,
                 root_cause: str = "", severity: str = "MEDIUM") -> dict:
        with self._lock:
            text = (finding_description + " " + root_cause).lower()
            fix = "Review and address the identified finding"
            expected_benefit = "System improvement"
            risk_level = "MEDIUM"
            complexity = "MEDIUM"
            expected_roi = "Moderate improvement expected"

            for keywords, f, rl, cx, eb in KEYWORD_DEFAULTS:
                if any(kw in text for kw in keywords):
                    fix = f
                    risk_level = rl
                    complexity = cx
                    expected_benefit = eb
                    expected_roi = f"High — addresses {keywords[0]} issue"
                    break

            base_score = SEVERITY_PRIORITY.get(severity.upper(), 5.0)
            complexity_factor = {"LOW": 1.2, "MEDIUM": 1.0, "HIGH": 0.7}.get(complexity, 1.0)
            priority_score = round(base_score * complexity_factor, 2)

            rec = CTRecommendation(
                rec_id=self._next_id(),
                finding_id=finding_id,
                recommended_fix=fix,
                expected_benefit=expected_benefit,
                risk_level=risk_level,
                complexity=complexity,
                expected_roi=expected_roi,
                priority_score=priority_score,
                status="PENDING",
                created_at=time.time(),
            )
            self._recs.append(rec)
            return asdict(rec)

    def _update_status(self, rec_id: str, status: str) -> dict:
        for r in self._recs:
            if r.rec_id == rec_id:
                r.status = status
                return {"updated": rec_id, "status": status}
        return {"error": f"Recommendation {rec_id} not found"}

    def approve(self, rec_id: str) -> dict:
        with self._lock:
            return self._update_status(rec_id, "APPROVED")

    def implement(self, rec_id: str) -> dict:
        with self._lock:
            return self._update_status(rec_id, "IMPLEMENTED")

    def reject(self, rec_id: str) -> dict:
        with self._lock:
            return self._update_status(rec_id, "REJECTED")

    def bury(self, rec_id: str) -> dict:
        with self._lock:
            return self._update_status(rec_id, "BURIED")

    def pending_recommendations(self) -> List[dict]:
        with self._lock:
            pending = [r for r in self._recs if r.status == "PENDING"]
            return [asdict(r) for r in sorted(pending, key=lambda x: x.priority_score, reverse=True)]

    def implemented_recommendations(self) -> List[dict]:
        with self._lock:
            return [asdict(r) for r in self._recs if r.status == "IMPLEMENTED"]

    def rec_stats(self) -> dict:
        with self._lock:
            statuses = ["PENDING", "APPROVED", "IMPLEMENTED", "REJECTED", "BURIED"]
            return {s.lower(): sum(1 for r in self._recs if r.status == s) for s in statuses} | {"total": len(self._recs)}


ctao_recommendation_engine = CTAORecommendationEngine()
