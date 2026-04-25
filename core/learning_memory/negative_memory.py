"""
FTD-030B — negative_memory.py
Blacklist store for patterns that caused rollbacks.

Rules:
  - 1 rollback  → blacklisted (with decay: 0.90^age)
  - 3 rollbacks → permanently banned (no decay, no rehabilitation)
  - Blacklisted (non-permanent) entries decay and can be rehabilitated after ~22 cycles
"""
from __future__ import annotations

import json
import pathlib
import time
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List

NEGATIVE_PATH        = pathlib.Path("reports/learning_memory/negative_memory.jsonl")
PERMANENT_BAN_COUNT  = 3      # rollbacks in distinct cycles before permanent ban
BLACKLIST_DECAY      = 0.90   # per-cycle weight decay for non-permanent entries


@dataclass
class NegativeEntry:
    pattern_id:     str
    rollback_count: int   = 1
    permanent:      bool  = False
    weight:         float = 1.0   # starts at 1.0, decays over cycles
    first_seen:     float = field(default_factory=time.time)
    last_rollback:  float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class NegativeMemory:
    """
    Manages blacklisted patterns that have caused rollbacks.
    Provides fast O(1) lookup for is_blacklisted() checks.
    """

    def __init__(self, path: pathlib.Path = NEGATIVE_PATH):
        self._path:    pathlib.Path = path
        self._entries: Dict[str, NegativeEntry] = {}
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    # ── Public API ────────────────────────────────────────────────────────────

    def record_rollback(self, pattern_id: str) -> NegativeEntry:
        """Record a rollback for this pattern. Promotes to permanent if threshold reached."""
        entry = self._entries.get(pattern_id)
        if entry is None:
            entry = NegativeEntry(pattern_id=pattern_id)
            self._entries[pattern_id] = entry
        else:
            entry.rollback_count  += 1
            entry.last_rollback    = time.time()
            entry.weight           = 1.0   # reset weight on new rollback

        if entry.rollback_count >= PERMANENT_BAN_COUNT:
            entry.permanent = True

        self._append_to_disk(entry)
        return entry

    def is_blacklisted(self, pattern_id: str) -> bool:
        """Returns True if the pattern is blacklisted (permanent or active weight > 0.1)."""
        entry = self._entries.get(pattern_id)
        if entry is None:
            return False
        if entry.permanent:
            return True
        return entry.weight > 0.1   # not yet rehabilitated

    def is_permanently_banned(self, pattern_id: str) -> bool:
        entry = self._entries.get(pattern_id)
        return entry is not None and entry.permanent

    def decay_cycle(self) -> List[str]:
        """Apply one cycle of weight decay. Returns list of rehabilitated pattern IDs."""
        rehabilitated: List[str] = []
        for pid, entry in self._entries.items():
            if not entry.permanent:
                entry.weight = round(entry.weight * BLACKLIST_DECAY, 4)
                if entry.weight <= 0.1:
                    rehabilitated.append(pid)
        return rehabilitated

    def all_entries(self) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self._entries.values()]

    def permanent_count(self) -> int:
        return sum(1 for e in self._entries.values() if e.permanent)

    def blacklisted_count(self) -> int:
        return sum(1 for pid in self._entries if self.is_blacklisted(pid))

    # ── Internal ──────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if not self._path.exists():
            return
        seen: Dict[str, NegativeEntry] = {}
        for line in self._path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                pid = d.get("pattern_id")
                if not pid:
                    continue
                # Keep latest entry per pattern_id
                seen[pid] = NegativeEntry(**{k: v for k, v in d.items()
                                             if k in NegativeEntry.__dataclass_fields__})
            except Exception:
                pass
        self._entries = seen

    def _append_to_disk(self, entry: NegativeEntry) -> None:
        try:
            with self._path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry.to_dict(), default=str) + "\n")
        except Exception:
            pass

    def summary(self) -> Dict[str, Any]:
        return {
            "total_entries":     len(self._entries),
            "blacklisted":       self.blacklisted_count(),
            "permanently_banned": self.permanent_count(),
            "module": "NEGATIVE_MEMORY",
            "phase":  "030B",
        }
