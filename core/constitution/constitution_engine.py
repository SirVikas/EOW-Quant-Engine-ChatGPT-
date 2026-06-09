"""
PHOENIX Constitution Engine
Orchestrates constitutional validation, recording, and enforcement.
"""
from __future__ import annotations
import threading
from datetime import datetime, timezone


class ConstitutionEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def check(self, action_description: str, actor: str = "SYSTEM") -> dict:
        from core.constitution.constitutional_validator import constitutional_validator
        from core.constitution.change_history import change_history

        result = constitutional_validator.validate(action_description)

        if not result["passed"]:
            for art_id in result["violated_articles"]:
                change_history.record(
                    "VIOLATION_DETECTED",
                    art_id,
                    f"Violation by: {action_description[:100]}",
                    actor,
                )
        else:
            change_history.record("VALIDATION", "ALL", f"Action validated: {action_description[:100]}", actor)

        return result

    def constitution_report(self) -> dict:
        from core.constitution.article_registry import article_registry
        from core.constitution.change_history import change_history
        from core.constitution.constitutional_validator import constitutional_validator

        articles = article_registry.all_articles()
        stats = change_history.history_stats()
        recent_violations = change_history.violations(limit=5)
        amendment_props = change_history.amendment_proposals()
        const_status = constitutional_validator.constitution_status()

        violation_rate = stats["violations_count"] / max(1, stats["total_events"])
        health_score = round(max(0.0, 1.0 - violation_rate), 4)
        return {
            "articles_count": len(articles),
            "recent_violations": recent_violations,
            "amendment_proposals": amendment_props,
            "constitutional_health_score": health_score,
            "constitution_status": const_status,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def enforce(self, action_description: str, actor: str = "SYSTEM"):
        result = self.check(action_description, actor)
        if not result["passed"]:
            violated = result["violated_articles"]
            raise ValueError(
                f"Constitutional violation — action blocked. Violated: {violated}. Action: {action_description[:100]}"
            )
        return result


constitution_engine = ConstitutionEngine()
