"""Real Market Validation Engine — orchestrates end-to-end market validation."""
import threading
import time


class RealMarketValidationEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def validate(self, subject_id: str, subject_type: str, expected_outcome: dict,
                 actual_outcome: dict, market_regime: str = "UNKNOWN") -> dict:
        from core.real_market_validation.outcome_tracker import outcome_tracker
        from core.real_market_validation.expectation_vs_reality import expectation_vs_reality
        from core.real_market_validation.market_evidence_registry import market_evidence_registry

        with self._lock:
            outcome_tracker.register_expectation(subject_id, subject_type, expected_outcome)
            outcome_result = outcome_tracker.record_actual(subject_id, actual_outcome)

            evr_report = expectation_vs_reality.generate_report(
                subject_id, expected_outcome, actual_outcome, market_regime
            )

            confidence = evr_report.get("accuracy_score", 0.5)
            condition = f"regime={market_regime}, status={outcome_result.get('status', 'UNKNOWN')}"
            evidence_id = market_evidence_registry.record(
                subject_id, subject_type, condition, confidence,
                notes=f"Validated via RMV engine"
            )

            status = outcome_result.get("status", "UNKNOWN")
            verdict = "PASS" if status == "CONFIRMED" else ("FAIL" if status == "FAILED" else "INCONCLUSIVE")

            return {
                "subject_id": subject_id,
                "subject_type": subject_type,
                "verdict": verdict,
                "outcome_status": status,
                "variance_pct": outcome_result.get("variance_pct", 0.0),
                "accuracy_score": confidence,
                "evr_report_id": evr_report.get("report_id"),
                "evidence_id": evidence_id,
                "market_regime": market_regime,
                "validated_at": time.time(),
            }

    def validation_summary(self) -> dict:
        from core.real_market_validation.outcome_tracker import outcome_tracker
        from core.real_market_validation.expectation_vs_reality import expectation_vs_reality
        from core.real_market_validation.market_evidence_registry import market_evidence_registry

        return {
            "outcome_stats": outcome_tracker.outcome_stats(),
            "accuracy_trend": expectation_vs_reality.accuracy_trend(),
            "evidence_stats": market_evidence_registry.evidence_stats(),
            "generated_at": time.time(),
        }

    def pending_validations(self) -> list:
        from core.real_market_validation.outcome_tracker import outcome_tracker
        return outcome_tracker.pending_validations()


real_market_validation_engine = RealMarketValidationEngine()
