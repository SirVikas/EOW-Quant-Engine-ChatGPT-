"""Cross Instance Audit — audits compliance across federation instances."""
import threading
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AuditRecord:
    audit_id: str
    node_id: str
    audit_type: str
    result: str
    findings: list
    audited_at: datetime


class CrossInstanceAudit:
    def __init__(self):
        self._lock = threading.RLock()
        self._audits: dict[str, AuditRecord] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"CIA-{self._counter:03d}"

    def audit(self, node_id: str, audit_type: str, result: str,
              findings: list) -> AuditRecord:
        with self._lock:
            rec = AuditRecord(
                audit_id=self._next_id(),
                node_id=node_id,
                audit_type=audit_type,
                result=result,
                findings=list(findings),
                audited_at=datetime.utcnow(),
            )
            self._audits[rec.audit_id] = rec
            return rec

    def non_compliant_nodes(self) -> list[dict]:
        with self._lock:
            # Latest audit per node
            latest: dict[str, AuditRecord] = {}
            for a in sorted(self._audits.values(), key=lambda x: x.audited_at):
                latest[a.node_id] = a
            return [
                {"node_id": a.node_id, "result": a.result,
                 "findings": a.findings, "audited_at": a.audited_at.isoformat()}
                for a in latest.values() if a.result != "COMPLIANT"
            ]

    def audit_summary(self) -> dict:
        with self._lock:
            by_result: dict[str, int] = {}
            for a in self._audits.values():
                by_result[a.result] = by_result.get(a.result, 0) + 1
            return {"total_audits": len(self._audits), "by_result": by_result}


cross_instance_audit = CrossInstanceAudit()
