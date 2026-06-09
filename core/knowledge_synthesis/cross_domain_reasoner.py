"""Cross-Domain Reasoner — reasoning sessions across multiple knowledge domains."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List


@dataclass
class ReasoningSession:
    session_id: str
    domain_a: str
    domain_b: str
    insight: str
    confidence_pct: float
    created_at: str


DOMAINS = ["Research", "Trust", "Economics", "Governance", "Forecasting"]


class CrossDomainReasoner:
    def __init__(self):
        self._lock = threading.RLock()
        self._sessions: List[ReasoningSession] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"CDS-{self._counter:03d}"

    def reason(self, domain_a: str, domain_b: str, insight: str, confidence_pct: float = 50.0) -> dict:
        with self._lock:
            session = ReasoningSession(
                session_id=self._next_id(),
                domain_a=domain_a,
                domain_b=domain_b,
                insight=insight,
                confidence_pct=confidence_pct,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            self._sessions.append(session)
            return asdict(session)

    def all_sessions(self, limit: int = 50) -> List[dict]:
        with self._lock:
            return [asdict(s) for s in self._sessions[-limit:]]

    def sessions_by_domain(self, domain: str) -> List[dict]:
        with self._lock:
            return [asdict(s) for s in self._sessions if domain in (s.domain_a, s.domain_b)]

    def high_confidence_sessions(self, threshold: float = 70.0) -> List[dict]:
        with self._lock:
            return [asdict(s) for s in self._sessions if s.confidence_pct >= threshold]

    def reasoning_stats(self) -> dict:
        with self._lock:
            total = len(self._sessions)
            if total == 0:
                return {"total_sessions": 0, "avg_confidence": 0.0, "available_domains": DOMAINS}
            avg_conf = sum(s.confidence_pct for s in self._sessions) / total
            return {
                "total_sessions": total,
                "avg_confidence": avg_conf,
                "available_domains": DOMAINS,
            }


cross_domain_reasoner = CrossDomainReasoner()
