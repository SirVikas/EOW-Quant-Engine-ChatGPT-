"""
FTD-029 — Correction Orchestrator (Main Entry Point)

Full correction loop (Q1–Q15):
  1. IssueExtractor  → extract issues from FTD-028 validators
  2. ConfidenceEngine → compute composite confidence (locked formula)
  3. PolicyGuard      → enforce all gates (Q4, Q7, Q8, Q14, Q15)
  4. CooldownManager  → session/frequency limit with critical bypass (Q6)
  5. PriorityResolver → sort by risk-safety first (Part 4)
  6. ChangePlanner    → generate bounded change plans (Part 5)
  7. CollisionHandler → resolve parameter conflicts (Part 4b)
  8. ChangeApplier    → apply via session overlay, delegate to owners (Part 6)
  9. RollbackManager  → re-validate and rollback if needed (Part 8)
  10. AuditLogger     → immutable append-only log (Q11)
"""
from __future__ import annotations
import time
import uuid
from typing import Any, Dict, List, Optional

from loguru import logger

from core.self_correction.issue_extractor     import IssueExtractor
from core.self_correction.confidence_engine   import ConfidenceEngine
from core.self_correction.policy_guard        import PolicyGuard
from core.self_correction.cooldown_manager    import CooldownManager
from core.self_correction.priority_resolver   import PriorityResolver
from core.self_correction.change_planner      import ChangePlanner
from core.self_correction.collision_handler   import CollisionHandler
from core.self_correction.change_applier      import ChangeApplier
from core.self_correction.rollback_manager    import RollbackManager
from core.self_correction.audit_logger        import AuditLogger, FinalState


class CorrectionOrchestrator:
    """
    Main FTD-029 entry point. Wires all 11 sub-modules.
    Stateful singleton — one instance per session.
    """

    MODULE = "CORRECTION_ORCHESTRATOR"
    PHASE  = "029"

    def __init__(self):
        self._enabled:       bool = True
        self._human_stopped: bool = False

        self._issue_extractor   = IssueExtractor()
        self._confidence_engine = ConfidenceEngine()
        self._policy_guard      = PolicyGuard()
        self._cooldown          = CooldownManager()
        self._priority_resolver = PriorityResolver()
        self._change_planner    = ChangePlanner()
        self._collision_handler = CollisionHandler()
        self._change_applier    = ChangeApplier()
        self._rollback_manager  = RollbackManager()
        self._audit_logger      = AuditLogger()

        self._last_cycle_id: Optional[str] = None

    # ── Main correction cycle ─────────────────────────────────────────────────

    def run_cycle(
        self,
        ftd028_validators:    Dict[str, Dict[str, Any]],
        ftd028_meta:          Dict[str, Any],
        current_params:       Dict[str, float],
        system_state:         Dict[str, Any],
        ftd027_result:        Optional[Dict[str, Any]] = None,
        ai_brain_score:       float = 0.0,
        risk_halted:          bool  = False,
        risk_violated:        bool  = False,
        contradiction_critical: bool = False,
    ) -> Dict[str, Any]:
        cycle_id = str(uuid.uuid4())[:8]
        self._last_cycle_id = cycle_id
        now = int(time.time() * 1000)

        n_trades     = system_state.get("total_trades", 0) or 0
        pnl_before   = float(system_state.get("total_pnl", 0.0) or 0.0)
        meta_score   = float(ftd028_meta.get("system_score", 0.0) or 0.0)
        stability    = float(ftd028_meta.get("stability_score", 0.0) or 0.0)
        consistency  = float(ftd028_meta.get("confidence_score", 0.0) or 0.0)

        # ── Step 1: Extract issues ────────────────────────────────────────────
        issues = self._issue_extractor.extract(ftd028_validators, ftd027_result)

        # ── Step 2: Compute confidence ────────────────────────────────────────
        decision_result = ftd028_validators.get("decision_quality", {})
        decision_raw    = float(decision_result.get("score", 0.0) or 0.0)
        conf_result     = self._confidence_engine.compute(
            meta_score=meta_score,
            decision_score=decision_raw,
            stability_score=stability,
            consistency_score=consistency,
        )
        confidence       = conf_result["confidence"]
        allowed_delta    = conf_result["allowed_delta_pct"]

        # ── Step 3: Policy guard ──────────────────────────────────────────────
        cooldown_check = self._cooldown.can_run(
            risk_violated=risk_violated,
            contradiction_critical=contradiction_critical,
            system_score=meta_score,
        )
        in_cooldown = not cooldown_check["allowed"] and not cooldown_check.get("bypass_active", False)
        # If session limit exceeded, cooldown.can_run already returns allowed=False
        session_limit_hit = self._cooldown._session_cycles >= self._cooldown.max_cycles if hasattr(self._cooldown, 'max_cycles') else False

        policy = self._policy_guard.check(
            n_trades=n_trades,
            ftd027_passed=ftd027_result.get("passed", True) if ftd027_result else True,
            ftd028_score=meta_score,
            ai_brain_score=ai_brain_score,
            meta_score=meta_score,
            in_cooldown=in_cooldown,
            risk_halted=risk_halted,
            human_stopped=self._human_stopped,
            rollback_stop=self._rollback_manager.should_stop(),
            disabled=not self._enabled,
            system_score=meta_score,
            risk_violated=risk_violated,
            contradiction_critical=contradiction_critical,
        )

        if not cooldown_check["allowed"] and not cooldown_check.get("bypass_active", False):
            return self._blocked_response(
                cycle_id, cooldown_check.get("blocking_reason", "COOLDOWN"), now
            )

        if not policy["allowed"]:
            reasons = policy["blocking_reasons"]
            return self._blocked_response(cycle_id, reasons[0] if reasons else "POLICY_BLOCKED", now,
                                          extra={"blocking_reasons": reasons})

        if not issues:
            self._cooldown.record_cycle()
            return {
                "cycle_id": cycle_id, "module": self.MODULE, "phase": self.PHASE,
                "verdict": "NO_ACTION", "detail": "No issues detected — system healthy",
                "issues_found": 0, "applied": [], "blocked": [], "ts": now,
            }

        # ── Step 4: Priority → sort issues ────────────────────────────────────
        sorted_issues = self._priority_resolver.sort(issues)

        # ── Step 5: Change planner ────────────────────────────────────────────
        effective_params = {**current_params, **self._change_applier.get_overlay()}
        plans = self._change_planner.plan(sorted_issues, effective_params, allowed_delta)

        if not plans:
            self._cooldown.record_cycle()
            return {
                "cycle_id": cycle_id, "module": self.MODULE, "phase": self.PHASE,
                "verdict": "NO_ACTION", "detail": "Issues found but no parameter changes planned",
                "issues_found": len(issues), "applied": [], "blocked": [], "ts": now,
            }

        # ── Step 6: Collision handling ────────────────────────────────────────
        plan_dicts  = [self._plan_to_dict(p) for p in plans]
        safe_plans_d, queued_d = self._collision_handler.resolve(plan_dicts)
        # Re-lookup ChangePlan objects matching safe_plans
        safe_param_set = {p["parameter"] for p in safe_plans_d}
        safe_plans  = [p for p in plans if p.parameter in safe_param_set]

        # ── Step 7: Apply ─────────────────────────────────────────────────────
        applied_changes, blocked_plans = self._change_applier.apply(safe_plans, effective_params)

        # ── Step 8: Audit applied changes ─────────────────────────────────────
        issue_by_param: Dict[str, Any] = {}
        for plan in safe_plans:
            issue_by_param[plan.parameter] = (plan.issue_type, plan.target_module, plan.rationale)

        for ch in applied_changes:
            iss_type, iss_mod, rationale = issue_by_param.get(
                ch.parameter, ("UNKNOWN", "unknown", ch.rationale)
            )
            self._audit_logger.log_applied(
                change_id=ch.change_id,
                issue_type=iss_type,
                issue_severity="HIGH",
                affected_module=iss_mod,
                rationale=rationale,
                parameter=ch.parameter,
                value_before=ch.before,
                value_after=ch.after,
                delta_pct=ch.delta_pct,
                confidence=confidence,
                pre_score=meta_score,
            )

        self._cooldown.record_cycle()

        logger.info(
            f"[FTD-029] Cycle {cycle_id}: {len(applied_changes)} applied, "
            f"{len(blocked_plans)} blocked, {len(queued_d)} queued, "
            f"confidence={confidence:.1f}"
        )

        verdict = "APPLIED" if applied_changes else ("BLOCKED" if blocked_plans else "NO_ACTION")

        return {
            "cycle_id":        cycle_id,
            "module":          self.MODULE,
            "phase":           self.PHASE,
            "verdict":         verdict,
            "issues_found":    len(issues),
            "confidence":      round(confidence, 1),
            "allowed_delta":   allowed_delta,
            "applied":         [self._change_applier._serialise(c) for c in applied_changes],
            "blocked":         blocked_plans,
            "queued":          queued_d,
            "param_overlay":   self._change_applier.get_overlay(),
            "ts":              now,
        }

    def resolve_cycle(
        self,
        cycle_id:        str,
        post_state:      Dict[str, Any],
        post_ftd028_score: float,
        risk_violated:   bool = False,
        validation_passed: bool = True,
    ) -> Dict[str, Any]:
        """
        Step 9: Post-correction re-validation and rollback decisions.
        Call after allowing a few trades/ticks to pass following a correction.
        """
        pnl_after = float(post_state.get("total_pnl", 0.0) or 0.0)
        rollbacks: List[Dict[str, Any]] = []

        recent_applied = self._change_applier.recent_applied(10)
        for ch in recent_applied:
            pre_entry = next(
                (e for e in self._audit_logger.recent(50) if e.get("change_id") == ch["change_id"]),
                None,
            )
            if pre_entry is None:
                continue

            pnl_before = 0.0   # best approximation without per-trade snapshot
            decision = self._rollback_manager.evaluate(
                change_id=ch["change_id"],
                parameter=ch["parameter"],
                value_before=ch["before"],
                pnl_before=pnl_before,
                pnl_after=pnl_after,
                score_before=pre_entry.get("pre_score", 0.0),
                score_after=post_ftd028_score,
                risk_violated=risk_violated,
                validation_passed=validation_passed,
            )

            final = FinalState.KEPT if decision["decision"] == "KEEP" else FinalState.ROLLED_BACK
            self._audit_logger.resolve(
                change_id=ch["change_id"],
                post_score=post_ftd028_score,
                final_state=final,
                rollback_trigger=decision.get("trigger"),
            )

            if decision["decision"] == "ROLLBACK":
                self._change_applier.rollback_change(ch["change_id"])
                rollbacks.append(decision)
                logger.warning(f"[FTD-029] ROLLBACK {ch['parameter']} ← {ch['before']} ({decision['trigger']})")

        stop = self._rollback_manager.should_stop()
        if stop:
            logger.error("[FTD-029] Auto-correction STOPPED after 3 consecutive rollbacks (Q10)")

        return {
            "cycle_id":    cycle_id,
            "rollbacks":   rollbacks,
            "rollback_count": len(rollbacks),
            "engine_stopped": stop,
            "post_score":  post_ftd028_score,
            "ts":          int(time.time() * 1000),
        }

    # ── Dashboard controls (Q13) ──────────────────────────────────────────────

    def enable(self)  -> None:
        self._enabled = True
        self._human_stopped = False
        self._rollback_manager.reset()
        self._cooldown.reset()

    def disable(self) -> None:
        self._enabled = False

    def human_override_stop(self) -> None:
        self._human_stopped = True
        logger.warning("[FTD-029] HUMAN OVERRIDE: auto-correction stopped")

    def human_override_resume(self) -> None:
        self._human_stopped = False
        self._rollback_manager.reset()

    def clear_overlay(self) -> None:
        self._change_applier.rollback_all()
        logger.info("[FTD-029] Overlay cleared — reverted to base config")

    def get_overlay(self) -> Dict[str, float]:
        return self._change_applier.get_overlay()

    # ── Q12: Export / Q13: Status ─────────────────────────────────────────────

    def summary(self) -> Dict[str, Any]:
        from core.self_correction.correction_proposal import HARD_LIMITS
        return {
            "module":           self.MODULE,
            "phase":            self.PHASE,
            "enabled":          self._enabled,
            "human_stopped":    self._human_stopped,
            "cooldown":         self._cooldown.summary(),
            "rollback_manager": self._rollback_manager.summary(),
            "change_applier":   self._change_applier.summary(),
            "collision_queue":  self._collision_handler.summary(),
            "audit":            self._audit_logger.summary(),
            "hard_limits":      HARD_LIMITS,
            "snapshot_ts":      int(time.time() * 1000),
        }

    def logs(self, n: int = 50) -> List[Dict[str, Any]]:
        """Q13: return recent audit log entries."""
        return self._audit_logger.recent(n)

    def last_change(self) -> Optional[Dict[str, Any]]:
        """Q13: last correction card."""
        return self._audit_logger.last_change()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _blocked_response(
        self,
        cycle_id: str,
        reason: str,
        ts: int,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        r: Dict[str, Any] = {
            "cycle_id": cycle_id, "module": self.MODULE, "phase": self.PHASE,
            "verdict": "BLOCKED", "code": reason.split(":")[0].strip(), "detail": reason,
            "applied": [], "blocked": [], "ts": ts,
        }
        if extra:
            r.update(extra)
        return r

    @staticmethod
    def _plan_to_dict(p: Any) -> Dict[str, Any]:
        return {
            "plan_id":       p.plan_id,
            "issue_type":    p.issue_type,
            "target_module": p.target_module,
            "parameter":     p.parameter,
            "current_value": p.current_value,
            "proposed_value": p.proposed_value,
            "delta_pct":     p.delta_pct,
            "rationale":     p.rationale,
            "expected_impact": p.expected_impact,
            "auto_eligible": p.auto_eligible,
            "priority_rank": p.priority_rank,
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
correction_orchestrator = CorrectionOrchestrator()
