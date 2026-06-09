"""Auto postmortem generator for self-diagnostics."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Postmortem:
    pm_id: str
    incident_id: str
    timeline: list
    root_cause: str
    contributing_factors: list
    what_went_wrong: list
    what_went_right: list
    action_items: list
    generated_at: str


class AutoPostmortemGenerator:
    def __init__(self):
        self._lock = threading.RLock()
        self._postmortems: list = []
        self._counter = 0

    def generate(self, incident_id: str) -> dict:
        from core.self_diagnostics.incident_analyzer import incident_analyzer
        incidents = incident_analyzer.all_incidents()
        incident = next((i for i in incidents if i["incident_id"] == incident_id), None)
        if not incident:
            return {"error": f"Incident {incident_id} not found"}

        timeline = [
            {"time": incident.get("detected_at", ""), "event": "Incident detected"},
            {"time": incident.get("resolved_at") or datetime.utcnow().isoformat(), "event": "Investigation completed"},
        ]

        contributing_factors = []
        try:
            from core.pccp.layer_dependency_engine import layer_dependency_engine
            for layer in incident.get("affected_layers", []):
                deps = layer_dependency_engine.get_dependents(layer) if hasattr(layer_dependency_engine, "get_dependents") else []
                if deps:
                    contributing_factors.append(f"Cascade from {layer}: {deps}")
        except Exception:
            pass
        if not contributing_factors and incident.get("affected_layers"):
            contributing_factors = [f"Layer failure: {l}" for l in incident["affected_layers"]]

        severity = incident.get("severity", "P3")
        action_items = [
            f"Review {severity} incident root cause: {incident.get('root_cause', 'unknown')}",
            "Update monitoring thresholds if applicable",
            "Validate recovery procedures were followed",
        ]
        if severity in ("P1", "P2"):
            action_items.append("Schedule stakeholder debrief within 48 hours")

        with self._lock:
            self._counter += 1
            pm = Postmortem(
                pm_id=f"PM-{self._counter:03d}",
                incident_id=incident_id,
                timeline=timeline,
                root_cause=incident.get("root_cause", "Under investigation"),
                contributing_factors=contributing_factors,
                what_went_wrong=[incident.get("description", "")],
                what_went_right=["Incident was detected and logged", "Investigation was triggered"],
                action_items=action_items,
                generated_at=datetime.utcnow().isoformat(),
            )
            self._postmortems.append(pm)
            return asdict(pm)

    def all_postmortems(self, limit: int = 20) -> list:
        with self._lock:
            return [asdict(p) for p in self._postmortems[-limit:]]


auto_postmortem_generator = AutoPostmortemGenerator()
