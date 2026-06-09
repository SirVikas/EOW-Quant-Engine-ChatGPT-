"""GAP-05: Regime Survival Engine — master regime survivability aggregator."""
from __future__ import annotations

import time
from typing import Dict, Any

from loguru import logger


class RegimeSurvivalEngine:
    """Master regime survivability. Aggregates scorecard, resilience, and crisis response."""

    def survival_report(self) -> Dict[str, Any]:
        from core.regime_survivability.regime_scorecard import regime_scorecard
        from core.regime_survivability.transition_resilience_tracker import transition_resilience_tracker
        from core.regime_survivability.crisis_response_validator import crisis_response_validator

        scorecard = regime_scorecard.scorecard_summary()
        resilience = transition_resilience_tracker.resilience_report()
        crisis = crisis_response_validator.crisis_summary()

        regimes_covered = scorecard.get("regimes_covered", [])
        avg_score = scorecard.get("avg_survival_score", 0.0)
        by_regime = scorecard.get("by_regime_avg_score", {})

        # Weakest regime
        weakest = min(by_regime, key=lambda k: by_regime[k]) if by_regime else "unknown"

        crisis_rate = crisis.get("survival_rate_pct", 0.0)
        total_crises = crisis.get("total_crises", 0)

        # Regimes survived = regimes with score > 50
        regimes_survived = sum(1 for v in by_regime.values() if v >= 50)
        regimes_failed = len(by_regime) - regimes_survived

        if avg_score >= 70 and crisis_rate >= 80:
            robustness = "ROBUST"
        elif avg_score >= 50:
            robustness = "ADEQUATE"
        else:
            robustness = "FRAGILE"

        return {
            "regimes_survived": regimes_survived,
            "regimes_failed": regimes_failed,
            "avg_survival_score": avg_score,
            "weakest_regime": weakest,
            "crisis_survival_rate_pct": crisis_rate,
            "total_crises_tested": total_crises,
            "overall_robustness": robustness,
            "ts": int(time.time() * 1000),
        }

    def one_liner(self) -> str:
        report = self.survival_report()
        return (
            f"RegimeSurvival: {report['regimes_survived']} survived | "
            f"crisis_rate={report['crisis_survival_rate_pct']}% | "
            f"robustness={report['overall_robustness']}"
        )


regime_survival_engine = RegimeSurvivalEngine()
