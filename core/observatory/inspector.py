"""
PHOENIX OBSERVATORY-X — PHOENIX Inspector  [OX-3B]

The Inspector is the automated investigator subsystem of OBSERVATORY-X.
Given an anomaly signal (e.g. "30 consecutive losing trades"), it performs
a systematic multi-dimensional investigation and returns a structured
InvestigationReport answering:

  • Which module / actor is most implicated?
  • Which market session or time window dominates?
  • Which regime was active?
  • Which strategy was used most?
  • Which risk setting allowed the trade through?
  • Are there common parameter values across the loss events?

The Inspector does NOT modify any parameters — it is a read-only forensic
tool.  Recommendations are produced by the RecommendationEngine (OX-3C).

Investigation types
───────────────────
  LOSS_INVESTIGATION    Triggered by N consecutive losses or high loss rate
  ANOMALY_INVESTIGATION Triggered by anomaly_detector flagging an event
  STALE_REPORT          Triggered by report health going critical
  CUSTOM                Triggered manually via API
"""
from __future__ import annotations

import time
import threading
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ── Data Model ────────────────────────────────────────────────────────────────

@dataclass
class InvestigationFinding:
    dimension: str       # "actor" | "session" | "regime" | "strategy" | "parameter"
    label: str           # human label for this finding
    value: Any           # the specific value (e.g. "06-08 UTC", "momentum_engine")
    frequency: float     # fraction of loss events that share this value (0–1)
    sample_count: int
    significance: str    # "high" | "medium" | "low"


@dataclass
class InvestigationReport:
    investigation_id: str
    investigation_type: str
    trigger: str                      # what caused this investigation
    started_at: float
    completed_at: float = 0.0
    status: str = "pending"           # pending | complete | inconclusive
    findings: List[InvestigationFinding] = field(default_factory=list)
    summary: str = ""
    primary_suspect: str = ""         # top finding label
    evidence_sample_size: int = 0
    recommendations: List[str] = field(default_factory=list)  # filled by RecommendationEngine


# ── Inspector ─────────────────────────────────────────────────────────────────

class PhoenixInspector:
    """
    Read-only automated investigator.  Interrogates lineage, health, and
    (where available) trade history to isolate root contributors to losses
    and anomalies.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._investigations: Dict[str, InvestigationReport] = {}

    # ── Public API ────────────────────────────────────────────────────────────

    def investigate_losses(
        self,
        trigger: str = "manual",
        loss_limit: int = 100,
    ) -> InvestigationReport:
        """
        Investigate recent loss events from the lineage tracker.
        Returns a completed InvestigationReport.
        """
        inv_id = f"LOSS_{int(time.time())}"
        report = InvestigationReport(
            investigation_id   = inv_id,
            investigation_type = "LOSS_INVESTIGATION",
            trigger            = trigger,
            started_at         = time.time(),
        )
        self._store(report)

        try:
            from core.observatory.lineage_tracker import event_lineage_tracker
            loss_events = event_lineage_tracker.losses(limit=loss_limit)
            report.evidence_sample_size = len(loss_events)

            if len(loss_events) < 3:
                report.status  = "inconclusive"
                report.summary = f"Insufficient loss events for analysis (found {len(loss_events)}, need ≥ 3)"
                report.completed_at = time.time()
                return report

            findings = []
            findings.extend(self._analyse_actors(loss_events))
            findings.extend(self._analyse_timestamps(loss_events))
            findings.extend(self._analyse_event_types(loss_events))

            # Sort by frequency descending
            findings.sort(key=lambda f: f.frequency, reverse=True)
            report.findings = findings

            if findings:
                top = findings[0]
                report.primary_suspect = f"{top.dimension}: {top.value} ({top.frequency:.0%} of losses)"
                report.summary = (
                    f"Investigated {len(loss_events)} loss events. "
                    f"Highest concentration: {report.primary_suspect}."
                )
            else:
                report.summary = "No strong concentration found across investigated dimensions."

            report.status = "complete"

        except Exception as exc:
            report.status  = "inconclusive"
            report.summary = f"Investigation failed: {exc}"

        report.completed_at = time.time()
        return report

    def investigate_defect(
        self,
        defect_id: str,
        trigger: str = "defect_engine",
    ) -> InvestigationReport:
        """
        Drill into a specific defect identified by the DefectDiscoveryEngine.
        """
        inv_id = f"DEFECT_{defect_id}_{int(time.time())}"
        report = InvestigationReport(
            investigation_id   = inv_id,
            investigation_type = "ANOMALY_INVESTIGATION",
            trigger            = trigger,
            started_at         = time.time(),
        )
        self._store(report)

        try:
            from core.observatory.defect_engine import defect_engine
            scan = defect_engine.scan()
            target = next(
                (d for d in scan.get("defects", []) if d["defect_id"] == defect_id),
                None,
            )
            if not target:
                report.status  = "inconclusive"
                report.summary = f"Defect '{defect_id}' not found in latest scan"
                report.completed_at = time.time()
                return report

            report.evidence_sample_size = 1
            findings = [
                InvestigationFinding(
                    dimension   = "defect_type",
                    label       = target.get("title", defect_id),
                    value       = target.get("defect_type", ""),
                    frequency   = 1.0,
                    sample_count= 1,
                    significance= "high" if target.get("severity") == "CRITICAL" else "medium",
                )
            ]
            affected = target.get("affected_reports", [])
            if affected:
                findings.append(InvestigationFinding(
                    dimension   = "affected_reports",
                    label       = "Reports impacted",
                    value       = affected,
                    frequency   = len(affected) / 47,  # fraction of total report catalog
                    sample_count= len(affected),
                    significance= "high" if len(affected) > 5 else "medium",
                ))
            report.findings = findings
            report.primary_suspect = target.get("probable_cause", "")
            report.summary = target.get("description", "")
            report.status  = "complete"

        except Exception as exc:
            report.status  = "inconclusive"
            report.summary = f"Investigation failed: {exc}"

        report.completed_at = time.time()
        return report

    def get_investigation(self, inv_id: str) -> Optional[dict]:
        with self._lock:
            r = self._investigations.get(inv_id)
        return self._serialise(r) if r else None

    def recent_investigations(self, limit: int = 10) -> List[dict]:
        with self._lock:
            items = list(reversed(list(self._investigations.values())))
        return [self._serialise(r) for r in items[:limit]]

    def summary(self) -> dict:
        with self._lock:
            total = len(self._investigations)
            by_status: Dict[str, int] = {}
            by_type: Dict[str, int] = {}
            for r in self._investigations.values():
                by_status[r.status] = by_status.get(r.status, 0) + 1
                by_type[r.investigation_type] = by_type.get(r.investigation_type, 0) + 1
        return {
            "total_investigations": total,
            "by_status": by_status,
            "by_type":   by_type,
        }

    # ── Dimension Analysers ───────────────────────────────────────────────────

    @staticmethod
    def _analyse_actors(events: List[dict]) -> List[InvestigationFinding]:
        """Which actors appear most in loss lineages."""
        actor_hits: Counter = Counter()
        total = len(events)
        for evt in events:
            actors_seen = set()
            for node in evt.get("nodes", []):
                actor = node.get("actor", "")
                if actor and actor not in actors_seen:
                    actor_hits[actor] += 1
                    actors_seen.add(actor)
        findings = []
        for actor, count in actor_hits.most_common(5):
            freq = count / total
            if freq < 0.25:
                break
            findings.append(InvestigationFinding(
                dimension   = "actor",
                label       = f"Module: {actor}",
                value       = actor,
                frequency   = round(freq, 3),
                sample_count= count,
                significance= "high" if freq >= 0.6 else ("medium" if freq >= 0.4 else "low"),
            ))
        return findings

    @staticmethod
    def _analyse_timestamps(events: List[dict]) -> List[InvestigationFinding]:
        """Which UTC hour appears most in loss event timestamps."""
        hour_hits: Counter = Counter()
        total = len(events)
        import datetime
        for evt in events:
            ts = evt.get("created_at", 0)
            if ts:
                hour = datetime.datetime.utcfromtimestamp(ts).hour
                hour_hits[hour] += 1
        findings = []
        for hour, count in hour_hits.most_common(3):
            freq = count / total
            if freq < 0.3:
                break
            findings.append(InvestigationFinding(
                dimension   = "session",
                label       = f"UTC hour {hour:02d}:00",
                value       = f"{hour:02d}:00 UTC",
                frequency   = round(freq, 3),
                sample_count= count,
                significance= "high" if freq >= 0.5 else "medium",
            ))
        return findings

    @staticmethod
    def _analyse_event_types(events: List[dict]) -> List[InvestigationFinding]:
        """Which event sub-types appear most."""
        type_hits: Counter = Counter()
        total = len(events)
        for evt in events:
            for node in evt.get("nodes", []):
                label = node.get("label", "")
                if label:
                    type_hits[label] += 1
        findings = []
        for label, count in type_hits.most_common(3):
            freq = count / total
            if freq < 0.3:
                break
            findings.append(InvestigationFinding(
                dimension   = "step_type",
                label       = label,
                value       = label,
                frequency   = round(freq, 3),
                sample_count= count,
                significance= "medium",
            ))
        return findings

    # ── Storage ───────────────────────────────────────────────────────────────

    def _store(self, report: InvestigationReport) -> None:
        with self._lock:
            if len(self._investigations) >= 200:
                oldest = next(iter(self._investigations))
                del self._investigations[oldest]
            self._investigations[report.investigation_id] = report

    @staticmethod
    def _serialise(r: InvestigationReport) -> dict:
        return {
            "investigation_id":    r.investigation_id,
            "investigation_type":  r.investigation_type,
            "trigger":             r.trigger,
            "started_at":          r.started_at,
            "completed_at":        r.completed_at,
            "status":              r.status,
            "summary":             r.summary,
            "primary_suspect":     r.primary_suspect,
            "evidence_sample_size": r.evidence_sample_size,
            "findings": [
                {
                    "dimension":    f.dimension,
                    "label":        f.label,
                    "value":        f.value,
                    "frequency":    f.frequency,
                    "sample_count": f.sample_count,
                    "significance": f.significance,
                }
                for f in r.findings
            ],
            "recommendations": r.recommendations,
        }


# Singleton
phoenix_inspector = PhoenixInspector()
