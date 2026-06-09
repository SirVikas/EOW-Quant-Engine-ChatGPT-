"""
Evidence Orchestration Engine — turns passive evidence infrastructure into
active accumulation. Runs due schedules (daily collection, weekly audit,
monthly validation review, quarterly certification review) and deposits the
results back into the Evidence Warehouse.
"""
import threading
import time
from typing import List


class EvidenceOrchestrator:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._runs: List[dict] = []
        self._counter = 0

    # ── schedule task implementations ────────────────────────────────────────

    def _daily_collection(self) -> dict:
        from core.evidence_warehouse.evidence_warehouse import evidence_warehouse
        harvest = evidence_warehouse.auto_harvest()
        from core.evidence_orchestration.evidence_campaign_manager import evidence_campaign_manager
        synced = evidence_campaign_manager.sync_from_warehouse()
        return {"harvested": harvest.get("harvested_count", 0),
                "campaigns_synced": synced}

    def _weekly_audit(self) -> dict:
        from core.evidence_warehouse.evidence_warehouse import evidence_warehouse
        report = evidence_warehouse.warehouse_report()
        from core.evidence_orchestration.evidence_retention_controller import (
            evidence_retention_controller)
        retention = evidence_retention_controller.retention_report()
        return {"warehouse_health_score": report.get("warehouse_health_score", 0),
                "gap_report_count": report.get("gap_report_count", 0),
                "expired_candidates": retention.get("expired_candidates", 0)}

    def _monthly_validation_review(self) -> dict:
        from core.readiness_v2.continuous_readiness_engine import continuous_readiness_engine
        report = continuous_readiness_engine.readiness_report()
        return {"overall_readiness_pct": report.get("overall_readiness_pct", 0.0),
                "recommendation": report.get("production_recommendation", "UNKNOWN")}

    def _quarterly_certification_review(self) -> dict:
        from core.certification_pipeline.certification_engine import certification_engine
        cert = certification_engine.run_certification("QUARTERLY")
        return {"verdict": cert.get("verdict", "UNKNOWN"),
                "composite_score": cert.get("composite_score", 0.0)}

    _TASKS = {
        "DAILY_EVIDENCE_COLLECTION": _daily_collection,
        "WEEKLY_EVIDENCE_AUDIT": _weekly_audit,
        "MONTHLY_VALIDATION_REVIEW": _monthly_validation_review,
        "QUARTERLY_CERTIFICATION_REVIEW": _quarterly_certification_review,
    }

    # ── orchestration ─────────────────────────────────────────────────────────

    def run_due(self, force: bool = False) -> dict:
        from core.evidence_orchestration.evidence_scheduler import evidence_scheduler
        if force:
            due = list(evidence_scheduler._schedules.values())
        else:
            due = evidence_scheduler.due_schedules()
        runs = []
        for sched in due:
            task = self._TASKS.get(sched.name)
            if task is None:
                continue
            try:
                result = task(self)
                outcome = "OK"
            except Exception as exc:
                result = {"error": str(exc)}
                outcome = "ERROR"
            evidence_scheduler.mark_run(sched.name)
            with self._lock:
                self._counter += 1
                run = {
                    "run_id": f"EOR-{self._counter:03d}",
                    "schedule": sched.name,
                    "outcome": outcome,
                    "result": result,
                    "ran_at": time.time(),
                }
                self._runs.append(run)
            runs.append(run)
            self._deposit(run)
        return {"runs": runs, "forced": force}

    def _deposit(self, run: dict) -> None:
        try:
            from core.evidence_warehouse.evidence_warehouse import evidence_warehouse
            evidence_warehouse.deposit(
                "GOVERNANCE", run["schedule"], "evidence_orchestrator",
                run, quality=0.7, tags=["orchestrated"],
            )
        except Exception:
            pass

    def orchestration_report(self) -> dict:
        from core.evidence_orchestration.evidence_scheduler import evidence_scheduler
        from core.evidence_orchestration.evidence_campaign_manager import evidence_campaign_manager
        with self._lock:
            runs = list(self._runs)
        return {
            "total_runs": len(runs),
            "errors": sum(1 for r in runs if r["outcome"] == "ERROR"),
            "recent_runs": runs[-10:],
            "schedules": evidence_scheduler.schedule_status(),
            "campaigns": evidence_campaign_manager.campaign_summary(),
        }

    def one_liner(self) -> str:
        r = self.orchestration_report()
        return (
            f"Evidence Orchestration | Runs={r['total_runs']} | "
            f"Errors={r['errors']} | "
            f"Due={r['schedules']['due_now']}/{r['schedules']['total']}"
        )


evidence_orchestrator = EvidenceOrchestrator()
