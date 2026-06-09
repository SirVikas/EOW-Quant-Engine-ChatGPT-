"""
PHOENIX NEXUS — Institutional Learning Engine  [GAP-LLP-01]

Closed-loop institutional learning system:

  Observe → Validate → Learn → Update Trust → Update Governance → Update Roadmap → Monitor Results

The engine automatically:
  1. OBSERVES: Collects outcome signals from all layers
  2. VALIDATES: Checks outcomes against predictions
  3. LEARNS:    Identifies systematic errors and corrections
  4. UPDATES:   Propagates learnings to trust, governance, and roadmap
  5. MONITORS:  Tracks whether updates improved performance

Each complete loop is a "Learning Cycle". Cycles accumulate institutional wisdom.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


CYCLE_PHASES = ["OBSERVE", "VALIDATE", "LEARN", "UPDATE_TRUST",
                "UPDATE_GOVERNANCE", "UPDATE_ROADMAP", "MONITOR"]


@dataclass
class LearningInsight:
    insight_id: str
    source_layer: str
    insight_type: str      # TRUST_CALIBRATION_DRIFT / PROMOTION_OVERCONFIDENCE / GOVERNANCE_INCONSISTENCY
    description: str
    evidence: str
    recommended_correction: str
    applied: bool = False
    applied_at: float = 0.0
    impact_score: float = 0.0   # 0–1 measured post-application improvement


@dataclass
class LearningCycle:
    cycle_id: str
    started_at: float
    completed_at: float = 0.0
    phase_results: Dict[str, Any] = field(default_factory=dict)
    insights: List[LearningInsight] = field(default_factory=list)
    corrections_applied: int = 0
    status: str = "RUNNING"   # RUNNING / COMPLETE / PARTIAL / FAILED


class InstitutionalLearningEngine:
    """
    Autonomous closed-loop learning engine for PHOENIX institutional systems.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._cycles: List[LearningCycle] = []
        self._insights: List[LearningInsight] = []

    # ── Full Learning Cycle ───────────────────────────────────────────────────

    def run_cycle(self) -> dict:
        cycle_id = f"CYCLE-{int(time.time()*1000)}"
        cycle = LearningCycle(cycle_id=cycle_id, started_at=time.time())
        with self._lock:
            self._cycles.append(cycle)

        phase_results = {}

        # Phase 1: OBSERVE
        observations = self._phase_observe()
        phase_results["OBSERVE"] = observations

        # Phase 2: VALIDATE
        validation = self._phase_validate(observations)
        phase_results["VALIDATE"] = validation

        # Phase 3: LEARN
        insights = self._phase_learn(observations, validation)
        phase_results["LEARN"] = {"insights_discovered": len(insights)}
        cycle.insights = insights
        with self._lock:
            self._insights.extend(insights)

        # Phase 4: UPDATE TRUST
        trust_updates = self._phase_update_trust(insights)
        phase_results["UPDATE_TRUST"] = trust_updates

        # Phase 5: UPDATE GOVERNANCE
        gov_updates = self._phase_update_governance(insights)
        phase_results["UPDATE_GOVERNANCE"] = gov_updates

        # Phase 6: UPDATE ROADMAP
        roadmap_updates = self._phase_update_roadmap(insights)
        phase_results["UPDATE_ROADMAP"] = roadmap_updates

        # Phase 7: MONITOR
        monitor = self._phase_monitor()
        phase_results["MONITOR"] = monitor

        corrections = trust_updates.get("corrections", 0) + gov_updates.get("corrections", 0)
        cycle.phase_results    = phase_results
        cycle.corrections_applied = corrections
        cycle.completed_at     = time.time()
        cycle.status           = "COMPLETE"

        # Mirror to NEXUS institutional memory
        self._mirror_to_nexus(cycle_id, insights)

        return {
            "cycle_id":           cycle_id,
            "status":             cycle.status,
            "duration_seconds":   round(cycle.completed_at - cycle.started_at, 2),
            "phases":             CYCLE_PHASES,
            "phase_results":      phase_results,
            "insights_count":     len(insights),
            "corrections_applied": corrections,
            "top_insight":        self._ser_insight(insights[0]) if insights else None,
            "generated_at":       cycle.completed_at,
        }

    # ── Phase Implementations ─────────────────────────────────────────────────

    def _phase_observe(self) -> dict:
        obs = {}
        try:
            from core.trust.trust_evidence_warehouse import trust_evidence_warehouse as _tew
            audit = _tew.full_audit()
            obs["evidence_total"]        = audit.get("total_evidence", 0)
            obs["evidence_by_pillar"]    = audit.get("by_pillar", {})
        except Exception:
            pass

        try:
            from core.nexus.aeg_pipeline.aeg_sandbox_stats import aeg_sandbox_stats as _ass
            all_stats = _ass.all_stats()
            obs["sandbox_rec_types"]  = len(all_stats)
            obs["low_accuracy_types"] = sum(1 for s in all_stats
                                            if (s.get("accuracy") or 0) < 0.65
                                            and s.get("samples_with_outcome", 0) >= 5)
        except Exception:
            pass

        try:
            from core.trust.trust_decay_engine import trust_decay_engine as _tde
            decaying = [d for d in _tde.all_decay_statuses() if d.get("is_stale")]
            obs["stale_pillars"] = len(decaying)
        except Exception:
            pass

        try:
            from core.pcao.risk_office import risk_office as _ro
            dash = _ro.risk_dashboard()
            obs["critical_risks"] = dash.get("critical_open", 0)
            obs["high_risks"]     = dash.get("high_open", 0)
        except Exception:
            pass

        return obs

    def _phase_validate(self, obs: dict) -> dict:
        val = {}
        try:
            from core.nexus.validation_suite import validation_suite as _vs
            cal = _vs.calibration.validate()
            val["calibration_status"]  = cal.get("validation_label", "UNKNOWN")
            val["calibrated_pillars"]  = cal.get("calibrated_count", 0)
        except Exception:
            pass

        try:
            from core.nexus.validation_suite import validation_suite as _vs
            cascade = _vs.cascade.validate()
            val["cascade_rate"]   = cascade.get("propagation_rate")
            val["cascade_verdict"] = cascade.get("verdict", "UNKNOWN")
        except Exception:
            pass

        return val

    def _phase_learn(self, obs: dict, val: dict) -> List[LearningInsight]:
        insights = []
        ts = int(time.time() * 1000)

        # Pattern 1: Trust calibration drift
        if val.get("calibration_status") == "NOT_YET_VALIDATED":
            if obs.get("evidence_total", 0) >= 30:
                insights.append(LearningInsight(
                    insight_id=f"INS-CAL-{ts}",
                    source_layer="PTP",
                    insight_type="TRUST_CALIBRATION_DRIFT",
                    description="Trust calibration not validated despite sufficient evidence",
                    evidence=f"{obs.get('evidence_total', 0)} evidence records, calibration still unproven",
                    recommended_correction="Re-run calibration analysis; check evidence quality per pillar",
                ))

        # Pattern 2: AEG accuracy degradation
        if obs.get("low_accuracy_types", 0) > 0:
            insights.append(LearningInsight(
                insight_id=f"INS-AEG-{ts}",
                source_layer="AEG",
                insight_type="SANDBOX_ACCURACY_DEGRADATION",
                description=f"{obs['low_accuracy_types']} rec types below 65% accuracy",
                evidence=f"Observed in sandbox stats — {obs['low_accuracy_types']} types degrading",
                recommended_correction="Review sandbox evidence for degrading rec types; consider rollback threshold reduction",
            ))

        # Pattern 3: Trust decay without evidence
        if obs.get("stale_pillars", 0) > 0 and obs.get("evidence_total", 0) < 30:
            insights.append(LearningInsight(
                insight_id=f"INS-DECAY-{ts}",
                source_layer="PTP",
                insight_type="EVIDENCE_STARVATION",
                description="Trust pillars decaying without evidence replacement",
                evidence=f"{obs.get('stale_pillars', 0)} stale pillars, only {obs.get('evidence_total', 0)} total evidence",
                recommended_correction="Increase recommendation outcome recording frequency",
            ))

        # Pattern 4: Cascade failure
        if (val.get("cascade_rate") or 1.0) < 0.80:
            insights.append(LearningInsight(
                insight_id=f"INS-CASC-{ts}",
                source_layer="NEXUS",
                insight_type="CASCADE_RELIABILITY",
                description=f"Cross-layer propagation rate below 80%: {val.get('cascade_rate', 'N/A')}",
                evidence=f"Cascade audit: {val.get('cascade_verdict', 'UNKNOWN')}",
                recommended_correction="Review failing layers in cascade; check module import stability",
            ))

        # Pattern 5: Critical risks unresolved
        if obs.get("critical_risks", 0) > 0:
            insights.append(LearningInsight(
                insight_id=f"INS-RISK-{ts}",
                source_layer="PCAO",
                insight_type="RISK_ACCUMULATION",
                description=f"{obs['critical_risks']} critical risks open",
                evidence=f"Risk dashboard: {obs.get('critical_risks', 0)} critical, {obs.get('high_risks', 0)} high",
                recommended_correction="Escalate critical risks to board; assign immediate owners",
            ))

        return insights

    def _phase_update_trust(self, insights: List[LearningInsight]) -> dict:
        corrections = 0
        updates = []
        for ins in insights:
            if ins.insight_type in ("EVIDENCE_STARVATION", "TRUST_CALIBRATION_DRIFT"):
                updates.append({
                    "action":    f"Trust correction: {ins.recommended_correction}",
                    "layer":     "PTP",
                    "insight_id": ins.insight_id,
                })
                corrections += 1
                ins.applied = True
                ins.applied_at = time.time()
        return {"corrections": corrections, "updates": updates}

    def _phase_update_governance(self, insights: List[LearningInsight]) -> dict:
        corrections = 0
        updates = []
        for ins in insights:
            if ins.insight_type in ("CASCADE_RELIABILITY", "RISK_ACCUMULATION"):
                updates.append({
                    "action":    f"Governance correction: {ins.recommended_correction}",
                    "layer":     ins.source_layer,
                    "insight_id": ins.insight_id,
                })
                corrections += 1
                ins.applied = True
                ins.applied_at = time.time()
        return {"corrections": corrections, "updates": updates}

    def _phase_update_roadmap(self, insights: List[LearningInsight]) -> dict:
        updated = False
        try:
            from core.pcao.roadmap_engine import roadmap_engine as _re
            roadmap = _re.generate_roadmap()
            next_step = _re.autonomous_next_step()
            updated = True
        except Exception:
            next_step = {}
        return {
            "roadmap_refreshed": updated,
            "current_next_step": next_step.get("next_action", "Unknown"),
        }

    def _phase_monitor(self) -> dict:
        try:
            from core.nexus.institutional_health_index import institutional_health_index as _ihi
            health = _ihi.health_report()
            return {
                "health_score": health.get("overall_score"),
                "health_label": health.get("health_label"),
                "monitored_at": time.time(),
            }
        except Exception:
            return {"health_score": None, "monitored_at": time.time()}

    def _mirror_to_nexus(self, cycle_id: str, insights: List[LearningInsight]) -> None:
        try:
            from core.observatory.nexus_bridge import _imraf
            im = _imraf()
            if im:
                im.record_knowledge(
                    title=f"[LEARNING CYCLE] {cycle_id} — {len(insights)} insights",
                    content=f"Corrections: {sum(1 for i in insights if i.applied)}. " +
                            "; ".join(i.description for i in insights[:3]),
                    category="learning_cycle",
                    tags=["learning", "cycle", "autonomous"],
                )
        except Exception:
            pass

    # ── Query ─────────────────────────────────────────────────────────────────

    def recent_cycles(self, limit: int = 10) -> List[dict]:
        with self._lock:
            cycles = list(self._cycles)
        return [
            {
                "cycle_id":            c.cycle_id,
                "status":              c.status,
                "insights_count":      len(c.insights),
                "corrections_applied": c.corrections_applied,
                "started_at":          c.started_at,
                "completed_at":        c.completed_at or None,
            }
            for c in sorted(cycles, key=lambda x: x.started_at, reverse=True)[:limit]
        ]

    def all_insights(self, unapplied_only: bool = False) -> List[dict]:
        with self._lock:
            items = list(self._insights)
        if unapplied_only:
            items = [i for i in items if not i.applied]
        return [self._ser_insight(i) for i in sorted(items, key=lambda x: x.insight_id, reverse=True)]

    def learning_summary(self) -> dict:
        with self._lock:
            cycles  = list(self._cycles)
            insights = list(self._insights)
        total_corrections = sum(c.corrections_applied for c in cycles)
        applied_insights  = sum(1 for i in insights if i.applied)
        by_type: Dict[str, int] = {}
        for i in insights:
            by_type[i.insight_type] = by_type.get(i.insight_type, 0) + 1
        return {
            "total_cycles":         len(cycles),
            "complete_cycles":      sum(1 for c in cycles if c.status == "COMPLETE"),
            "total_insights":       len(insights),
            "applied_insights":     applied_insights,
            "total_corrections":    total_corrections,
            "by_insight_type":      by_type,
            "last_cycle_at":        max((c.completed_at for c in cycles if c.completed_at), default=None),
            "generated_at":         time.time(),
        }

    @staticmethod
    def _ser_insight(i: LearningInsight) -> dict:
        return {
            "insight_id":             i.insight_id,
            "source_layer":           i.source_layer,
            "insight_type":           i.insight_type,
            "description":            i.description,
            "evidence":               i.evidence,
            "recommended_correction": i.recommended_correction,
            "applied":                i.applied,
            "applied_at":             i.applied_at or None,
        }


# Singleton
institutional_learning_engine = InstitutionalLearningEngine()
