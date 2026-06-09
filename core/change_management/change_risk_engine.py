"""Change Risk Engine — assesses change risk."""
import threading
from typing import List

RISK_SCORE_MAP = {"LOW": 20, "MEDIUM": 50, "HIGH": 75, "CRITICAL": 95}


class ChangeRiskEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def assess(self, change_id: str) -> dict:
        from core.change_management.change_registry import change_registry
        with self._lock:
            change = change_registry.get(change_id)
            if change is None:
                return {"change_id": change_id, "risk_score": 0, "risk_factors": [], "recommendation": "UNKNOWN"}
            risk_score = RISK_SCORE_MAP.get(change.risk_level, 50)
            risk_factors = []
            if change.risk_level in ("HIGH", "CRITICAL"):
                risk_factors.append(f"Risk level is {change.risk_level}")
            if change.change_type == "ARCHITECTURAL":
                risk_factors.append("Architectural changes have broad impact")
                risk_score = min(100, risk_score + 10)
            recommendation = (
                "HOLD" if risk_score >= 75
                else "CAUTION" if risk_score >= 40
                else "PROCEED"
            )
            return {
                "change_id": change_id,
                "risk_score": risk_score,
                "risk_factors": risk_factors,
                "recommendation": recommendation,
            }

    def high_risk_changes(self) -> List[dict]:
        from core.change_management.change_registry import change_registry
        with self._lock:
            return [
                self.assess(c["change_id"])
                for c in change_registry.pending_changes()
                if c["risk_level"] in ("HIGH", "CRITICAL")
            ]


change_risk_engine = ChangeRiskEngine()
