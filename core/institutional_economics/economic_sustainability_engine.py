"""Economic Sustainability Engine — master institutional economics."""
import threading


class EconomicSustainabilityEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def sustainability_report(self) -> dict:
        from core.institutional_economics.efficiency_governor import efficiency_governor
        from core.institutional_economics.institutional_cost_engine import institutional_cost_engine
        from core.institutional_economics.value_creation_tracker import value_creation_tracker

        efficiency = efficiency_governor.compute_efficiency()
        trend_data = efficiency_governor.efficiency_trend()

        roi = efficiency["roi_pct"]
        sustainability_score = max(0, min(100, int(50 + roi)))

        # Trend from history
        if len(trend_data) >= 2:
            recent = trend_data[-1]["roi_pct"]
            prev = trend_data[-2]["roi_pct"]
            cost_trend = "IMPROVING" if recent > prev else ("STABLE" if recent == prev else "DETERIORATING")
        else:
            cost_trend = "STABLE"

        if sustainability_score >= 70:
            verdict = "SUSTAINABLE"
        elif sustainability_score >= 40:
            verdict = "AT_RISK"
        else:
            verdict = "UNSUSTAINABLE"

        return {
            "economic_roi_pct": roi,
            "cost_trend": cost_trend,
            "value_trend": cost_trend,  # mirrors cost trend for simplicity
            "sustainability_score": sustainability_score,
            "verdict": verdict,
        }

    def one_liner(self) -> str:
        report = self.sustainability_report()
        return (f"IEcon: verdict={report['verdict']} | "
                f"ROI={report['economic_roi_pct']}% | "
                f"score={report['sustainability_score']}")


economic_sustainability_engine = EconomicSustainabilityEngine()
