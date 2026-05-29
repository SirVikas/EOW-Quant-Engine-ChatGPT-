"""FTD-AIL-001: Finding Generator — converts rule hits into Finding objects with lineage IDs."""
from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class Finding:
    lineage_id: str
    title: str
    category: str           # PERFORMANCE | RISK | GENOME | COST | SYSTEM
    severity: str           # CRITICAL | HIGH | MEDIUM | LOW | INFO
    evidence: list
    confidence_score: float
    sample_size: int
    economic_impact_est: str
    risk_level: str
    recommendation: str
    ftd_draft: Optional[str]
    status: str             # PENDING | APPROVED | REJECTED | NEEDS_MORE_EVIDENCE
    created_at: str
    approved_at: Optional[str]
    rejected_at: Optional[str]
    rejection_reason: Optional[str]
    source_reports: list
    rule: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _make_lineage_id(content: dict) -> str:
    ts_ms  = int(time.time() * 1000)
    ts_str = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S") + f"{ts_ms % 1000:03d}"
    payload = json.dumps(content, sort_keys=True, default=str)
    hash16  = hashlib.sha256(payload.encode()).hexdigest()[:16]
    return f"AIL-{ts_str}-{hash16}"


def generate_findings(rule_hits: list[dict]) -> list[Finding]:
    findings = []
    for hit in rule_hits:
        content = {k: v for k, v in hit.items() if k not in ("evidence",)}
        lineage_id = _make_lineage_id(content)
        finding = Finding(
            lineage_id=lineage_id,
            title=hit["title"],
            category=hit["category"],
            severity=hit["severity"],
            evidence=hit.get("evidence", []),
            confidence_score=hit.get("confidence_score", 0.5),
            sample_size=hit.get("sample_size", 0),
            economic_impact_est=hit.get("economic_impact_est", "UNKNOWN"),
            risk_level=hit.get("risk_level", "LOW"),
            recommendation=hit.get("recommendation", ""),
            ftd_draft=None,
            status="PENDING",
            created_at=datetime.now(timezone.utc).isoformat(),
            approved_at=None,
            rejected_at=None,
            rejection_reason=None,
            source_reports=hit.get("source_reports", []),
            rule=hit.get("rule", ""),
        )
        findings.append(finding)
    return findings
