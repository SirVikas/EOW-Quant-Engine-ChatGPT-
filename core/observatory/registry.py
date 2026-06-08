"""
PHOENIX OBSERVATORY-X — Universal Report Registry (URR)  [OX-1A]

Catalog of every report type known to PHOENIX.  Each entry records:
  - identity   : unique key, human name, category
  - provenance : source module / API endpoint that generates it
  - logistics  : output format, nominal frequency, storage path
  - graph      : which other reports this depends on

Reports register themselves at boot via register().  The registry also ships
a built-in catalog of all reports that existed at the time OX-1 was built so
that legacy reports are visible even before their generators are updated.

Thread-safe: a single RLock guards all mutations.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ── Data Model ────────────────────────────────────────────────────────────────

@dataclass
class ReportDefinition:
    key: str                          # Unique identifier, e.g. "trade_report_1d"
    name: str                         # Human-readable label
    category: str                     # performance | signal | risk | governance | intelligence | infrastructure
    source_module: str                # Python module path or "API:/endpoint"
    output_format: str                # json | html | csv | bundle
    frequency: str                    # realtime | hourly | session | daily | weekly | on_demand
    storage_path: Optional[str]       # Relative path under reports/
    dependencies: List[str]           # Keys of reports that must run first
    tier: str                         # A (direct PnL) | B (indirect PnL) | C (observability) | D (infra)
    description: str = ""
    registered_at: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)


# ── Registry ──────────────────────────────────────────────────────────────────

class UniversalReportRegistry:
    """Central catalog of all PHOENIX report types."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._catalog: Dict[str, ReportDefinition] = {}
        self._bootstrap_builtin_catalog()

    # ── Public API ────────────────────────────────────────────────────────────

    def register(self, definition: ReportDefinition) -> None:
        """Register or update a report definition."""
        with self._lock:
            self._catalog[definition.key] = definition

    def get(self, key: str) -> Optional[ReportDefinition]:
        with self._lock:
            return self._catalog.get(key)

    def all(self) -> List[ReportDefinition]:
        with self._lock:
            return list(self._catalog.values())

    def by_category(self, category: str) -> List[ReportDefinition]:
        with self._lock:
            return [r for r in self._catalog.values() if r.category == category]

    def by_tier(self, tier: str) -> List[ReportDefinition]:
        with self._lock:
            return [r for r in self._catalog.values() if r.tier == tier]

    def summary(self) -> dict:
        with self._lock:
            cats: Dict[str, int] = {}
            tiers: Dict[str, int] = {}
            freqs: Dict[str, int] = {}
            for r in self._catalog.values():
                cats[r.category]   = cats.get(r.category, 0) + 1
                tiers[r.tier]      = tiers.get(r.tier, 0) + 1
                freqs[r.frequency] = freqs.get(r.frequency, 0) + 1
            return {
                "total_registered": len(self._catalog),
                "by_category": cats,
                "by_tier": tiers,
                "by_frequency": freqs,
                "keys": sorted(self._catalog.keys()),
            }

    # ── Built-in Catalog ──────────────────────────────────────────────────────
    # Populated from architecture census (qFTD-PHOENIX-OBSX-CORTEX-001).
    # Covers every report type that existed at OX-1 build time.

    def _bootstrap_builtin_catalog(self) -> None:
        _BUILTIN: List[ReportDefinition] = [
            # ── Performance Reports ──────────────────────────────────────────
            ReportDefinition(
                key="perf_report_1d", name="Performance Report (1D)",
                category="performance", tier="C",
                source_module="API:/api/report/full-system-v2",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/report_1D.json",
                dependencies=[],
                description="1-day rolling performance snapshot",
            ),
            ReportDefinition(
                key="perf_report_7d", name="Performance Report (7D)",
                category="performance", tier="C",
                source_module="API:/api/report/full-system-v2",
                output_format="json", frequency="daily",
                storage_path="reports_for_analyzation/*/report_7D.json",
                dependencies=["perf_report_1d"],
                description="7-day rolling performance snapshot",
            ),
            ReportDefinition(
                key="perf_report_20d", name="Performance Report (20D)",
                category="performance", tier="C",
                source_module="API:/api/report/full-system-v2",
                output_format="json", frequency="weekly",
                storage_path="reports_for_analyzation/*/report_20D.json",
                dependencies=["perf_report_7d"],
                description="20-day rolling performance snapshot",
            ),
            ReportDefinition(
                key="perf_report_all", name="Performance Report (ALL)",
                category="performance", tier="C",
                source_module="API:/api/report/full-system-v2",
                output_format="json", frequency="weekly",
                storage_path="reports_for_analyzation/*/report_ALL.json",
                dependencies=["perf_report_20d"],
                description="Full history performance snapshot",
            ),
            ReportDefinition(
                key="capital_efficiency", name="Capital Efficiency Report",
                category="performance", tier="B",
                source_module="core.reporting.unified_report_engine_v2",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/capital_efficiency.json",
                dependencies=[],
                description="Capital utilisation and efficiency analysis",
            ),
            ReportDefinition(
                key="fee_drag_analysis", name="Fee Drag Analysis",
                category="performance", tier="B",
                source_module="core.reporting.unified_report_engine_v2",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/fee_drag_analysis.json",
                dependencies=[],
                description="Impact of fees on net returns",
            ),
            ReportDefinition(
                key="hourly_performance", name="Hourly Performance Heatmap",
                category="performance", tier="C",
                source_module="core.reporting.unified_report_engine_v2",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/hourly_performance.json",
                dependencies=[],
                description="PnL breakdown by hour of day",
            ),
            ReportDefinition(
                key="exit_analysis", name="Exit Analysis Report",
                category="performance", tier="B",
                source_module="core.exit_attribution",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/exit_analysis.json",
                dependencies=[],
                description="Exit method attribution and quality",
            ),
            # ── Signal Quality Reports ───────────────────────────────────────
            ReportDefinition(
                key="signal_truth_matrix", name="Signal Truth Matrix",
                category="signal", tier="B",
                source_module="core.signal_truth.signal_truth_engine",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/signal_truth_matrix.json",
                dependencies=[],
                description="Signal quality validation matrix (PRP-001)",
            ),
            ReportDefinition(
                key="signal_funnel", name="Signal Funnel Report",
                category="signal", tier="B",
                source_module="core.reporting.unified_report_engine_v2",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/signal_funnel.json",
                dependencies=[],
                description="Signal filtering pipeline funnel analysis",
            ),
            ReportDefinition(
                key="false_positive_clusters", name="False Positive Clusters",
                category="signal", tier="B",
                source_module="core.signal_truth.false_positive_forensics",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/false_positive_clusters.json",
                dependencies=["signal_truth_matrix"],
                description="FP pattern clustering for filter improvement",
            ),
            ReportDefinition(
                key="directional_legitimacy", name="Directional Legitimacy Report",
                category="signal", tier="B",
                source_module="core.signal_truth.directional_legitimacy",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/directional_legitimacy.json",
                dependencies=[],
                description="Entry direction correctness analysis",
            ),
            ReportDefinition(
                key="asymmetry_validation", name="Asymmetry Validation Report",
                category="signal", tier="B",
                source_module="core.signal_truth.asymmetry_validation",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/asymmetry_validation.json",
                dependencies=[],
                description="Win/loss asymmetry validation",
            ),
            ReportDefinition(
                key="context_quality_analysis", name="Context Quality Analysis",
                category="signal", tier="B",
                source_module="core.signal_truth.context_quality_engine",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/context_quality_analysis.json",
                dependencies=[],
                description="Signal context quality scoring",
            ),
            ReportDefinition(
                key="noise_participation_audit", name="Noise Participation Audit",
                category="signal", tier="B",
                source_module="core.signal_truth.signal_truth_engine",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/noise_participation_audit.json",
                dependencies=["signal_truth_matrix"],
                description="Proportion of trades driven by noise vs edge",
            ),
            ReportDefinition(
                key="predictive_integrity_monitor", name="Predictive Integrity Monitor",
                category="signal", tier="B",
                source_module="analytics.odyssey.predictive_integrity_reports",
                output_format="json", frequency="daily",
                storage_path="reports_for_analyzation/*/predictive_integrity_monitor.json",
                dependencies=[],
                description="Forward-looking signal integrity tracking",
            ),
            # ── Risk Reports ─────────────────────────────────────────────────
            ReportDefinition(
                key="regime_performance_matrix", name="Regime Performance Matrix",
                category="risk", tier="B",
                source_module="core.regime_memory",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/regime_performance_matrix.json",
                dependencies=[],
                description="PnL performance breakdown by market regime",
            ),
            ReportDefinition(
                key="system_health", name="System Health Report",
                category="risk", tier="C",
                source_module="core.observability.orchestrator",
                output_format="json", frequency="hourly",
                storage_path="reports_for_analyzation/*/system_health.json",
                dependencies=[],
                description="Overall system health scoring",
            ),
            ReportDefinition(
                key="consistency", name="Consistency Report",
                category="risk", tier="B",
                source_module="core.consistency_engine",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/consistency.json",
                dependencies=[],
                description="Engine behavioral consistency validation (FTD-040)",
            ),
            ReportDefinition(
                key="confidence_calibration_report", name="Confidence Calibration Report",
                category="risk", tier="B",
                source_module="core.reporting.unified_report_engine_v2",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/confidence_calibration_report.json",
                dependencies=[],
                description="Signal confidence vs actual outcome calibration",
            ),
            # ── Governance & Audit Reports ───────────────────────────────────
            ReportDefinition(
                key="audit_log", name="Audit Log",
                category="governance", tier="C",
                source_module="API:/api/audit-log",
                output_format="json", frequency="realtime",
                storage_path="reports_for_analyzation/*/audit_log.json",
                dependencies=[],
                description="Full system audit trail",
            ),
            ReportDefinition(
                key="adaptive_decision_audit", name="Adaptive Decision Audit",
                category="governance", tier="B",
                source_module="core.adaptive_execution_governance",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/adaptive_decision_audit.json",
                dependencies=[],
                description="Audit of adaptive execution decisions",
            ),
            ReportDefinition(
                key="escalations", name="Escalation Log",
                category="governance", tier="C",
                source_module="core.observability.escalation_engine",
                output_format="json", frequency="realtime",
                storage_path="reports_for_analyzation/*/escalations.json",
                dependencies=[],
                description="Alert escalation events",
            ),
            # ── Intelligence Reports ─────────────────────────────────────────
            ReportDefinition(
                key="intelligence_maturity_report", name="Intelligence Maturity Report",
                category="intelligence", tier="C",
                source_module="core.reporting.intelligence_layer",
                output_format="json", frequency="daily",
                storage_path="reports_for_analyzation/*/intelligence_maturity_report.json",
                dependencies=["perf_report_1d"],
                description="Maturity score of autonomous intelligence systems",
            ),
            ReportDefinition(
                key="strategy_evolution_report", name="Strategy Evolution Report",
                category="intelligence", tier="B",
                source_module="core.genome_engine",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/strategy_evolution_report.json",
                dependencies=[],
                description="Strategy DNA evolution and genome state",
            ),
            ReportDefinition(
                key="rl_intelligence", name="RL Intelligence Report",
                category="intelligence", tier="B",
                source_module="API:/api/rl-intelligence",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/rl_intelligence.json",
                dependencies=[],
                description="RL contextual bandit state and learning progress",
            ),
            ReportDefinition(
                key="ai_brain", name="AI Brain State Report",
                category="intelligence", tier="C",
                source_module="API:/api/ai-brain",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/ai_brain.json",
                dependencies=[],
                description="Autonomous intelligence engine state snapshot",
            ),
            ReportDefinition(
                key="edge_validation_report", name="Edge Validation Report",
                category="intelligence", tier="B",
                source_module="core.edge_engine",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/edge_validation_report.json",
                dependencies=[],
                description="Statistical edge validity across strategies",
            ),
            ReportDefinition(
                key="alpha_persistence_report", name="Alpha Persistence Report",
                category="intelligence", tier="B",
                source_module="core.adaptive_edge_engine",
                output_format="json", frequency="daily",
                storage_path="reports_for_analyzation/*/alpha_persistence_report.json",
                dependencies=["edge_validation_report"],
                description="Alpha decay and persistence analysis",
            ),
            ReportDefinition(
                key="reward_propagation_report", name="Reward Propagation Report",
                category="intelligence", tier="B",
                source_module="core.rl_engine",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/reward_propagation_report.json",
                dependencies=["rl_intelligence"],
                description="RL reward signal quality and propagation",
            ),
            ReportDefinition(
                key="confidence_reality_divergence", name="Confidence–Reality Divergence",
                category="intelligence", tier="B",
                source_module="core.signal_truth.signal_truth_engine",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/confidence_reality_divergence.json",
                dependencies=["confidence_calibration_report"],
                description="Gap between model confidence and actual win rate",
            ),
            # ── Diagnostic Reports ───────────────────────────────────────────
            ReportDefinition(
                key="ct_scan", name="CT-SCAN Thought Log",
                category="intelligence", tier="C",
                source_module="API:/api/thoughts",
                output_format="json", frequency="realtime",
                storage_path="reports_for_analyzation/*/ct_scan.json",
                dependencies=[],
                description="Real-time engine decision trace (CT-SCAN)",
            ),
            ReportDefinition(
                key="anomalies", name="Anomaly Report",
                category="risk", tier="C",
                source_module="core.observability.anomaly_detector",
                output_format="json", frequency="hourly",
                storage_path="reports_for_analyzation/*/anomalies.json",
                dependencies=[],
                description="Detected statistical anomalies",
            ),
            ReportDefinition(
                key="patterns", name="Pattern Report",
                category="intelligence", tier="B",
                source_module="core.learning_memory.pattern_engine",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/patterns.json",
                dependencies=[],
                description="Discovered trade patterns from learning memory",
            ),
            ReportDefinition(
                key="failed_patterns", name="Failed Pattern Report",
                category="intelligence", tier="B",
                source_module="core.learning_memory.negative_memory",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/failed_patterns.json",
                dependencies=["patterns"],
                description="Patterns associated with losses — avoidance library",
            ),
            ReportDefinition(
                key="negative_memory", name="Negative Memory Report",
                category="intelligence", tier="B",
                source_module="core.learning_memory.negative_memory",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/negative_memory.json",
                dependencies=[],
                description="Loss-encoded memory for future avoidance",
            ),
            # ── Infrastructure Reports ───────────────────────────────────────
            ReportDefinition(
                key="eow_state", name="Engine State Snapshot",
                category="infrastructure", tier="D",
                source_module="API:/api/status",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/eow_state.json",
                dependencies=[],
                description="Full engine runtime state snapshot",
            ),
            ReportDefinition(
                key="metadata", name="Session Metadata",
                category="infrastructure", tier="D",
                source_module="core.export_engine",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/metadata.json",
                dependencies=[],
                description="Session metadata: version, timestamps, run config",
            ),
            ReportDefinition(
                key="sync", name="GitHub Sync Report",
                category="infrastructure", tier="D",
                source_module="core.observability.github_sync_engine",
                output_format="json", frequency="session",
                storage_path="reports_for_analyzation/*/sync.json",
                dependencies=[],
                description="GitHub sync status for observability reports",
            ),
            ReportDefinition(
                key="all_reports_bundle", name="Full Report Bundle",
                category="infrastructure", tier="D",
                source_module="utils.report_generator",
                output_format="bundle", frequency="session",
                storage_path="reports_for_analyzation/*/all_reports_bundle.json",
                dependencies=[
                    "perf_report_1d", "perf_report_7d",
                    "signal_truth_matrix", "system_health",
                    "audit_log", "consistency",
                ],
                description="Consolidated archive of all session reports",
            ),
            ReportDefinition(
                key="dashboard_summary", name="Dashboard Summary",
                category="performance", tier="C",
                source_module="API:/api/report",
                output_format="html", frequency="realtime",
                storage_path="reports_for_analyzation/*/00_dashboard_summary.json",
                dependencies=[],
                description="Live trading dashboard summary",
            ),
            # ── Odyssey Analytics Reports ────────────────────────────────────
            ReportDefinition(
                key="odyssey_signal_truth", name="Odyssey Signal Truth Report",
                category="signal", tier="B",
                source_module="analytics.odyssey.signal_truth_reports",
                output_format="json", frequency="daily",
                storage_path="reports/upe/",
                dependencies=["signal_truth_matrix"],
                description="Deep signal truth analytics (Odyssey framework)",
            ),
            ReportDefinition(
                key="odyssey_signal_density", name="Odyssey Signal Density Report",
                category="signal", tier="B",
                source_module="analytics.odyssey.signal_density_reports",
                output_format="json", frequency="daily",
                storage_path="reports/upe/",
                dependencies=[],
                description="Signal density and opportunity analysis (Odyssey)",
            ),
            ReportDefinition(
                key="odyssey_asymmetry", name="Odyssey Asymmetry Report",
                category="signal", tier="B",
                source_module="analytics.odyssey.asymmetry_reports",
                output_format="json", frequency="daily",
                storage_path="reports/upe/",
                dependencies=["asymmetry_validation"],
                description="Deep asymmetry analysis (Odyssey framework)",
            ),
            ReportDefinition(
                key="odyssey_predictive_integrity", name="Odyssey Predictive Integrity",
                category="signal", tier="B",
                source_module="analytics.odyssey.predictive_integrity_reports",
                output_format="json", frequency="daily",
                storage_path="reports/upe/",
                dependencies=["predictive_integrity_monitor"],
                description="Deep predictive integrity analytics (Odyssey)",
            ),
            ReportDefinition(
                key="odyssey_context_clusters", name="Odyssey Context Clusters",
                category="intelligence", tier="B",
                source_module="analytics.odyssey.context_cluster_reports",
                output_format="json", frequency="daily",
                storage_path="reports/upe/",
                dependencies=["context_quality_analysis"],
                description="Context cluster analysis (Odyssey framework)",
            ),
            ReportDefinition(
                key="odyssey_exploration", name="Odyssey Exploration Report",
                category="intelligence", tier="B",
                source_module="analytics.odyssey.exploration_reports",
                output_format="json", frequency="daily",
                storage_path="reports/upe/",
                dependencies=[],
                description="Exploration mode analysis (Odyssey framework)",
            ),
        ]
        for defn in _BUILTIN:
            self._catalog[defn.key] = defn


# Singleton
report_registry = UniversalReportRegistry()
