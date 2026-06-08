"""
PHOENIX OBSERVATORY-X — Defect Discovery Engine (DDE)  [OX-3A]

Continuously scans all report health records and recent event lineage to
surface systemic defects — patterns that indicate something is structurally
wrong in the PHOENIX ecosystem.

A defect is different from a single report failure:
  • A single failure = transient error
  • A systemic defect = same failure type recurring across multiple reports,
    time windows, or modules, indicating a root-cause worth investigating

Defect types
────────────
  RECURRING_FAILURE   Same report fails repeatedly
  STALENESS_CLUSTER   Multiple related reports are all stale simultaneously
  DATA_QUALITY        Completeness scores falling across a report family
  PATTERN_DIVERGENCE  Signals or patterns are contradicting each other
  GOVERNANCE_GAP      Governance-tier reports are absent or perpetually failing
  LOSS_CONCENTRATION  Lineage shows losses clustering in a specific actor/regime

Each defect produces a DefectRecord with:
  - severity (INFO / WARN / CRITICAL)
  - affected reports list
  - probable root cause description
  - recommended investigator action

The engine runs on-demand (called from the scheduler or /api/observatory/inspect).
"""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ── Severity ──────────────────────────────────────────────────────────────────

INFO     = "INFO"
WARN     = "WARN"
CRITICAL = "CRITICAL"


# ── Data Model ────────────────────────────────────────────────────────────────

@dataclass
class DefectRecord:
    defect_id: str
    defect_type: str
    severity: str
    title: str
    description: str
    affected_reports: List[str]
    probable_cause: str
    recommended_action: str
    detected_at: float = field(default_factory=time.time)
    evidence: Dict = field(default_factory=dict)


# ── Engine ────────────────────────────────────────────────────────────────────

class DefectDiscoveryEngine:
    """
    Scans health + lineage data and returns a list of DefectRecords.
    Stateless per scan — every call to scan() produces a fresh result.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._last_scan: Optional[dict] = None
        self._last_scan_ts: float = 0.0

    def scan(self) -> dict:
        """
        Run a full defect scan.  Returns a scan report dict.
        Results are cached for 60 s so rapid API calls don't re-scan.
        """
        now = time.time()
        with self._lock:
            if now - self._last_scan_ts < 60 and self._last_scan:
                return self._last_scan

        defects: List[DefectRecord] = []
        defects.extend(self._scan_recurring_failures())
        defects.extend(self._scan_staleness_cluster())
        defects.extend(self._scan_governance_gap())
        defects.extend(self._scan_data_quality())
        defects.extend(self._scan_loss_concentration())

        # Sort by severity priority
        _pri = {CRITICAL: 0, WARN: 1, INFO: 2}
        defects.sort(key=lambda d: _pri.get(d.severity, 9))

        result = {
            "scan_timestamp": now,
            "total_defects":  len(defects),
            "by_severity": {
                "CRITICAL": sum(1 for d in defects if d.severity == CRITICAL),
                "WARN":      sum(1 for d in defects if d.severity == WARN),
                "INFO":      sum(1 for d in defects if d.severity == INFO),
            },
            "defects": [self._serialise(d) for d in defects],
        }

        with self._lock:
            self._last_scan = result
            self._last_scan_ts = now

        return result

    # ── Scan Routines ─────────────────────────────────────────────────────────

    def _scan_recurring_failures(self) -> List[DefectRecord]:
        """Reports with error_count ≥ 3 or consecutive failures."""
        results = []
        try:
            from core.observatory.health_monitor import report_health_monitor
            assessments = report_health_monitor.assess_all()
        except Exception:
            return results

        for a in assessments:
            ec = a.get("error_count", 0)
            if ec >= 5:
                sev = CRITICAL
            elif ec >= 3:
                sev = WARN
            else:
                continue
            results.append(DefectRecord(
                defect_id   = f"RECURRING_FAILURE_{a['report_key']}",
                defect_type = "RECURRING_FAILURE",
                severity    = sev,
                title       = f"Recurring failure: {a['report_key']}",
                description = (
                    f"Report '{a['report_key']}' has failed {ec} times. "
                    f"Last error: {a.get('last_error_msg', 'unknown')}"
                ),
                affected_reports  = [a["report_key"]],
                probable_cause    = "Generator crash, missing dependency, or data corruption",
                recommended_action= (
                    f"Investigate generator at {a.get('source_module', 'unknown source')}. "
                    "Check data_lake for underlying data gaps."
                ),
                evidence = {"error_count": ec, "last_error": a.get("last_error_msg", "")},
            ))
        return results

    def _scan_staleness_cluster(self) -> List[DefectRecord]:
        """3+ related reports all stale at the same time."""
        results = []
        try:
            from core.observatory.health_monitor import report_health_monitor
            from core.observatory.relationship_engine import report_relationship_engine
            assessments = report_health_monitor.assess_all()
        except Exception:
            return results

        stale_keys = {
            a["report_key"]
            for a in assessments
            if a.get("verdict") in ("warn", "critical", "failed")
        }
        if len(stale_keys) < 3:
            return results

        # Group by category
        try:
            from core.observatory.registry import report_registry
            by_cat: Dict[str, List[str]] = {}
            for key in stale_keys:
                defn = report_registry.get(key)
                if defn:
                    by_cat.setdefault(defn.category, []).append(key)
        except Exception:
            return results

        for cat, keys in by_cat.items():
            if len(keys) >= 3:
                results.append(DefectRecord(
                    defect_id   = f"STALENESS_CLUSTER_{cat.upper()}",
                    defect_type = "STALENESS_CLUSTER",
                    severity    = WARN,
                    title       = f"Staleness cluster in '{cat}' reports",
                    description = (
                        f"{len(keys)} reports in the '{cat}' category are stale "
                        f"simultaneously, suggesting a shared upstream dependency failure."
                    ),
                    affected_reports  = keys,
                    probable_cause    = (
                        "Shared data source (data_lake, market_data, or API) unavailable"
                    ),
                    recommended_action= (
                        "Check data_lake health, exchange API connectivity, "
                        "and Report Scheduler status."
                    ),
                    evidence = {"stale_in_category": keys},
                ))
        return results

    def _scan_governance_gap(self) -> List[DefectRecord]:
        """Governance-tier reports that have never run or are critical-stale."""
        results = []
        try:
            from core.observatory.registry import report_registry
            from core.observatory.health_monitor import report_health_monitor
            gov_reports = report_registry.by_category("governance")
        except Exception:
            return results

        never_run = []
        critical  = []
        for r in gov_reports:
            a = report_health_monitor.assess(r.key)
            if a.get("verdict") == "never_run":
                never_run.append(r.key)
            elif a.get("verdict") == "critical":
                critical.append(r.key)

        if never_run:
            results.append(DefectRecord(
                defect_id   = "GOVERNANCE_GAP_NEVER_RUN",
                defect_type = "GOVERNANCE_GAP",
                severity    = WARN,
                title       = "Governance reports have never executed",
                description = (
                    f"{len(never_run)} governance reports have no recorded run: "
                    f"{', '.join(never_run)}"
                ),
                affected_reports  = never_run,
                probable_cause    = "Scheduler handlers not yet wired, or cold start",
                recommended_action= (
                    "Attach handlers via report_scheduler.register_handler() "
                    "or trigger manually via /api/observatory/scheduler/trigger/{key}"
                ),
                evidence = {"never_run_reports": never_run},
            ))
        if critical:
            results.append(DefectRecord(
                defect_id   = "GOVERNANCE_GAP_CRITICAL_STALE",
                defect_type = "GOVERNANCE_GAP",
                severity    = CRITICAL,
                title       = "Critical-stale governance reports",
                description = (
                    f"{len(critical)} governance reports are critically overdue: "
                    f"{', '.join(critical)}"
                ),
                affected_reports  = critical,
                probable_cause    = "Generator failure or scheduler disruption",
                recommended_action= "Immediate investigation of governance report generators",
                evidence = {"critical_reports": critical},
            ))
        return results

    def _scan_data_quality(self) -> List[DefectRecord]:
        """Reports whose data_completeness has fallen below 70 %."""
        results = []
        try:
            from core.observatory.health_monitor import report_health_monitor
            assessments = report_health_monitor.assess_all()
        except Exception:
            return results

        low_quality = [
            a for a in assessments
            if a.get("data_completeness", 100) < 70
            and a.get("verdict") not in ("never_run",)
        ]
        if low_quality:
            results.append(DefectRecord(
                defect_id   = "DATA_QUALITY_LOW_COMPLETENESS",
                defect_type = "DATA_QUALITY",
                severity    = WARN,
                title       = f"Low data completeness on {len(low_quality)} reports",
                description = (
                    f"{len(low_quality)} reports are reporting data_completeness < 70 %, "
                    "indicating partial or missing upstream data."
                ),
                affected_reports  = [a["report_key"] for a in low_quality],
                probable_cause    = "Upstream data source returning partial data",
                recommended_action= (
                    "Check DataLake trade count and market data feed continuity. "
                    "Verify report generators are receiving full data windows."
                ),
                evidence = {
                    r["report_key"]: r.get("data_completeness")
                    for r in low_quality
                },
            ))
        return results

    def _scan_loss_concentration(self) -> List[DefectRecord]:
        """Lineage shows multiple losses attributed to the same actor."""
        results = []
        try:
            from core.observatory.lineage_tracker import event_lineage_tracker
            loss_events = event_lineage_tracker.losses(limit=100)
        except Exception:
            return results

        if len(loss_events) < 5:
            return results

        # Count actors in loss lineages
        actor_counts: Dict[str, int] = {}
        for evt in loss_events:
            for node in evt.get("nodes", []):
                actor = node.get("actor", "")
                if actor:
                    actor_counts[actor] = actor_counts.get(actor, 0) + 1

        total_losses = len(loss_events)
        for actor, count in actor_counts.items():
            pct = count / total_losses
            if pct >= 0.6 and count >= 5:
                results.append(DefectRecord(
                    defect_id   = f"LOSS_CONCENTRATION_{actor.upper().replace('.', '_')}",
                    defect_type = "LOSS_CONCENTRATION",
                    severity    = CRITICAL if pct >= 0.8 else WARN,
                    title       = f"Loss concentration: {actor}",
                    description = (
                        f"Actor '{actor}' appears in {count}/{total_losses} loss event lineages "
                        f"({pct:.0%}).  High concentration suggests a systemic issue."
                    ),
                    affected_reports  = [],
                    probable_cause    = (
                        f"'{actor}' may have misconfigured parameters or be generating "
                        "signals in unsuitable market conditions"
                    ),
                    recommended_action= (
                        f"Review parameters and recent decisions of '{actor}'. "
                        "Consider CORTEX weight reduction for this module."
                    ),
                    evidence = {
                        "actor": actor,
                        "loss_appearances": count,
                        "total_losses": total_losses,
                        "concentration_pct": round(pct * 100, 1),
                    },
                ))
        return results

    # ── Serialisation ─────────────────────────────────────────────────────────

    @staticmethod
    def _serialise(d: DefectRecord) -> dict:
        return {
            "defect_id":          d.defect_id,
            "defect_type":        d.defect_type,
            "severity":           d.severity,
            "title":              d.title,
            "description":        d.description,
            "affected_reports":   d.affected_reports,
            "probable_cause":     d.probable_cause,
            "recommended_action": d.recommended_action,
            "detected_at":        d.detected_at,
            "evidence":           d.evidence,
        }


# Singleton
defect_engine = DefectDiscoveryEngine()
