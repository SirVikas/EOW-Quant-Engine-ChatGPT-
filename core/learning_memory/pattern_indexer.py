"""
FTD-030B — pattern_indexer.py
Builds and maintains the in-memory pattern lookup index.

Loaded from memory_store.jsonl at startup.
Rebuilt automatically; provides O(1) pattern lookup by key.
The serialised index is written to pattern_index.json for diagnostics.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any, Dict, List, Optional

from core.learning_memory.pattern_engine import Pattern, PatternEngine
from core.learning_memory.confidence_updater import compute_confidence

INDEX_PATH = pathlib.Path("reports/learning_memory/pattern_index.json")


class PatternIndexer:
    """
    Startup loader + in-memory index for patterns.
    Delegates all mutation to PatternEngine; this class only handles
    persistence of the index and fast lookups.
    """

    def __init__(self, engine: PatternEngine, index_path: pathlib.Path = INDEX_PATH):
        self._engine     = engine
        self._index_path = index_path
        self._index_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Public API ────────────────────────────────────────────────────────────

    def build_from_records(self, records: list) -> int:
        """
        Rebuild pattern index from a list of MemoryRecord objects.
        Called once at startup after MemoryStore is loaded.
        Returns the number of valid patterns found.
        """
        for record in records:
            pat = self._engine.update(record, confidence_fn=compute_confidence)
        valid_count = len(self._engine.valid_patterns())
        self.flush_index()
        return valid_count

    def lookup(self, regime: str, volatility: str, instrument: str,
               parameter: str, direction: str) -> Optional[Pattern]:
        """Fast O(1) lookup for a specific pattern key."""
        key = f"{regime}:{volatility}:{instrument}:{parameter}:{direction}"
        return self._engine.get(key)

    def flush_index(self) -> None:
        """Write current valid patterns to pattern_index.json."""
        try:
            data = {
                "valid_count":  len(self._engine.valid_patterns()),
                "total_count":  len(self._engine.all_patterns()),
                "patterns":     [p.to_dict() for p in self._engine.valid_patterns()],
            }
            self._index_path.write_text(
                json.dumps(data, indent=2, default=str), encoding="utf-8"
            )
        except Exception:
            pass

    def valid_patterns(self) -> List[Pattern]:
        return self._engine.valid_patterns()

    def summary(self) -> Dict[str, Any]:
        return {
            "valid_patterns": len(self._engine.valid_patterns()),
            "total_patterns": len(self._engine.all_patterns()),
            "index_path":     str(self._index_path),
            "module": "PATTERN_INDEXER",
            "phase":  "030B",
        }
