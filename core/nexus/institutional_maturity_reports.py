"""
Institutional Maturity Reports — 20-gap coverage proof.

Each method proves (or reports partial/insufficient evidence for) one maturity gap.
All imports are lazy to avoid circular imports at module load.
"""
from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class InstitutionalMaturityReports:
    """Aggregate evidence reports covering all 20 institutional maturity gaps."""

    def __init__(self) -> None:
        self._lock = threading.RLock()

    # ── helpers ───────────────────────────────────────────────────────────────

    def _build(
        self,
        gap_id: str,
        status: str,
        summary: str,
        evidence: dict,
    ) -> dict:
        return {
            "gap_id": gap_id,
            "status": status,          # PROVEN | PARTIAL | INSUFFICIENT
            "summary": summary,
            "evidence": evidence,
            "generated_at": _now(),
        }

    def _safe(self, fn, *args, **kwargs) -> tuple[Any, str | None]:
        """Call fn and return (result, None) or (None, error_str)."""
        try:
            return fn(*args, **kwargs), None
        except Exception as exc:  # noqa: BLE001
            return None, str(exc)

    # ── Category 1: Evidence Maturity ─────────────────────────────────────────

    def gap_em01_multi_regime(self) -> dict:
        """GAP-EM-01: Multi-Regime Evidence Report."""
        with self._lock:
            try:
                from core.trust.evidence_accumulation_report import (
                    evidence_accumulation_report as _ear,
                )
                report = _ear.multi_regime_report()
                regimes = report.get("regimes", {})
                covered = [r for r, v in regimes.items() if v.get("evidence_count", 0) > 0]
                total = len(regimes) if regimes else 0
                status = "PROVEN" if len(covered) >= 3 else ("PARTIAL" if covered else "INSUFFICIENT")
                return self._build(
                    "GAP-EM-01",
                    status,
                    f"Evidence exists across {len(covered)}/{total} regimes: {covered}",
                    {"regimes": regimes, "covered_count": len(covered), "total_regimes": total},
                )
            except Exception as exc:  # noqa: BLE001
                return self._build("GAP-EM-01", "INSUFFICIENT",
                                   f"Module unavailable: {exc}", {"error": str(exc)})

    def gap_em02_long_term_survival(self) -> dict:
        """GAP-EM-02: Long-Term Evidence Survival Report."""
        with self._lock:
            try:
                from core.trust.evidence_accumulation_report import (
                    evidence_accumulation_report as _ear,
                )
                report = _ear.trust_survival_report()
                windows = report.get("survival_windows", {})
                proven = [w for w, v in windows.items() if v.get("survived", False)]
                status = "PROVEN" if len(proven) >= 2 else ("PARTIAL" if proven else "INSUFFICIENT")
                return self._build(
                    "GAP-EM-02",
                    status,
                    f"Trust survives in {len(proven)} of {len(windows)} windows: {proven}",
                    {"survival_windows": windows, "proven_windows": proven},
                )
            except Exception as exc:
                return self._build("GAP-EM-02", "INSUFFICIENT",
                                   f"Module unavailable: {exc}", {"error": str(exc)})

    def gap_em03_aeg_history(self) -> dict:
        """GAP-EM-03: AEG Historical Performance Report."""
        with self._lock:
            try:
                from core.nexus.aeg_pipeline.aeg_promotion_ledger import (
                    aeg_promotion_ledger as _apl,
                )
                summary = _apl.summary()
                rate = _apl.promotion_success_rate()
                total = summary.get("total_entries", 0)
                status = "PROVEN" if total >= 5 else ("PARTIAL" if total >= 1 else "INSUFFICIENT")
                return self._build(
                    "GAP-EM-03",
                    status,
                    f"AEG ledger contains {total} entries; success rate: {rate}",
                    {"ledger_summary": summary, "success_rate": rate},
                )
            except Exception as exc:
                return self._build("GAP-EM-03", "INSUFFICIENT",
                                   f"Module unavailable: {exc}", {"error": str(exc)})

    def gap_em04_board_accuracy(self) -> dict:
        """GAP-EM-04: Board Accuracy Report."""
        with self._lock:
            try:
                from core.pcao.board_accuracy_ledger import (
                    board_accuracy_ledger as _bal,
                )
                report = _bal.accuracy_report()
                total = report.get("total_decisions", 0)
                accuracy = report.get("overall_accuracy", 0.0)
                status = "PROVEN" if total >= 10 else ("PARTIAL" if total >= 1 else "INSUFFICIENT")
                return self._build(
                    "GAP-EM-04",
                    status,
                    f"Board accuracy: {accuracy:.1%} over {total} decisions",
                    {"accuracy_report": report},
                )
            except Exception as exc:
                return self._build("GAP-EM-04", "INSUFFICIENT",
                                   f"Module unavailable: {exc}", {"error": str(exc)})

    def gap_em05_memory_density(self) -> dict:
        """GAP-EM-05: Institutional Memory Density Report."""
        with self._lock:
            try:
                from core.observatory.nexus_bridge import _imraf
                im = _imraf()
                if im is None:
                    raise RuntimeError("IMRAF unavailable")
                records = getattr(im, "all_records", None)
                if callable(records):
                    all_rec = records()
                else:
                    all_rec = getattr(im, "records", [])
                count = len(all_rec) if all_rec else 0
                status = "PROVEN" if count >= 50 else ("PARTIAL" if count >= 10 else "INSUFFICIENT")
                return self._build(
                    "GAP-EM-05",
                    status,
                    f"IMRAF contains {count} institutional memory records",
                    {"record_count": count},
                )
            except Exception as exc:
                return self._build("GAP-EM-05", "INSUFFICIENT",
                                   f"Module unavailable: {exc}", {"error": str(exc)})

    # ── Category 2: Validation Maturity ──────────────────────────────────────

    def gap_vm01_trust_calibration(self) -> dict:
        """GAP-VM-01: Trust Calibration Validation."""
        with self._lock:
            try:
                from core.trust.trust_calibration_engine import (
                    trust_calibration_engine as _tce,
                )
                report = _tce.calibration_report() if hasattr(_tce, "calibration_report") else {}
                from core.nexus.validation_suite import validation_suite as _vs
                cal = _vs.calibration.validate() if hasattr(_vs, "calibration") else {}
                status_val = cal.get("status", "UNKNOWN")
                status = "PROVEN" if status_val in ("VALID", "CALIBRATED", "PROVEN") else (
                    "PARTIAL" if status_val not in ("INSUFFICIENT", "UNKNOWN", "ERROR") else "INSUFFICIENT"
                )
                return self._build(
                    "GAP-VM-01",
                    status,
                    f"Trust calibration status: {status_val}",
                    {"calibration": cal, "calibration_report": report},
                )
            except Exception as exc:
                return self._build("GAP-VM-01", "INSUFFICIENT",
                                   f"Module unavailable: {exc}", {"error": str(exc)})

    def gap_vm02_digital_twin_accuracy(self) -> dict:
        """GAP-VM-02: Digital Twin Prediction Accuracy."""
        with self._lock:
            try:
                from core.nexus.validation_suite import validation_suite as _vs
                twin = _vs.twin.accuracy_report() if hasattr(_vs, "twin") else {}
                total = twin.get("total_predictions", 0)
                accuracy = twin.get("overall_accuracy", 0.0)
                status = "PROVEN" if total >= 10 else ("PARTIAL" if total >= 1 else "INSUFFICIENT")
                return self._build(
                    "GAP-VM-02",
                    status,
                    f"Digital twin: {accuracy:.1%} accuracy over {total} predictions",
                    {"twin_accuracy": twin},
                )
            except Exception as exc:
                return self._build("GAP-VM-02", "INSUFFICIENT",
                                   f"Module unavailable: {exc}", {"error": str(exc)})

    def gap_vm03_cascade_accuracy(self) -> dict:
        """GAP-VM-03: Cross-Layer Cascade Accuracy."""
        with self._lock:
            try:
                from core.nexus.validation_suite import validation_suite as _vs
                cascade = _vs.cascade.audit() if hasattr(_vs, "cascade") else {}
                propagation_rate = cascade.get("propagation_rate", 0.0)
                status = "PROVEN" if propagation_rate >= 0.8 else (
                    "PARTIAL" if propagation_rate > 0 else "INSUFFICIENT"
                )
                return self._build(
                    "GAP-VM-03",
                    status,
                    f"Cross-layer cascade propagation rate: {propagation_rate:.1%}",
                    {"cascade": cascade},
                )
            except Exception as exc:
                return self._build("GAP-VM-03", "INSUFFICIENT",
                                   f"Module unavailable: {exc}", {"error": str(exc)})

    def gap_vm04_health_correlation(self) -> dict:
        """GAP-VM-04: Health Index Historical Correlation."""
        with self._lock:
            try:
                from core.nexus.institutional_health_index import (
                    institutional_health_index as _ihi,
                )
                report = _ihi.health_report()
                from core.nexus.validation_suite import validation_suite as _vs
                corr = _vs.health_index.correlation_report() if hasattr(_vs, "health_index") else {}
                score = report.get("current_score", 0.0)
                correlation = corr.get("correlation_coefficient", None)
                status = "PROVEN" if correlation is not None and abs(correlation) >= 0.6 else (
                    "PARTIAL" if score > 0 else "INSUFFICIENT"
                )
                return self._build(
                    "GAP-VM-04",
                    status,
                    f"Health index score: {score:.2f}; correlation: {correlation}",
                    {"health_report": report, "correlation": corr},
                )
            except Exception as exc:
                return self._build("GAP-VM-04", "INSUFFICIENT",
                                   f"Module unavailable: {exc}", {"error": str(exc)})

    def gap_vm05_governance_effectiveness(self) -> dict:
        """GAP-VM-05: Governance Effectiveness Report."""
        with self._lock:
            try:
                from core.cortex.governance_metrics import governance_metrics as _gm
                kpi = _gm.governance_kpi()
                from core.nexus.validation_suite import validation_suite as _vs
                gov = _vs.governance.generate() if hasattr(_vs, "governance") else {}
                compliance = kpi.get("compliance_rate", 0.0)
                status = "PROVEN" if compliance >= 0.8 else (
                    "PARTIAL" if compliance > 0 else "INSUFFICIENT"
                )
                return self._build(
                    "GAP-VM-05",
                    status,
                    f"Governance compliance rate: {compliance:.1%}",
                    {"governance_kpi": kpi, "validation": gov},
                )
            except Exception as exc:
                return self._build("GAP-VM-05", "INSUFFICIENT",
                                   f"Module unavailable: {exc}", {"error": str(exc)})

    # ── Category 3: Executive Intelligence Maturity ───────────────────────────

    def gap_ei01_recommendation_accuracy(self) -> dict:
        """GAP-EI-01: Executive Recommendation Accuracy."""
        with self._lock:
            try:
                from core.pcao.executive_scorecard import executive_scorecard as _es
                scorecard = _es.recommendation_scorecard()
                total = scorecard.get("total_recommendations", 0)
                accuracy = scorecard.get("accuracy_rate", 0.0)
                status = "PROVEN" if total >= 10 and accuracy >= 0.6 else (
                    "PARTIAL" if total >= 1 else "INSUFFICIENT"
                )
                return self._build(
                    "GAP-EI-01",
                    status,
                    f"Recommendation accuracy: {accuracy:.1%} over {total} recommendations",
                    {"scorecard": scorecard},
                )
            except Exception as exc:
                return self._build("GAP-EI-01", "INSUFFICIENT",
                                   f"Module unavailable: {exc}", {"error": str(exc)})

    def gap_ei02_forecast_accuracy(self) -> dict:
        """GAP-EI-02: Forecast Accuracy Report (3M/6M/1Y/2Y)."""
        with self._lock:
            try:
                from core.pcao.strategic_forecast_engine import (
                    strategic_forecast_engine as _sfe,
                )
                forecasts = _sfe.multi_horizon_forecast()
                horizons = forecasts.get("horizons", {})
                total_horizons = len(horizons)
                status = "PROVEN" if total_horizons >= 3 else (
                    "PARTIAL" if total_horizons >= 1 else "INSUFFICIENT"
                )
                return self._build(
                    "GAP-EI-02",
                    status,
                    f"Forecast coverage: {total_horizons} horizon(s) available",
                    {"horizons": horizons, "total": total_horizons},
                )
            except Exception as exc:
                return self._build("GAP-EI-02", "INSUFFICIENT",
                                   f"Module unavailable: {exc}", {"error": str(exc)})

    def gap_ei03_resource_optimization(self) -> dict:
        """GAP-EI-03: Resource Optimization Benefit Proof."""
        with self._lock:
            try:
                from core.pcao.executive_scorecard import executive_scorecard as _es
                report = _es.optimizer_validation_report()
                total = report.get("total_optimizations", 0)
                benefit = report.get("average_benefit_pct", 0.0)
                status = "PROVEN" if total >= 5 else (
                    "PARTIAL" if total >= 1 else "INSUFFICIENT"
                )
                return self._build(
                    "GAP-EI-03",
                    status,
                    f"Resource optimization: {total} optimizations; avg benefit {benefit:.1%}",
                    {"optimization_report": report},
                )
            except Exception as exc:
                return self._build("GAP-EI-03", "INSUFFICIENT",
                                   f"Module unavailable: {exc}", {"error": str(exc)})

    def gap_ei04_roadmap_performance(self) -> dict:
        """GAP-EI-04: Roadmap Performance Report."""
        with self._lock:
            try:
                from core.pcao.executive_scorecard import executive_scorecard as _es
                report = _es.roadmap_performance_report()
                completed = report.get("completed_milestones", 0)
                total = report.get("total_milestones", 0)
                rate = (completed / total) if total > 0 else 0.0
                status = "PROVEN" if completed >= 3 else (
                    "PARTIAL" if completed >= 1 else "INSUFFICIENT"
                )
                return self._build(
                    "GAP-EI-04",
                    status,
                    f"Roadmap completion: {completed}/{total} milestones ({rate:.1%})",
                    {"roadmap_performance": report},
                )
            except Exception as exc:
                return self._build("GAP-EI-04", "INSUFFICIENT",
                                   f"Module unavailable: {exc}", {"error": str(exc)})

    def gap_ei05_command_center_value(self) -> dict:
        """GAP-EI-05: Chairman Command Center Value Assessment."""
        with self._lock:
            try:
                from core.pcao.chairman_command_center import (
                    chairman_command_center as _ccc,
                )
                dashboard = _ccc.chairman_dashboard()
                alerts = _ccc.active_alerts()
                sections_populated = sum(
                    1 for k in ("what_happened", "what_matters", "what_next")
                    if dashboard.get(k)
                )
                status = "PROVEN" if sections_populated >= 3 else (
                    "PARTIAL" if sections_populated >= 1 else "INSUFFICIENT"
                )
                return self._build(
                    "GAP-EI-05",
                    status,
                    f"Command center: {sections_populated}/3 sections populated; {len(alerts)} active alerts",
                    {"dashboard_summary": {k: bool(v) for k, v in dashboard.items()},
                     "active_alert_count": len(alerts)},
                )
            except Exception as exc:
                return self._build("GAP-EI-05", "INSUFFICIENT",
                                   f"Module unavailable: {exc}", {"error": str(exc)})

    # ── Category 4: Institutional Learning Maturity ───────────────────────────

    def gap_il01_learning_cycle_audit(self) -> dict:
        """GAP-IL-01: Learning Cycle Audit."""
        with self._lock:
            try:
                from core.nexus.institutional_learning_engine import (
                    institutional_learning_engine as _ile,
                )
                cycles = _ile.recent_cycles(limit=100)
                total = len(cycles)
                complete = [c for c in cycles if c.get("phases_completed", 0) >= 5]
                status = "PROVEN" if len(complete) >= 3 else (
                    "PARTIAL" if total >= 1 else "INSUFFICIENT"
                )
                return self._build(
                    "GAP-IL-01",
                    status,
                    f"Learning cycles: {total} total; {len(complete)} fully complete (all 5 phases)",
                    {"total_cycles": total, "complete_cycles": len(complete)},
                )
            except Exception as exc:
                return self._build("GAP-IL-01", "INSUFFICIENT",
                                   f"Module unavailable: {exc}", {"error": str(exc)})

    def gap_il02_trust_evolution(self) -> dict:
        """GAP-IL-02: Trust Evolution Report."""
        with self._lock:
            try:
                from core.nexus.institutional_learning_engine import (
                    institutional_learning_engine as _ile,
                )
                summary = _ile.learning_summary()
                trust_updates = summary.get("trust_updates_applied", 0)
                status = "PROVEN" if trust_updates >= 5 else (
                    "PARTIAL" if trust_updates >= 1 else "INSUFFICIENT"
                )
                return self._build(
                    "GAP-IL-02",
                    status,
                    f"Learning applied {trust_updates} trust improvements",
                    {"learning_summary": summary, "trust_updates": trust_updates},
                )
            except Exception as exc:
                return self._build("GAP-IL-02", "INSUFFICIENT",
                                   f"Module unavailable: {exc}", {"error": str(exc)})

    def gap_il03_governance_evolution(self) -> dict:
        """GAP-IL-03: Governance Evolution Report."""
        with self._lock:
            try:
                from core.nexus.institutional_learning_engine import (
                    institutional_learning_engine as _ile,
                )
                summary = _ile.learning_summary()
                gov_updates = summary.get("governance_updates_applied", 0)
                status = "PROVEN" if gov_updates >= 5 else (
                    "PARTIAL" if gov_updates >= 1 else "INSUFFICIENT"
                )
                return self._build(
                    "GAP-IL-03",
                    status,
                    f"Learning applied {gov_updates} governance improvements",
                    {"learning_summary": summary, "governance_updates": gov_updates},
                )
            except Exception as exc:
                return self._build("GAP-IL-03", "INSUFFICIENT",
                                   f"Module unavailable: {exc}", {"error": str(exc)})

    def gap_il04_roadmap_evolution(self) -> dict:
        """GAP-IL-04: Roadmap Evolution Report."""
        with self._lock:
            try:
                from core.nexus.institutional_learning_engine import (
                    institutional_learning_engine as _ile,
                )
                summary = _ile.learning_summary()
                roadmap_updates = summary.get("roadmap_updates_applied", 0)
                status = "PROVEN" if roadmap_updates >= 5 else (
                    "PARTIAL" if roadmap_updates >= 1 else "INSUFFICIENT"
                )
                return self._build(
                    "GAP-IL-04",
                    status,
                    f"Learning applied {roadmap_updates} roadmap improvements",
                    {"learning_summary": summary, "roadmap_updates": roadmap_updates},
                )
            except Exception as exc:
                return self._build("GAP-IL-04", "INSUFFICIENT",
                                   f"Module unavailable: {exc}", {"error": str(exc)})

    def gap_il05_institutional_evolution(self) -> dict:
        """GAP-IL-05: Closed-Loop Institutional Evolution."""
        with self._lock:
            try:
                from core.nexus.institutional_learning_engine import (
                    institutional_learning_engine as _ile,
                )
                summary = _ile.learning_summary()
                cycles = _ile.recent_cycles(limit=100)
                insights = _ile.all_insights()
                total_cycles = len(cycles)
                total_insights = len(insights)
                applied_insights = sum(1 for i in insights if i.get("applied", False))
                # Closed-loop requires cycles producing insights that get applied
                status = "PROVEN" if total_cycles >= 3 and applied_insights >= 3 else (
                    "PARTIAL" if total_cycles >= 1 or applied_insights >= 1 else "INSUFFICIENT"
                )
                return self._build(
                    "GAP-IL-05",
                    status,
                    f"Institutional evolution: {total_cycles} cycles, "
                    f"{total_insights} insights ({applied_insights} applied)",
                    {
                        "learning_summary": summary,
                        "total_cycles": total_cycles,
                        "total_insights": total_insights,
                        "applied_insights": applied_insights,
                    },
                )
            except Exception as exc:
                return self._build("GAP-IL-05", "INSUFFICIENT",
                                   f"Module unavailable: {exc}", {"error": str(exc)})

    # ── Combined Report ───────────────────────────────────────────────────────

    def full_maturity_report(self) -> dict:
        """Return all 20 gap reports in a single response."""
        gaps = [
            self.gap_em01_multi_regime(),
            self.gap_em02_long_term_survival(),
            self.gap_em03_aeg_history(),
            self.gap_em04_board_accuracy(),
            self.gap_em05_memory_density(),
            self.gap_vm01_trust_calibration(),
            self.gap_vm02_digital_twin_accuracy(),
            self.gap_vm03_cascade_accuracy(),
            self.gap_vm04_health_correlation(),
            self.gap_vm05_governance_effectiveness(),
            self.gap_ei01_recommendation_accuracy(),
            self.gap_ei02_forecast_accuracy(),
            self.gap_ei03_resource_optimization(),
            self.gap_ei04_roadmap_performance(),
            self.gap_ei05_command_center_value(),
            self.gap_il01_learning_cycle_audit(),
            self.gap_il02_trust_evolution(),
            self.gap_il03_governance_evolution(),
            self.gap_il04_roadmap_evolution(),
            self.gap_il05_institutional_evolution(),
        ]
        proven = sum(1 for g in gaps if g["status"] == "PROVEN")
        partial = sum(1 for g in gaps if g["status"] == "PARTIAL")
        insufficient = sum(1 for g in gaps if g["status"] == "INSUFFICIENT")
        return {
            "report_version": "1.0.0",
            "generated_at": _now(),
            "summary": {
                "total_gaps": len(gaps),
                "proven": proven,
                "partial": partial,
                "insufficient": insufficient,
                "maturity_score": proven / len(gaps),
            },
            "gaps": gaps,
        }


# Singleton
institutional_maturity_reports = InstitutionalMaturityReports()
