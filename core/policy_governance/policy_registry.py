"""Policy registry — institutional policy store."""
import threading
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional


@dataclass
class Policy:
    policy_id: str
    title: str
    category: str
    rules: list
    status: str
    current_version: int
    created_at: str
    approved_at: Optional[str]


class PolicyRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._policies: list = []
        self._counter = 0
        self._seed_foundational_policies()

    def _seed_foundational_policies(self):
        seeds = [
            ("RISK_POSITION_LIMITS", "RISK",
             ["max position size must not exceed 5% of portfolio", "stop loss mandatory on all positions",
              "no single asset above 20% allocation"]),
            ("TRUST_PROMOTION_CRITERIA", "TRUST",
             ["trust score above 0.7 required for promotion", "minimum 10 trades required before promotion",
              "manual review required for ELITE tier"]),
            ("EVOLUTION_APPROVAL_REQUIRED", "EVOLUTION",
             ["all evolution changes require approval", "rollback plan mandatory before deployment",
              "canary deployment required for major changes"]),
            ("CAPITAL_DRAWDOWN_LIMITS", "CAPITAL",
             ["max daily drawdown 3% of equity", "max weekly drawdown 10% of equity",
              "halt trading if monthly drawdown exceeds 15%"]),
            ("GOVERNANCE_AUDIT_FREQUENCY", "GOVERNANCE",
             ["weekly automated audit required", "monthly human review required",
              "quarterly board review required"]),
        ]
        for title, cat, rules in seeds:
            self._counter += 1
            now = datetime.utcnow().isoformat()
            p = Policy(
                policy_id=f"POL-{self._counter:03d}",
                title=title, category=cat, rules=rules,
                status="ACTIVE", current_version=1,
                created_at=now, approved_at=now,
            )
            self._policies.append(p)

    def create(self, title: str, category: str, rules: list) -> str:
        with self._lock:
            self._counter += 1
            policy_id = f"POL-{self._counter:03d}"
            p = Policy(
                policy_id=policy_id, title=title, category=category, rules=rules,
                status="DRAFT", current_version=1,
                created_at=datetime.utcnow().isoformat(), approved_at=None,
            )
            self._policies.append(p)
            return policy_id

    def activate(self, policy_id: str) -> bool:
        with self._lock:
            for p in self._policies:
                if p.policy_id == policy_id:
                    p.status = "ACTIVE"
                    p.approved_at = datetime.utcnow().isoformat()
                    return True
            return False

    def deprecate(self, policy_id: str) -> bool:
        with self._lock:
            for p in self._policies:
                if p.policy_id == policy_id:
                    p.status = "DEPRECATED"
                    return True
            return False

    def archive(self, policy_id: str) -> bool:
        with self._lock:
            for p in self._policies:
                if p.policy_id == policy_id:
                    p.status = "ARCHIVED"
                    return True
            return False

    def active_policies(self, category: Optional[str] = None) -> list:
        with self._lock:
            result = [p for p in self._policies if p.status == "ACTIVE"]
            if category:
                result = [p for p in result if p.category == category]
            return [asdict(p) for p in result]

    def policy_stats(self) -> dict:
        with self._lock:
            total = len(self._policies)
            by_cat: dict = {}
            by_status: dict = {}
            for p in self._policies:
                by_cat[p.category] = by_cat.get(p.category, 0) + 1
                by_status[p.status] = by_status.get(p.status, 0) + 1
            return {
                "total": total,
                "active": by_status.get("ACTIVE", 0),
                "draft": by_status.get("DRAFT", 0),
                "deprecated": by_status.get("DEPRECATED", 0),
                "by_category": by_cat,
            }


policy_registry = PolicyRegistry()
