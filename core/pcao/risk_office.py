"""
PHOENIX PCAO — Risk Office  [GAP-R9]

Executive-level risk registry:
  - Open risks with severity, mitigation, owner
  - Risk escalation when severity increases
  - Risk closure when mitigated
  - Cross-layer risk aggregation

Risk severity tiers:
  CRITICAL  — system stability at risk (immediate action)
  HIGH      — institutional integrity at risk (action this sprint)
  MEDIUM    — process risk (action this quarter)
  LOW       — informational (monitor)

Sources:
  - Observatory disease detections
  - PTP trust revocations
  - AEG rollbacks
  - Evidence supremacy blocks
  - CORTEX governance violations
  - Manual registration
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


SEVERITY_RANK = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}


@dataclass
class RiskItem:
    risk_id: str
    title: str
    description: str
    severity: str           # CRITICAL / HIGH / MEDIUM / LOW
    source_layer: str       # OBSERVATORY / PTP / AEG / CORTEX / NEXUS / PCAO / MANUAL
    owner: str
    mitigation: str
    status: str = "OPEN"   # OPEN / IN_PROGRESS / MITIGATED / CLOSED / ACCEPTED
    opened_at: float = field(default_factory=time.time)
    closed_at: float = 0.0
    last_updated: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)


class RiskOffice:
    """
    PCAO executive risk registry with cross-layer risk aggregation.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._risks: Dict[str, RiskItem] = {}
        self._seed_known_risks()

    def _seed_known_risks(self) -> None:
        seed = [
            ("RISK-ETE-001", "ETE Phase-2 not yet calibrated", "ETE gate cannot activate without 500+ trades", "HIGH", "TRUTH_ENGINE", "SYSTEM", "Accumulate 500 trades, then run Phase-2 calibration"),
            ("RISK-KGE-001", "KGE not yet implemented", "Knowledge graph limited to founding nodes only", "MEDIUM", "NEXUS", "SYSTEM", "Implement FTD-KGE-001"),
            ("RISK-AEG-001", "AEG shadow validation not completed", "AEG cannot graduate to full autonomy without shadow track record", "HIGH", "AEG", "SYSTEM", "Complete AEG shadow validation program"),
            ("RISK-PTP-001", "Trust evidence sparse", "Accuracy windows lack sufficient evidence for PROVEN status", "MEDIUM", "PTP", "SYSTEM", "Continue accumulating validation evidence across all pillars"),
        ]
        for risk_id, title, desc, severity, source, owner, mitigation in seed:
            r = RiskItem(risk_id=risk_id, title=title, description=desc, severity=severity,
                         source_layer=source, owner=owner, mitigation=mitigation)
            self._risks[risk_id] = r

    # ── Risk Management ───────────────────────────────────────────────────────

    def register_risk(
        self,
        title: str,
        description: str,
        severity: str,
        source_layer: str,
        owner: str = "UNASSIGNED",
        mitigation: str = "",
        tags: Optional[List[str]] = None,
    ) -> RiskItem:
        risk_id = f"RISK-{source_layer[:4]}-{int(time.time()*1000)}"
        r = RiskItem(
            risk_id=risk_id,
            title=title,
            description=description,
            severity=severity,
            source_layer=source_layer,
            owner=owner,
            mitigation=mitigation,
            tags=tags or [],
        )
        with self._lock:
            self._risks[risk_id] = r
        return r

    def update_risk(self, risk_id: str, **kwargs) -> dict:
        with self._lock:
            r = self._risks.get(risk_id)
        if not r:
            return {"error": f"Risk '{risk_id}' not found"}
        for k, v in kwargs.items():
            if hasattr(r, k):
                setattr(r, k, v)
        r.last_updated = time.time()
        if r.status in ("MITIGATED", "CLOSED"):
            r.closed_at = time.time()
        return {"updated": True, "risk_id": risk_id, "status": r.status}

    def close_risk(self, risk_id: str, reason: str = "") -> dict:
        return self.update_risk(risk_id, status="CLOSED", mitigation=reason or "Resolved")

    # ── Cross-Layer Risk Scan ─────────────────────────────────────────────────

    def scan_and_auto_register(self) -> List[str]:
        new_ids = []
        try:
            from core.trust.trust_decay_engine import trust_decay_engine
            for ds in trust_decay_engine.all_decay_statuses():
                if ds.get("is_stale") and ds.get("decay_applied", 0) > 10:
                    existing = [r for r in self._risks.values() if "decay" in r.title.lower() and ds["pillar"] in r.title and r.status == "OPEN"]
                    if not existing:
                        r = self.register_risk(
                            title=f"Trust decay critical: {ds['pillar']}",
                            description=f"Score degraded by {ds.get('decay_applied', 0):.1f} pts — {ds.get('decay_note', '')}",
                            severity="HIGH",
                            source_layer="PTP",
                            mitigation="Record new validation evidence for this pillar",
                        )
                        new_ids.append(r.risk_id)
        except Exception:
            pass

        try:
            from core.nexus.aeg_pipeline.aeg_rollback_framework import aeg_rollback_framework
            for sus in aeg_rollback_framework.suspended_rec_types():
                rt = sus["rec_type"]
                existing = [r for r in self._risks.values() if rt in r.title and "rollback" in r.title.lower() and r.status == "OPEN"]
                if not existing:
                    r = self.register_risk(
                        title=f"AEG rollback suspension: {rt}",
                        description=f"rec_type suspended for {sus.get('remaining_days', 0):.1f} more days",
                        severity="MEDIUM",
                        source_layer="AEG",
                        mitigation="Wait for suspension to lift, then rebuild sandbox accuracy",
                    )
                    new_ids.append(r.risk_id)
        except Exception:
            pass

        return new_ids

    # ── Query ─────────────────────────────────────────────────────────────────

    def open_risks(self, severity: Optional[str] = None) -> List[dict]:
        with self._lock:
            items = [r for r in self._risks.values() if r.status == "OPEN"]
        if severity:
            items = [r for r in items if r.severity == severity]
        return [self._ser(r) for r in sorted(items, key=lambda x: SEVERITY_RANK.get(x.severity, 0), reverse=True)]

    def risk_dashboard(self) -> dict:
        with self._lock:
            all_risks = list(self._risks.values())
        open_risks = [r for r in all_risks if r.status == "OPEN"]
        by_severity: Dict[str, int] = {}
        for r in open_risks:
            by_severity[r.severity] = by_severity.get(r.severity, 0) + 1
        return {
            "total_risks":       len(all_risks),
            "open_risks":        len(open_risks),
            "by_severity":       by_severity,
            "critical_open":     by_severity.get("CRITICAL", 0),
            "high_open":         by_severity.get("HIGH", 0),
            "top_risks":         [self._ser(r) for r in sorted(open_risks, key=lambda x: SEVERITY_RANK.get(x.severity, 0), reverse=True)[:5]],
        }

    @staticmethod
    def _ser(r: RiskItem) -> dict:
        return {
            "risk_id":     r.risk_id,
            "title":       r.title,
            "description": r.description,
            "severity":    r.severity,
            "source_layer": r.source_layer,
            "owner":       r.owner,
            "mitigation":  r.mitigation,
            "status":      r.status,
            "opened_at":   r.opened_at,
            "closed_at":   r.closed_at or None,
            "tags":        r.tags,
        }


# Singleton
risk_office = RiskOffice()
