"""GAP-08: Economic Claim Auditor — audits all economic claims made by the system."""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Dict, Any, List

from loguru import logger


@dataclass
class AuditRecord:
    audit_id: str
    claim_source: str
    claim_text: str
    supporting_evidence: List[str]
    audit_result: str  # SUPPORTED/UNSUPPORTED/PARTIALLY_SUPPORTED
    audited_at: int


class EconomicClaimAuditor:
    """Audits all economic claims made by the system. Thread-safe."""

    def __init__(self):
        self._lock = threading.RLock()
        self._records: Dict[str, AuditRecord] = {}
        self._counter = 0
        logger.info("[GAP-08] EconomicClaimAuditor initialized")

    def _next_id(self) -> str:
        self._counter += 1
        return f"ECA-{self._counter:03d}"

    def _determine_result(self, supporting_evidence: List[str]) -> str:
        n = len(supporting_evidence)
        if n >= 3:
            return "SUPPORTED"
        elif n >= 1:
            return "PARTIALLY_SUPPORTED"
        return "UNSUPPORTED"

    def audit(self, claim_source: str, claim_text: str, supporting_evidence: List[str]) -> str:
        with self._lock:
            aid = self._next_id()
            self._records[aid] = AuditRecord(
                audit_id=aid,
                claim_source=claim_source,
                claim_text=claim_text,
                supporting_evidence=list(supporting_evidence),
                audit_result=self._determine_result(supporting_evidence),
                audited_at=int(time.time() * 1000),
            )
            return aid

    def unsupported_claims(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [vars(r) for r in self._records.values() if r.audit_result == "UNSUPPORTED"]

    def audit_summary(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._records)
            supported = sum(1 for r in self._records.values() if r.audit_result == "SUPPORTED")
            unsupported = sum(1 for r in self._records.values() if r.audit_result == "UNSUPPORTED")
            partial = total - supported - unsupported
            return {
                "total_audited": total,
                "supported": supported,
                "partially_supported": partial,
                "unsupported": unsupported,
                "support_rate_pct": round(supported / total * 100, 2) if total > 0 else 0.0,
                "ts": int(time.time() * 1000),
            }


economic_claim_auditor = EconomicClaimAuditor()
