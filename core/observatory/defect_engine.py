"""
PHOENIX OBSERVATORY-X — Defect Discovery Engine (DDE)  [OX-3A — v2]

Continuously scans all report health records and recent event lineage to
surface systemic defects — patterns that indicate something is structurally
wrong in the PHOENIX ecosystem.

Severity Framework (P0–P3 — Institutional Standard)
────────────────────────────────────────────────────
  P0  PRODUCTION_EMERGENCY  Trading halted or imminent PnL catastrophe
  P1  CRITICAL              Significant PnL risk, immediate action required
  P2  WARNING               Degraded capability, action within 24 hours
  P3  INFORMATIONAL         Minor issue, action within 7 days

Defect Aging States
───────────────────
  OPEN          Detected, no action taken
  ACKNOWLEDGED  Someone has seen it
  IN_PROGRESS   Fix being applied
  RESOLVED      Verified improvement recorded
  WONT_FIX      Accepted risk — documented reason required
  EXPIRED       Auto-closed after 90 days without action (P3 only)

Each DefectRecord also carries:
  - opened_at, age_days, aging_state, aging_history
"""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ── Priority / Severity ───────────────────────────────────────────────────────

P0 = "P0"   # Production emergency
P1 = "P1"   # Critical
P2 = "P2"   # Warning
P3 = "P3"   # Informational

# Legacy aliases for backward compat
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
    # ── Aging (v2) ────────────────────────────────────────────────────────────
    priority: str = P2          # P0 | P1 | P2 | P3
    aging_state: str = "OPEN"   # OPEN | ACKNOWLEDGED | IN_PROGRESS | RESOLVED | WONT_FIX | EXPIRED
    opened_at: float = field(default_factory=time.time)
    aging_history: List[dict] = field(default_factory=list)

    @property
    def age_days(self) -> float:
        return (time.time() - self.opened_at) / 86400

    def transition_aging(self, new_state: str, reason: str = "") -> None:
        self.aging_history.append({
            "from": self.aging_state,
            "to":   new_state,
            "reason": reason,
            "timestamp": time.time(),
        })
        self.aging_state = new_state


# ── Aging Expiry ──────────────────────────────────────────────────────────────
_EXPIRY_DAYS: Dict[str, int] = {P0: 0, P1: 0, P2: 30, P3: 90}


# ── Engine ────────────────────────────────────────────────────────────────────

class DefectDiscoveryEngine:
    """
    Scans health + lineage data and returns a list of DefectRecords.
    Maintains a persistent defect registry with aging lifecycle management.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._last_scan: Optional[dict] = None
        self._last_scan_ts: float = 0.0
        self._known_defects: Dict[str, DefectRecord] = {}  # persisted across scans

    def acknowledge(self, defect_id: str, reason: str = "") -> bool:
        with self._lock:
            d = self._known_defects.get(defect_id)
            if not d:
                return False
            d.transition_aging("ACKNOWLEDGED", reason)
        return True

    def resolve(self, defect_id: str, reason: str = "") -> bool:
        with self._lock:
            d = self._known_defects.get(defect_id)
            if not d:
                return False
            d.transition_aging("RESOLVED", reason)
        return True

    def wont_fix(self, defect_id: str, reason: str = "") -> bool:
        with self._lock:
            d = self._known_defects.get(defect_id)
            if not d:
                return False
            d.transition_aging("WONT_FIX", reason)
        return True

    def get_defect(self, defect_id: str) -> Optional[dict]:
        with self._lock:
            d = self._known_defects.get(defect_id)
        return self._full_serialise(d) if d else None

    def open_defects(self) -> List[dict]:
        with self._lock:
            items = [d for d in self._known_defects.values()
                     if d.aging_state in ("OPEN", "ACKNOWLEDGED", "IN_PROGRESS")]
        return [self._full_serialise(d) for d in items]

    def scan(self) -> dict:
        """
        Run a full defect scan.  Returns a scan report dict.
        Results are cached for 60 s so rapid API calls don't re-scan.
        New defects are persisted in _known_defects for aging lifecycle.
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

        # Assign P0-P3 priorities and persist new defects
        for d in defects:
            d.priority = self._severity_to_priority(d.severity)
            with self._lock:
                if d.defect_id not in self._known_defects:
                    self._known_defects[d.defect_id] = d

        # Auto-expire old P2/P3 defects
        self._age_defects()

        # Sort by priority
        _pri = {P0: 0, P1: 1, P2: 2, P3: 3, CRITICAL: 0, WARN: 1, INFO: 2}
        defects.sort(key=lambda d: _pri.get(d.priority, 9))

        result = {
            "scan_timestamp": now,
            "total_defects":  len(defects),
            "by_priority": {P0: 0, P1: 0, P2: 0, P3: 0,
                            **{d.priority: sum(1 for x in defects if x.priority == d.priority)
                               for d in defects}},
            "by_severity": {
                "CRITICAL": sum(1 for d in defects if d.severity == CRITICAL),
                "WARN":      sum(1 for d in defects if d.severity == WARN),
                "INFO":      sum(1 for d in defects if d.severity == INFO),
            },
            "open_defects_total": len(self.open_defects()),
            "defects": [self._serialise(d) for d in defects],
        }

        with self._lock:
            self._last_scan = result
            self._last_scan_ts = now

        return result

    @staticmethod
    def _severity_to_priority(severity: str) -> str:
        return {CRITICAL: P0, WARN: P1, INFO: P2}.get(severity, P3)

    def _age_defects(self) -> None:
        """Auto-expire P2/P3 defects past their expiry threshold."""
        now = time.time()
        with self._lock:
            for d in list(self._known_defects.values()):
                if d.aging_state not in ("OPEN", "ACKNOWLEDGED"):
                    continue
                expiry = _EXPIRY_DAYS.get(d.priority, 90)
                if expiry > 0 and d.age_days > expiry:
                    d.transition_aging("EXPIRED", f"Auto-expired after {expiry} days")

    def _full_serialise(self, d: DefectRecord) -> dict:
        return {
            **self._serialise(d),
            "priority":       d.priority,
            "aging_state":    d.aging_state,
            "age_days":       round(d.age_days, 1),
            "opened_at":      d.opened_at,
            "aging_history":  d.aging_history,
        }

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
