"""
PHOENIX PCAO — Chairman Command Center  [BRD-01, BRD-02, BRD-03]

BRD-01: Institutional Command Center — single view of all 6 layers
BRD-02: Chairman Dashboard           — 3 questions: What Happened? What Matters? What Next?
BRD-03: Executive Alert System       — critical issue detection and routing

This is the top-level executive intelligence layer.
The Chairman sees:
  1. What has happened across all PHOENIX layers (recent events)
  2. What matters most right now (prioritized by risk and impact)
  3. What the institution should do next (autonomous recommendation)
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


ALERT_SEVERITY = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}


@dataclass
class ExecutiveAlert:
    alert_id: str
    severity: str           # CRITICAL / HIGH / MEDIUM / LOW
    layer: str              # NEXUS / OBSX / CORTEX / PTP / AEG / PCAO
    title: str
    detail: str
    action_required: str
    created_at: float = field(default_factory=time.time)
    acknowledged: bool = False


class ChairmanCommandCenter:
    """
    Top-level executive intelligence: command center, chairman dashboard, alert system.
    """

    def __init__(self) -> None:
        self._alerts: List[ExecutiveAlert] = []

    # ── BRD-01: Institutional Command Center ─────────────────────────────────

    def command_center(self) -> dict:
        layers = {}

        # NEXUS
        try:
            from core.nexus.institutional_health_index import institutional_health_index as _ihi
            health = _ihi.health_report()
            layers["NEXUS"] = {
                "score":   health.get("component_scores", {}).get("NEXUS", 0),
                "status":  "HEALTHY" if health.get("component_scores", {}).get("NEXUS", 0) >= 60 else "DEGRADED",
                "summary": f"Institutional memory active — health {health.get('component_scores', {}).get('NEXUS', 0):.0f}/100",
            }
        except Exception:
            layers["NEXUS"] = {"score": 50, "status": "UNKNOWN", "summary": "Unable to query NEXUS"}

        # OBSX
        try:
            from core.observatory.long_term_archive import long_term_archive as _lta
            summ = _lta.summary()
            archived = summ.get("total_archived", 0)
            layers["OBSX"] = {
                "score":   min(100, archived * 2),
                "status":  "HEALTHY" if archived >= 20 else "DEVELOPING",
                "summary": f"{archived} recommendations archived",
            }
        except Exception:
            layers["OBSX"] = {"score": 50, "status": "UNKNOWN", "summary": "Unable to query OBSX"}

        # CORTEX
        try:
            from core.cortex.governance_metrics import governance_metrics as _gm
            kpi = _gm.governance_kpi()
            score = kpi.get("governance_score", 50)
            layers["CORTEX"] = {
                "score":   score,
                "status":  kpi.get("governance_label", "UNKNOWN"),
                "summary": f"Governance score {score:.0f}/100 — {kpi.get('governance_label')}",
            }
        except Exception:
            layers["CORTEX"] = {"score": 50, "status": "UNKNOWN", "summary": "Unable to query CORTEX"}

        # PTP
        try:
            from core.trust.live_accuracy_validator import live_accuracy_validator as _lav
            report = _lav.all_pillars_report()
            proven = report.get("proven_pillars", 0)
            total_pillars = 5
            layers["PTP"] = {
                "score":   min(100, proven * 20),
                "status":  "PROVEN" if proven >= 3 else "ACCUMULATING",
                "summary": f"{proven}/{total_pillars} pillars PROVEN",
            }
        except Exception:
            layers["PTP"] = {"score": 30, "status": "UNKNOWN", "summary": "Unable to query PTP"}

        # AEG
        try:
            from core.nexus.aeg_pipeline.aeg_validation_program import aeg_validation_program as _avp
            readiness = _avp.autonomy_readiness_index()
            score = readiness.get("readiness_score", 20)
            layers["AEG"] = {
                "score":   score,
                "status":  readiness.get("readiness_label", "UNKNOWN"),
                "summary": f"AEG readiness {score:.0f}/100 — {readiness.get('readiness_label')}",
            }
        except Exception:
            layers["AEG"] = {"score": 20, "status": "UNKNOWN", "summary": "Unable to query AEG"}

        # PCAO
        try:
            from core.pcao.risk_office import risk_office as _ro
            dash = _ro.risk_dashboard()
            critical = dash.get("critical_open", 0)
            high = dash.get("high_open", 0)
            pcao_score = max(0, 80 - critical * 20 - high * 8)
            layers["PCAO"] = {
                "score":   pcao_score,
                "status":  "CRITICAL" if critical > 0 else ("HIGH_RISK" if high > 0 else "STABLE"),
                "summary": f"{critical} critical, {high} high risks open",
            }
        except Exception:
            layers["PCAO"] = {"score": 50, "status": "UNKNOWN", "summary": "Unable to query PCAO"}

        overall = sum(v.get("score", 0) for v in layers.values()) / max(1, len(layers))
        return {
            "layers":         layers,
            "overall_health": round(overall, 1),
            "health_label":   "OPTIMAL" if overall >= 80 else "HEALTHY" if overall >= 60 else "STABLE" if overall >= 40 else "DEGRADED",
            "generated_at":   time.time(),
        }

    # ── BRD-02: Chairman Dashboard ────────────────────────────────────────────

    def chairman_dashboard(self) -> dict:
        what_happened = self._what_happened()
        what_matters  = self._what_matters()
        what_next     = self._what_next()
        return {
            "what_happened": what_happened,
            "what_matters":  what_matters,
            "what_next":     what_next,
            "generated_at":  time.time(),
        }

    def _what_happened(self) -> List[dict]:
        events = []
        try:
            from core.pcao.human_governance_layer import human_governance_layer as _hgl
            recent = _hgl.recent_actions(limit=5)
            for a in recent:
                events.append({
                    "layer": "PCAO",
                    "event": f"[{a['action_type']}] {a['subject_id']} by {a['actor']}",
                    "when":  a.get("recorded_at"),
                })
        except Exception:
            pass

        try:
            from core.nexus.cross_layer_intelligence import cross_layer_intelligence as _cli
            cascades = _cli.recent_cascades(limit=5)
            for c in cascades:
                events.append({
                    "layer": "NEXUS",
                    "event": f"Cross-layer cascade: {c.get('cascade_type')}",
                    "when":  c.get("triggered_at"),
                })
        except Exception:
            pass

        return sorted(events, key=lambda x: x.get("when", 0), reverse=True)[:10]

    def _what_matters(self) -> List[dict]:
        items = []
        try:
            from core.pcao.risk_office import risk_office as _ro
            dash = _ro.risk_dashboard()
            for r in dash.get("top_risks", [])[:3]:
                items.append({
                    "priority": 1 if r.get("severity") == "CRITICAL" else 2,
                    "layer":    "PCAO",
                    "title":    r["title"],
                    "severity": r["severity"],
                    "action":   r["mitigation"],
                })
        except Exception:
            pass

        try:
            from core.nexus.evidence_supremacy_engine import evidence_supremacy_engine as _ese
            summ = _ese.summary()
            blocks = summ.get("active_blocks", 0)
            if blocks > 0:
                items.append({
                    "priority": 2,
                    "layer": "NEXUS",
                    "title": f"{blocks} governance actions blocked by Evidence Supremacy",
                    "severity": "HIGH",
                    "action": "Review blocked actions at /api/nexus/evidence-supremacy/blocked",
                })
        except Exception:
            pass

        try:
            alerts = self.detect_alerts()
            for a in alerts[:3]:
                items.append({
                    "priority": 1 if a["severity"] == "CRITICAL" else 2,
                    "layer":    a["layer"],
                    "title":    a["title"],
                    "severity": a["severity"],
                    "action":   a["action_required"],
                })
        except Exception:
            pass

        return sorted(items, key=lambda x: x.get("priority", 99))[:8]

    def _what_next(self) -> dict:
        try:
            from core.pcao.roadmap_engine import roadmap_engine as _re
            next_step = _re.autonomous_next_step()
            return next_step
        except Exception:
            try:
                from core.pcao.decision_support import decision_support as _ds
                recs = _ds.generate_recommendations()
                return {
                    "next_action": recs.get("top_action", "Continue evidence accumulation"),
                    "urgency": "HIGH",
                }
            except Exception:
                return {"next_action": "Continue evidence accumulation across all pillars", "urgency": "MEDIUM"}

    # ── BRD-03: Executive Alert System ────────────────────────────────────────

    def detect_alerts(self) -> List[dict]:
        alerts: List[ExecutiveAlert] = []
        ts = int(time.time() * 1000)

        # Trust decay alerts
        try:
            from core.trust.trust_decay_engine import trust_decay_engine as _tde
            for ds in _tde.all_decay_statuses():
                if ds.get("is_stale") and ds.get("current_score", 100) < 30:
                    alerts.append(ExecutiveAlert(
                        alert_id=f"ALERT-DECAY-{ts}",
                        severity="CRITICAL",
                        layer="PTP",
                        title=f"Trust score critical: {ds['pillar']} at {ds['current_score']:.1f}",
                        detail=f"Score decaying — revocation risk imminent",
                        action_required="Record new validation evidence immediately",
                    ))
        except Exception:
            pass

        # Critical open risks
        try:
            from core.pcao.risk_office import risk_office as _ro
            for r in _ro.open_risks(severity="CRITICAL"):
                alerts.append(ExecutiveAlert(
                    alert_id=f"ALERT-RISK-{ts}",
                    severity="CRITICAL",
                    layer="PCAO",
                    title=f"Critical risk: {r['title']}",
                    detail=r["description"],
                    action_required=r["mitigation"],
                ))
        except Exception:
            pass

        # AEG rollbacks
        try:
            from core.nexus.aeg_pipeline.aeg_rollback_framework import aeg_rollback_framework as _arf
            for sus in _arf.suspended_rec_types():
                alerts.append(ExecutiveAlert(
                    alert_id=f"ALERT-ROLLBACK-{ts}",
                    severity="HIGH",
                    layer="AEG",
                    title=f"AEG rollback: {sus.get('rec_type')} suspended",
                    detail=f"{sus.get('remaining_days', 0):.0f} days remaining",
                    action_required="Review rollback cause; rebuild sandbox accuracy",
                ))
        except Exception:
            pass

        self._alerts.extend(alerts)
        return [self._ser_alert(a) for a in sorted(alerts, key=lambda x: ALERT_SEVERITY.get(x.severity, 0), reverse=True)]

    def acknowledge_alert(self, alert_id: str) -> dict:
        for a in self._alerts:
            if a.alert_id == alert_id:
                a.acknowledged = True
                return {"acknowledged": True, "alert_id": alert_id}
        return {"error": f"Alert '{alert_id}' not found"}

    def active_alerts(self) -> List[dict]:
        return [self._ser_alert(a) for a in self._alerts if not a.acknowledged]

    @staticmethod
    def _ser_alert(a: ExecutiveAlert) -> dict:
        return {
            "alert_id":       a.alert_id,
            "severity":       a.severity,
            "layer":          a.layer,
            "title":          a.title,
            "detail":         a.detail,
            "action_required": a.action_required,
            "created_at":     a.created_at,
            "acknowledged":   a.acknowledged,
        }


# Singleton
chairman_command_center = ChairmanCommandCenter()
