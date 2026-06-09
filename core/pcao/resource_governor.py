"""
PHOENIX PCAO — Resource Governor  [GAP-014]

Tracks capacity allocation across PHOENIX subsystems:
  - Developer Capacity (human engineering hours)
  - System Capacity (CPU / memory intensive modules)
  - Research Capacity (evidence accumulation rate)

Answers:
  - "Which subsystem has the most work queued vs capacity?"
  - "Is the research pipeline producing evidence fast enough for trust promotion?"
  - "Where should the next sprint be focused?"

All allocations are advisory at v0.1.0.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


CAPACITY_TYPES = ["DEVELOPER", "SYSTEM", "RESEARCH"]

SUBSYSTEMS = [
    "KGE", "HKE", "AEG", "PCAO",
    "OBSERVATORY_X", "CORTEX", "PTP",
    "TRUTH_ENGINE", "NEXUS",
]


@dataclass
class CapacityRecord:
    subsystem: str
    capacity_type: str
    allocated: float       # 0–100%
    consumed: float        # 0–100%
    queued_work: int       # number of open tasks/objectives
    recorded_at: float = field(default_factory=time.time)
    note: str = ""


class ResourceGovernor:
    """
    PCAO resource allocation tracking and advisory capacity planning.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: Dict[str, CapacityRecord] = {}    # f"{subsystem}:{type}" → record
        self._history: List[CapacityRecord] = []
        self._seed_initial_state()

    def _seed_initial_state(self) -> None:
        initial = {
            "KGE":           (0, 0, 3),
            "HKE":           (0, 0, 2),
            "AEG":           (30, 20, 5),
            "PCAO":          (20, 10, 4),
            "OBSERVATORY_X": (10, 5, 0),
            "CORTEX":        (10, 5, 0),
            "PTP":           (20, 15, 2),
            "TRUTH_ENGINE":  (5, 5, 1),
            "NEXUS":         (5, 3, 0),
        }
        for sub, (alloc, consumed, queued) in initial.items():
            r = CapacityRecord(
                subsystem=sub,
                capacity_type="DEVELOPER",
                allocated=alloc,
                consumed=consumed,
                queued_work=queued,
                note="Initial seed",
            )
            self._records[f"{sub}:DEVELOPER"] = r

    # ── Allocation Management ─────────────────────────────────────────────────

    def set_allocation(
        self,
        subsystem: str,
        capacity_type: str,
        allocated: float,
        consumed: float,
        queued_work: int = 0,
        note: str = "",
    ) -> CapacityRecord:
        key = f"{subsystem}:{capacity_type}"
        r = CapacityRecord(
            subsystem=subsystem,
            capacity_type=capacity_type,
            allocated=min(100.0, max(0.0, allocated)),
            consumed=min(100.0, max(0.0, consumed)),
            queued_work=queued_work,
            note=note,
        )
        with self._lock:
            self._records[key] = r
            self._history.append(r)
            if len(self._history) > 5000:
                self._history = self._history[-5000:]
        return r

    # ── Query ─────────────────────────────────────────────────────────────────

    def allocation_for(self, subsystem: str) -> List[dict]:
        with self._lock:
            items = [r for key, r in self._records.items() if r.subsystem == subsystem]
        return [self._ser(r) for r in items]

    def all_allocations(self) -> List[dict]:
        with self._lock:
            items = list(self._records.values())
        return [self._ser(r) for r in sorted(items, key=lambda x: x.subsystem)]

    def bottlenecks(self) -> List[dict]:
        with self._lock:
            items = list(self._records.values())
        return [
            self._ser(r) for r in items
            if r.consumed > r.allocated * 0.9 or r.queued_work > 3
        ]

    def priority_recommendation(self) -> dict:
        with self._lock:
            items = list(self._records.values())
        # Score by queued_work and under-allocation
        scored = []
        for r in items:
            score = r.queued_work * 2 + max(0, r.consumed - r.allocated)
            scored.append((score, r.subsystem, r))
        scored.sort(reverse=True)
        top3 = [{"subsystem": s, "score": sc, "record": self._ser(r)} for sc, s, r in scored[:3]]
        return {
            "top_priority_subsystems": top3,
            "rationale": "Ranked by queued work + over-allocation pressure",
            "generated_at": time.time(),
        }

    def research_pipeline_health(self) -> dict:
        try:
            from core.trust.trust_evidence_warehouse import trust_evidence_warehouse as _tew
            audit = _tew.full_audit()
            total_evidence = audit.get("total_evidence", 0)
        except Exception:
            total_evidence = 0
        try:
            from core.trust.trust_accuracy_ledger import trust_accuracy_ledger as _tal
            all_windows = _tal.all_pillars_windows()
            total_claims = sum(
                w.get("count", 0) for pillar_windows in all_windows.values()
                for w in pillar_windows if w.get("window_days") == 30
            )
        except Exception:
            total_claims = 0
        return {
            "total_evidence_in_warehouse": total_evidence,
            "30day_claims_across_pillars": total_claims,
            "health": "SUFFICIENT" if total_evidence >= 100 else ("ACCUMULATING" if total_evidence >= 20 else "INSUFFICIENT"),
            "note": "Research capacity determines trust promotion eligibility",
        }

    @staticmethod
    def _ser(r: CapacityRecord) -> dict:
        return {
            "subsystem":     r.subsystem,
            "capacity_type": r.capacity_type,
            "allocated_pct": r.allocated,
            "consumed_pct":  r.consumed,
            "queued_work":   r.queued_work,
            "utilization":   round(r.consumed / r.allocated, 2) if r.allocated > 0 else 0.0,
            "note":          r.note,
            "recorded_at":   r.recorded_at,
        }


# Singleton
resource_governor = ResourceGovernor()
