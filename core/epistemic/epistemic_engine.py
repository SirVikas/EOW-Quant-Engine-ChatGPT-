"""
PHOENIX Epistemic Intelligence Engine
Aggregates knowledge coverage, uncertainty, and confidence into a unified epistemic audit.
"""
from __future__ import annotations
import threading
from datetime import datetime, timezone


class EpistemicEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def epistemic_audit(self) -> dict:
        from core.epistemic.evidence_tracker import evidence_tracker
        from core.epistemic.uncertainty_registry import uncertainty_registry
        from core.epistemic.confidence_boundary_engine import confidence_boundary_engine

        coverage = evidence_tracker.evidence_coverage()
        unc_summary = uncertainty_registry.uncertainty_summary()
        low_conf = confidence_boundary_engine.low_confidence_domains()

        well_evidenced_pct = coverage.get("well_evidenced_pct", 0)
        total_unc = unc_summary.get("total", 1)
        critical_open = unc_summary.get("critical_open", 0)

        health_score = (
            well_evidenced_pct * 0.5
            + (1 - critical_open / max(1, total_unc)) * 50
        )
        health_score = round(min(100, max(0, health_score)), 2)

        return {
            "knowledge_coverage": coverage,
            "uncertainty_exposure": unc_summary,
            "low_confidence_areas": low_conf,
            "epistemic_health_score": health_score,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def what_do_we_know(self) -> list:
        from core.epistemic.evidence_tracker import evidence_tracker
        return evidence_tracker.all_evidence(status_filter="WELL_EVIDENCED")

    def what_do_we_assume(self) -> list:
        from core.epistemic.evidence_tracker import evidence_tracker
        assumed = evidence_tracker.all_evidence(status_filter="ASSUMED")
        partial = evidence_tracker.all_evidence(status_filter="PARTIALLY_EVIDENCED")
        return assumed + partial

    def what_dont_we_know(self) -> list:
        from core.epistemic.uncertainty_registry import uncertainty_registry
        uu = uncertainty_registry.open_uncertainties()
        return [u for u in uu if u["uncertainty_type"] in ("UNKNOWN_UNKNOWN", "KNOWN_UNKNOWN")]


epistemic_engine = EpistemicEngine()
