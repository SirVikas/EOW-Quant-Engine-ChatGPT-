"""Observability engine — mission control aggregator."""
import threading
from datetime import datetime


class ObservabilityEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def mission_control(self) -> dict:
        from core.observability_platform.cross_layer_telemetry import cross_layer_telemetry
        from core.observability_platform.anomaly_center import anomaly_center
        from core.observability_platform.real_time_metrics_bus import real_time_metrics_bus as bus

        telemetry = cross_layer_telemetry.telemetry_snapshot()
        anomaly_scan = anomaly_center.scan()

        layer_health = {}
        try:
            from core.pccp.layer_registry import all_layers
            layer_health = all_layers() if callable(all_layers) else {}
        except Exception:
            pass

        system_status = {}
        try:
            from core.pccp.pccp_orchestrator import system_status
            system_status = system_status() if callable(system_status) else {}
        except Exception:
            pass

        critical = anomaly_scan.get("critical", 0)
        warning = anomaly_scan.get("warning", 0)
        if critical > 0:
            status = "RED"
        elif warning > 0:
            status = "AMBER"
        else:
            status = "GREEN"

        return {
            "mission_control_status": status,
            "layer_health": layer_health,
            "telemetry": telemetry,
            "anomalies": anomaly_scan,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def observability_health(self) -> dict:
        from core.observability_platform.real_time_metrics_bus import real_time_metrics_bus as bus
        from core.observability_platform.anomaly_center import anomaly_center
        all_latest = bus.all_latest()
        stats = anomaly_center.anomaly_stats()
        layers = list(all_latest.keys())
        total_metrics = sum(len(v) for v in all_latest.values())
        return {
            "status": "OK",
            "metrics_collected": total_metrics,
            "active_anomalies": stats.get("active", 0),
            "layers_monitored": len(layers),
        }


observability_engine = ObservabilityEngine()
