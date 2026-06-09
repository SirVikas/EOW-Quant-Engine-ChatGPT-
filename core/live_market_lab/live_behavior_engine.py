"""GAP-02: Live Behavior Engine — master live market lab aggregator."""
from __future__ import annotations

import time
from typing import Dict, Any

from loguru import logger


class LiveBehaviorEngine:
    """Master live market lab. Aggregates gap tracking, reaction analysis, and hypothesis validation."""

    def lab_report(self) -> Dict[str, Any]:
        from core.live_market_lab.expectation_gap_tracker import expectation_gap_tracker
        from core.live_market_lab.market_reaction_analyzer import market_reaction_analyzer
        from core.live_market_lab.behavior_validation_engine import behavior_validation_engine

        gap_summary = expectation_gap_tracker.gap_summary()
        reaction_report = market_reaction_analyzer.reaction_report()
        hyp_summary = behavior_validation_engine.hypothesis_summary()

        total_gaps = gap_summary["total_gaps"]
        sig_gaps = len(expectation_gap_tracker.significant_gaps())
        confirmed = hyp_summary["confirmed"]
        refuted = hyp_summary["refuted"]
        total_hyp = hyp_summary["total"]

        # Market learning score: 0-100 based on confirmed hypotheses and gap tracking activity
        if total_hyp > 0:
            confirm_rate = confirmed / total_hyp
        else:
            confirm_rate = 0.0
        learning_score = min(100, int(confirm_rate * 60 + min(total_gaps, 40)))

        return {
            "total_gaps_tracked": total_gaps,
            "significant_gaps_count": sig_gaps,
            "confirmed_hypotheses": confirmed,
            "refuted_hypotheses": refuted,
            "market_learning_score": learning_score,
            "total_reactions_analyzed": reaction_report["total_reactions"],
            "ts": int(time.time() * 1000),
        }

    def one_liner(self) -> str:
        report = self.lab_report()
        return (
            f"LiveMarketLab: {report['total_gaps_tracked']} gaps | "
            f"{report['confirmed_hypotheses']} confirmed hypotheses | "
            f"learning_score={report['market_learning_score']}"
        )


live_behavior_engine = LiveBehaviorEngine()
