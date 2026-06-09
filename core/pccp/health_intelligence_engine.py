"""Health Intelligence Engine — predictive health analysis for system layers."""
import threading
import time
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class HealthPrediction:
    layer_id: str
    degradation_risk: float
    failure_risk: float
    capacity_risk: float
    resource_exhaustion_risk: float
    overall_risk: float
    predicted_at: float
    warning_message: str


_KNOWN_LAYERS = [
    "PCCP", "CTAO", "OBSERVATORY-X", "NEXUS", "CORTEX",
    "AEG", "PCAO", "TRUST_ENGINE", "RISK_ENGINE", "DIGITAL_TWIN",
    "IMRAF",
]


class HealthIntelligenceEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def predict_health(self, layer_id: str) -> dict:
        degradation_risk = 0.0
        failure_risk = 0.0
        capacity_risk = 0.0
        resource_exhaustion_risk = 0.0
        warnings = []

        try:
            from core.pccp.resource_governor import resource_governor
            budget = resource_governor.get_budget(layer_id)
            if budget:
                cpu_budget = budget["cpu_budget_pct"]
                cpu_usage = budget["current_cpu_usage"]
                if cpu_budget > 0 and cpu_usage > cpu_budget * 0.8:
                    resource_exhaustion_risk += 0.4
                    warnings.append(f"CPU usage at {cpu_usage:.1f}% vs budget {cpu_budget:.1f}%")
        except Exception:
            pass

        try:
            from core.pccp.layer_registry import layer_registry
            layer = layer_registry.get_layer(layer_id) if hasattr(layer_registry, "get_layer") else None
            if layer:
                status = layer.get("status", "")
                if status == "WARNING":
                    degradation_risk += 0.3
                    warnings.append("Layer status: WARNING")
                elif status == "DEGRADED":
                    degradation_risk += 0.6
                    warnings.append("Layer status: DEGRADED")
                elif status == "CRITICAL":
                    failure_risk = 1.0
                    warnings.append("Layer status: CRITICAL")
        except Exception:
            pass

        try:
            from core.pccp.layer_dependency_engine import layer_dependency_engine
            reverse = layer_dependency_engine._reverse
            dependent_count = len(reverse.get(layer_id, []))
            if dependent_count >= 3:
                capacity_risk += 0.2
                warnings.append(f"{dependent_count} layers depend on this layer")
        except Exception:
            pass

        overall_risk = max(degradation_risk, failure_risk, capacity_risk, resource_exhaustion_risk)
        warning_message = "; ".join(warnings) if warnings else "No warnings"

        return asdict(HealthPrediction(
            layer_id=layer_id,
            degradation_risk=round(degradation_risk, 4),
            failure_risk=round(failure_risk, 4),
            capacity_risk=round(capacity_risk, 4),
            resource_exhaustion_risk=round(resource_exhaustion_risk, 4),
            overall_risk=round(overall_risk, 4),
            predicted_at=time.time(),
            warning_message=warning_message,
        ))

    def predict_all(self) -> list:
        predictions = [self.predict_health(layer) for layer in _KNOWN_LAYERS]
        return sorted(predictions, key=lambda p: p["overall_risk"], reverse=True)

    def at_risk_layers(self, threshold: float = 0.5) -> list:
        return [p for p in self.predict_all() if p["overall_risk"] >= threshold]

    def health_forecast_report(self) -> dict:
        predictions = self.predict_all()
        at_risk = [p for p in predictions if p["overall_risk"] >= 0.5]
        critical = [p for p in predictions if p["failure_risk"] >= 0.8]
        return {
            "predictions_count": len(predictions),
            "at_risk_count": len(at_risk),
            "critical_predictions": critical,
            "summary": f"{len(at_risk)} of {len(predictions)} layers at risk",
            "generated_at": time.time(),
        }


health_intelligence_engine = HealthIntelligenceEngine()
