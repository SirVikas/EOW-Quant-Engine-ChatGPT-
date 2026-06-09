"""
Postmortem engine — master orchestrator for full post-mortem lifecycle.
"""
import threading
from datetime import datetime
from typing import List


class PostmortemEngine:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._postmortems: List[str] = []   # incident IDs processed
        self._counter = 0

    def _next_pm_id(self) -> str:
        self._counter += 1
        return f"PM-{self._counter:03d}"

    def run_postmortem(
        self,
        incident_id: str,
        timeline: List[dict],
        root_cause: str,
        lessons: List[dict],   # each: {text, type, applicable_to}
        actions: List[dict],   # each: {text, owner, due_date_days}
    ) -> str:
        from core.postmortem.incident_reconstructor import incident_reconstructor
        from core.postmortem.lesson_extractor import lesson_extractor
        from core.postmortem.corrective_action_tracker import corrective_action_tracker

        contributing = [entry.get("event", "") for entry in timeline if entry.get("component")]
        incident_reconstructor.reconstruct(incident_id, timeline, root_cause, contributing)

        for lesson in lessons:
            lesson_extractor.extract(
                incident_id,
                lesson.get("text", ""),
                lesson.get("type", "TECHNICAL"),
                lesson.get("applicable_to", []),
            )

        for action in actions:
            corrective_action_tracker.create(
                incident_id,
                action.get("text", ""),
                action.get("owner", "UNASSIGNED"),
                action.get("due_date_days", 30),
            )

        pm_id = self._next_pm_id()
        with self._lock:
            self._postmortems.append(incident_id)
        return pm_id

    def postmortem_report(self) -> dict:
        from core.postmortem.lesson_extractor import lesson_extractor
        from core.postmortem.corrective_action_tracker import corrective_action_tracker

        action_summary = corrective_action_tracker.action_summary()
        lessons = lesson_extractor._lessons
        systemic = sum(1 for l in lessons if l.lesson_type == "GOVERNANCE")

        with self._lock:
            return {
                "total_postmortems": len(self._postmortems),
                "open_actions": action_summary["open"] + action_summary["in_progress"],
                "lessons_extracted": len(lessons),
                "systemic_issues_identified": systemic,
            }

    def one_liner(self) -> str:
        r = self.postmortem_report()
        return (
            f"Postmortem | Total={r['total_postmortems']} | "
            f"OpenActions={r['open_actions']} | "
            f"Lessons={r['lessons_extracted']} | "
            f"Systemic={r['systemic_issues_identified']}"
        )


postmortem_engine = PostmortemEngine()
