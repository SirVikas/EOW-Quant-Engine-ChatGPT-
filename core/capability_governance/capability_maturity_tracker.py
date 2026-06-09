"""Capability Maturity Tracker — detailed maturity assessments for capabilities."""
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Optional
import uuid


@dataclass
class MaturityAssessment:
    assessment_id: str
    cap_id: str
    score: float  # 0-100
    strengths: List[str]
    weaknesses: List[str]
    next_milestone: str
    assessed_at: str


class CapabilityMaturityTracker:
    def __init__(self):
        self._lock = threading.RLock()
        self._assessments: List[MaturityAssessment] = []

    def assess(self, cap_id: str, score: float, strengths: Optional[List[str]] = None,
               weaknesses: Optional[List[str]] = None, next_milestone: str = "") -> dict:
        with self._lock:
            assessment = MaturityAssessment(
                assessment_id=str(uuid.uuid4())[:8],
                cap_id=cap_id,
                score=score,
                strengths=strengths or [],
                weaknesses=weaknesses or [],
                next_milestone=next_milestone,
                assessed_at=datetime.now(timezone.utc).isoformat(),
            )
            self._assessments.append(assessment)
            return asdict(assessment)

    def latest_assessment(self, cap_id: str) -> Optional[dict]:
        with self._lock:
            cap_assessments = [a for a in self._assessments if a.cap_id == cap_id]
            if not cap_assessments:
                return None
            return asdict(cap_assessments[-1])

    def all_assessments(self, cap_id: Optional[str] = None) -> List[dict]:
        with self._lock:
            assessments = self._assessments
            if cap_id:
                assessments = [a for a in assessments if a.cap_id == cap_id]
            return [asdict(a) for a in assessments]

    def capabilities_needing_attention(self, score_threshold: float = 60) -> List[dict]:
        with self._lock:
            # Get latest assessment for each cap_id
            latest: dict[str, MaturityAssessment] = {}
            for a in self._assessments:
                latest[a.cap_id] = a
            return [asdict(a) for a in latest.values() if a.score < score_threshold]


capability_maturity_tracker = CapabilityMaturityTracker()
