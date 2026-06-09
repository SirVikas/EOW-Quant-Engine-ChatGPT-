"""Federation Policy Manager — manages federation-wide policies."""
import threading
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FederationPolicy:
    policy_id: str
    policy_name: str
    applies_to_all: bool
    policy_text: str
    enforced_since: datetime
    status: str


class FederationPolicyManager:
    def __init__(self):
        self._lock = threading.RLock()
        self._policies: dict[str, FederationPolicy] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"FP-{self._counter:03d}"

    def publish(self, policy_name: str, policy_text: str,
                applies_to_all: bool = True) -> FederationPolicy:
        with self._lock:
            p = FederationPolicy(
                policy_id=self._next_id(),
                policy_name=policy_name,
                applies_to_all=applies_to_all,
                policy_text=policy_text,
                enforced_since=datetime.utcnow(),
                status="ACTIVE",
            )
            self._policies[p.policy_id] = p
            return p

    def retire(self, policy_id: str) -> bool:
        with self._lock:
            p = self._policies.get(policy_id)
            if p:
                p.status = "RETIRED"
                return True
            return False

    def active_policies(self) -> list[dict]:
        with self._lock:
            return [
                {"policy_id": p.policy_id, "policy_name": p.policy_name,
                 "applies_to_all": p.applies_to_all,
                 "enforced_since": p.enforced_since.isoformat()}
                for p in self._policies.values() if p.status == "ACTIVE"
            ]


federation_policy_manager = FederationPolicyManager()
