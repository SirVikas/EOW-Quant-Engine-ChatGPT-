"""
FTD-030B — Pattern Indexer (spec §PART 8)

Builds in-memory lookup index from the JSONL store on startup.
Provides O(1) access to pattern metadata by pattern_id.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from core.memory.memory_store import MemoryStore
from core.memory.pattern_detector import PatternDetector, Pattern


class PatternIndexer:
    """
    Maintains an in-memory index of patterns built from the JSONL store.
    Rebuilt on startup and refreshed on each index() call.
    """

    def __init__(self, store: MemoryStore, detector: PatternDetector):
        self._store    = store
        self._detector = detector
        self._index:   Dict[str, Pattern] = {}
        self.rebuild()

    def rebuild(self) -> int:
        """Rebuild index from all store entries. Returns pattern count."""
        self._index = self._detector.detect(self._store.all_entries())
        return len(self._index)

    def lookup(self, pattern_id: str) -> Optional[Pattern]:
        """O(1) lookup by pattern_id."""
        return self._index.get(pattern_id)

    def all_patterns(self) -> Dict[str, Pattern]:
        return dict(self._index)

    def validated_patterns(self) -> Dict[str, Pattern]:
        return {pid: p for pid, p in self._index.items() if p.validated}

    def search(
        self,
        regime:    Optional[str] = None,
        parameter: Optional[str] = None,
        direction: Optional[str] = None,
        min_confidence: float = 0.0,
    ) -> List[Pattern]:
        """Filter patterns by optional criteria."""
        results = []
        for p in self._index.values():
            if regime and p.regime != regime:
                continue
            if parameter and p.parameter != parameter:
                continue
            if direction and p.direction != direction:
                continue
            if p.confidence < min_confidence:
                continue
            results.append(p)
        return sorted(results, key=lambda x: x.confidence, reverse=True)

    def top_n(self, n: int = 10) -> List[Pattern]:
        """Return top-N patterns by confidence."""
        return sorted(self._index.values(), key=lambda x: x.confidence, reverse=True)[:n]

    def summary(self) -> Dict[str, Any]:
        validated = self.validated_patterns()
        return {
            "total_indexed":    len(self._index),
            "validated":        len(validated),
            "parameters":       list({p.parameter for p in self._index.values()}),
            "regimes":          list({p.regime for p in self._index.values()}),
            "top_pattern":      max(
                (p.pattern_id for p in self._index.values()),
                key=lambda pid: self._index[pid].confidence,
                default=None,
            ),
        }
