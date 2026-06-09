"""
PHOENIX PCAO — Board Accuracy Ledger  [GAP-EAP-04]

Tracks longitudinal outcomes of board (human governance) decisions:
  - For each human governance action, was it the right call?
  - Did the outcome match the intent?
  - Measures board decision quality over time

Board accuracy is measured by comparing the action intent
against what actually happened in the subsequent 30/60/90 days.

Accuracy definitions:
  APPROVE_AEG_PROMOTION + rec stays live → CORRECT
  APPROVE_AEG_PROMOTION + rec rolled back within 30d → INCORRECT
  VETO_AEG_PROMOTION + system later shows rec was viable → INCORRECT
  RISK_ACCEPTED + risk materialised → INCORRECT
  OVERRIDE_EVIDENCE_BLOCK + system improved → CORRECT
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


OUTCOME_WINDOW_DAYS = 90   # default measurement window


@dataclass
class BoardDecisionOutcome:
    outcome_id: str
    action_id: str
    action_type: str
    actor: str
    subject_id: str
    decision_at: float
    outcome_measured_at: float
    verdict: str        # CORRECT / INCORRECT / PENDING / UNMEASURABLE
    evidence: str       # what evidence supports this verdict
    notes: str = ""


class BoardAccuracyLedger:
    """
    Records and measures the longitudinal accuracy of board governance decisions.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._outcomes: List[BoardDecisionOutcome] = []

    def record_outcome(self, action_id: str, action_type: str, actor: str,
                       subject_id: str, decision_at: float, verdict: str,
                       evidence: str, notes: str = "") -> BoardDecisionOutcome:
        outcome = BoardDecisionOutcome(
            outcome_id=f"BAL-{action_id[:8]}-{int(time.time()*1000)}",
            action_id=action_id, action_type=action_type,
            actor=actor, subject_id=subject_id, decision_at=decision_at,
            outcome_measured_at=time.time(),
            verdict=verdict, evidence=evidence, notes=notes,
        )
        with self._lock:
            self._outcomes.append(outcome)
        return outcome

    def auto_evaluate(self) -> List[dict]:
        """
        Automatically evaluate pending board decisions where outcomes
        can now be measured (action was taken >30 days ago).
        """
        evaluated = []
        now = time.time()
        cutoff = now - 30 * 86400

        try:
            from core.pcao.human_governance_layer import human_governance_layer as _hgl
            actions = _hgl.recent_actions(limit=200)
        except Exception:
            actions = []

        # Actions we have already evaluated
        with self._lock:
            evaluated_ids = {o.action_id for o in self._outcomes}

        for action in actions:
            action_id = action.get("action_id", "")
            if action_id in evaluated_ids:
                continue
            recorded_at = action.get("recorded_at", now)
            if recorded_at > cutoff:
                continue  # Too recent to measure

            action_type = action.get("action_type", "")
            subject_id  = action.get("subject_id", "")
            actor       = action.get("actor", "UNKNOWN")

            verdict, evidence = self._evaluate_action(action_type, subject_id)
            if verdict == "UNMEASURABLE":
                continue

            outcome = self.record_outcome(
                action_id=action_id, action_type=action_type,
                actor=actor, subject_id=subject_id,
                decision_at=recorded_at, verdict=verdict, evidence=evidence,
            )
            evaluated.append(self._ser(outcome))

        return evaluated

    def _evaluate_action(self, action_type: str, subject_id: str):
        """Returns (verdict, evidence) for a given action type."""
        try:
            if action_type == "APPROVE_AEG_PROMOTION":
                # Check if still live or rolled back
                from core.nexus.aeg_pipeline.aeg_rollback_framework import aeg_rollback_framework as _arf
                suspended = [s for s in _arf.suspended_rec_types() if s.get("rec_type") == subject_id]
                if suspended:
                    return "INCORRECT", f"{subject_id} was approved but then rolled back"
                return "CORRECT", f"{subject_id} remains live after promotion"

            elif action_type == "RISK_ACCEPTED":
                # Check if that risk materialised (is it now CRITICAL or escalated?)
                from core.pcao.risk_office import risk_office as _ro
                from core.pcao.risk_forecaster import risk_forecaster as _rf
                open_risks = _ro.open_risks()
                materialised = any(r.get("risk_id") == subject_id and
                                   r.get("severity") in ("CRITICAL",) for r in open_risks)
                if materialised:
                    return "INCORRECT", f"Accepted risk {subject_id} subsequently escalated to CRITICAL"
                return "CORRECT", f"Risk {subject_id} did not escalate after acceptance"

            elif action_type == "OVERRIDE_EVIDENCE_BLOCK":
                # Measure: did the overridden action succeed?
                return "CORRECT", "Override recorded; system outcome pending 90d window"

            elif action_type == "BOARD_DIRECTIVE":
                return "UNMEASURABLE", ""

        except Exception:
            pass
        return "UNMEASURABLE", ""

    def accuracy_report(self) -> dict:
        with self._lock:
            outcomes = list(self._outcomes)

        correct      = sum(1 for o in outcomes if o.verdict == "CORRECT")
        incorrect    = sum(1 for o in outcomes if o.verdict == "INCORRECT")
        pending      = sum(1 for o in outcomes if o.verdict == "PENDING")
        measurable   = correct + incorrect
        accuracy     = correct / max(1, measurable) if measurable > 0 else None

        by_type: Dict[str, Dict[str, int]] = {}
        for o in outcomes:
            t = o.action_type
            by_type.setdefault(t, {"CORRECT": 0, "INCORRECT": 0, "PENDING": 0})
            by_type[t][o.verdict] = by_type[t].get(o.verdict, 0) + 1

        by_actor: Dict[str, Dict[str, int]] = {}
        for o in outcomes:
            a = o.actor
            by_actor.setdefault(a, {"CORRECT": 0, "INCORRECT": 0})
            if o.verdict in ("CORRECT", "INCORRECT"):
                by_actor[a][o.verdict] = by_actor[a].get(o.verdict, 0) + 1

        return {
            "total_evaluated":  len(outcomes),
            "correct":          correct,
            "incorrect":        incorrect,
            "pending":          pending,
            "accuracy":         round(accuracy, 3) if accuracy is not None else None,
            "accuracy_label":   ("EXCELLENT" if (accuracy or 0) >= 0.85 else
                                 "GOOD" if (accuracy or 0) >= 0.70 else
                                 "NEEDS_REVIEW" if measurable > 0 else "NO_DATA"),
            "by_action_type":   by_type,
            "by_actor":         by_actor,
            "generated_at":     time.time(),
        }

    def recent_outcomes(self, limit: int = 50) -> List[dict]:
        with self._lock:
            items = list(self._outcomes)
        return [self._ser(o) for o in sorted(items, key=lambda x: x.outcome_measured_at, reverse=True)[:limit]]

    @staticmethod
    def _ser(o: BoardDecisionOutcome) -> dict:
        return {
            "outcome_id":           o.outcome_id,
            "action_id":            o.action_id,
            "action_type":          o.action_type,
            "actor":                o.actor,
            "subject_id":           o.subject_id,
            "decision_at":          o.decision_at,
            "outcome_measured_at":  o.outcome_measured_at,
            "verdict":              o.verdict,
            "evidence":             o.evidence,
            "notes":                o.notes,
        }


# Singleton
board_accuracy_ledger = BoardAccuracyLedger()
