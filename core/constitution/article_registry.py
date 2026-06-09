"""
PHOENIX Constitution — Article Registry
Foundational constitutional articles governing system behavior.
"""
from __future__ import annotations
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class Article:
    article_id: str
    title: str
    doctrine: str
    category: str  # CAPITAL/TRUTH/GOVERNANCE/EVOLUTION/TRUST/AUDIT/HUMAN_CONTROL/SAFETY
    immutable: bool
    created_at: str
    amendment_count: int


_FOUNDATIONAL = [
    ("ART-001", "Capital Preservation First", "Never risk capital beyond defined limits", "CAPITAL", True),
    ("ART-002", "Truth Before Optimism", "Never suppress negative evidence", "TRUTH", True),
    ("ART-003", "No Hidden Decisions", "All decisions must be logged and auditable", "GOVERNANCE", True),
    ("ART-004", "No Unverified Evolution", "No change without validation proof", "EVOLUTION", True),
    ("ART-005", "Evidence Before Promotion", "Trust requires evidence, not assumptions", "TRUST", True),
    ("ART-006", "Auditability Required", "All system actions must be traceable", "AUDIT", True),
    ("ART-007", "Human Override Authority", "Humans retain final override rights", "HUMAN_CONTROL", True),
    ("ART-008", "Graceful Degradation", "System must fail safely, never catastrophically", "SAFETY", True),
]


class ArticleRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._articles: Dict[str, Article] = {}
        self._amendment_proposals: List[dict] = []
        seed_time = datetime.now(timezone.utc).isoformat()
        for art_id, title, doctrine, category, immutable in _FOUNDATIONAL:
            self._articles[art_id] = Article(
                article_id=art_id,
                title=title,
                doctrine=doctrine,
                category=category,
                immutable=immutable,
                created_at=seed_time,
                amendment_count=0,
            )

    def get(self, article_id: str) -> Optional[dict]:
        with self._lock:
            a = self._articles.get(article_id)
        return asdict(a) if a else None

    def all_articles(self) -> list:
        with self._lock:
            return [asdict(a) for a in self._articles.values()]

    def propose_amendment(self, article_id: str, proposed_change: str, justification: str) -> dict:
        with self._lock:
            article = self._articles.get(article_id)
            if not article:
                return {"error": f"{article_id} not found"}
            proposal = {
                "article_id": article_id,
                "proposed_change": proposed_change,
                "justification": justification,
                "immutable": article.immutable,
                "proposed_at": datetime.now(timezone.utc).isoformat(),
                "status": "PENDING" if not article.immutable else "BLOCKED_IMMUTABLE",
            }
            self._amendment_proposals.append(proposal)
            if not article.immutable:
                article.amendment_count += 1
        return proposal

    def pending_amendment_proposals(self) -> list:
        with self._lock:
            return [p for p in self._amendment_proposals if p["status"] == "PENDING"]


article_registry = ArticleRegistry()
