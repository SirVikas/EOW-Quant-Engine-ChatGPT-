"""Failure reconstruction engine — full incident reconstruction."""
import threading
from datetime import datetime


class FailureReconstructionEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def reconstruct(self, incident_id: str) -> dict:
        from core.self_diagnostics.incident_analyzer import incident_analyzer
        from core.self_diagnostics.auto_postmortem_generator import auto_postmortem_generator
        from core.self_diagnostics.remediation_tracker import remediation_tracker

        incidents = incident_analyzer.all_incidents()
        incident = next((i for i in incidents if i["incident_id"] == incident_id), None)
        if not incident:
            return {"error": f"Incident {incident_id} not found"}

        timeline_events = []
        try:
            from core.lineage.timeline_reconstruction_engine import full_timeline
            detected_at = incident.get("detected_at", "")
            timeline_events = full_timeline(near=detected_at) if callable(full_timeline) else []
        except Exception:
            pass

        postmortem = auto_postmortem_generator.generate(incident_id)
        open_actions = remediation_tracker.open_actions(incident_id)

        return {
            "incident": incident,
            "timeline_events": timeline_events,
            "postmortem": postmortem,
            "open_remediation_actions": open_actions,
            "reconstructed_at": datetime.utcnow().isoformat(),
        }

    def diagnostic_summary(self) -> dict:
        from core.self_diagnostics.incident_analyzer import incident_analyzer
        from core.self_diagnostics.remediation_tracker import remediation_tracker

        stats = incident_analyzer.incident_stats()
        action_stats = remediation_tracker.action_stats()
        all_inc = incident_analyzer.all_incidents()
        last_at = all_inc[-1]["detected_at"] if all_inc else None
        return {
            "total_incidents": stats.get("total", 0),
            "open_incidents": stats.get("open", 0),
            "unresolved_actions": action_stats.get("open", 0),
            "last_incident_at": last_at,
        }


failure_reconstruction_engine = FailureReconstructionEngine()
