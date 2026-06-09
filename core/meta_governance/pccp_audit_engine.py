"""
PHOENIX Meta Governance — PCCP Audit Engine
Audits PCCP coordination quality, conflict resolution, and priority decisions.
"""
from __future__ import annotations
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List
import uuid


@dataclass
class AuditRecord:
    audit_id: str
    audit_type: str   # COORDINATION_CYCLE/CONFLICT_RESOLUTION/PRIORITY_DECISION/BUS_ROUTING
    subject: str
    findings: List[str]
    compliance_score: float
    audited_at: str


class PCCPAuditEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: List[AuditRecord] = []

    def _make_record(self, audit_type: str, subject: str, findings: list, score: float) -> dict:
        rec = AuditRecord(
            audit_id=f"AUDIT-{uuid.uuid4().hex[:8].upper()}",
            audit_type=audit_type,
            subject=subject,
            findings=findings,
            compliance_score=score,
            audited_at=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            self._records.append(rec)
        return asdict(rec)

    def audit_coordination_cycle(self) -> dict:
        findings = []
        score = 1.0
        try:
            from core.pccp.pccp_orchestrator import pccp_orchestrator
            status = pccp_orchestrator.system_status()
            layers = status.get("registered_layers", [])
            if len(layers) == 0:
                findings.append("No layers registered in PCCP")
                score -= 0.3
            critical = [l for l in layers if l.get("health") == "CRITICAL"]
            if critical:
                findings.append(f"{len(critical)} CRITICAL layers detected")
                score -= 0.2 * len(critical)
        except Exception as e:
            findings.append(f"PCCP orchestrator unavailable: {e}")
            score -= 0.5

        score = max(0.0, score)
        return self._make_record("COORDINATION_CYCLE", "PCCP Orchestrator", findings, score)

    def audit_conflict_resolutions(self) -> dict:
        findings = []
        score = 1.0
        try:
            from core.pccp.conflict_resolver import conflict_resolver
            stats = conflict_resolver.conflict_stats()
            unresolved = stats.get("open_conflicts", 0)
            if unresolved > 5:
                findings.append(f"{unresolved} unresolved conflicts — above threshold")
                score -= 0.3
        except Exception as e:
            findings.append(f"Conflict resolver unavailable: {e}")
            score -= 0.3
        score = max(0.0, score)
        return self._make_record("CONFLICT_RESOLUTION", "Conflict Resolver", findings, score)

    def audit_priority_decisions(self) -> dict:
        findings = []
        score = 1.0
        try:
            from core.pccp.global_priority_manager import global_priority_manager
            summary = global_priority_manager.priority_summary()
            queued = summary.get("queued", [])
            stale = [q for q in queued if q.get("age_days", 0) > 7]
            if stale:
                findings.append(f"{len(stale)} QUEUED priorities older than 7 days")
                score -= 0.2
        except Exception as e:
            findings.append(f"Priority manager unavailable: {e}")
            score -= 0.2
        score = max(0.0, score)
        return self._make_record("PRIORITY_DECISION", "Global Priority Manager", findings, score)

    def full_pccp_audit(self) -> dict:
        a1 = self.audit_coordination_cycle()
        a2 = self.audit_conflict_resolutions()
        a3 = self.audit_priority_decisions()
        audits = [a1, a2, a3]
        overall = sum(a["compliance_score"] for a in audits) / len(audits)
        all_findings = [f for a in audits for f in a["findings"]]
        return {
            "audits": audits,
            "overall_compliance_score": round(overall, 4),
            "findings_summary": all_findings,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


pccp_audit_engine = PCCPAuditEngine()
