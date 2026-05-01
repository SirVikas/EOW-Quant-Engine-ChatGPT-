"""
FTD-030B — Negative Memory (Q13-C blacklist + confidence penalty)

Rules (spec §PART 7):
  - rollback → blacklist entry
  - 3 rollbacks on same pattern → permanent ban
  - decay: 0.90^age (faster than positive memory)
  - Blacklisted patterns are NEVER applied by MemoryApplier
"""
from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Dict, Optional

ROLLBACK_BAN_THRESHOLD = 3       # 3 rollbacks = permanent ban
NEGATIVE_DECAY_BASE    = 0.90    # per-day decay (faster than positive 0.95)
NEGATIVE_PURGE_WEIGHT  = 0.10    # purge when weight < 0.10


@dataclass
class NegativeRecord:
    pattern_id:    str
    rollback_count: int
    permanently_banned: bool
    first_rollback_ts: int
    last_rollback_ts:  int
    decay_weight:      float = 1.0


class NegativeMemory:
    """
    Tracks rollback patterns and enforces permanent bans after ROLLBACK_BAN_THRESHOLD.
    """

    def __init__(self):
        self._records: Dict[str, NegativeRecord] = {}

    # ── API ──────────────────────────────────────────────────────────────────

    def record_rollback(self, pattern_id: str) -> NegativeRecord:
        """Record a rollback for the given pattern. Returns updated record."""
        now = int(time.time() * 1000)
        if pattern_id in self._records:
            r = self._records[pattern_id]
            if r.permanently_banned:
                return r   # already banned; no change
            r.rollback_count    += 1
            r.last_rollback_ts   = now
            r.decay_weight       = 1.0  # reset weight on new rollback
            r.permanently_banned = r.rollback_count >= ROLLBACK_BAN_THRESHOLD
        else:
            self._records[pattern_id] = NegativeRecord(
                pattern_id=pattern_id,
                rollback_count=1,
                permanently_banned=False,
                first_rollback_ts=now,
                last_rollback_ts=now,
                decay_weight=1.0,
            )
        return self._records[pattern_id]

    def is_banned(self, pattern_id: str) -> bool:
        """True if pattern is permanently banned OR still has active negative weight."""
        r = self._records.get(pattern_id)
        if r is None:
            return False
        if r.permanently_banned:
            return True
        return r.decay_weight >= NEGATIVE_PURGE_WEIGHT

    def is_permanently_banned(self, pattern_id: str) -> bool:
        r = self._records.get(pattern_id)
        return r is not None and r.permanently_banned

    def apply_decay(self) -> int:
        """Apply 0.90^age decay, purge non-banned entries below threshold. Returns purge count."""
        now_ms = int(time.time() * 1000)
        to_purge = []
        for pid, r in self._records.items():
            if r.permanently_banned:
                continue  # permanent bans never decay
            age_days = (now_ms - r.last_rollback_ts) / (1000.0 * 86400.0)
            r.decay_weight *= NEGATIVE_DECAY_BASE ** age_days
            if r.decay_weight < NEGATIVE_PURGE_WEIGHT:
                to_purge.append(pid)
        for pid in to_purge:
            del self._records[pid]
        return len(to_purge)

    def rollback_count(self, pattern_id: str) -> int:
        r = self._records.get(pattern_id)
        return r.rollback_count if r else 0

    def summary(self) -> Dict[str, object]:
        banned = [pid for pid, r in self._records.items() if r.permanently_banned]
        active = [pid for pid, r in self._records.items() if not r.permanently_banned]
        return {
            "total_negative": len(self._records),
            "permanently_banned": len(banned),
            "active_negative": len(active),
            "banned_patterns": banned,
        }

    def all_records(self) -> Dict[str, NegativeRecord]:
        return dict(self._records)
