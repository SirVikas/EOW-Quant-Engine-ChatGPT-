"""
PHOENIX Evolution Governance — Evolution Registry
Central registry for all system evolution proposals and their lifecycle.
"""
from __future__ import annotations
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class Evolution:
    evo_id: str
    title: str
    description: str
    proposed_by: str
    evo_type: str  # LEARNING/BEHAVIOR/POLICY/CONFIGURATION/ARCHITECTURE
    status: str    # PROPOSED/SIMULATED/APPROVED/REJECTED/DEPLOYED/ROLLED_BACK
    proposed_at: str
    deployed_at: Optional[str]
    rolled_back_at: Optional[str]
    rationale: str
    risk_level: str  # LOW/MEDIUM/HIGH/CRITICAL


class EvolutionRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._evolutions: Dict[str, Evolution] = {}
        self._counters: Dict[str, int] = {}

    def _next_id(self) -> str:
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        with self._lock:
            self._counters[today] = self._counters.get(today, 0) + 1
            seq = self._counters[today]
        return f"EVO-{today}-{seq:03d}"

    def propose(
        self,
        title: str,
        description: str,
        proposed_by: str,
        evo_type: str,
        rationale: str,
        risk_level: str = "MEDIUM",
    ) -> str:
        evo_id = self._next_id()
        evo = Evolution(
            evo_id=evo_id,
            title=title,
            description=description,
            proposed_by=proposed_by,
            evo_type=evo_type,
            status="PROPOSED",
            proposed_at=datetime.now(timezone.utc).isoformat(),
            deployed_at=None,
            rolled_back_at=None,
            rationale=rationale,
            risk_level=risk_level,
        )
        with self._lock:
            self._evolutions[evo_id] = evo
        return evo_id

    def get(self, evo_id: str) -> Optional[dict]:
        with self._lock:
            e = self._evolutions.get(evo_id)
        return asdict(e) if e else None

    def update_status(self, evo_id: str, status: str, **kwargs):
        with self._lock:
            e = self._evolutions.get(evo_id)
            if e:
                e.status = status
                for k, v in kwargs.items():
                    if hasattr(e, k):
                        setattr(e, k, v)

    def all_evolutions(
        self, status_filter: str = None, type_filter: str = None
    ) -> list:
        with self._lock:
            items = list(self._evolutions.values())
        if status_filter:
            items = [e for e in items if e.status == status_filter]
        if type_filter:
            items = [e for e in items if e.evo_type == type_filter]
        return [asdict(e) for e in items]

    def evolution_stats(self) -> dict:
        with self._lock:
            items = list(self._evolutions.values())
        total = len(items)
        by_status: Dict[str, int] = {}
        by_type: Dict[str, int] = {}
        rolled_back = 0
        deployed = 0
        for e in items:
            by_status[e.status] = by_status.get(e.status, 0) + 1
            by_type[e.evo_type] = by_type.get(e.evo_type, 0) + 1
            if e.status == "ROLLED_BACK":
                rolled_back += 1
            if e.status in ("DEPLOYED", "ROLLED_BACK"):
                deployed += 1
        rollback_rate = rolled_back / deployed if deployed else 0.0
        return {
            "total": total,
            "by_status": by_status,
            "by_type": by_type,
            "rollback_rate": round(rollback_rate, 4),
        }


evolution_registry = EvolutionRegistry()
