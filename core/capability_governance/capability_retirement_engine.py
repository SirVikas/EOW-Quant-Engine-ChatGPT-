"""Capability Retirement Engine — manages formal retirement of deprecated capabilities."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class RetirementRecord:
    record_id: str
    cap_id: str
    cap_name: str
    retirement_reason: str
    replacement_cap_id: Optional[str]
    retired_by: str
    retired_at: str
    data_preserved: bool


class CapabilityRetirementEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: List[RetirementRecord] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"RET-{self._counter:03d}"

    def retire(self, cap_id: str, reason: str, replacement_cap_id: Optional[str] = None,
               retired_by: str = "SYSTEM") -> dict:
        with self._lock:
            from core.capability_governance.capability_registry import capability_registry
            caps = capability_registry.all_capabilities()
            cap_name = cap_id
            for c in caps:
                if c["cap_id"] == cap_id:
                    cap_name = c["name"]
                    break
            capability_registry.retire(cap_id)

            record = RetirementRecord(
                record_id=self._next_id(),
                cap_id=cap_id,
                cap_name=cap_name,
                retirement_reason=reason,
                replacement_cap_id=replacement_cap_id,
                retired_by=retired_by,
                retired_at=datetime.now(timezone.utc).isoformat(),
                data_preserved=True,
            )
            self._records.append(record)
            return asdict(record)

    def retirement_history(self, limit: int = 20) -> List[dict]:
        with self._lock:
            return [asdict(r) for r in self._records[-limit:]]

    def retirement_stats(self) -> dict:
        with self._lock:
            total = len(self._records)
            with_replacement = sum(1 for r in self._records if r.replacement_cap_id)
            preserved = sum(1 for r in self._records if r.data_preserved)
            return {
                "total_retired": total,
                "with_replacement": with_replacement,
                "data_preserved_count": preserved,
            }


capability_retirement_engine = CapabilityRetirementEngine()
