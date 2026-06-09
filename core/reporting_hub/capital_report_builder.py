"""Capital Report Builder — assembles capital performance and validation reports."""
import threading
import time


class CapitalReportBuilder:
    def __init__(self):
        self._lock = threading.RLock()

    def build(self) -> dict:
        with self._lock:
            sections: dict = {}

            try:
                from core.economic_intelligence.economic_intelligence_engine import economic_intelligence_engine
                sections["economic_intelligence"] = economic_intelligence_engine.economic_report()
            except Exception as e:
                sections["economic_intelligence"] = {"error": str(e)}

            try:
                from core.performance_attribution.performance_attribution_engine import performance_attribution_engine
                sections["performance_attribution"] = performance_attribution_engine.attribution_report()
            except Exception as e:
                sections["performance_attribution"] = {"error": str(e)}

            try:
                from core.real_market_validation.validation_engine import real_market_validation_engine
                sections["market_validation"] = real_market_validation_engine.validation_summary()
            except Exception as e:
                sections["market_validation"] = {"error": str(e)}

            return {
                "report_type": "CAPITAL",
                "generated_at": time.time(),
                "sections": sections,
            }


capital_report_builder = CapitalReportBuilder()
