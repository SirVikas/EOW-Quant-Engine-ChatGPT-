"""Economic Intelligence Engine — orchestrates economic evaluation of recommendations."""
import threading
import time


class EconomicIntelligenceEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def evaluate_recommendation(self, rec_id: str, expected_profit_pct: float,
                                 expected_drawdown_reduction: float,
                                 expected_sharpe_delta: float) -> str:
        from core.economic_intelligence.profit_impact_analyzer import profit_impact_analyzer
        from core.economic_intelligence.capital_efficiency_tracker import capital_efficiency_tracker
        from core.economic_intelligence.sharpe_impact_tracker import sharpe_impact_tracker

        profit_impact_analyzer.record_expected(rec_id, expected_profit_pct, expected_drawdown_reduction)
        # Record expected capital efficiency as util_before=0, util_after=expected_profit_pct proxy
        capital_efficiency_tracker.record(rec_id, 0.0, expected_profit_pct, 0.0)
        # Record expected sharpe as sharpe_before=0, after=expected_sharpe_delta proxy
        sharpe_impact_tracker.record(rec_id, 0.0, expected_sharpe_delta)
        return f"EVAL-{rec_id}-{int(time.time())}"

    def record_outcome(self, rec_id: str, actual_profit_pct: float,
                       actual_drawdown_reduction: float, actual_sharpe_before: float,
                       actual_sharpe_after: float, period_days: int = 30) -> str:
        from core.economic_intelligence.profit_impact_analyzer import profit_impact_analyzer
        from core.economic_intelligence.sharpe_impact_tracker import sharpe_impact_tracker

        profit_impact_analyzer.record_actual(rec_id, actual_profit_pct, actual_drawdown_reduction)
        sharpe_impact_tracker.record(f"{rec_id}-actual", actual_sharpe_before, actual_sharpe_after, period_days)

        stats = profit_impact_analyzer.impact_stats()
        accuracy = 0.0
        rec_data = profit_impact_analyzer._records.get(rec_id)
        if rec_data and rec_data.accuracy_pct is not None:
            accuracy = rec_data.accuracy_pct

        sharpe_delta = actual_sharpe_after - actual_sharpe_before

        if accuracy >= 70 and sharpe_delta > 0:
            return "ECONOMIC_SUCCESS"
        elif accuracy >= 40:
            return "PARTIAL_SUCCESS"
        else:
            return "ECONOMIC_FAILURE"

    def economic_report(self) -> dict:
        from core.economic_intelligence.profit_impact_analyzer import profit_impact_analyzer
        from core.economic_intelligence.capital_efficiency_tracker import capital_efficiency_tracker
        from core.economic_intelligence.sharpe_impact_tracker import sharpe_impact_tracker

        p_stats = profit_impact_analyzer.impact_stats()
        c_stats = capital_efficiency_tracker.efficiency_stats()
        s_stats = sharpe_impact_tracker.sharpe_stats()

        # Health score: blend of avg_profit_accuracy + positive sharpe pct + positive capital pct
        health_score = (
            p_stats.get("avg_profit_accuracy", 0) * 0.5 +
            s_stats.get("positive_impact_pct", 0) * 0.3 +
            c_stats.get("positive_impact_pct", 0) * 0.2
        )

        return {
            "profit_impact": p_stats,
            "capital_efficiency": c_stats,
            "sharpe_impact": s_stats,
            "overall_economic_health_score": round(min(health_score, 100), 2),
            "generated_at": time.time(),
        }

    def no_recommendation_validated_without_economics(self, rec_id: str) -> bool:
        from core.economic_intelligence.profit_impact_analyzer import profit_impact_analyzer
        return rec_id in profit_impact_analyzer._records


economic_intelligence_engine = EconomicIntelligenceEngine()
