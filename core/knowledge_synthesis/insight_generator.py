"""Insight Generator — creates and stores cross-domain synthesized insights."""
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class Insight:
    insight_id: str
    title: str
    content: str
    domains_combined: List[str]
    novelty_score: float  # 0-1
    confidence: float     # 0-1
    generated_from: List[str]
    created_at: str


class InsightGenerator:
    def __init__(self):
        self._lock = threading.RLock()
        self._insights: List[Insight] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"INS-{self._counter:03d}"

    def generate(self, title: str, content: str, domains_combined: List[str],
                 novelty_score: float = 0.5, confidence: float = 0.5,
                 generated_from: Optional[List[str]] = None) -> dict:
        with self._lock:
            insight = Insight(
                insight_id=self._next_id(),
                title=title,
                content=content,
                domains_combined=list(domains_combined),
                novelty_score=novelty_score,
                confidence=confidence,
                generated_from=generated_from or [],
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            self._insights.append(insight)
            return asdict(insight)

    def all_insights(self, limit: int = 50) -> List[dict]:
        with self._lock:
            return [asdict(i) for i in self._insights[-limit:]]

    def novel_insights(self, threshold: float = 0.7) -> List[dict]:
        with self._lock:
            return [asdict(i) for i in self._insights if i.novelty_score >= threshold]

    def insight_stats(self) -> dict:
        with self._lock:
            total = len(self._insights)
            if total == 0:
                return {"total": 0, "avg_novelty": 0, "avg_confidence": 0, "by_domain_combo_count": 0}
            avg_novelty = sum(i.novelty_score for i in self._insights) / total
            avg_conf = sum(i.confidence for i in self._insights) / total
            combos = set(tuple(sorted(i.domains_combined)) for i in self._insights)
            return {
                "total": total,
                "avg_novelty": avg_novelty,
                "avg_confidence": avg_conf,
                "by_domain_combo_count": len(combos),
            }


insight_generator = InsightGenerator()
