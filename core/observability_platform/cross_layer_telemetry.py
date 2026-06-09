"""Cross-layer telemetry collector."""
import threading
from datetime import datetime
from typing import Any


class CrossLayerTelemetry:
    def __init__(self):
        self._lock = threading.RLock()

    def collect_all(self) -> dict:
        from core.observability_platform.real_time_metrics_bus import real_time_metrics_bus as bus
        collected = 0
        layers_sampled = []

        def _safe(fn, *a, **kw):
            try:
                return fn(*a, **kw)
            except Exception:
                return None

        # health_score
        try:
            from core.nexus.institutional_health_index import health_report
            r = _safe(health_report)
            if r:
                score = r.get("health_score", r.get("overall_health", 0))
                bus.publish("nexus", "health_score", float(score))
                collected += 1; layers_sampled.append("nexus")
        except Exception:
            pass

        # trust fabric
        try:
            from core.trust_fabric.trust_registry import trust_summary
            r = _safe(trust_summary)
            if r:
                bus.publish("trust_fabric", "avg_trust_score", float(r.get("avg_trust_score", 0)))
                bus.publish("trust_fabric", "trusted_count", float(r.get("trusted_count", 0)))
                collected += 2; layers_sampled.append("trust_fabric")
        except Exception:
            pass

        # pccp
        try:
            from core.pccp.layer_registry import system_health_summary
            r = _safe(system_health_summary)
            if r:
                bus.publish("pccp", "healthy_layers", float(r.get("healthy_layers", r.get("healthy", 0))))
                bus.publish("pccp", "degraded_layers", float(r.get("degraded_layers", r.get("degraded", 0))))
                collected += 2; layers_sampled.append("pccp")
        except Exception:
            pass

        # economic intelligence
        try:
            from core.economic_intelligence.economic_intelligence_engine import economic_report
            r = _safe(economic_report)
            if r:
                score = r.get("economic_health_score", r.get("health_score", 0))
                bus.publish("economic_intelligence", "economic_health_score", float(score))
                collected += 1; layers_sampled.append("economic_intelligence")
        except Exception:
            pass

        # constitution
        try:
            from core.constitution.constitution_engine import constitution_report
            r = _safe(constitution_report)
            if r:
                score = r.get("constitutional_health_score", r.get("health_score", 0))
                bus.publish("constitution", "constitutional_health_score", float(score))
                collected += 1; layers_sampled.append("constitution")
        except Exception:
            pass

        # autonomous improvement
        try:
            from core.autonomous_improvement.improvement_engine import improvement_status
            r = _safe(improvement_status)
            if r:
                bus.publish("autonomous_improvement", "total_cycles_run", float(r.get("total_cycles_run", r.get("cycles", 0))))
                collected += 1; layers_sampled.append("autonomous_improvement")
        except Exception:
            pass

        # evidence warehouse
        try:
            from core.evidence_warehouse.evidence_warehouse import warehouse_report
            r = _safe(warehouse_report)
            if r:
                score = r.get("warehouse_health_score", r.get("health_score", 0))
                bus.publish("evidence_warehouse", "warehouse_health_score", float(score))
                collected += 1; layers_sampled.append("evidence_warehouse")
        except Exception:
            pass

        # disaster recovery
        try:
            from core.disaster_recovery.failover_manager import disaster_recovery_status
            r = _safe(disaster_recovery_status)
            if r:
                bus.publish("disaster_recovery", "active_failovers", float(r.get("active_failovers", 0)))
                collected += 1; layers_sampled.append("disaster_recovery")
        except Exception:
            pass

        return {
            "collected_metrics": collected,
            "layers_sampled": layers_sampled,
            "collected_at": datetime.utcnow().isoformat(),
        }

    def telemetry_snapshot(self) -> dict:
        from core.observability_platform.real_time_metrics_bus import real_time_metrics_bus as bus
        self.collect_all()
        return bus.all_latest()


cross_layer_telemetry = CrossLayerTelemetry()
