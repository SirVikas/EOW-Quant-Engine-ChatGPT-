"""Policy enforcement engine — compliance checking."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class EnforcementRecord:
    record_id: str
    policy_id: str
    action_checked: str
    compliant: bool
    violation_detail: str
    checked_at: str


class PolicyEnforcementEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: list = []
        self._counter = 0

    def check_compliance(self, policy_id: str, action_description: str) -> dict:
        from core.policy_governance.policy_registry import policy_registry
        policies = policy_registry.active_policies()
        policy = next((p for p in policies if p["policy_id"] == policy_id), None)
        if not policy:
            result = {"compliant": False, "violation_detail": f"Policy {policy_id} not found or not active"}
        else:
            rules = policy.get("rules", [])
            action_lower = action_description.lower()
            violated = []
            for rule in rules:
                keywords = rule.lower().split()
                if any(kw in action_lower for kw in keywords if len(kw) > 4):
                    violated.append(rule)
            compliant = len(violated) == 0
            violation_detail = "; ".join(violated) if violated else ""
            result = {"compliant": compliant, "violation_detail": violation_detail}

        self.record_enforcement(policy_id, action_description, result["compliant"], result["violation_detail"])
        return result

    def record_enforcement(self, policy_id: str, action_checked: str, compliant: bool,
                            violation_detail: str = "") -> dict:
        with self._lock:
            self._counter += 1
            r = EnforcementRecord(
                record_id=f"ENF-{self._counter:04d}",
                policy_id=policy_id,
                action_checked=action_checked,
                compliant=compliant,
                violation_detail=violation_detail,
                checked_at=datetime.utcnow().isoformat(),
            )
            self._records.append(r)
            return asdict(r)

    def violation_report(self, policy_id: Optional[str] = None) -> list:
        with self._lock:
            result = [r for r in self._records if not r.compliant]
            if policy_id:
                result = [r for r in result if r.policy_id == policy_id]
            return [asdict(r) for r in result]

    def enforcement_stats(self) -> dict:
        with self._lock:
            total = len(self._records)
            compliant = sum(1 for r in self._records if r.compliant)
            violations = total - compliant
            rate = compliant / max(1, total)
            return {"total_checks": total, "compliant": compliant, "violations": violations,
                    "compliance_rate": rate}


policy_enforcement_engine = PolicyEnforcementEngine()
