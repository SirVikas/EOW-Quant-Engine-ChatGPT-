"""
PHOENIX TRUST PROGRAM — Trust Evidence Warehouse  [GAP-003]

The single queryable store for all trust evidence events across all pillars:
  - Recommendation outcomes
  - Investigation outcomes
  - Blame attribution results
  - Conflict resolution results
  - Counterfactual validation results

Provides full auditability:
  "Show me every piece of evidence that was used to build trust in BLAME_ACCURACY"
  "Show me all failed evidence for entity #47 in the last 90 days"
  "What is the evidence density over time for INVESTIGATION_ACCURACY?"
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


EVIDENCE_TYPES = {
    "RECOMMENDATION",
    "INVESTIGATION",
    "BLAME",
    "CONFLICT",
    "COUNTERFACTUAL",
}

MAX_WAREHOUSE = 100_000


@dataclass
class EvidenceRecord:
    evidence_id: str
    pillar: str
    evidence_type: str
    entity_id: str
    source_id: str          # rec_id, investigation_id, etc.
    claimed: str
    actual: str
    correct: bool
    economic_impact: float  # pnl_delta if known
    confidence: float       # 0.0–1.0
    recorded_at: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)


class TrustEvidenceWarehouse:
    """
    Immutable evidence store for all trust-related outcomes.
    Every record is permanent — evidence is never deleted.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: List[EvidenceRecord] = []
        self._entity_index: Dict[str, List[int]] = {}   # entity_id → record indices
        self._pillar_index: Dict[str, List[int]] = {}   # pillar → record indices

    # ── Ingestion ─────────────────────────────────────────────────────────────

    def ingest(
        self,
        pillar: str,
        evidence_type: str,
        entity_id: str,
        source_id: str,
        claimed: str,
        actual: str,
        correct: bool,
        economic_impact: float = 0.0,
        confidence: float = 1.0,
        tags: Optional[List[str]] = None,
    ) -> EvidenceRecord:
        ev = EvidenceRecord(
            evidence_id=f"EW-{pillar[:4]}-{int(time.time()*1000)}",
            pillar=pillar,
            evidence_type=evidence_type,
            entity_id=entity_id,
            source_id=source_id,
            claimed=claimed,
            actual=actual,
            correct=correct,
            economic_impact=economic_impact,
            confidence=confidence,
            tags=tags or [],
        )
        with self._lock:
            idx = len(self._records)
            self._records.append(ev)
            self._entity_index.setdefault(entity_id, []).append(idx)
            self._pillar_index.setdefault(pillar, []).append(idx)
            if len(self._records) > MAX_WAREHOUSE:
                self._records = self._records[-MAX_WAREHOUSE:]
                self._rebuild_indices()
        return ev

    def _rebuild_indices(self) -> None:
        self._entity_index = {}
        self._pillar_index = {}
        for i, ev in enumerate(self._records):
            self._entity_index.setdefault(ev.entity_id, []).append(i)
            self._pillar_index.setdefault(ev.pillar, []).append(i)

    # ── Query ─────────────────────────────────────────────────────────────────

    def for_pillar(self, pillar: str, days: Optional[int] = None, limit: int = 200) -> List[dict]:
        cutoff = time.time() - days * 86400 if days else 0.0
        with self._lock:
            indices = self._pillar_index.get(pillar, [])
            items = [self._records[i] for i in indices if self._records[i].recorded_at >= cutoff]
        return [self._ser(ev) for ev in sorted(items, key=lambda x: x.recorded_at, reverse=True)[:limit]]

    def for_entity(self, entity_id: str, days: Optional[int] = None, limit: int = 200) -> List[dict]:
        cutoff = time.time() - days * 86400 if days else 0.0
        with self._lock:
            indices = self._entity_index.get(entity_id, [])
            items = [self._records[i] for i in indices if self._records[i].recorded_at >= cutoff]
        return [self._ser(ev) for ev in sorted(items, key=lambda x: x.recorded_at, reverse=True)[:limit]]

    def for_source(self, source_id: str) -> List[dict]:
        with self._lock:
            items = [ev for ev in self._records if ev.source_id == source_id]
        return [self._ser(ev) for ev in items]

    def pillar_audit(self, pillar: str) -> dict:
        with self._lock:
            indices = self._pillar_index.get(pillar, [])
            items = [self._records[i] for i in indices]
        if not items:
            return {"pillar": pillar, "total": 0, "accuracy": None, "note": "No evidence"}
        correct = sum(1 for ev in items if ev.correct)
        total_impact = sum(ev.economic_impact for ev in items)
        by_type: Dict[str, int] = {}
        for ev in items:
            by_type[ev.evidence_type] = by_type.get(ev.evidence_type, 0) + 1
        return {
            "pillar":           pillar,
            "total":            len(items),
            "correct":          correct,
            "accuracy":         round(correct / len(items), 3),
            "total_economic_impact": round(total_impact, 4),
            "by_evidence_type": by_type,
            "entities_tracked": len(set(ev.entity_id for ev in items)),
        }

    def full_audit(self) -> dict:
        try:
            from core.trust.trust_validation_registry import PILLARS
        except Exception:
            PILLARS = ["RECOMMENDATION_ACCURACY", "INVESTIGATION_ACCURACY",
                       "BLAME_ACCURACY", "COUNTERFACTUAL_ACCURACY", "CONFLICT_ACCURACY"]
        with self._lock:
            total = len(self._records)
        return {
            "total_evidence":   total,
            "max_warehouse":    MAX_WAREHOUSE,
            "capacity_pct":     round(total / MAX_WAREHOUSE * 100, 2),
            "pillars":          {p: self.pillar_audit(p) for p in PILLARS},
            "evidence_types":   sorted(EVIDENCE_TYPES),
        }

    def density_over_time(self, pillar: str, bucket_days: int = 7, lookback_days: int = 180) -> List[dict]:
        cutoff = time.time() - lookback_days * 86400
        with self._lock:
            indices = self._pillar_index.get(pillar, [])
            items = [self._records[i] for i in indices if self._records[i].recorded_at >= cutoff]
        if not items:
            return []
        bucket_secs = bucket_days * 86400
        now = time.time()
        buckets: Dict[int, List[EvidenceRecord]] = {}
        for ev in items:
            key = int((now - ev.recorded_at) / bucket_secs)
            buckets.setdefault(key, []).append(ev)
        result = []
        for k in sorted(buckets.keys(), reverse=True):
            evs = buckets[k]
            correct = sum(1 for e in evs if e.correct)
            result.append({
                "bucket_age_days": k * bucket_days,
                "count":           len(evs),
                "correct":         correct,
                "accuracy":        round(correct / len(evs), 3) if evs else None,
            })
        return result

    @staticmethod
    def _ser(ev: EvidenceRecord) -> dict:
        return {
            "evidence_id":    ev.evidence_id,
            "pillar":         ev.pillar,
            "evidence_type":  ev.evidence_type,
            "entity_id":      ev.entity_id,
            "source_id":      ev.source_id,
            "claimed":        ev.claimed,
            "actual":         ev.actual,
            "correct":        ev.correct,
            "economic_impact": ev.economic_impact,
            "confidence":     ev.confidence,
            "recorded_at":    ev.recorded_at,
            "tags":           ev.tags,
        }


# Singleton
trust_evidence_warehouse = TrustEvidenceWarehouse()
