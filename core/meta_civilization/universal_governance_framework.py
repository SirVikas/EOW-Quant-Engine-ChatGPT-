"""Universal Governance Framework — universal governance principles."""
import threading
from dataclasses import dataclass
from datetime import datetime


@dataclass
class GovernancePrinciple:
    principle_id: str
    principle_text: str
    applies_to: str
    enforced: bool
    adopted_at: datetime


class UniversalGovernanceFramework:
    def __init__(self):
        self._lock = threading.RLock()
        self._principles: dict[str, GovernancePrinciple] = {}
        self._counter = 0
        self._seed()

    def _next_id(self) -> str:
        self._counter += 1
        return f"UGP-{self._counter:03d}"

    def _seed(self):
        seeds = [
            ("Transparency: All decisions must be traceable and auditable", "ALL"),
            ("Non-maleficence: Systems must not harm the financial ecosystem", "ALL"),
            ("Accountability: Every action must have an accountable owner", "GOVERNANCE"),
            ("Proportionality: Risk responses must be proportionate to threat severity", "TRADING"),
            ("Institutional memory: Knowledge must be preserved across sessions", "ALL"),
        ]
        for text, applies_to in seeds:
            self._adopt_internal(text, applies_to)

    def _adopt_internal(self, principle_text: str, applies_to: str) -> GovernancePrinciple:
        p = GovernancePrinciple(
            principle_id=self._next_id(),
            principle_text=principle_text,
            applies_to=applies_to,
            enforced=True,
            adopted_at=datetime.utcnow(),
        )
        self._principles[p.principle_id] = p
        return p

    def adopt(self, principle_text: str, applies_to: str) -> GovernancePrinciple:
        with self._lock:
            return self._adopt_internal(principle_text, applies_to)

    def all_principles(self) -> list[dict]:
        with self._lock:
            return [
                {"principle_id": p.principle_id, "principle_text": p.principle_text,
                 "applies_to": p.applies_to, "enforced": p.enforced,
                 "adopted_at": p.adopted_at.isoformat()}
                for p in self._principles.values()
            ]

    def enforced_principles(self) -> list[dict]:
        with self._lock:
            return [
                {"principle_id": p.principle_id, "principle_text": p.principle_text,
                 "applies_to": p.applies_to}
                for p in self._principles.values() if p.enforced
            ]


universal_governance_framework = UniversalGovernanceFramework()
