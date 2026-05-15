"""
PRP-001 Analytics — Signal Truth Reports

Generates all 10 forensic reports for PRP-001 Signal Truth Reconstruction.
Each report is a self-contained dict suitable for JSON export.

Reports:
  01_signal_truth_matrix
  02_false_positive_clusters
  03_directional_legitimacy_report
  04_confidence_reality_divergence
  05_context_quality_analysis
  06_asymmetry_validation_report
  07_noise_participation_audit
  08_predictive_integrity_monitor
  09_regime_signal_validity
  10_truth_density_summary
"""
from __future__ import annotations

import time
from typing import Dict, Any, List

from core.signal_truth.signal_truth_engine    import signal_truth_engine
from core.signal_truth.false_positive_forensics import false_positive_forensics
from core.signal_truth.directional_legitimacy  import directional_legitimacy
from core.signal_truth.context_quality_engine  import context_quality_engine
from core.signal_truth.asymmetry_validation    import asymmetry_validation


def generate_all_reports() -> Dict[str, Any]:
    """Generate all 10 PRP-001 forensic reports as a bundle."""
    return {
        "prp":        "001",
        "phase":      "SIGNAL_TRUTH_RECONSTRUCTION",
        "generated_ts": int(time.time() * 1000),
        "reports": {
            "01_signal_truth_matrix":         signal_truth_engine.signal_truth_matrix(),
            "02_false_positive_clusters":     false_positive_forensics.false_positive_clusters(),
            "03_directional_legitimacy":      directional_legitimacy.directional_legitimacy_report(),
            "04_confidence_reality_divergence": asymmetry_validation.confidence_reality_divergence(),
            "05_context_quality_analysis":    context_quality_engine.context_quality_analysis(),
            "06_asymmetry_validation_report": asymmetry_validation.asymmetry_validation_report(),
            "07_noise_participation_audit":   false_positive_forensics.noise_participation_audit(),
            "08_predictive_integrity_monitor": signal_truth_engine.predictive_integrity_monitor(),
            "09_regime_signal_validity":      directional_legitimacy.regime_signal_validity(),
            "10_truth_density_summary":       signal_truth_engine.truth_density_summary(),
        },
    }


def get_dashboard_summary() -> Dict[str, Any]:
    """Compact summary for dashboard display."""
    ste = signal_truth_engine.get_telemetry()
    dl  = directional_legitimacy.get_telemetry()
    av  = asymmetry_validation.get_telemetry()
    cq  = context_quality_engine.get_telemetry()
    fp  = false_positive_forensics.get_telemetry()

    return {
        "prp":                  "001",
        "module":               "SignalTruthReports",
        "truth_density":        ste["truth_density"],
        "directional_legit":    dl["global_score"],
        "directional_label":    dl["label"],
        "noise_ratio":          ste["noise_ratio"],
        "asymmetry_health":     av["asymmetry_health"],
        "rr_achievement_ratio": av["achievement_ratio"],
        "optimism_bias_rate":   av["optimism_bias_rate"],
        "false_positive_rate":  fp["false_positive_rate"],
        "active_fp_clusters":   fp["active_clusters"],
        "total_signals":        ste["total_signals"],
        "total_outcomes":       ste["total_outcomes"],
        "total_net_pnl":        ste["total_net_pnl"],
        "ts":                   int(time.time() * 1000),
    }
