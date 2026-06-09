"""Agent Certification Engine — manages agent certifications."""
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class Certification:
    cert_id: str
    agent_id: str
    cert_type: str
    domain: str
    issued_at: datetime
    expires_at: Optional[datetime]
    status: str


class AgentCertificationEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._certs: dict[str, Certification] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"CRT-{self._counter:03d}"

    def issue(self, agent_id: str, cert_type: str, domain: str,
              expires_days: Optional[int] = None) -> Certification:
        with self._lock:
            issued = datetime.utcnow()
            expires = issued + timedelta(days=expires_days) if expires_days else None
            cert = Certification(
                cert_id=self._next_id(),
                agent_id=agent_id,
                cert_type=cert_type,
                domain=domain,
                issued_at=issued,
                expires_at=expires,
                status="ACTIVE",
            )
            self._certs[cert.cert_id] = cert
            return cert

    def certifications_for(self, agent_id: str) -> list[dict]:
        with self._lock:
            return [
                {"cert_id": c.cert_id, "cert_type": c.cert_type, "domain": c.domain,
                 "status": c.status, "issued_at": c.issued_at.isoformat(),
                 "expires_at": c.expires_at.isoformat() if c.expires_at else None}
                for c in self._certs.values() if c.agent_id == agent_id
            ]

    def expired_certs(self) -> list[dict]:
        now = datetime.utcnow()
        with self._lock:
            expired = []
            for c in self._certs.values():
                if c.expires_at and c.expires_at < now and c.status == "ACTIVE":
                    c.status = "EXPIRED"
                    expired.append({"cert_id": c.cert_id, "agent_id": c.agent_id,
                                    "cert_type": c.cert_type, "domain": c.domain})
            return expired


agent_certification_engine = AgentCertificationEngine()
