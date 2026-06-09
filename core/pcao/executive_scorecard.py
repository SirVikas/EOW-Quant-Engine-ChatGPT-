"""
PHOENIX PCAO — Executive Scorecard  [GAP-EIP-01, GAP-EIP-02, GAP-EIP-03]

Tracks the accuracy and effectiveness of executive-level intelligence:

EIP-01: Executive Recommendation Accuracy
  — Did the decision support recommendations lead to improvement?

EIP-02: Resource Optimizer Validation
  — Did applied optimizations measurably improve throughput/utilization?

EIP-03: Roadmap Engine Validation
  — Did completed roadmap milestones lead to the predicted outcomes?
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RecommendationRecord:
    rec_id: str
    recommendation: str
    layer: str
    urgency_score: float
    issued_at: float
    applied_at: Optional[float] = None
    outcome_measured_at: Optional[float] = None
    outcome: Optional[str] = None   # IMPROVED / NO_CHANGE / DEGRADED
    evidence: str = ""


@dataclass
class OptimizationRecord:
    opt_id: str
    subsystem: str
    recommended_delta: float
    applied: bool
    applied_at: Optional[float]
    baseline_metric: Optional[float]
    post_metric: Optional[float]
    improvement: Optional[float]
    verdict: str = "PENDING"   # EFFECTIVE / INEFFECTIVE / NO_CHANGE / PENDING


@dataclass
class MilestoneRecord:
    milestone_id: str
    title: str
    subsystem: str
    recommended_at: float
    completed_at: Optional[float]
    gate_conditions_met: bool
    outcome_notes: str
    verdict: str = "PENDING"   # ON_TRACK / COMPLETED / MISSED / BLOCKED


class ExecutiveScorecard:
    """
    Measures the accuracy of PCAO executive intelligence outputs.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._recs:   List[RecommendationRecord] = []
        self._opts:   List[OptimizationRecord]   = []
        self._milestones: List[MilestoneRecord]  = []

    # ── EIP-01: Decision Support Recommendation Tracking ─────────────────────

    def record_recommendation(self, recommendation: str, layer: str,
                               urgency_score: float) -> str:
        rec_id = f"DREC-{layer[:4]}-{int(time.time()*1000)}"
        with self._lock:
            self._recs.append(RecommendationRecord(
                rec_id=rec_id, recommendation=recommendation,
                layer=layer, urgency_score=urgency_score,
                issued_at=time.time(),
            ))
        return rec_id

    def record_recommendation_outcome(self, rec_id: str, outcome: str,
                                      evidence: str = "") -> dict:
        with self._lock:
            for r in self._recs:
                if r.rec_id == rec_id:
                    r.applied_at = r.applied_at or time.time()
                    r.outcome_measured_at = time.time()
                    r.outcome = outcome
                    r.evidence = evidence
                    return {"updated": True, "rec_id": rec_id}
        return {"error": f"Record '{rec_id}' not found"}

    def recommendation_scorecard(self) -> dict:
        with self._lock:
            recs = list(self._recs)
        evaluated = [r for r in recs if r.outcome is not None]
        improved  = sum(1 for r in evaluated if r.outcome == "IMPROVED")
        no_change = sum(1 for r in evaluated if r.outcome == "NO_CHANGE")
        degraded  = sum(1 for r in evaluated if r.outcome == "DEGRADED")
        accuracy  = improved / max(1, len(evaluated)) if evaluated else None

        return {
            "total_recommendations": len(recs),
            "evaluated":             len(evaluated),
            "improved":              improved,
            "no_change":             no_change,
            "degraded":              degraded,
            "recommendation_accuracy": round(accuracy, 3) if accuracy is not None else None,
            "verdict":               ("EFFECTIVE" if (accuracy or 0) >= 0.60 else
                                      "DEVELOPING" if len(evaluated) > 0 else "NO_DATA"),
            "generated_at":          time.time(),
        }

    def auto_capture_recommendations(self) -> int:
        """Snapshot current decision support recommendations into the ledger."""
        captured = 0
        try:
            from core.pcao.decision_support import decision_support as _ds
            result = _ds.generate_recommendations()
            for rec in result.get("recommendations", []):
                self.record_recommendation(
                    recommendation=rec.get("action", ""),
                    layer=rec.get("layer", "PCAO"),
                    urgency_score=rec.get("urgency_score", 0),
                )
                captured += 1
        except Exception:
            pass
        return captured

    # ── EIP-02: Resource Optimizer Validation ────────────────────────────────

    def record_optimization(self, subsystem: str, recommended_delta: float,
                             applied: bool, baseline_metric: Optional[float] = None) -> str:
        opt_id = f"OPT-{subsystem[:6]}-{int(time.time()*1000)}"
        with self._lock:
            self._opts.append(OptimizationRecord(
                opt_id=opt_id, subsystem=subsystem,
                recommended_delta=recommended_delta, applied=applied,
                applied_at=time.time() if applied else None,
                baseline_metric=baseline_metric,
                post_metric=None, improvement=None,
            ))
        return opt_id

    def record_optimization_result(self, opt_id: str, post_metric: float) -> dict:
        with self._lock:
            for o in self._opts:
                if o.opt_id == opt_id and o.baseline_metric is not None:
                    o.post_metric = post_metric
                    o.improvement = post_metric - o.baseline_metric
                    o.verdict = ("EFFECTIVE" if o.improvement > 0 else
                                 "NO_CHANGE" if abs(o.improvement) < 0.01 else "INEFFECTIVE")
                    return {"updated": True, "opt_id": opt_id, "improvement": o.improvement}
        return {"error": f"Optimization '{opt_id}' not found or missing baseline"}

    def optimizer_validation_report(self) -> dict:
        with self._lock:
            opts = list(self._opts)
        evaluated = [o for o in opts if o.verdict != "PENDING"]
        effective  = sum(1 for o in evaluated if o.verdict == "EFFECTIVE")
        applied    = sum(1 for o in opts if o.applied)
        avg_improvement = (
            sum(o.improvement for o in evaluated if o.improvement is not None) / max(1, len(evaluated))
            if evaluated else None
        )
        return {
            "total_optimizations": len(opts),
            "applied":             applied,
            "evaluated":           len(evaluated),
            "effective":           effective,
            "effectiveness_rate":  round(effective / max(1, len(evaluated)), 3) if evaluated else None,
            "avg_improvement":     round(avg_improvement, 4) if avg_improvement is not None else None,
            "verdict":             ("VALIDATED" if (effective / max(1, len(evaluated))) >= 0.60
                                    else "DEVELOPING" if evaluated else "NO_DATA"),
            "generated_at":        time.time(),
        }

    # ── EIP-03: Roadmap Engine Validation ────────────────────────────────────

    def record_milestone_completion(self, milestone_id: str, title: str,
                                    subsystem: str, gate_conditions_met: bool,
                                    outcome_notes: str = "") -> MilestoneRecord:
        m = MilestoneRecord(
            milestone_id=milestone_id, title=title, subsystem=subsystem,
            recommended_at=time.time(), completed_at=time.time(),
            gate_conditions_met=gate_conditions_met,
            outcome_notes=outcome_notes,
            verdict="COMPLETED" if gate_conditions_met else "MISSED",
        )
        with self._lock:
            self._milestones.append(m)
        return m

    def roadmap_performance_report(self) -> dict:
        with self._lock:
            milestones = list(self._milestones)

        # Also check live milestone state from roadmap engine
        live_milestones = []
        try:
            from core.pcao.roadmap_engine import roadmap_engine as _re
            roadmap = _re.generate_roadmap()
            for m in roadmap.get("milestones", []):
                live_milestones.append({
                    "milestone_id": m["milestone_id"],
                    "title":        m["title"],
                    "current_state": m["current_state"],
                    "blocking":     m["blocking"],
                })
        except Exception:
            pass

        completed = sum(1 for m in milestones if m.verdict == "COMPLETED")
        missed    = sum(1 for m in milestones if m.verdict == "MISSED")
        met_live  = sum(1 for m in live_milestones if m["current_state"] == "MET")

        return {
            "tracked_milestones":  len(milestones),
            "completed":           completed,
            "missed":              missed,
            "live_milestones":     live_milestones,
            "live_milestones_met": met_live,
            "completion_rate":     round(completed / max(1, len(milestones)), 3) if milestones else None,
            "verdict":             ("EFFECTIVE" if (completed / max(1, len(milestones))) >= 0.70
                                    else "DEVELOPING" if milestones else "NO_DATA"),
            "generated_at":        time.time(),
        }

    def full_scorecard(self) -> dict:
        return {
            "recommendation_scorecard":   self.recommendation_scorecard(),
            "optimizer_validation":       self.optimizer_validation_report(),
            "roadmap_performance":        self.roadmap_performance_report(),
            "generated_at":               time.time(),
        }


# Singleton
executive_scorecard = ExecutiveScorecard()
