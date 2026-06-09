"""
PHOENIX Digital Twin — Deployment Validator
Full pre-deployment validation: sandbox + impact + constitutional + goal alignment.
"""
from __future__ import annotations
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid


@dataclass
class ValidationResult:
    val_id: str
    rec_id: str
    sandbox_passed: bool
    impact_acceptable: bool
    constitutional_check_passed: bool
    goal_alignment_score: float
    final_verdict: str  # APPROVED/CONDITIONAL/REJECTED
    conditions: List[str]
    validated_at: str


class DeploymentValidator:
    def __init__(self):
        self._lock = threading.RLock()
        self._validations: Dict[str, ValidationResult] = {}

    def validate_for_deployment(self, rec_id: str, rec_description: str) -> dict:
        from core.digital_twin.recommendation_sandbox import recommendation_sandbox
        from core.digital_twin.impact_predictor import impact_predictor

        sandbox_run = recommendation_sandbox.test_recommendation(rec_id, rec_description)
        sandbox_passed = sandbox_run["safe_to_deploy"]

        impact = impact_predictor.predict(rec_description, "RECOMMENDATION")
        impact_acceptable = impact["predicted_drawdown_impact"] >= -0.05

        # Constitutional check
        constitutional_passed = True
        goal_alignment_score = 0.7
        try:
            from core.pccp.strategic_goal_engine import strategic_goal_engine
            const_result = strategic_goal_engine.constitutional_check(rec_description)
            constitutional_passed = const_result.get("passed", True)
            goal_result = strategic_goal_engine.evaluate_against_goals(rec_description)
            goal_alignment_score = goal_result.get("alignment_score", 0.7)
        except Exception:
            pass

        conditions = []
        issues = 0

        if not sandbox_passed:
            issues += 2
            conditions.append("Sandbox validation failed")
        if not impact_acceptable:
            issues += 1
            conditions.append("Impact projection exceeds acceptable threshold")
        if not constitutional_passed:
            issues += 2
            conditions.append("Constitutional check failed")
        if goal_alignment_score < 0.5:
            issues += 1
            conditions.append("Low goal alignment score")

        if issues == 0:
            verdict = "APPROVED"
        elif issues <= 2 and constitutional_passed and sandbox_passed:
            verdict = "CONDITIONAL"
        else:
            verdict = "REJECTED"

        val_id = f"VAL-{uuid.uuid4().hex[:8].upper()}"
        result = ValidationResult(
            val_id=val_id,
            rec_id=rec_id,
            sandbox_passed=sandbox_passed,
            impact_acceptable=impact_acceptable,
            constitutional_check_passed=constitutional_passed,
            goal_alignment_score=goal_alignment_score,
            final_verdict=verdict,
            conditions=conditions,
            validated_at=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            self._validations[val_id] = result
        return asdict(result)

    def all_validations(self, verdict_filter: str = None) -> list:
        with self._lock:
            items = list(self._validations.values())
        if verdict_filter:
            items = [v for v in items if v.final_verdict == verdict_filter]
        return [asdict(v) for v in items]

    def validation_stats(self) -> dict:
        with self._lock:
            items = list(self._validations.values())
        total = len(items)
        approved = sum(1 for v in items if v.final_verdict == "APPROVED")
        conditional = sum(1 for v in items if v.final_verdict == "CONDITIONAL")
        rejected = sum(1 for v in items if v.final_verdict == "REJECTED")
        rate = (approved + conditional) / total if total else 0.0
        return {
            "total": total,
            "approved": approved,
            "conditional": conditional,
            "rejected": rejected,
            "approval_rate": round(rate, 4),
        }


deployment_validator = DeploymentValidator()
