"""Strategic Memory Engine — Consolidates institutional patterns into lessons."""
import threading
import time


class StrategicMemoryEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._last_extraction_run: float = 0.0

    def consolidate(self) -> dict:
        from core.strategic_memory.pattern_extractor import pattern_extractor
        total = pattern_extractor.run_full_extraction()
        self._last_extraction_run = time.time()
        return {"status": "ok", "lessons_extracted": total, "run_at": self._last_extraction_run}

    def institutional_memory_report(self) -> dict:
        from core.strategic_memory.lesson_registry import lesson_registry
        from core.strategic_memory.repeat_failure_tracker import repeat_failure_tracker

        all_lessons = lesson_registry.all_lessons()
        validated = [l for l in all_lessons if l["validated"]]
        top = lesson_registry.top_lessons()
        chronic = repeat_failure_tracker.chronic_failures()
        top_failures = repeat_failure_tracker.most_repeated()

        return {
            "total_lessons": len(all_lessons),
            "validated_lessons": len(validated),
            "chronic_failures": len(chronic),
            "top_lessons": top,
            "top_failures": top_failures,
            "extraction_last_run": self._last_extraction_run,
            "generated_at": time.time(),
        }

    def memory_status(self) -> dict:
        from core.strategic_memory.lesson_registry import lesson_registry
        from core.strategic_memory.repeat_failure_tracker import repeat_failure_tracker

        all_lessons = lesson_registry.all_lessons()
        stats = repeat_failure_tracker.failure_stats()
        avg_conf = (
            sum(l["confidence"] for l in all_lessons) / len(all_lessons)
            if all_lessons else 0.0
        )
        return {
            "lesson_count": len(all_lessons),
            "failure_types": stats["total_types"],
            "confidence_avg": round(avg_conf, 4),
        }


strategic_memory_engine = StrategicMemoryEngine()
