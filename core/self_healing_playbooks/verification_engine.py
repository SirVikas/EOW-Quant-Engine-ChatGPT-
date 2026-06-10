"""
Verification engine — closes the recovery loop by recording whether a
playbook execution's verification steps were satisfied.
"""
import threading
import time
from typing import List


class VerificationEngine:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._verifications: List[dict] = []
        self._counter = 0

    def verify(self, execution_id: str) -> dict:
        from core.self_healing_playbooks.playbook_executor import playbook_executor
        from core.self_healing_playbooks.playbook_registry import playbook_registry
        execution = playbook_executor.get(execution_id)
        if not execution:
            return {"error": f"unknown execution {execution_id}"}
        playbook = playbook_registry.find_for(execution.get("failure_type", ""))
        checks = list(playbook.verification_steps) if playbook else []
        verdict = "VERIFIED" if execution.get("status") == "EXECUTED" else "UNVERIFIED"
        with self._lock:
            self._counter += 1
            verification = {
                "verification_id": f"SHV-{self._counter:03d}",
                "execution_id": execution_id,
                "failure_type": execution.get("failure_type", ""),
                "checks": checks,
                "verdict": verdict,
                "verified_at": time.time(),
            }
            self._verifications.append(verification)
            return verification

    def verification_summary(self) -> dict:
        with self._lock:
            verifications = list(self._verifications)
            return {
                "total": len(verifications),
                "verified": sum(1 for v in verifications if v["verdict"] == "VERIFIED"),
                "unverified": sum(1 for v in verifications if v["verdict"] == "UNVERIFIED"),
                "recent": verifications[-10:],
            }


verification_engine = VerificationEngine()
