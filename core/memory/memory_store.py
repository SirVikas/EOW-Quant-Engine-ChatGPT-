"""
FTD-030B — Memory Store
Append-only JSONL persistent store for correction memory entries (Q16-A, Q1-G ALL).

Rules (spec §PART 1):
  - Append-only JSONL (one JSON object per line)
  - Partial record = REJECT
  - Stored after resolve_cycle()
"""
from __future__ import annotations
import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

MEMORY_LOG_PATH = "reports/memory/memory_store.jsonl"


@dataclass
class MemoryEntry:
    entry_id:         str
    ts:               int
    # Context (Q3-E ALL normalized)
    market_regime:    str
    volatility:       float
    symbol:           str
    # Correction details (Q1-A)
    change_id:        str
    parameter:        str
    delta_pct:        float
    direction:        str           # "UP" | "DOWN"
    value_before:     float
    value_after:      float
    # Outcome (Q1-B)
    pnl_delta:        float
    score_delta:      float
    rolled_back:      bool
    rollback_trigger: Optional[str]
    # Decision trace (Q1-D)
    rationale:        str
    confidence:       float
    # Derived
    outcome_score:    float         # +1.0 success, -1.0 failure, 0.0 neutral
    decay_weight:     float = 1.0


class MemoryStore:
    """Append-only JSONL store. Each new entry is a single appended line."""

    def __init__(self, path: str = MEMORY_LOG_PATH):
        self._path    = path
        self._entries: List[MemoryEntry] = []
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._load()

    # ── Write ────────────────────────────────────────────────────────────────

    def append(self, entry: MemoryEntry) -> None:
        """Validate completeness then append as a single JSONL line."""
        self._validate(entry)
        self._entries.append(entry)
        with open(self._path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(entry)) + "\n")

    def update_weights(self, updates: Dict[str, float]) -> None:
        for e in self._entries:
            if e.entry_id in updates:
                e.decay_weight = max(0.0, updates[e.entry_id])
        self._rewrite()

    def purge_below_weight(self, threshold: float = 0.25) -> int:
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.decay_weight >= threshold]
        if len(self._entries) < before:
            self._rewrite()
        return before - len(self._entries)

    def clear(self) -> None:
        self._entries.clear()
        self._rewrite()

    # ── Read ─────────────────────────────────────────────────────────────────

    def all_entries(self) -> List[MemoryEntry]:
        return list(self._entries)

    def recent(self, n: int) -> List[MemoryEntry]:
        return self._entries[-n:]

    def count(self) -> int:
        return len(self._entries)

    # ── Persistence ───────────────────────────────────────────────────────────

    def _rewrite(self) -> None:
        """Full rewrite used after purge / weight update."""
        with open(self._path, "w", encoding="utf-8") as fh:
            for e in self._entries:
                fh.write(json.dumps(asdict(e)) + "\n")

    def _load(self) -> None:
        if not os.path.exists(self._path):
            return
        try:
            with open(self._path, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        self._entries.append(MemoryEntry(**json.loads(line)))
        except Exception:
            self._entries = []

    @staticmethod
    def _validate(entry: MemoryEntry) -> None:
        """Reject partial records (spec: partial record = REJECT)."""
        required = [
            entry.entry_id, entry.parameter, entry.direction,
            entry.change_id, entry.market_regime,
        ]
        if not all(required):
            raise ValueError(f"[MEMORY-STORE] Partial record rejected: {entry.entry_id}")
