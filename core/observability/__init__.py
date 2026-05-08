"""
EOW Quant Engine — Observability Layer  (FTD-053-GAIA Phase 1 + Phase 2)

Governed, token-safe, non-blocking intelligence observability.
All modules in this package are READ-ONLY with respect to trading state.
Failures in this package must NEVER halt the trading engine.

Phase 1: intelligence_compressor, report_lifecycle_engine
Phase 2: delta_reporter, anomaly_detector
"""
from core.observability.intelligence_compressor import intelligence_compressor, IntelligenceCompressor
from core.observability.report_lifecycle_engine import report_lifecycle_engine, ReportLifecycleEngine
from core.observability.delta_reporter import delta_reporter, DeltaReporter
from core.observability.anomaly_detector import anomaly_detector, AnomalyDetector

__all__ = [
    "intelligence_compressor",
    "IntelligenceCompressor",
    "report_lifecycle_engine",
    "ReportLifecycleEngine",
    "delta_reporter",
    "DeltaReporter",
    "anomaly_detector",
    "AnomalyDetector",
]
