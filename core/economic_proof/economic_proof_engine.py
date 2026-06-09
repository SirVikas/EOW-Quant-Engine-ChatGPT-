"""GAP-08: Economic Proof Engine — master economic proof aggregator."""
from __future__ import annotations

import time
from typing import Dict, Any

from loguru import logger


class EconomicProofEngine:
    """Master economic proof. Aggregates ROI validation, capital efficiency, and claim auditing."""

    def proof_report(self) -> Dict[str, Any]:
        from core.economic_proof.roi_validation_engine import roi_validation_engine
        from core.economic_proof.capital_efficiency_validator import capital_efficiency_validator
        from core.economic_proof.economic_claim_auditor import economic_claim_auditor

        roi_summary = roi_validation_engine.validation_summary()
        eff_report = capital_efficiency_validator.efficiency_report()
        audit_summary = economic_claim_auditor.audit_summary()

        proven_roi = roi_summary.get("proven", 0)
        refuted_roi = roi_summary.get("refuted", 0)
        efficient_pct = eff_report.get("efficient_pct", 0.0)
        unsupported = audit_summary.get("unsupported", 0)

        # Determine proof confidence
        if proven_roi >= 3 and efficient_pct >= 70 and unsupported == 0:
            confidence = "STRONG"
        elif proven_roi >= 1 and efficient_pct >= 50:
            confidence = "MODERATE"
        else:
            confidence = "WEAK"

        return {
            "proven_roi_claims": proven_roi,
            "refuted_claims": refuted_roi,
            "efficient_metrics_pct": efficient_pct,
            "unsupported_economic_claims": unsupported,
            "proof_confidence": confidence,
            "roi_summary": roi_summary,
            "audit_summary": audit_summary,
            "ts": int(time.time() * 1000),
        }

    def one_liner(self) -> str:
        report = self.proof_report()
        return (
            f"EconomicProof: {report['proven_roi_claims']} proven ROI | "
            f"efficiency={report['efficient_metrics_pct']}% | "
            f"confidence={report['proof_confidence']}"
        )


economic_proof_engine = EconomicProofEngine()
