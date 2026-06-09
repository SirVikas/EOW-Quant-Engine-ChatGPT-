"""PCCP — PHOENIX Central Control Plane Orchestrator: the brain of brains."""
import threading
import time


class PCCPOrchestrator:
    def __init__(self):
        self._lock = threading.RLock()

    def system_status(self) -> dict:
        from core.pccp.layer_registry import layer_registry
        from core.pccp.global_priority_manager import global_priority_manager
        from core.pccp.intelligence_bus import intelligence_bus

        health = layer_registry.system_health_summary()
        priorities = global_priority_manager.priority_summary()
        bus = intelligence_bus.bus_stats()

        ihi_report = None
        try:
            from core.nexus.institutional_health_index import institutional_health_index
            ihi_report = institutional_health_index.health_report()
        except Exception:
            pass

        return {
            "system_name": "PHOENIX CENTRAL CONTROL PLANE",
            "pccp_version": "1.0.0",
            "timestamp": time.time(),
            "layer_health": health,
            "priority_summary": priorities,
            "bus_stats": bus,
            "institutional_health": ihi_report,
        }

    def run_coordination_cycle(self) -> dict:
        from core.pccp.layer_registry import layer_registry
        from core.pccp.global_priority_manager import global_priority_manager
        from core.pccp.intelligence_bus import intelligence_bus

        # Refresh layer health
        health_summary = layer_registry.system_health_summary()

        # Pull top priority
        top = global_priority_manager.top_priority()

        # Conflict check placeholder
        conflict_check = {"conflicts_detected": 0, "note": "No active conflicts in this cycle"}

        # Publish coordination event
        event_id = intelligence_bus.publish(
            source_layer="PCCP",
            event_type="COORDINATION_CYCLE",
            payload={
                "overall_status": health_summary["overall_status"],
                "top_priority": top,
                "cycle_ts": time.time(),
            },
        )

        return {
            "cycle_completed_at": time.time(),
            "overall_health": health_summary["overall_status"],
            "layers_checked": health_summary["total"],
            "top_priority": top,
            "conflict_check": conflict_check,
            "bus_event_id": event_id,
        }

    def route_intelligence(self, source_layer: str, event_type: str, payload: dict) -> dict:
        from core.pccp.intelligence_bus import intelligence_bus
        event_id = intelligence_bus.publish(source_layer, event_type, payload)
        return {
            "routed": True,
            "event_id": event_id,
            "source_layer": source_layer,
            "event_type": event_type,
        }

    def pccp_dashboard(self) -> dict:
        from core.pccp.layer_registry import layer_registry
        from core.pccp.global_priority_manager import global_priority_manager
        from core.pccp.intelligence_bus import intelligence_bus
        from core.pccp.decision_ledger import decision_ledger
        from core.pccp.conflict_resolver import conflict_resolver

        return {
            "system_status": self.system_status(),
            "top_priorities": global_priority_manager.get_ranked_list(status_filter="QUEUED")[:10],
            "recent_events": intelligence_bus.recent_events(limit=10),
            "recent_decisions": decision_ledger.all_decisions(limit=10),
            "conflict_stats": conflict_resolver.conflict_stats(),
        }


pccp_orchestrator = PCCPOrchestrator()
