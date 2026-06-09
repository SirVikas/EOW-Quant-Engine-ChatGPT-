"""Institutional Memory Engine — unified interface for long-term institutional memory."""
import threading
from datetime import datetime, timezone


class InstitutionalMemoryEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def memory_report(self) -> dict:
        with self._lock:
            from core.institutional_memory.long_term_lesson_archive import long_term_lesson_archive
            from core.institutional_memory.institutional_wisdom_registry import institutional_wisdom_registry
            from core.institutional_memory.memory_consolidation_engine import memory_consolidation_engine

            archive_stats = long_term_lesson_archive.archive_stats()
            wisdom_stats = institutional_wisdom_registry.wisdom_stats()
            consolidation_status = memory_consolidation_engine.consolidation_status()

            memory_health_score = min(100,
                archive_stats["total"] * 0.5 + wisdom_stats["canonical"] * 5)

            return {
                "archive_stats": archive_stats,
                "wisdom_stats": wisdom_stats,
                "consolidation_status": consolidation_status,
                "memory_health_score": memory_health_score,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

    def recall(self, query: str) -> dict:
        with self._lock:
            from core.institutional_memory.long_term_lesson_archive import long_term_lesson_archive
            from core.institutional_memory.institutional_wisdom_registry import institutional_wisdom_registry

            lessons = long_term_lesson_archive.search(query)
            wisdom = []
            for w in institutional_wisdom_registry.all_wisdom():
                if query.lower() in w["principle"].lower() or query.lower() in w["domain"].lower():
                    wisdom.append(w)

            return {
                "query": query,
                "lessons_found": lessons,
                "wisdom_found": wisdom,
                "total_results": len(lessons) + len(wisdom),
            }

    def preserve_moment(self, title: str, content: str, source_type: str,
                        importance: float = 5) -> str:
        with self._lock:
            from core.institutional_memory.long_term_lesson_archive import long_term_lesson_archive
            return long_term_lesson_archive.archive(
                title=title,
                content=content,
                source_type=source_type,
                importance=importance,
            )


institutional_memory_engine = InstitutionalMemoryEngine()
