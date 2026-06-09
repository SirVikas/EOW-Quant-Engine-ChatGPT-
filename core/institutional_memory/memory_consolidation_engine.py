"""Memory Consolidation Engine — pulls knowledge from multiple sources into long-term archive."""
import threading
from datetime import datetime, timezone
from typing import Optional


class MemoryConsolidationEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._last_consolidated_at: Optional[str] = None

    def consolidate(self) -> dict:
        with self._lock:
            from core.institutional_memory.long_term_lesson_archive import long_term_lesson_archive
            from core.institutional_memory.institutional_wisdom_registry import institutional_wisdom_registry

            archived_count = 0
            wisdom_promoted = 0
            sources_consolidated = []

            # Pull from strategic_memory lesson registry
            try:
                from core.strategic_memory.lesson_registry import lesson_registry
                lessons = lesson_registry.top_lessons(20)
                for lesson in lessons:
                    long_term_lesson_archive.archive(
                        title=lesson.get("title", "Strategic Lesson"),
                        content=lesson.get("content", ""),
                        source_type="SUCCESS",
                        importance=lesson.get("importance", 5),
                    )
                    archived_count += 1
                sources_consolidated.append("strategic_memory")
            except Exception:
                pass

            # Pull from ct_knowledge_vault
            try:
                from core.ctao.ct_knowledge_vault import ct_knowledge_vault
                lessons = ct_knowledge_vault.top_lessons(10)
                for lesson in lessons:
                    long_term_lesson_archive.archive(
                        title=lesson.get("title", "CT Lesson"),
                        content=lesson.get("content", ""),
                        source_type="EVOLUTION",
                        importance=lesson.get("importance", 5),
                    )
                    archived_count += 1
                sources_consolidated.append("ct_knowledge_vault")
            except Exception:
                pass

            # Promote high-confidence archive lessons to wisdom
            stats = long_term_lesson_archive.archive_stats()
            top = long_term_lesson_archive.most_accessed(10)
            for lesson in top:
                if lesson.get("importance", 0) >= 8:
                    institutional_wisdom_registry.record(
                        principle=lesson["title"],
                        domain=lesson.get("source_type", "GENERAL"),
                        confidence=min(1.0, lesson["importance"] / 10.0),
                    )
                    wisdom_promoted += 1

            self._last_consolidated_at = datetime.now(timezone.utc).isoformat()
            return {
                "archived_count": archived_count,
                "wisdom_promoted": wisdom_promoted,
                "sources_consolidated": sources_consolidated,
                "consolidated_at": self._last_consolidated_at,
            }

    def consolidation_status(self) -> dict:
        with self._lock:
            from core.institutional_memory.long_term_lesson_archive import long_term_lesson_archive
            from core.institutional_memory.institutional_wisdom_registry import institutional_wisdom_registry
            return {
                "last_consolidated_at": self._last_consolidated_at,
                "total_archived": long_term_lesson_archive.archive_stats()["total"],
                "total_wisdom": institutional_wisdom_registry.wisdom_stats()["total"],
            }


memory_consolidation_engine = MemoryConsolidationEngine()
