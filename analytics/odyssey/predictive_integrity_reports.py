"""
PRP-001 Analytics — Predictive Integrity Reports

Provides predictive integrity monitoring: rolling stability,
confidence calibration drift, and regime-specific validity decay.
"""
from __future__ import annotations

import time
from typing import Dict, Any

from core.signal_truth.signal_truth_engine   import signal_truth_engine
from core.signal_truth.directional_legitimacy import directional_legitimacy


def predictive_integrity_summary() -> Dict[str, Any]:
    """Rolling predictive stability assessment."""
    ste = signal_truth_engine.predictive_integrity_monitor()
    dl  = directional_legitimacy.get_telemetry()

    return {
        "prp":                    "001",
        "report":                 "predictive_integrity_summary",
        "global_truth_density":   ste["global_truth_density"],
        "recent_win_rate":        ste["recent_win_rate"],
        "rolling_drift":          ste["rolling_drift"],
        "stability_label":        "STABLE" if ste["rolling_drift"] < 0.10 else "DRIFTING",
        "global_directional":     dl["global_score"],
        "rolling_directional":    dl["rolling_score"],
        "confidence_calibration": ste["confidence_calibration"],
        "ts":                     int(time.time() * 1000),
    }
