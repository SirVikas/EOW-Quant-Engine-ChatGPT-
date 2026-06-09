"""Capital Reserve Manager — manages capital reserves."""
import threading
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Reserve:
    reserve_id: str
    reserve_type: str
    amount: float
    target_amount: float
    status: str
    updated_at: datetime


class CapitalReserveManager:
    def __init__(self):
        self._lock = threading.RLock()
        self._reserves: dict[str, Reserve] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"RSV-{self._counter:03d}"

    def _compute_status(self, amount: float, target: float) -> str:
        if target == 0:
            return "ADEQUATE"
        ratio = amount / target
        if ratio >= 0.8:
            return "ADEQUATE"
        elif ratio >= 0.5:
            return "LOW"
        return "CRITICAL"

    def set_reserve(self, reserve_type: str, amount: float, target_amount: float) -> Reserve:
        with self._lock:
            # Update existing if same type
            for r in self._reserves.values():
                if r.reserve_type == reserve_type:
                    r.amount = amount
                    r.target_amount = target_amount
                    r.status = self._compute_status(amount, target_amount)
                    r.updated_at = datetime.utcnow()
                    return r
            r = Reserve(
                reserve_id=self._next_id(),
                reserve_type=reserve_type,
                amount=amount,
                target_amount=target_amount,
                status=self._compute_status(amount, target_amount),
                updated_at=datetime.utcnow(),
            )
            self._reserves[r.reserve_id] = r
            return r

    def check_reserves(self) -> list[dict]:
        with self._lock:
            return [
                {"reserve_id": r.reserve_id, "reserve_type": r.reserve_type,
                 "amount": r.amount, "target_amount": r.target_amount,
                 "status": r.status}
                for r in self._reserves.values()
            ]

    def reserve_health(self) -> str:
        with self._lock:
            if not self._reserves:
                return "ADEQUATE"
            statuses = [r.status for r in self._reserves.values()]
            if "CRITICAL" in statuses:
                return "CRITICAL"
            if "LOW" in statuses:
                return "LOW"
            return "ADEQUATE"


capital_reserve_manager = CapitalReserveManager()
