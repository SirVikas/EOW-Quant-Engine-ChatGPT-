"""
PHOENIX Autonomous Improvement Engine
Orchestrates the full autonomous improvement cycle: learn → propose → apply → feedback.
"""
from __future__ import annotations
import threading
import time
from datetime import datetime, timezone


class ImprovementEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._cycles_run = 0
        self._last_cycle_at: float = 0.0
        self._total_lessons = 0
        self._total_policy_updates = 0

    def run_improvement_cycle(self) -> dict:
        lessons_processed = 0
        policy_updates_proposed = 0
        learning_cycle_run = False
        feedback_cycles_completed = 0

        # Step 1: Extract new lessons from strategic memory
        try:
            from core.strategic_memory.strategic_memory_engine import strategic_memory_engine
            strategic_memory_engine.consolidate()
        except Exception:
            pass

        # Step 2: Get top lessons
        top_lessons = []
        try:
            from core.strategic_memory.lesson_registry import lesson_registry
            top_lessons = lesson_registry.top_lessons(5)
        except Exception:
            pass

        # Step 3: Propose policy updates from lessons
        from core.autonomous_improvement.policy_update_engine import policy_update_engine
        for lesson in top_lessons:
            lessons_processed += 1
            lesson_text = lesson.get("lesson", str(lesson)) if isinstance(lesson, dict) else str(lesson)
            policy_update_engine.propose_update(
                policy_name=f"lesson_policy_{lessons_processed}",
                old_value="current",
                new_value="lesson-derived",
                reason=lesson_text[:200],
                evidence_basis="strategic_memory",
            )
            policy_updates_proposed += 1

        # Step 4: Run institutional learning cycle
        try:
            from core.pccp.institutional_learning_engine import institutional_learning_engine
            institutional_learning_engine.run_cycle()
            learning_cycle_run = True
        except Exception:
            pass

        # Step 5: Start and complete a feedback cycle
        from core.autonomous_improvement.feedback_loop_engine import feedback_loop_engine
        cycle = feedback_loop_engine.start_cycle(
            trigger_event="IMPROVEMENT_ENGINE_CYCLE",
            outcome_observed=f"Processed {lessons_processed} lessons, proposed {policy_updates_proposed} policy updates",
        )
        if top_lessons:
            lesson_text = top_lessons[0].get("lesson", "") if isinstance(top_lessons[0], dict) else str(top_lessons[0])
            feedback_loop_engine.add_lesson(cycle["cycle_id"], lesson_text[:200])
        feedback_loop_engine.complete_cycle(cycle["cycle_id"])
        feedback_cycles_completed = 1

        with self._lock:
            self._cycles_run += 1
            self._last_cycle_at = time.time()
            self._total_lessons += lessons_processed
            self._total_policy_updates += policy_updates_proposed

        return {
            "lessons_processed": lessons_processed,
            "policy_updates_proposed": policy_updates_proposed,
            "learning_cycle_run": learning_cycle_run,
            "feedback_cycles_completed": feedback_cycles_completed,
            "ran_at": datetime.now(timezone.utc).isoformat(),
        }

    def improvement_status(self) -> dict:
        from core.autonomous_improvement.policy_update_engine import policy_update_engine
        with self._lock:
            return {
                "last_cycle_at": datetime.fromtimestamp(self._last_cycle_at, tz=timezone.utc).isoformat() if self._last_cycle_at else None,
                "total_cycles_run": self._cycles_run,
                "total_lessons_processed": self._total_lessons,
                "total_policy_updates": self._total_policy_updates,
                "pending_policy_applications": len(policy_update_engine.pending_updates()),
            }


improvement_engine = ImprovementEngine()
