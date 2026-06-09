"""
PHOENIX Constitution — Constitutional Validator
Validates actions against constitutional articles using keyword heuristics.
"""
from __future__ import annotations
import threading
from datetime import datetime, timezone
from typing import Dict, List


class ConstitutionalValidator:
    ARTICLE_KEYWORDS: Dict[str, List[str]] = {
        "ART-001": ["capital risk", "position size increase", "leverage increase", "margin"],
        "ART-002": ["suppress", "hide", "ignore negative", "filter out loss"],
        "ART-003": ["no log", "skip record", "bypass audit"],
        "ART-004": ["deploy without", "skip validation", "force deploy"],
        "ART-005": ["promote without evidence", "assume trust", "skip proof"],
        "ART-006": ["untraceable", "anonymous decision", "no audit trail"],
    }

    def __init__(self):
        self._lock = threading.RLock()

    def validate(self, action_description: str) -> dict:
        text = action_description.lower()
        violated = []
        warnings = []

        for art_id, keywords in self.ARTICLE_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    violated.append(art_id)
                    break

        # Soft warnings for borderline cases
        if "increase" in text and "risk" not in text:
            warnings.append("Action involves increase — verify ART-001 compliance")

        passed = len(violated) == 0
        score = max(0.0, 1.0 - len(violated) * 0.15)
        return {
            "passed": passed,
            "violated_articles": violated,
            "warnings": warnings,
            "constitutional_score": round(score, 4),
            "action_description": action_description,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    def validate_batch(self, actions: list) -> list:
        return [self.validate(a) for a in actions]

    def constitution_status(self) -> dict:
        from core.constitution.article_registry import article_registry
        articles = article_registry.all_articles()
        immutable_count = sum(1 for a in articles if a["immutable"])
        pending = len(article_registry.pending_amendment_proposals())
        return {
            "total_articles": len(articles),
            "immutable_articles": immutable_count,
            "amendment_proposals_pending": pending,
        }


constitutional_validator = ConstitutionalValidator()
