"""Decision Accuracy Tracker — master decision intelligence engine."""
import threading


class DecisionAccuracyTracker:
    def __init__(self):
        self._lock = threading.RLock()

    def accuracy_report(self) -> dict:
        from core.decision_intelligence.decision_registry import decision_registry
        from core.decision_intelligence.decision_regret_tracker import decision_regret_tracker
        with self._lock:
            decisions = decision_registry.all_decisions()
            total = len(decisions)
            with_outcomes = [d for d in decisions if d["actual_outcome"] is not None]
            matches = [d for d in with_outcomes if d["actual_outcome"] == d["expected_outcome"]]
            accuracy_pct = (len(matches) / len(with_outcomes) * 100) if with_outcomes else 0.0
            avg_conf = (sum(d["confidence_pct"] for d in decisions) / total) if total else 0.0
            regret_summary = decision_regret_tracker.regret_summary()
            return {
                "total_decisions": total,
                "decisions_with_outcomes": len(with_outcomes),
                "accuracy_pct": round(accuracy_pct, 2),
                "avg_confidence": round(avg_conf, 2),
                "regret_count": regret_summary["total_regrets"],
            }

    def intelligence_summary(self) -> dict:
        with self._lock:
            report = self.accuracy_report()
            report["status"] = "HEALTHY" if report["accuracy_pct"] >= 60 else "NEEDS_REVIEW"
            return report


decision_accuracy_tracker = DecisionAccuracyTracker()
