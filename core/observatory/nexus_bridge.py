"""
PHOENIX OBSERVATORY-X — NEXUS Bridge

Every Observatory event must enter IMRAF (Institutional Memory).
Without this, institutional memory breaks — NEXUS cannot learn from what
Observatory discovers, and AEG has no evidence base for governance decisions.

Events that enter IMRAF:
  - Defect detected           → record_incident()
  - Investigation completed   → record_decision()
  - Recommendation generated  → record_decision()
  - Truth state transition    → record_knowledge()
  - SLA breach                → record_incident()
  - Blame record created      → record_incident()

All calls are non-fatal — Observatory continues operating even if IMRAF
is unavailable (e.g. during tests or early boot).
"""
from __future__ import annotations

import time
from typing import Optional


def _imraf():
    """Lazy import to avoid circular imports at module load time."""
    try:
        from core.institutional_memory.imraf_engine import imraf as _i
        return _i
    except Exception:
        return None


# ── Event Recorders ───────────────────────────────────────────────────────────

def record_defect(defect: dict) -> None:
    """Record a detected defect as an IMRAF incident."""
    try:
        im = _imraf()
        if not im:
            return
        severity = defect.get("severity", "WARN")
        imraf_severity = (
            "critical" if severity == "CRITICAL" else
            "high"     if severity == "WARN" else
            "medium"
        )
        im.record_incident(
            title=f"[OBSERVATORY] Defect: {defect.get('title', defect.get('defect_id', '?'))}",
            description=defect.get("description", ""),
            severity=imraf_severity,
            component="observatory_defect_engine",
            resolution=defect.get("recommended_action", ""),
            metadata={
                "defect_id":       defect.get("defect_id", ""),
                "defect_type":     defect.get("defect_type", ""),
                "affected_reports": defect.get("affected_reports", []),
                "evidence":        defect.get("evidence", {}),
            },
        )
    except Exception:
        pass  # non-fatal


def record_investigation(report: dict) -> None:
    """Record a completed investigation as an IMRAF decision."""
    try:
        im = _imraf()
        if not im:
            return
        im.record_decision(
            title=(
                f"[OBSERVATORY] Investigation: {report.get('investigation_type', '?')} "
                f"— {report.get('investigation_id', '?')}"
            ),
            rationale=report.get("summary", ""),
            outcome=report.get("status", "unknown"),
            component="phoenix_inspector",
            metadata={
                "investigation_id":  report.get("investigation_id", ""),
                "primary_suspect":   report.get("primary_suspect", ""),
                "evidence_size":     report.get("evidence_sample_size", 0),
                "findings_count":    len(report.get("findings", [])),
            },
        )
    except Exception:
        pass


def record_recommendation_bundle(bundle: dict) -> None:
    """Record generated recommendations as IMRAF decisions."""
    try:
        im = _imraf()
        if not im:
            return
        recs = bundle.get("recommendations", [])
        if not recs:
            return
        # Record as a batch decision
        im.record_decision(
            title=(
                f"[OBSERVATORY] Recommendations: {len(recs)} generated "
                f"for investigation {bundle.get('source_investigation_id', '?')}"
            ),
            rationale="; ".join(r.get("title", "") for r in recs[:3]),
            outcome="pending_application",
            component="recommendation_engine",
            metadata={
                "rec_count": len(recs),
                "rec_types": [r.get("rec_type") for r in recs],
                "top_action": recs[0].get("action", "") if recs else "",
            },
        )
    except Exception:
        pass


def record_truth_transition(truth_record: dict, new_state: str) -> None:
    """Record a truth state transition as IMRAF knowledge."""
    try:
        im = _imraf()
        if not im:
            return
        im.record_knowledge(
            title=(
                f"[OBSERVATORY] Truth transition: {truth_record.get('subject', '?')} "
                f"→ {new_state}"
            ),
            content=(
                f"Subject: {truth_record.get('subject', '?')} "
                f"({truth_record.get('subject_type', '?')}) "
                f"transitioned to {new_state}. "
                f"{truth_record.get('description', '')}"
            ),
            source="observatory_truth_layer",
            metadata={
                "truth_id":   truth_record.get("truth_id", ""),
                "new_state":  new_state,
                "prev_state": truth_record.get("state", ""),
            },
        )
    except Exception:
        pass


def record_sla_breach(report_key: str, sla_status: dict) -> None:
    """Record an SLA breach as an IMRAF incident."""
    try:
        im = _imraf()
        if not im:
            return
        criticality = sla_status.get("criticality", "P2")
        severity = "critical" if criticality == "P0" else "high" if criticality == "P1" else "medium"
        im.record_incident(
            title=f"[OBSERVATORY] SLA Breach: {report_key} ({sla_status.get('sla_status','?')})",
            description=(
                f"Report '{report_key}' breached its SLA. "
                f"Age: {sla_status.get('age_mins', '?')} min. "
                f"Criticality: {criticality}."
            ),
            severity=severity,
            component="observatory_sla",
            resolution=(
                f"Contact: {', '.join(sla_status.get('escalation_contacts', []))}. "
                f"Trigger: POST /api/observatory/scheduler/trigger/{report_key}"
            ),
            metadata=sla_status,
        )
    except Exception:
        pass


def record_blame(blame_record: dict) -> None:
    """Record a blame attribution event as an IMRAF incident."""
    try:
        im = _imraf()
        if not im:
            return
        im.record_incident(
            title=(
                f"[CORTEX] Blame: Trade {blame_record.get('trade_id', '?')} "
                f"— primary: {blame_record.get('primary_cause', '?')}"
            ),
            description=blame_record.get("root_cause_description", ""),
            severity="medium",
            component="blame_attribution_engine",
            resolution=(
                f"Review module '{blame_record.get('primary_cause', '?')}'. "
                "Check /api/cortex/blame for full attribution."
            ),
            metadata={
                "trade_id":        blame_record.get("trade_id", ""),
                "loss_amount":     blame_record.get("loss_amount", 0),
                "primary_cause":   blame_record.get("primary_cause", ""),
                "primary_score":   blame_record.get("primary_cause_score", 0),
            },
        )
    except Exception:
        pass
