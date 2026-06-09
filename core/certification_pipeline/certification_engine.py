"""
Certification engine — continuous automated certification.
Aggregates maturity, readiness, evidence, and proof scores from sibling
layers, evaluates them against readiness gates, and archives the verdict.
"""
import threading
import time


class CertificationEngine:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._counter = 0
        self._last_run: dict = {}

    # ── score collection (each source optional — defaults to 0) ─────────────

    def _collect_scores(self) -> dict:
        scores = {"MATURITY": 0.0, "READINESS": 0.0, "EVIDENCE": 0.0, "PROOF": 0.0}
        try:
            from core.maturity_scorecard.maturity_engine import maturity_engine
            scores["MATURITY"] = float(maturity_engine.assess().get("total_score", 0.0))
        except Exception:
            pass
        try:
            from core.readiness_v2.continuous_readiness_engine import continuous_readiness_engine
            scores["READINESS"] = float(
                continuous_readiness_engine.readiness_report().get("overall_readiness_pct", 0.0))
        except Exception:
            pass
        try:
            from core.evidence_warehouse.evidence_warehouse import evidence_warehouse
            scores["EVIDENCE"] = float(
                evidence_warehouse.warehouse_report().get("warehouse_health_score", 0.0))
        except Exception:
            pass
        try:
            from core.proof_maturity.proof_maturity_engine import proof_maturity_engine
            scores["PROOF"] = float(
                proof_maturity_engine.proof_maturity_report().get("proof_maturity_index", 0.0))
        except Exception:
            pass
        return scores

    # ── certification ────────────────────────────────────────────────────────

    def daily_readiness_score(self) -> dict:
        scores = self._collect_scores()
        composite = round(sum(scores.values()) / len(scores), 2)
        return {"composite_score": composite, "dimension_scores": scores,
                "generated_at": time.time()}

    def run_certification(self, period: str = "DAILY") -> dict:
        from core.certification_pipeline.readiness_gate_manager import readiness_gate_manager
        from core.certification_pipeline.certification_archive import certification_archive
        scores = self._collect_scores()
        gate_result = readiness_gate_manager.evaluate(scores)
        composite = round(sum(scores.values()) / len(scores), 2)
        if gate_result["all_passed"]:
            verdict = "CERTIFIED"
        elif gate_result["passed"] * 2 >= gate_result["total"]:
            verdict = "PROVISIONAL"
        else:
            verdict = "NOT_CERTIFIED"
        with self._lock:
            self._counter += 1
            record = {
                "certification_id": f"CPC-{self._counter:03d}",
                "period": period,
                "verdict": verdict,
                "composite_score": composite,
                "dimension_scores": scores,
                "gate_result": gate_result,
                "certified_at": time.time(),
            }
            self._last_run = record
        certification_archive.archive(record)
        return record

    def pipeline_report(self) -> dict:
        from core.certification_pipeline.certification_archive import certification_archive
        from core.certification_pipeline.certification_scheduler import certification_scheduler
        with self._lock:
            last_run = dict(self._last_run)
        return {
            "last_certification": last_run,
            "archive": certification_archive.archive_summary(),
            "schedules": certification_scheduler.schedule_status(),
        }

    def one_liner(self) -> str:
        with self._lock:
            last = self._last_run
        if not last:
            return "Certification Pipeline | No certification run yet"
        return (
            f"Certification Pipeline | Verdict={last['verdict']} | "
            f"Score={last['composite_score']} | Period={last['period']}"
        )


certification_engine = CertificationEngine()
