"""
Automated Anomaly Response System — converts detection into a structured
pipeline: Detection → Escalation → Recommended Action → Resolution Tracking.
"""
import threading
import time
from typing import Dict


class ResponseEngine:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._responses: Dict[str, dict] = {}
        self._counter = 0

    def handle_anomaly(self, anomaly_type: str, severity: str = "MEDIUM",
                       source: str = "manual", detail: str = "") -> dict:
        from core.anomaly_response.escalation_manager import escalation_manager
        from core.anomaly_response.containment_manager import containment_manager
        from core.anomaly_response.recovery_recommender import recovery_recommender
        with self._lock:
            self._counter += 1
            response_id = f"ARR-{self._counter:03d}"
        escalation = escalation_manager.escalate(response_id, severity)
        containment = containment_manager.contain(response_id, anomaly_type)
        recommendation = recovery_recommender.recommend(response_id, anomaly_type)
        response = {
            "response_id": response_id,
            "anomaly_type": str(anomaly_type).upper(),
            "severity": str(severity).upper(),
            "source": source,
            "detail": detail,
            "escalation": escalation,
            "containment": containment,
            "recommendation": recommendation,
            "status": "OPEN",
            "resolution": "",
            "opened_at": time.time(),
            "resolved_at": 0.0,
        }
        with self._lock:
            self._responses[response_id] = response
        return response

    def resolve(self, response_id: str, resolution: str = "") -> dict:
        with self._lock:
            response = self._responses.get(response_id)
            if not response:
                return {"error": f"unknown response {response_id}"}
            response["status"] = "RESOLVED"
            response["resolution"] = resolution
            response["resolved_at"] = time.time()
            return response

    def response_report(self) -> dict:
        with self._lock:
            responses = list(self._responses.values())
            return {
                "total": len(responses),
                "open": sum(1 for r in responses if r["status"] == "OPEN"),
                "resolved": sum(1 for r in responses if r["status"] == "RESOLVED"),
                "recent": responses[-10:],
            }

    def one_liner(self) -> str:
        r = self.response_report()
        return (
            f"Anomaly Response | Total={r['total']} | "
            f"Open={r['open']} | Resolved={r['resolved']}"
        )


response_engine = ResponseEngine()
