"""
PHOENIX OBSERVATORY-X — Long-Term Recommendation Outcome Archive  [OBX-ARCHIVE-01]

The Observatory generates hundreds of recommendations per session.
This archive stores outcome records beyond the active registry's working window.

Features:
  - Stores finalized recommendation outcomes indefinitely (up to MAX_ARCHIVE)
  - Supports querying by rec_type, date range, pillar, entity
  - Provides aggregate statistics for historical analysis
  - Used by AEG as long-run evidence base

Complements RecommendationOutcomeRegistry (active tracking)
and RecommendationCemetery (failed/rejected recommendations).
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


MAX_ARCHIVE = 50_000


@dataclass
class ArchivedOutcome:
    archive_id: str
    rec_id: str
    rec_type: str
    entity_id: str
    pillar: str
    claimed_outcome: str
    actual_outcome: str
    correct: bool
    trade_count_at_resolution: int
    pnl_delta: float
    win_rate_delta: float
    archived_at: float = field(default_factory=time.time)
    original_recorded_at: float = 0.0


class LongTermRecommendationArchive:
    """
    Permanent outcome store for all verified Observatory recommendations.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: List[ArchivedOutcome] = []

    # ── Archiving ─────────────────────────────────────────────────────────────

    def archive(
        self,
        rec_id: str,
        rec_type: str,
        entity_id: str,
        pillar: str,
        claimed_outcome: str,
        actual_outcome: str,
        correct: bool,
        trade_count_at_resolution: int = 0,
        pnl_delta: float = 0.0,
        win_rate_delta: float = 0.0,
        original_recorded_at: float = 0.0,
    ) -> ArchivedOutcome:
        ao = ArchivedOutcome(
            archive_id=f"ARC-{rec_type[:4]}-{int(time.time()*1000)}",
            rec_id=rec_id,
            rec_type=rec_type,
            entity_id=entity_id,
            pillar=pillar,
            claimed_outcome=claimed_outcome,
            actual_outcome=actual_outcome,
            correct=correct,
            trade_count_at_resolution=trade_count_at_resolution,
            pnl_delta=pnl_delta,
            win_rate_delta=win_rate_delta,
            original_recorded_at=original_recorded_at or time.time(),
        )
        with self._lock:
            self._records.append(ao)
            if len(self._records) > MAX_ARCHIVE:
                self._records = self._records[-MAX_ARCHIVE:]
        return ao

    # ── Query ──────────────────────────────────────────────────────────────────

    def by_rec_type(self, rec_type: str, limit: int = 100) -> List[dict]:
        with self._lock:
            items = [r for r in self._records if r.rec_type == rec_type]
        return [self._ser(r) for r in sorted(items, key=lambda x: x.archived_at, reverse=True)[:limit]]

    def by_pillar(self, pillar: str, limit: int = 100) -> List[dict]:
        with self._lock:
            items = [r for r in self._records if r.pillar == pillar]
        return [self._ser(r) for r in sorted(items, key=lambda x: x.archived_at, reverse=True)[:limit]]

    def by_date_range(self, start_ts: float, end_ts: float, limit: int = 500) -> List[dict]:
        with self._lock:
            items = [r for r in self._records if start_ts <= r.archived_at <= end_ts]
        return [self._ser(r) for r in sorted(items, key=lambda x: x.archived_at, reverse=True)[:limit]]

    def aggregate_by_rec_type(self) -> List[dict]:
        with self._lock:
            items = list(self._records)
        groups: Dict[str, List[ArchivedOutcome]] = {}
        for r in items:
            groups.setdefault(r.rec_type, []).append(r)
        out = []
        for rt, recs in groups.items():
            correct = sum(1 for r in recs if r.correct)
            total_pnl = sum(r.pnl_delta for r in recs)
            out.append({
                "rec_type":   rt,
                "count":      len(recs),
                "correct":    correct,
                "accuracy":   round(correct / len(recs), 3) if recs else None,
                "total_pnl_delta": round(total_pnl, 4),
                "avg_pnl_delta":   round(total_pnl / len(recs), 4) if recs else 0,
            })
        return sorted(out, key=lambda x: x["accuracy"] or 0, reverse=True)

    def aggregate_by_pillar(self) -> List[dict]:
        with self._lock:
            items = list(self._records)
        groups: Dict[str, List[ArchivedOutcome]] = {}
        for r in items:
            groups.setdefault(r.pillar, []).append(r)
        out = []
        for p, recs in groups.items():
            correct = sum(1 for r in recs if r.correct)
            out.append({
                "pillar":    p,
                "count":     len(recs),
                "correct":   correct,
                "accuracy":  round(correct / len(recs), 3) if recs else None,
            })
        return out

    def summary(self) -> dict:
        with self._lock:
            total = len(self._records)
            correct = sum(1 for r in self._records if r.correct)
        return {
            "total_archived":    total,
            "total_correct":     correct,
            "overall_accuracy":  round(correct / total, 3) if total else None,
            "max_archive":       MAX_ARCHIVE,
            "capacity_pct":      round(total / MAX_ARCHIVE * 100, 1) if total else 0,
        }

    @staticmethod
    def _ser(r: ArchivedOutcome) -> dict:
        return {
            "archive_id":                r.archive_id,
            "rec_id":                    r.rec_id,
            "rec_type":                  r.rec_type,
            "entity_id":                 r.entity_id,
            "pillar":                    r.pillar,
            "claimed_outcome":           r.claimed_outcome,
            "actual_outcome":            r.actual_outcome,
            "correct":                   r.correct,
            "trade_count_at_resolution": r.trade_count_at_resolution,
            "pnl_delta":                 r.pnl_delta,
            "win_rate_delta":            r.win_rate_delta,
            "archived_at":               r.archived_at,
            "original_recorded_at":      r.original_recorded_at,
        }


# Singleton
long_term_archive = LongTermRecommendationArchive()
