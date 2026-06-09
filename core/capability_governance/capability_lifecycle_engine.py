"""Capability Lifecycle Engine — aggregated lifecycle health across all capabilities."""
import threading
from datetime import datetime, timezone


class CapabilityLifecycleEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def lifecycle_report(self) -> dict:
        with self._lock:
            from core.capability_governance.capability_registry import capability_registry
            from core.capability_governance.capability_maturity_tracker import capability_maturity_tracker
            from core.capability_governance.capability_retirement_engine import capability_retirement_engine

            return {
                "capability_stats": capability_registry.capability_stats(),
                "maturity_summary": {
                    "total_assessments": len(capability_maturity_tracker.all_assessments()),
                    "needing_attention": len(capability_maturity_tracker.capabilities_needing_attention()),
                },
                "retirement_history": capability_retirement_engine.retirement_stats(),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

    def advance_ready_capabilities(self) -> dict:
        with self._lock:
            from core.capability_governance.capability_registry import capability_registry
            from core.capability_governance.capability_maturity_tracker import capability_maturity_tracker

            advanced = []
            for cap in capability_registry.all_capabilities():
                if cap["maturity_stage"] not in ("EXPERIMENTAL", "EMERGING"):
                    continue
                cap_id = cap["cap_id"]
                assessments = capability_maturity_tracker.all_assessments(cap_id)
                if len(assessments) >= 2:
                    last_two = assessments[-2:]
                    if all(a["score"] >= 80 for a in last_two):
                        capability_registry.advance_stage(cap_id)
                        advanced.append(cap["name"])

            return {
                "advanced_count": len(advanced),
                "advanced_capabilities": advanced,
            }

    def lifecycle_health(self) -> dict:
        with self._lock:
            from core.capability_governance.capability_registry import capability_registry
            from core.capability_governance.capability_retirement_engine import capability_retirement_engine

            stats = capability_registry.capability_stats()
            total = stats["total"]
            mature_ops = (stats["by_stage"].get("MATURE", 0) +
                          stats["by_stage"].get("OPERATIONAL", 0))
            mature_operational_pct = (mature_ops / total * 100) if total > 0 else 0
            legacy_risk = stats["by_stage"].get("LEGACY", 0)
            retirement_pending = legacy_risk

            return {
                "total_capabilities": total,
                "mature_operational_pct": mature_operational_pct,
                "legacy_risk_count": legacy_risk,
                "retirement_pending": retirement_pending,
            }


capability_lifecycle_engine = CapabilityLifecycleEngine()
