"""Master Orchestrator — coordinates all civilization-layer components."""
import threading
from datetime import datetime, timezone
from typing import List


class MasterOrchestrator:
    def __init__(self):
        self._lock = threading.RLock()

    def orchestrate(self) -> dict:
        with self._lock:
            from core.civilization_orchestrator.institutional_alignment_engine import institutional_alignment_engine
            from core.civilization_orchestrator.long_horizon_director import long_horizon_director

            alignment_summary = institutional_alignment_engine.alignment_summary()
            horizon_outlook = long_horizon_director.horizon_outlook()

            return {
                "alignment": alignment_summary,
                "horizon": horizon_outlook,
                "orchestrated_at": datetime.now(timezone.utc).isoformat(),
            }

    def system_readiness(self) -> dict:
        with self._lock:
            from core.civilization_orchestrator.institutional_alignment_engine import institutional_alignment_engine

            alignment = institutional_alignment_engine.alignment_summary()
            blocking_issues: List[str] = []

            misaligned = alignment.get("misaligned", 0)
            if misaligned > 0:
                blocking_issues.append(f"{misaligned} institutional layers are MISALIGNED")

            return {
                "is_ready": len(blocking_issues) == 0,
                "blocking_issues": blocking_issues,
                "alignment_score": alignment.get("average_alignment_score", 0),
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }

    def orchestration_status(self) -> dict:
        with self._lock:
            orchestration = self.orchestrate()
            readiness = self.system_readiness()
            return {
                "orchestration": orchestration,
                "readiness": readiness,
                "status": "READY" if readiness["is_ready"] else "BLOCKED",
            }


master_orchestrator = MasterOrchestrator()
