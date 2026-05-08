"""
EOW Quant Engine — Observability Layer  (FTD-053-GAIA Phase 1 + 2 + 3)

Governed, token-safe, non-blocking intelligence observability.
All modules in this package are READ-ONLY with respect to trading state.
Failures in this package must NEVER halt the trading engine.

Phase 1: intelligence_compressor, report_lifecycle_engine
Phase 2: delta_reporter, anomaly_detector
Phase 3: github_sync_engine
Phase 4: ai_summary_engine, strategic_feed
"""
from core.observability.intelligence_compressor import intelligence_compressor, IntelligenceCompressor
from core.observability.report_lifecycle_engine import report_lifecycle_engine, ReportLifecycleEngine
from core.observability.delta_reporter import delta_reporter, DeltaReporter
from core.observability.anomaly_detector import anomaly_detector, AnomalyDetector
from core.observability.github_sync_engine import github_sync_engine, GitHubSyncEngine
from core.observability.ai_summary_engine import ai_summary_engine, AISummaryEngine
from core.observability.strategic_feed import strategic_feed, StrategicFeed

__all__ = [
    "intelligence_compressor",
    "IntelligenceCompressor",
    "report_lifecycle_engine",
    "ReportLifecycleEngine",
    "delta_reporter",
    "DeltaReporter",
    "anomaly_detector",
    "AnomalyDetector",
    "github_sync_engine",
    "GitHubSyncEngine",
    "ai_summary_engine",
    "AISummaryEngine",
    "strategic_feed",
    "StrategicFeed",
]
