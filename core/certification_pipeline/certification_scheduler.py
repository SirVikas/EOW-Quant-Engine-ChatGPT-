"""
Certification scheduler — cadence tracker for the automated certification
pipeline (daily readiness score, weekly report, monthly institutional cert).
"""
import threading
import time
from dataclasses import dataclass
from typing import Dict, List

CADENCE_SECONDS = {
    "DAILY": 86_400,
    "WEEKLY": 604_800,
    "MONTHLY": 2_592_000,
}

_SEED_SCHEDULES = [
    ("DAILY_READINESS_SCORE", "DAILY"),
    ("WEEKLY_CERTIFICATION_REPORT", "WEEKLY"),
    ("MONTHLY_INSTITUTIONAL_CERTIFICATION", "MONTHLY"),
]


@dataclass
class CertificationSchedule:
    schedule_id: str
    name: str
    cadence: str
    last_run: float
    run_count: int


class CertificationScheduler:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._schedules: Dict[str, CertificationSchedule] = {}
        self._counter = 0
        for name, cadence in _SEED_SCHEDULES:
            self._counter += 1
            self._schedules[name] = CertificationSchedule(
                schedule_id=f"CPS-{self._counter:03d}",
                name=name,
                cadence=cadence,
                last_run=0.0,
                run_count=0,
            )

    def due_schedules(self, now: float = None) -> List[CertificationSchedule]:
        now = now or time.time()
        with self._lock:
            return [
                s for s in self._schedules.values()
                if now - s.last_run >= CADENCE_SECONDS[s.cadence]
            ]

    def run_due(self) -> dict:
        from core.certification_pipeline.certification_engine import certification_engine
        runs = []
        for sched in self.due_schedules():
            try:
                if sched.name == "DAILY_READINESS_SCORE":
                    result = certification_engine.daily_readiness_score()
                else:
                    period = "WEEKLY" if "WEEKLY" in sched.name else "MONTHLY"
                    result = certification_engine.run_certification(period)
                outcome = "OK"
            except Exception as exc:
                result = {"error": str(exc)}
                outcome = "ERROR"
            with self._lock:
                sched.last_run = time.time()
                sched.run_count += 1
            runs.append({"schedule": sched.name, "outcome": outcome, "result": result})
        return {"runs": runs}

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
                    }
                    for s in self._schedules.values()
                ],
            }


certification_scheduler = CertificationScheduler()
