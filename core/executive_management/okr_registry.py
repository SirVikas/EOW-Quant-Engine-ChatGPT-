"""OKR Registry — registry of Objectives and Key Results."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal, Optional


OKRStatus = Literal["ACTIVE", "COMPLETED", "MISSED"]
Period = Literal["Q1-2026", "Q2-2026", "Annual-2026"]


@dataclass
class OKRRecord:
    okr_id: str
    objective: str
    period: str
    key_results: List[dict]
    owner: str
    status: OKRStatus
    created_at: datetime = field(default_factory=datetime.utcnow)


class OKRRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._okrs: List[OKRRecord] = []
        self._counter = 0
        self._seed()

    def _next_id(self) -> str:
        self._counter += 1
        return f"OKR-{self._counter:03d}"

    def _seed(self):
        seeds = [
            (
                "Achieve institutional-grade governance maturity",
                "Q1-2026",
                [
                    {"kr_text": "Complete 10 governance layers", "target": 10, "current": 10, "unit": "layers"},
                    {"kr_text": "Zero critical compliance gaps", "target": 0, "current": 0, "unit": "gaps"},
                ],
                "PHOENIX_SYSTEM",
            ),
            (
                "Expand institutional intelligence coverage",
                "Q2-2026",
                [
                    {"kr_text": "KGE entity coverage", "target": 500, "current": 11, "unit": "facts"},
                    {"kr_text": "HKE extraction completeness", "target": 100, "current": 0, "unit": "pct"},
                ],
                "PHOENIX_SYSTEM",
            ),
            (
                "Achieve 500+ trade calibration for ETE activation",
                "Annual-2026",
                [
                    {"kr_text": "Trades collected for ETE calibration", "target": 500, "current": 0, "unit": "trades"},
                ],
                "PHOENIX_SYSTEM",
            ),
        ]
        for obj, period, krs, owner in seeds:
            self._okrs.append(OKRRecord(self._next_id(), obj, period, krs, owner, "ACTIVE"))

    def create(self, objective: str, period: str, key_results: List[dict], owner: str) -> OKRRecord:
        with self._lock:
            rec = OKRRecord(self._next_id(), objective, period, key_results, owner, "ACTIVE")
            self._okrs.append(rec)
            return rec

    def update_kr_progress(self, okr_id: str, kr_index: int, current_value: float) -> bool:
        with self._lock:
            for o in self._okrs:
                if o.okr_id == okr_id and kr_index < len(o.key_results):
                    o.key_results[kr_index]["current"] = current_value
                    return True
            return False

    def active_okrs(self) -> List[dict]:
        with self._lock:
            return [vars(o) for o in self._okrs if o.status == "ACTIVE"]


okr_registry = OKRRegistry()
