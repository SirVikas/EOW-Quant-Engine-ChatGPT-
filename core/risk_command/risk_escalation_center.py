"""Risk Escalation Center — manages risk escalations."""
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Escalation:
    esc_id: str
    radar_entry_id: str
    escalated_to: str
    escalation_reason: str
    status: str
    created_at: datetime
    resolved_at: Optional[datetime]


class RiskEscalationCenter:
    def __init__(self):
        self._lock = threading.RLock()
        self._escalations: dict[str, Escalation] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"ESC-{self._counter:03d}"

    def escalate(self, radar_entry_id: str, escalated_to: str, reason: str) -> Escalation:
        with self._lock:
            esc = Escalation(
                esc_id=self._next_id(),
                radar_entry_id=radar_entry_id,
                escalated_to=escalated_to,
                escalation_reason=reason,
                status="OPEN",
                created_at=datetime.utcnow(),
                resolved_at=None,
            )
            self._escalations[esc.esc_id] = esc
            return esc

    def resolve(self, esc_id: str) -> Optional[Escalation]:
        with self._lock:
            esc = self._escalations.get(esc_id)
            if esc:
                esc.status = "RESOLVED"
                esc.resolved_at = datetime.utcnow()
            return esc

    def open_escalations(self) -> list[dict]:
        with self._lock:
            return [
                {"esc_id": e.esc_id, "radar_entry_id": e.radar_entry_id,
                 "escalated_to": e.escalated_to, "escalation_reason": e.escalation_reason,
                 "status": e.status, "created_at": e.created_at.isoformat()}
                for e in self._escalations.values() if e.status != "RESOLVED"
            ]


risk_escalation_center = RiskEscalationCenter()
