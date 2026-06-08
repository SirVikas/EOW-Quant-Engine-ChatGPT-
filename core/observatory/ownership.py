"""
PHOENIX OBSERVATORY-X — Report Ownership, SLA & Version Lineage

Every institutional report has three parties:
  Owner    — the module / team responsible for generating it (accountable)
  Steward  — the module responsible for its accuracy and freshness (responsible)
  Consumer — who reads / acts on it (informed)

SLA defines operational expectations:
  expected_runtime_utc — when the report should be ready (e.g. "09:00")
  late_after_mins      — minutes after expected_runtime before it is Late
  critical_after_mins  — minutes after expected_runtime before it is Critical
  escalation_contacts  — logical owners to notify on SLA breach

Version Lineage tracks report schema changes:
  Every time a report's structure or semantics changes, a version bump is
  recorded with a reason.  Audit queries can then answer "what changed?"
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ── Data Models ───────────────────────────────────────────────────────────────

@dataclass
class ReportSLA:
    expected_runtime_utc: Optional[str]   # e.g. "09:00" — None = no scheduled time
    late_after_mins: int                   # minutes past expected before "LATE"
    critical_after_mins: int               # minutes past expected before "CRITICAL"
    max_generation_secs: int               # max allowed generation time before timeout
    escalation_contacts: List[str]         # e.g. ["risk_team", "dev_lead"]
    criticality: str                       # P0 | P1 | P2 | P3


@dataclass
class ReportVersionEntry:
    version: str
    changed_at: float
    changed_by: str      # module or "manual"
    reason: str
    fields_changed: List[str] = field(default_factory=list)


@dataclass
class ReportOwnership:
    report_key: str
    owner: str             # module / system that creates this report
    steward: str           # module responsible for its accuracy
    consumers: List[str]   # who reads / acts on it
    sla: ReportSLA
    current_version: str = "1.0"
    version_history: List[ReportVersionEntry] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def bump_version(
        self,
        new_version: str,
        changed_by: str,
        reason: str,
        fields_changed: Optional[List[str]] = None,
    ) -> None:
        self.version_history.append(ReportVersionEntry(
            version=self.current_version,
            changed_at=time.time(),
            changed_by=changed_by,
            reason=reason,
            fields_changed=fields_changed or [],
        ))
        self.current_version = new_version


# ── Registry ──────────────────────────────────────────────────────────────────

class ReportOwnershipRegistry:
    """
    Maintains ownership records for all registered reports.
    Pre-populated with institutional defaults based on the architecture census.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: Dict[str, ReportOwnership] = {}
        self._bootstrap()

    def register(self, rec: ReportOwnership) -> None:
        with self._lock:
            self._records[rec.report_key] = rec

    def get(self, report_key: str) -> Optional[ReportOwnership]:
        with self._lock:
            return self._records.get(report_key)

    def all(self) -> List[ReportOwnership]:
        with self._lock:
            return list(self._records.values())

    def sla_status(self, report_key: str, last_generated: float) -> dict:
        """Compute SLA compliance status for a report given its last generation time."""
        rec = self.get(report_key)
        if not rec:
            return {"report_key": report_key, "sla_status": "no_sla", "criticality": "P3"}

        if last_generated == 0:
            return {
                "report_key": report_key,
                "sla_status": "never_run",
                "criticality": rec.sla.criticality,
                "escalation_contacts": rec.sla.escalation_contacts,
            }

        age_mins = (time.time() - last_generated) / 60
        if rec.sla.expected_runtime_utc is None:
            sla_state = "ok"
        elif age_mins > rec.sla.critical_after_mins:
            sla_state = "critical"
        elif age_mins > rec.sla.late_after_mins:
            sla_state = "late"
        else:
            sla_state = "ok"

        return {
            "report_key":          report_key,
            "sla_status":          sla_state,
            "criticality":         rec.sla.criticality,
            "age_mins":            round(age_mins, 1),
            "late_threshold_mins": rec.sla.late_after_mins,
            "critical_threshold_mins": rec.sla.critical_after_mins,
            "escalation_contacts": rec.sla.escalation_contacts,
            "owner":               rec.owner,
            "steward":             rec.steward,
        }

    def sla_dashboard(self) -> dict:
        """SLA compliance overview for all reports with SLA definitions."""
        from core.observatory.health_monitor import report_health_monitor
        breach_critical: List[str] = []
        breach_late: List[str] = []
        ok: List[str] = []
        no_sla: List[str] = []

        with self._lock:
            keys = list(self._records.keys())

        for key in keys:
            health = report_health_monitor.assess(key)
            last_gen = health.get("last_generated", 0)
            status = self.sla_status(key, last_gen)
            state = status.get("sla_status", "no_sla")
            if state == "critical":
                breach_critical.append(key)
            elif state == "late":
                breach_late.append(key)
            elif state == "no_sla":
                no_sla.append(key)
            else:
                ok.append(key)

        return {
            "sla_breach_critical": breach_critical,
            "sla_breach_late":     breach_late,
            "sla_ok":              ok,
            "sla_undefined":       no_sla,
            "total_with_sla":      len(keys),
        }

    def version_audit(self, report_key: str) -> dict:
        """Full version lineage for one report."""
        rec = self.get(report_key)
        if not rec:
            return {"report_key": report_key, "error": "not found"}
        return {
            "report_key":       report_key,
            "current_version":  rec.current_version,
            "created_at":       rec.created_at,
            "owner":            rec.owner,
            "steward":          rec.steward,
            "consumers":        rec.consumers,
            "version_history": [
                {
                    "version":        v.version,
                    "changed_at":     v.changed_at,
                    "changed_by":     v.changed_by,
                    "reason":         v.reason,
                    "fields_changed": v.fields_changed,
                }
                for v in rec.version_history
            ],
        }

    # ── Bootstrap ─────────────────────────────────────────────────────────────

    def _bootstrap(self) -> None:
        _P0 = lambda contacts=None: ReportSLA(
            expected_runtime_utc="09:00", late_after_mins=30,
            critical_after_mins=60, max_generation_secs=60,
            escalation_contacts=contacts or ["risk_team"],
            criticality="P0",
        )
        _P1 = lambda contacts=None: ReportSLA(
            expected_runtime_utc="09:00", late_after_mins=60,
            critical_after_mins=120, max_generation_secs=120,
            escalation_contacts=contacts or ["risk_team", "dev_lead"],
            criticality="P1",
        )
        _P2 = lambda contacts=None: ReportSLA(
            expected_runtime_utc=None, late_after_mins=240,
            critical_after_mins=480, max_generation_secs=300,
            escalation_contacts=contacts or ["dev_lead"],
            criticality="P2",
        )
        _P3 = lambda: ReportSLA(
            expected_runtime_utc=None, late_after_mins=1440,
            critical_after_mins=4320, max_generation_secs=600,
            escalation_contacts=[],
            criticality="P3",
        )

        _RECORDS = [
            # ── P0: Mission-critical ──────────────────────────────────────────
            ReportOwnership("system_health",      "observability_orchestrator",  "risk_engine",    ["dashboard", "board"],    _P0()),
            ReportOwnership("audit_log",           "governance_gate",             "compliance_team", ["risk_team", "board"],    _P0()),
            ReportOwnership("consistency",         "consistency_engine",          "risk_engine",    ["risk_team"],              _P0()),
            ReportOwnership("perf_report_1d",      "unified_report_engine_v2",    "analytics",      ["dashboard", "board"],    _P0(["risk_team", "board"])),
            # ── P1: High importance ───────────────────────────────────────────
            ReportOwnership("signal_truth_matrix", "signal_truth_engine",         "analytics",      ["strategy_team"],          _P1()),
            ReportOwnership("regime_performance_matrix","regime_memory",          "analytics",      ["strategy_team", "board"], _P1()),
            ReportOwnership("exit_analysis",       "exit_attribution",            "analytics",      ["strategy_team"],          _P1()),
            ReportOwnership("capital_efficiency",  "capital_flow_engine",         "risk_engine",    ["board", "risk_team"],     _P1()),
            ReportOwnership("intelligence_maturity_report","reporting_layer",     "analytics",      ["board"],                  _P1()),
            ReportOwnership("perf_report_7d",      "unified_report_engine_v2",    "analytics",      ["board"],                  _P1()),
            ReportOwnership("escalations",         "escalation_engine",           "risk_engine",    ["risk_team", "board"],     _P1()),
            # ── P2: Standard ──────────────────────────────────────────────────
            ReportOwnership("rl_intelligence",     "rl_engine",                   "analytics",      ["strategy_team"],          _P2()),
            ReportOwnership("strategy_evolution_report","genome_engine",          "analytics",      ["strategy_team"],          _P2()),
            ReportOwnership("edge_validation_report","edge_engine",               "analytics",      ["strategy_team"],          _P2()),
            ReportOwnership("false_positive_clusters","false_positive_forensics", "analytics",      ["strategy_team"],          _P2()),
            ReportOwnership("confidence_calibration_report","signal_truth_engine","analytics",      ["strategy_team"],          _P2()),
            ReportOwnership("anomalies",           "anomaly_detector",            "observability",  ["risk_team"],              _P2()),
            ReportOwnership("perf_report_20d",     "unified_report_engine_v2",    "analytics",      ["board"],                  _P2()),
            # ── P3: Informational ─────────────────────────────────────────────
            ReportOwnership("ct_scan",             "ct_scan_engine",              "ct_scan_engine", ["dev_lead"],               _P3()),
            ReportOwnership("negative_memory",     "learning_memory",             "analytics",      ["dev_lead"],               _P3()),
            ReportOwnership("patterns",            "learning_memory",             "analytics",      ["dev_lead"],               _P3()),
            ReportOwnership("metadata",            "export_engine",               "export_engine",  ["dev_lead"],               _P3()),
            ReportOwnership("sync",                "github_sync_engine",          "github_sync_engine", ["dev_lead"],           _P3()),
        ]
        for r in _RECORDS:
            self._records[r.report_key] = r


# Singleton
report_ownership_registry = ReportOwnershipRegistry()
