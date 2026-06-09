"""Workflow Engine — master workflow orchestrator."""
import threading


class WorkflowEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def orchestrate(self, workflow_id: str) -> dict:
        from core.workflow_orchestration.workflow_monitor import workflow_monitor
        from core.workflow_orchestration.workflow_dependency_manager import workflow_dependency_manager
        with self._lock:
            can = workflow_dependency_manager.can_start(workflow_id)
            run = workflow_monitor.start_run(workflow_id)
            return {"run_id": run.run_id, "workflow_id": workflow_id, "dependencies_met": can, "status": "RUNNING"}

    def execution_report(self) -> dict:
        from core.workflow_orchestration.workflow_monitor import workflow_monitor
        with self._lock:
            active = workflow_monitor.active_runs()
            all_runs = workflow_monitor._runs
            total = len(all_runs)
            completed = sum(1 for r in all_runs if r.status == "COMPLETED")
            success_rate = (completed / total * 100) if total else 0.0
            return {
                "total_runs": total,
                "success_rate": round(success_rate, 2),
                "active_runs": len(active),
            }

    def one_liner(self) -> str:
        report = self.execution_report()
        return f"Workflow Engine: {report['total_runs']} runs, {report['success_rate']}% success, {report['active_runs']} active"


workflow_engine = WorkflowEngine()
