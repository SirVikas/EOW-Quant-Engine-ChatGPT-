"""
Recovery playbook manager — facade mapping
Failure Type → Recovery Procedure → Verification.
"""
import threading
from typing import List


class RecoveryPlaybookManager:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._recoveries: List[dict] = []

    def handle_failure(self, failure_type: str, context: str = "") -> dict:
        from core.self_healing_playbooks.playbook_executor import playbook_executor
        from core.self_healing_playbooks.verification_engine import verification_engine
        execution = playbook_executor.execute(failure_type, context)
        verification = verification_engine.verify(execution["execution_id"])
        recovery = {
            "failure_type": execution["failure_type"],
            "execution": execution,
            "verification": verification,
        }
        with self._lock:
            self._recoveries.append(recovery)
        return recovery

    def recovery_report(self) -> dict:
        from core.self_healing_playbooks.playbook_registry import playbook_registry
        from core.self_healing_playbooks.playbook_executor import playbook_executor
        from core.self_healing_playbooks.verification_engine import verification_engine
        with self._lock:
            recoveries = list(self._recoveries)
        return {
            "total_recoveries": len(recoveries),
            "playbooks": playbook_registry.all_playbooks()["total"],
            "executions": playbook_executor.execution_summary(),
            "verifications": verification_engine.verification_summary(),
            "recent": recoveries[-5:],
        }

    def one_liner(self) -> str:
        r = self.recovery_report()
        return (
            f"Self-Healing Playbooks | Playbooks={r['playbooks']} | "
            f"Recoveries={r['total_recoveries']} | "
            f"Verified={r['verifications']['verified']}"
        )


recovery_playbook_manager = RecoveryPlaybookManager()
