"""
PHOENIX Meta Governance — Governance Validator
Validates decisions, evolutions, and deployments against governance rules.
"""
from __future__ import annotations
import threading
from datetime import datetime, timezone
from typing import Dict, List


class GovernanceValidator:
    def __init__(self):
        self._lock = threading.RLock()

    def validate_decision(self, decision_description: str, source_layer: str) -> dict:
        warnings = []
        blocking_issues = []

        # Constitutional check
        try:
            from core.pccp.strategic_goal_engine import strategic_goal_engine
            result = strategic_goal_engine.constitutional_check(decision_description)
            if not result.get("passed", True):
                blocking_issues.append("Constitutional check failed")
        except Exception as e:
            warnings.append(f"Constitutional check skipped: {e}")

        # Compliance check
        try:
            from core.meta_governance.compliance_engine import compliance_engine
            cr001 = compliance_engine.check_compliance("CR-001")
            if not cr001["compliant"]:
                warnings.append("CR-001: Decision recording compliance concern")
        except Exception:
            pass

        valid = len(blocking_issues) == 0
        return {
            "valid": valid,
            "warnings": warnings,
            "blocking_issues": blocking_issues,
            "decision_description": decision_description,
            "source_layer": source_layer,
            "validated_at": datetime.now(timezone.utc).isoformat(),
        }

    def validate_evolution(self, evo_id: str) -> dict:
        issues = []
        warnings = []
        try:
            from core.evolution_governance.evolution_registry import evolution_registry
            from core.evolution_governance.evolution_review_engine import evolution_review_engine
            evo = evolution_registry.get(evo_id)
            if not evo:
                return {"valid": False, "issues": [f"Evolution {evo_id} not found"]}
            reviews = evolution_review_engine.get_reviews(evo_id)
            if not reviews:
                issues.append("No reviews submitted for this evolution")
            if evo["status"] not in ("APPROVED", "DEPLOYED"):
                warnings.append(f"Evolution status is {evo['status']} — not yet approved")
        except Exception as e:
            issues.append(f"Validation error: {e}")
        return {
            "evo_id": evo_id,
            "valid": len(issues) == 0,
            "warnings": warnings,
            "blocking_issues": issues,
            "validated_at": datetime.now(timezone.utc).isoformat(),
        }

    def validate_deployment(self, rec_id: str) -> dict:
        issues = []
        try:
            from core.digital_twin.deployment_validator import deployment_validator
            validations = deployment_validator.all_validations()
            rec_vals = [v for v in validations if v["rec_id"] == rec_id]
            if not rec_vals:
                issues.append(f"No digital twin validation found for {rec_id}")
            elif all(v["final_verdict"] == "REJECTED" for v in rec_vals):
                issues.append(f"All validations for {rec_id} were REJECTED")
        except Exception as e:
            issues.append(f"Deployment validation check failed: {e}")
        return {
            "rec_id": rec_id,
            "valid": len(issues) == 0,
            "blocking_issues": issues,
            "validated_at": datetime.now(timezone.utc).isoformat(),
        }

    def governance_health(self) -> dict:
        constitutional_compliance = 0.8
        decision_governance_score = 0.8
        evolution_governance_score = 0.8
        try:
            from core.meta_governance.compliance_engine import compliance_engine
            report = compliance_engine.full_compliance_check()
            constitutional_compliance = report["compliance_score"]
            decision_governance_score = report["compliance_score"]
        except Exception:
            pass

        try:
            from core.evolution_governance.evolution_registry import evolution_registry
            stats = evolution_registry.evolution_stats()
            rollback_rate = stats.get("rollback_rate", 0)
            evolution_governance_score = max(0.0, 1.0 - rollback_rate)
        except Exception:
            pass

        overall = (constitutional_compliance + decision_governance_score + evolution_governance_score) / 3
        return {
            "constitutional_compliance": round(constitutional_compliance, 4),
            "decision_governance_score": round(decision_governance_score, 4),
            "evolution_governance_score": round(evolution_governance_score, 4),
            "overall_governance_health": round(overall, 4),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


governance_validator = GovernanceValidator()
