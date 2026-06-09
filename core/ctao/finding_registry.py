"""CTAO — Finding Registry: captures and stores all CT Scan findings."""
import threading
import time
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional


@dataclass
class CTFinding:
    finding_id: str
    category: str
    severity: str
    confidence: float
    detected_by: str
    description: str
    raw_data: dict
    status: str
    created_at: float
    resolved_at: float


class FindingRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._findings: List[CTFinding] = []
        self._counter: Dict[str, int] = {}

    def _next_id(self, year: int) -> str:
        key = str(year)
        self._counter[key] = self._counter.get(key, 0) + 1
        return f"CTF-{year}-{self._counter[key]:03d}"

    def record_finding(self, category: str, severity: str, confidence: float,
                       detected_by: str, description: str, raw_data: dict = None) -> str:
        with self._lock:
            year = int(time.strftime("%Y"))
            finding_id = self._next_id(year)
            f = CTFinding(
                finding_id=finding_id,
                category=category,
                severity=severity,
                confidence=confidence,
                detected_by=detected_by,
                description=description,
                raw_data=raw_data or {},
                status="OPEN",
                created_at=time.time(),
                resolved_at=0.0,
            )
            self._findings.append(f)
            return finding_id

    def acknowledge(self, finding_id: str) -> dict:
        with self._lock:
            for f in self._findings:
                if f.finding_id == finding_id:
                    f.status = "ACKNOWLEDGED"
                    return {"updated": finding_id, "status": "ACKNOWLEDGED"}
            return {"error": f"Finding {finding_id} not found"}

    def resolve(self, finding_id: str) -> dict:
        with self._lock:
            for f in self._findings:
                if f.finding_id == finding_id:
                    f.status = "RESOLVED"
                    f.resolved_at = time.time()
                    return {"updated": finding_id, "status": "RESOLVED"}
            return {"error": f"Finding {finding_id} not found"}

    def dismiss(self, finding_id: str) -> dict:
        with self._lock:
            for f in self._findings:
                if f.finding_id == finding_id:
                    f.status = "DISMISSED"
                    return {"updated": finding_id, "status": "DISMISSED"}
            return {"error": f"Finding {finding_id} not found"}

    def all_findings(self, status_filter: str = None, severity_filter: str = None) -> List[dict]:
        with self._lock:
            result = self._findings
            if status_filter:
                result = [f for f in result if f.status == status_filter]
            if severity_filter:
                result = [f for f in result if f.severity == severity_filter]
            return [asdict(f) for f in result]

    def open_findings(self) -> List[dict]:
        with self._lock:
            return [asdict(f) for f in self._findings if f.status in ("OPEN", "ACKNOWLEDGED")]

    def finding_stats(self) -> dict:
        with self._lock:
            total = len(self._findings)
            by_severity: Dict[str, int] = {}
            by_category: Dict[str, int] = {}
            for f in self._findings:
                by_severity[f.severity] = by_severity.get(f.severity, 0) + 1
                by_category[f.category] = by_category.get(f.category, 0) + 1
            return {
                "total": total,
                "open": sum(1 for f in self._findings if f.status == "OPEN"),
                "resolved": sum(1 for f in self._findings if f.status == "RESOLVED"),
                "dismissed": sum(1 for f in self._findings if f.status == "DISMISSED"),
                "by_severity": by_severity,
                "by_category": by_category,
            }


finding_registry = FindingRegistry()
