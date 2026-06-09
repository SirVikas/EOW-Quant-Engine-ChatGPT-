"""Capital Deployment Engine — tracks capital deployment decisions."""
import threading
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Deployment:
    deploy_id: str
    amount: float
    asset_class: str
    deployment_type: str
    rationale: str
    executed_at: datetime


class CapitalDeploymentEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._deployments: list[Deployment] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"CDP-{self._counter:03d}"

    def record_deployment(self, amount: float, asset_class: str,
                          deployment_type: str, rationale: str) -> Deployment:
        with self._lock:
            d = Deployment(
                deploy_id=self._next_id(),
                amount=amount,
                asset_class=asset_class,
                deployment_type=deployment_type,
                rationale=rationale,
                executed_at=datetime.utcnow(),
            )
            self._deployments.append(d)
            return d

    def recent_deployments(self, n: int = 20) -> list[dict]:
        with self._lock:
            return [
                {"deploy_id": d.deploy_id, "amount": d.amount,
                 "asset_class": d.asset_class, "deployment_type": d.deployment_type,
                 "rationale": d.rationale, "executed_at": d.executed_at.isoformat()}
                for d in self._deployments[-n:]
            ]

    def deployment_summary(self) -> dict:
        with self._lock:
            by_type: dict[str, float] = {}
            for d in self._deployments:
                by_type[d.deployment_type] = by_type.get(d.deployment_type, 0) + d.amount
            return {
                "total_deployments": len(self._deployments),
                "total_amount": sum(d.amount for d in self._deployments),
                "by_type": by_type,
            }


capital_deployment_engine = CapitalDeploymentEngine()
