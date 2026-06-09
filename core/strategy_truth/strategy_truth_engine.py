"""GAP-01: Strategy Truth Engine — master strategy truth aggregator."""
from __future__ import annotations

import time
from typing import Dict, Any

from loguru import logger


class StrategyTruthEngine:
    """Master strategy truth. Aggregates alpha sources, signal validation, and edge decay."""

    def truth_report(self) -> Dict[str, Any]:
        from core.strategy_truth.alpha_source_tracker import alpha_source_tracker
        from core.strategy_truth.signal_truth_validator import signal_truth_validator
        from core.strategy_truth.edge_decay_monitor import edge_decay_monitor

        source_summary = alpha_source_tracker.alpha_source_summary()
        validation_report = signal_truth_validator.validation_report()
        edge_report = edge_decay_monitor.edge_health_report()

        total_sources = source_summary["total_sources"]
        verified = source_summary["verified_sources"]
        noise_pct = validation_report["noise_pct"]
        decaying = edge_report["decaying"] + edge_report["depleted"]

        # Determine overall truth confidence
        if verified >= 3 and noise_pct < 30 and decaying == 0:
            confidence = "HIGH"
        elif verified >= 1 and noise_pct < 60:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        return {
            "proven_alpha_sources": source_summary["verified_sources"],
            "unverified_sources": source_summary["unverified_sources"],
            "decaying_edges": decaying,
            "noise_signals_pct": noise_pct,
            "overall_truth_confidence": confidence,
            "total_sources": total_sources,
            "edge_health_pct": edge_report["health_pct"],
            "ts": int(time.time() * 1000),
        }

    def one_liner(self) -> str:
        report = self.truth_report()
        return (
            f"StrategyTruth: {report['proven_alpha_sources']} proven sources | "
            f"noise={report['noise_signals_pct']}% | "
            f"confidence={report['overall_truth_confidence']}"
        )


strategy_truth_engine = StrategyTruthEngine()
