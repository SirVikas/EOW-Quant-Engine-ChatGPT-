"""
FTD-030B Part 8 — Pattern Indexer

Builds an in-memory lookup index from the JSONL memory store at startup.
Maintains real-time index updates as new records arrive.
"""
from __future__ import annotations
import json
import os
from typing import Any, Dict, List, Optional, Tuple

from core.learning_memory.memory_store   import MemoryStore
from core.learning_memory.pattern_engine import PatternEngine, PatternKey

INDEX_PATH = "reports/learning_memory/pattern_index.json"


class PatternIndexer:

    MODULE = "PATTERN_INDEXER"
    PHASE  = "030B"

    def __init__(self, store: MemoryStore, engine: PatternEngine):
        self._store  = store
        self._engine = engine

    def build_from_store(self) -> int:
        """
        Load all records from JSONL and feed into pattern engine.
        Called once at startup. Returns count of records processed.
        """
        records = self._store.load_all()
        for r in records:
            self._engine.ingest(r)
        self._save_index()
        return len(records)

    def ingest_record(self, record: Dict[str, Any]) -> None:
        """Feed a new record into the live index."""
        self._engine.ingest(record)
        self._save_index()

    def lookup(self, key: PatternKey) -> Optional[Dict[str, Any]]:
        pat = self._engine.get_pattern(key)
        if pat is None:
            return None
        return pat.to_dict()

    def formed_count(self) -> int:
        return len(self._engine.formed_patterns())

    def _save_index(self) -> None:
        os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
        data = {
            "total_patterns": len(self._engine.all_patterns()),
            "formed_patterns": self.formed_count(),
            "patterns": [p.to_dict() for p in self._engine.formed_patterns()],
        }
        with open(INDEX_PATH, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, default=str)
