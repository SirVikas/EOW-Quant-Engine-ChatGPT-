"""
FTD-030B Part 7 — Negative Memory

Blacklists patterns that lead to rollbacks.
Rules:
  - Any rollback → add pattern key to blacklist
  - 3 rollbacks for same key → permanent ban (no decay)
  - Temporary blacklist entries decay: 0.90 ^ age (cycle-based)
  - Decayed below threshold → removed from blacklist
"""
from __future__ import annotations
import json
import os
import time
from typing import Any, Dict, Tuple

NEGATIVE_STORE_PATH   = "reports/learning_memory/negative_memory.jsonl"
DECAY_RATE            = 0.90
PERMANENT_BAN_AFTER   = 3      # rollbacks before permanent ban
TEMP_REMOVAL_THRESHOLD = 0.10  # remove temporary entry when score < this


class NegativeMemory:

    MODULE = "NEGATIVE_MEMORY"
    PHASE  = "030B"

    def __init__(self, path: str = NEGATIVE_STORE_PATH):
        self._path    = path
        self._entries: Dict[str, Dict[str, Any]] = {}   # key_str → entry
        self._cycle:  int = 0
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._load()

    # ── Public API ────────────────────────────────────────────────────────────

    def record_rollback(self, key_tuple: tuple) -> None:
        """Record a rollback for the given pattern key."""
        key_str = self._key_str(key_tuple)
        entry   = self._entries.get(key_str)
        if entry is None:
            entry = {
                "key_str":    key_str,
                "rollbacks":  0,
                "permanent":  False,
                "score":      1.0,
                "last_cycle": self._cycle,
                "created_at": time.time(),
            }
            self._entries[key_str] = entry

        entry["rollbacks"]  += 1
        entry["last_cycle"]  = self._cycle
        entry["score"]       = 1.0   # reset decay on new rollback

        if entry["rollbacks"] >= PERMANENT_BAN_AFTER:
            entry["permanent"] = True

        self._persist(entry)

    def is_banned(self, key_tuple: tuple) -> bool:
        key_str = self._key_str(key_tuple)
        entry   = self._entries.get(key_str)
        if entry is None:
            return False
        if entry["permanent"]:
            return True
        return entry["score"] >= TEMP_REMOVAL_THRESHOLD

    def advance_cycle(self) -> None:
        """Age all temporary entries by one cycle."""
        self._cycle += 1
        to_remove = []
        for ks, entry in self._entries.items():
            if not entry["permanent"]:
                age          = self._cycle - entry.get("last_cycle", self._cycle)
                entry["score"] = DECAY_RATE ** age
                if entry["score"] < TEMP_REMOVAL_THRESHOLD:
                    to_remove.append(ks)
        for ks in to_remove:
            del self._entries[ks]

    def count(self) -> Dict[str, int]:
        permanent = sum(1 for e in self._entries.values() if e["permanent"])
        temporary = len(self._entries) - permanent
        return {"permanent": permanent, "temporary": temporary, "total": len(self._entries)}

    def to_list(self) -> list:
        return list(self._entries.values())

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _key_str(key_tuple: tuple) -> str:
        return "|".join(str(k) for k in key_tuple)

    def _load(self) -> None:
        if not os.path.exists(self._path):
            return
        with open(self._path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    self._entries[entry["key_str"]] = entry
                except (json.JSONDecodeError, KeyError):
                    continue

    def _persist(self, entry: Dict[str, Any]) -> None:
        with open(self._path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
