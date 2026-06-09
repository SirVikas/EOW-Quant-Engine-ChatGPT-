"""
Evidence retention controller — per-type retention policies for the
Evidence Warehouse. Advisory by default: reports expired candidates;
apply_retention() performs the prune.
"""
import threading
import time
from typing import Dict

# Retention horizon in days per evidence type; None = retained permanently.
_DEFAULT_POLICIES: Dict[str, int] = {
    "SIMULATION": 90,
    "RECOMMENDATION": 180,
    "TRUST": 365,
    "VALIDATION": 365,
}
_FALLBACK_DAYS = 365


class EvidenceRetentionController:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._policies: Dict[str, int] = dict(_DEFAULT_POLICIES)
        self._pruned_total = 0
        self._last_applied = 0.0

    def set_policy(self, evidence_type: str, retention_days: int) -> dict:
        with self._lock:
            self._policies[evidence_type] = max(1, int(retention_days))
            return {"evidence_type": evidence_type,
                    "retention_days": self._policies[evidence_type]}

    def _expired_ids(self) -> list:
        from core.evidence_warehouse.evidence_registry import evidence_registry
        now = time.time()
        expired = []
        with evidence_registry._lock:
            for item in evidence_registry._items.values():
                days = self._policies.get(item.evidence_type, _FALLBACK_DAYS)
                if now - item.created_at > days * 86_400:
                    expired.append(item.item_id)
        return expired

    def retention_report(self) -> dict:
        try:
            expired = self._expired_ids()
        except Exception:
            expired = []
        with self._lock:
            return {
                "policies_days": dict(self._policies),
                "fallback_days": _FALLBACK_DAYS,
                "expired_candidates": len(expired),
                "pruned_total": self._pruned_total,
                "last_applied": self._last_applied,
            }

    def apply_retention(self) -> dict:
        from core.evidence_warehouse.evidence_registry import evidence_registry
        expired = self._expired_ids()
        with evidence_registry._lock:
            for item_id in expired:
                evidence_registry._items.pop(item_id, None)
        with self._lock:
            self._pruned_total += len(expired)
            self._last_applied = time.time()
        return {"pruned": len(expired), "pruned_total": self._pruned_total}


evidence_retention_controller = EvidenceRetentionController()
