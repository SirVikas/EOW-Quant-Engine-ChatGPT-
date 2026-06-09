"""GAP-04: Validation Engine — master long-horizon validation aggregator."""
from __future__ import annotations

import time
from typing import Dict, Any

from loguru import logger


class ValidationEngine:
    """Master long-horizon validation. Aggregates survivability, stability, and persistence."""

    HORIZONS = ["30D", "90D", "180D", "365D"]

    def validation_report(self) -> Dict[str, Any]:
        from core.long_horizon_validation.survivability_tracker import survivability_tracker
        from core.long_horizon_validation.stability_monitor import stability_monitor
        from core.long_horizon_validation.performance_persistence_engine import performance_persistence_engine

        survivability_by_horizon = {
            h: survivability_tracker.survivability_rate(h) for h in self.HORIZONS
        }
        horizons_with_data = sum(1 for v in survivability_by_horizon.values() if v > 0)

        stability_report = stability_monitor.stability_report()
        stable_pct = stability_report.get("stable_pct", 100.0)

        persist_summary = performance_persistence_engine.persistence_summary()
        persistent_count = persist_summary.get("persistent", 0)
        total_analyzed = persist_summary.get("total_analyzed", 0)

        # Determine institutional proof level
        if horizons_with_data >= 3 and stable_pct >= 80 and persistent_count >= 2:
            proof_level = "PROVEN"
        elif horizons_with_data >= 2 and stable_pct >= 60:
            proof_level = "SUBSTANTIAL"
        elif horizons_with_data >= 1 or total_analyzed > 0:
            proof_level = "PARTIAL"
        else:
            proof_level = "NONE"

        return {
            "horizons_tracked": horizons_with_data,
            "survivability_by_horizon": survivability_by_horizon,
            "stable_metrics_pct": stable_pct,
            "persistent_strategies_count": persistent_count,
            "institutional_proof_level": proof_level,
            "ts": int(time.time() * 1000),
        }

    def one_liner(self) -> str:
        report = self.validation_report()
        return (
            f"LongHorizonValidation: {report['horizons_tracked']} horizons | "
            f"stable={report['stable_metrics_pct']}% | "
            f"proof={report['institutional_proof_level']}"
        )


validation_engine = ValidationEngine()
