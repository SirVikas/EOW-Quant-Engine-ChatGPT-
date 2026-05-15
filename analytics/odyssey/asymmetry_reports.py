"""
PRP-001 Analytics — Asymmetry Reports

Tracks RR achievement quality and confidence-reality divergence.
"""
from __future__ import annotations

import time
from typing import Dict, Any

from core.signal_truth.asymmetry_validation import asymmetry_validation


def asymmetry_health_summary() -> Dict[str, Any]:
    """Full asymmetry health report with regime and strategy breakdown."""
    report = asymmetry_validation.asymmetry_validation_report()
    divergence = asymmetry_validation.confidence_reality_divergence()
    telemetry  = asymmetry_validation.get_telemetry()

    return {
        "prp":                      "001",
        "report":                   "asymmetry_health_summary",
        "asymmetry_health":         telemetry["asymmetry_health"],
        "global_achievement_ratio": telemetry["achievement_ratio"],
        "optimism_bias_rate":       telemetry["optimism_bias_rate"],
        "divergence_count":         divergence["total_divergences"],
        "divergence_rate":          divergence["divergence_rate"],
        "by_strategy":              report["by_strategy"],
        "by_regime":                report["by_regime"],
        "ts":                       int(time.time() * 1000),
    }
