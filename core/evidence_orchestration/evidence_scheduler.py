"""
Evidence scheduler — cadence tracker for automated evidence campaigns.
Pre-seeded with the four institutional cadences (daily/weekly/monthly/quarterly).
"""
import threading
import time
from dataclasses import dataclass
from typing import Dict, List

CADENCE_SECONDS = {
    "DAILY": 86_400,
    "WEEKLY": 604_800,
    "MONTHLY": 2_592_000,
    "QUARTERLY": 7_776_000,
}

_SEED_SCHEDULES = [
    ("DAILY_EVIDENCE_COLLECTION", "DAILY"),
    ("WEEKLY_EVIDENCE_AUDIT", "WEEKLY"),
    ("MONTHLY_VALIDATION_REVIEW", "MONTHLY"),
    ("QUARTERLY_CERTIFICATION_REVIEW", "QUARTERLY"),
]


@dataclass
class EvidenceSchedule:
    schedule_id: str
    name: str
    cadence: str       # DAILY / WEEKLY / MONTHLY / QUARTERLY
    last_run: float    # epoch; 0.0 = never run (due immediately)
    run_count: int


class EvidenceScheduler:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._schedules: Dict[str, EvidenceSchedule] = {}
        self._counter = 0
        for name, cadence in _SEED_SCHEDULES:
            self._counter += 1
            self._schedules[name] = EvidenceSchedule(
                schedule_id=f"EOS-{self._counter:03d}",
                name=name,
                cadence=cadence,
                last_run=0.0,
                run_count=0,
            )

    def register(self, name: str, cadence: str) -> EvidenceSchedule:
        with self._lock:
            if name in self._schedules:
                return self._schedules[name]
            self._counter += 1
            sched = EvidenceSchedule(
                schedule_id=f"EOS-{self._counter:03d}",
                name=name,
                cadence=cadence if cadence in CADENCE_SECONDS else "DAILY",
                last_run=0.0,
                run_count=0,
            )
            self._schedules[name] = sched
            return sched

    def due_schedules(self, now: float = None) -> List[EvidenceSchedule]:
        now = now or time.time()
        with self._lock:
            return [
                s for s in self._schedules.values()
                if now - s.last_run >= CADENCE_SECONDS[s.cadence]
            ]

    def mark_run(self, name: str) -> None:
        with self._lock:
            sched = self._schedules.get(name)
            if sched:
                sched.last_run = time.time()
                sched.run_count += 1

    def schedule_status(self) -> dict:
        now = time.time()
        with self._lock:
            return {
                "total": len(self._schedules),
                "due_now": len(self.due_schedules(now)),
                "schedules": [
                    {
                        "schedule_id": s.schedule_id,
                        "name": s.name,
                        "cadence": s.cadence,
                        "run_count": s.run_count,
                        "last_run": s.last_run,
                        "next_due_in_sec": max(
                            0, int(CADENCE_SECONDS[s.cadence] - (now - s.last_run))
                        ) if s.last_run else 0,
                    }
                    for s in self._schedules.values()
                ],
            }


evidence_scheduler = EvidenceScheduler()
