"""Trust Report Builder — assembles trust and epistemic reports."""
import threading
import time


class TrustReportBuilder:
    def __init__(self):
        self._lock = threading.RLock()

    def build(self) -> dict:
        with self._lock:
            sections: dict = {}

            try:
                from core.trust_fabric.trust_fabric_engine import trust_fabric_engine
                sections["trust_fabric"] = trust_fabric_engine.unified_trust_report()
            except Exception as e:
                sections["trust_fabric"] = {"error": str(e)}

            try:
                from core.epistemic.epistemic_engine import epistemic_engine
                sections["epistemic_audit"] = epistemic_engine.epistemic_audit()
            except Exception as e:
                sections["epistemic_audit"] = {"error": str(e)}

            return {
                "report_type": "TRUST",
                "generated_at": time.time(),
                "sections": sections,
            }


trust_report_builder = TrustReportBuilder()
