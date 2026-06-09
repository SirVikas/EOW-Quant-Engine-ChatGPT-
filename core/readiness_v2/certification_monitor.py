"""
Certification monitor — tracks live certification status for all institutional dimensions.
Pre-seeded with 5 core certifications in PENDING state.
"""
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List


@dataclass
class CertStatus:
    cert_id: str
    certification_name: str
    last_checked: str
    status: str   # CERTIFIED / LAPSED / PENDING
    score: float  # 0–100
    checked_at: str


_SEED_CERTS = [
    "Architecture",
    "Governance",
    "Validation",
    "Operations",
    "Economic",
]


class CertificationMonitor:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._certs: Dict[str, CertStatus] = {}
        self._counter = 0
        now = datetime.utcnow().isoformat()
        for name in _SEED_CERTS:
            self._counter += 1
            self._certs[name] = CertStatus(
                cert_id=f"CMN-{self._counter:03d}",
                certification_name=name,
                last_checked=now,
                status="PENDING",
                score=0.0,
                checked_at=now,
            )

    def _next_id(self) -> str:
        self._counter += 1
        return f"CMN-{self._counter:03d}"

    def update(self, certification_name: str, status: str, score: float) -> CertStatus:
        now = datetime.utcnow().isoformat()
        with self._lock:
            if certification_name in self._certs:
                existing = self._certs[certification_name]
                existing.status = status
                existing.score = score
                existing.last_checked = now
                existing.checked_at = now
                return existing
            cert = CertStatus(
                cert_id=self._next_id(),
                certification_name=certification_name,
                last_checked=now,
                status=status,
                score=score,
                checked_at=now,
            )
            self._certs[certification_name] = cert
            return cert

    def lapsed_certifications(self) -> List[CertStatus]:
        with self._lock:
            return [c for c in self._certs.values() if c.status == "LAPSED"]

    def certification_summary(self) -> dict:
        with self._lock:
            certs = list(self._certs.values())
            return {
                "total": len(certs),
                "certified": sum(1 for c in certs if c.status == "CERTIFIED"),
                "lapsed": sum(1 for c in certs if c.status == "LAPSED"),
                "pending": sum(1 for c in certs if c.status == "PENDING"),
                "certifications": {
                    c.certification_name: {"status": c.status, "score": c.score}
                    for c in certs
                },
            }


certification_monitor = CertificationMonitor()
