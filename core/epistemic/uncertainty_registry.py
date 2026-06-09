"""
PHOENIX Epistemic Intelligence — Uncertainty Registry
Registers and tracks known and unknown uncertainties across domains.
"""
from __future__ import annotations
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid


@dataclass
class Uncertainty:
    uncertainty_id: str
    domain: str
    description: str
    uncertainty_type: str  # KNOWN_UNKNOWN/UNKNOWN_UNKNOWN/MODEL_UNCERTAINTY/DATA_UNCERTAINTY
    severity: str          # LOW/MEDIUM/HIGH/CRITICAL
    registered_at: str
    resolved: bool


class UncertaintyRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._uncertainties: Dict[str, Uncertainty] = {}

    def register(
        self, domain: str, description: str, uncertainty_type: str, severity: str = "MEDIUM"
    ) -> str:
        uid = f"UNC-{uuid.uuid4().hex[:8].upper()}"
        u = Uncertainty(
            uncertainty_id=uid,
            domain=domain,
            description=description,
            uncertainty_type=uncertainty_type,
            severity=severity,
            registered_at=datetime.now(timezone.utc).isoformat(),
            resolved=False,
        )
        with self._lock:
            self._uncertainties[uid] = u
        return uid

    def resolve(self, uncertainty_id: str) -> dict:
        with self._lock:
            u = self._uncertainties.get(uncertainty_id)
            if u:
                u.resolved = True
                return asdict(u)
        return {"error": f"{uncertainty_id} not found"}

    def open_uncertainties(self, domain: str = None) -> list:
        with self._lock:
            items = [u for u in self._uncertainties.values() if not u.resolved]
        if domain:
            items = [u for u in items if u.domain == domain]
        return [asdict(u) for u in items]

    def uncertainty_summary(self) -> dict:
        with self._lock:
            items = list(self._uncertainties.values())
        total = len(items)
        open_u = [u for u in items if not u.resolved]
        resolved = total - len(open_u)
        by_type: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        critical_open = 0
        for u in open_u:
            by_type[u.uncertainty_type] = by_type.get(u.uncertainty_type, 0) + 1
            by_severity[u.severity] = by_severity.get(u.severity, 0) + 1
            if u.severity == "CRITICAL":
                critical_open += 1
        return {
            "total": total,
            "open": len(open_u),
            "resolved": resolved,
            "by_type": by_type,
            "by_severity": by_severity,
            "critical_open": critical_open,
        }


uncertainty_registry = UncertaintyRegistry()
