"""
FTD-029 — Self-Correction Engine (Main Orchestrator)

Closed-loop intelligence: diagnose → propose → validate → apply → monitor → rollback.

Authority (Q7):  Combined AI Brain score + FTD-028 MetaScoreEngine score (both ≥ 70)
Safety (Q8):     Risk Engine veto + human override both enforced
Frequency (Q6):  ≤ 3 cycles/session, 4-hour cooldown between cycles
Start (Q15):     ≥ 30 trades AND FTD-028 system_score ≥ 70
"""
from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from loguru import logger

from core.self_correction.correction_proposal import (
    CorrectionProposal,
    HARD_LIMITS,
    TUNABLE_PARAMS,
    max_change_pct,
    Proposal,
)
from core.self_correction.correction_audit    import CorrectionAudit, CorrectionOutcome
from core.self_correction.rollback_engine     import RollbackEngine


# ── Session limits (Q6) ───────────────────────────────────────────────────────
MAX_CYCLES_PER_SESSION = 3
COOLDOWN_SECONDS       = 4 * 3600   # 4 hours

# ── Start conditions (Q15) ────────────────────────────────────────────────────
MIN_TRADES_TO_START      = 30
MIN_SYSTEM_SCORE_TO_START = 70.0

# ── Authority thresholds (Q7) ─────────────────────────────────────────────────
MIN_AI_BRAIN_SCORE    = 70.0
MIN_META_SCORE        = 70.0


@dataclass
class CorrectionCycle:
    cycle_id:        str
    proposals:       List[Dict[str, Any]]
    applied:         List[Dict[str, Any]]
    blocked:         List[Dict[str, Any]]
    rolled_back:     List[Dict[str, Any]]
    system_score_before: float
    system_score_after:  Optional[float]
    verdict:         str    # APPLIED | PARTIAL | BLOCKED | ROLLED_BACK
    ts:              int


class SelfCorrectionEngine:
    """
    Orchestrates the complete correction loop (Q1–Q15).

    Call flow:
        1. run_cycle(state, current_params, deep_validation_score, ai_brain_score)
           → CorrectionCycle result
        2. Periodically call resolve_cycle(cycle_id, post_state) to check rollback triggers.
        3. Query summary() for dashboard (Q13) and export (Q12).
    """

    MODULE = "SELF_CORRECTION_ENGINE"
    PHASE  = "029"

    def __init__(self):
        self._enabled:          bool = True             # Q13: enable/disable
        self._human_stopped:    bool = False            # Q8: human override
        self._session_cycles:   int  = 0
        self._last_cycle_ts:    float = 0.0
        self._param_overlay:    Dict[str, float] = {}  # live correction deltas
        self._param_snapshots:  Dict[str, Dict[str, float]] = {}  # cycle_id → pre-correction params
        self._cycles:           List[CorrectionCycle] = []

        self._proposal_gen = CorrectionProposal()
        self._audit        = CorrectionAudit()
        self._rollback     = RollbackEngine()

    # ── Public: main entry point ──────────────────────────────────────────────

    def run_cycle(
        self,
        state: Dict[str, Any],
        current_params: Dict[str, float],
        deep_validation_score: float = 0.0,   # FTD-028 MetaScoreEngine score
        ai_brain_score: float = 0.0,          # FTD-023 AI Brain score
        risk_halted: bool = False,             # Q8: Risk Engine veto
    ) -> Dict[str, Any]:
        """
        Executes one correction cycle.  Returns a structured cycle report.
        """
        n_trades    = state.get("total_trades", 0) or 0
        cycle_id    = str(uuid.uuid4())[:8]
        now         = time.time()

        # ── Guard: human or rollback-engine stop (Q8, Q10) ───────────────────
        if self._human_stopped:
            return self._blocked(cycle_id, "HUMAN_OVERRIDE", "Auto-correction disabled by human override")

        if not self._enabled:
            return self._blocked(cycle_id, "DISABLED", "Auto-correction is disabled")

        if self._rollback.should_stop():
            return self._blocked(cycle_id, "CONSECUTIVE_FAIL_STOP",
                f"Auto-correction stopped after {3} consecutive rollback failures (Q10)")

        # ── Guard: risk engine veto (Q8) ──────────────────────────────────────
        if risk_halted:
            return self._blocked(cycle_id, "RISK_ENGINE_VETO", "Risk engine halt — correction blocked")

        # ── Guard: start conditions (Q15) ─────────────────────────────────────
        if n_trades < MIN_TRADES_TO_START:
            return self._blocked(cycle_id, "INSUFFICIENT_TRADES",
                f"Need ≥{MIN_TRADES_TO_START} trades, have {n_trades}")

        if deep_validation_score < MIN_SYSTEM_SCORE_TO_START:
            return self._blocked(cycle_id, "DEEP_VALIDATION_NOT_PASSED",
                f"FTD-028 score={deep_validation_score:.1f} < {MIN_SYSTEM_SCORE_TO_START}")

        # ── Guard: frequency limits (Q6) ──────────────────────────────────────
        if self._session_cycles >= MAX_CYCLES_PER_SESSION:
            return self._blocked(cycle_id, "SESSION_LIMIT",
                f"Session limit of {MAX_CYCLES_PER_SESSION} correction cycles reached")

        elapsed = now - self._last_cycle_ts
        if self._last_cycle_ts > 0 and elapsed < COOLDOWN_SECONDS:
            remaining = int(COOLDOWN_SECONDS - elapsed)
            return self._blocked(cycle_id, "COOLDOWN",
                f"Cooldown active — {remaining}s remaining before next cycle")

        # ── Guard: combined authority (Q7) ────────────────────────────────────
        if ai_brain_score < MIN_AI_BRAIN_SCORE:
            return self._blocked(cycle_id, "AI_BRAIN_SCORE_LOW",
                f"AI Brain score={ai_brain_score:.1f} < {MIN_AI_BRAIN_SCORE} — not confident enough")

        if deep_validation_score < MIN_META_SCORE:
            return self._blocked(cycle_id, "META_SCORE_LOW",
                f"MetaScore={deep_validation_score:.1f} < {MIN_META_SCORE}")

        # ── Generate proposals ────────────────────────────────────────────────
        confidence  = (ai_brain_score + deep_validation_score) / 2.0
        effective_params = {**current_params, **self._param_overlay}
        proposals   = self._proposal_gen.generate(state, effective_params, confidence)

        if not proposals:
            return {
                "cycle_id":   cycle_id,
                "module":     self.MODULE,
                "phase":      self.PHASE,
                "verdict":    "NO_ACTION",
                "detail":     "System is healthy — no corrections needed",
                "proposals":  [],
                "applied":    [],
                "blocked":    [],
                "ts":         int(now * 1000),
            }

        # ── Apply proposals ───────────────────────────────────────────────────
        snapshot_before = dict(effective_params)
        applied:  List[Dict[str, Any]] = []
        blocked:  List[Dict[str, Any]] = []

        for prop in proposals:
            result = self._apply_proposal(prop, current_params, state.get("total_pnl", 0.0))
            if result["applied"]:
                applied.append(result)
            else:
                blocked.append(result)

        # Save snapshot for rollback lookup (Q5)
        self._param_snapshots[cycle_id] = snapshot_before

        self._session_cycles += 1
        self._last_cycle_ts   = now

        verdict = "APPLIED" if applied else ("BLOCKED" if blocked else "NO_ACTION")

        cycle = CorrectionCycle(
            cycle_id=cycle_id,
            proposals=[self._prop_dict(p) for p in proposals],
            applied=applied,
            blocked=blocked,
            rolled_back=[],
            system_score_before=deep_validation_score,
            system_score_after=None,
            verdict=verdict,
            ts=int(now * 1000),
        )
        self._cycles.append(cycle)

        logger.info(
            f"[FTD-029] Cycle {cycle_id}: {len(applied)} applied, {len(blocked)} blocked, "
            f"confidence={confidence:.1f}"
        )

        return {
            "cycle_id":          cycle_id,
            "module":            self.MODULE,
            "phase":             self.PHASE,
            "verdict":           verdict,
            "proposals_count":   len(proposals),
            "applied":           applied,
            "blocked":           blocked,
            "session_cycles":    self._session_cycles,
            "confidence":        round(confidence, 1),
            "ts":                int(now * 1000),
        }

    def resolve_cycle(
        self,
        cycle_id: str,
        post_state: Dict[str, Any],
        deep_validation_passed: bool = True,
        risk_violated: bool = False,
    ) -> Dict[str, Any]:
        """
        Called after a correction cycle to check rollback triggers (Q5).
        Returns rollback report if any parameter was restored.
        """
        pnl_after = float(post_state.get("total_pnl", 0.0) or 0.0)

        # Find applied entries for this cycle
        applied_entries = [
            e for e in self._audit.recent(100)
            if e.get("entry_id", "").startswith(cycle_id) and
               e.get("outcome") == CorrectionOutcome.APPLIED.value
        ]

        rollbacks_done: List[Dict[str, Any]] = []

        for entry in applied_entries:
            pnl_before = entry.get("pnl_before", 0.0) or 0.0
            rb = self._rollback.check(
                entry_id=entry["entry_id"],
                param=entry["param"],
                value_before=entry["before"],
                pnl_before=pnl_before,
                pnl_after=pnl_after,
                risk_violated=risk_violated,
                validation_passed=deep_validation_passed,
            )
            if rb is not None:
                # Restore the parameter in the overlay
                self._param_overlay[rb.param] = rb.restored_to
                self._audit.resolve(
                    entry["entry_id"],
                    CorrectionOutcome.ROLLED_BACK,
                    pnl_after,
                    rb.detail,
                )
                rollbacks_done.append({
                    "param":       rb.param,
                    "restored_to": rb.restored_to,
                    "trigger":     rb.trigger,
                    "detail":      rb.detail,
                })
                logger.warning(f"[FTD-029] ROLLBACK {rb.param} → {rb.restored_to} ({rb.trigger})")
            else:
                self._audit.resolve(entry["entry_id"], CorrectionOutcome.APPLIED, pnl_after)

        # Q10: if rollback engine says stop → alert
        if self._rollback.should_stop():
            logger.error("[FTD-029] Auto-correction STOPPED — 3 consecutive rollback failures")

        return {
            "cycle_id":      cycle_id,
            "rollbacks":     rollbacks_done,
            "rollback_count": len(rollbacks_done),
            "auto_correction_stopped": self._rollback.should_stop(),
            "ts":            int(time.time() * 1000),
        }

    # ── Q13: Dashboard controls ───────────────────────────────────────────────

    def enable(self) -> None:
        self._enabled = True
        self._human_stopped = False
        self._rollback.reset_stop()
        logger.info("[FTD-029] Auto-correction ENABLED")

    def disable(self) -> None:
        self._enabled = False
        logger.info("[FTD-029] Auto-correction DISABLED by user")

    def human_override_stop(self) -> None:
        """Q8: human override — immediately stops all auto-correction."""
        self._human_stopped = True
        logger.warning("[FTD-029] Auto-correction stopped by HUMAN OVERRIDE")

    def human_override_resume(self) -> None:
        """Q8: human resumes auto-correction."""
        self._human_stopped = False
        self._rollback.reset_stop()
        logger.info("[FTD-029] Human override: auto-correction RESUMED")

    def get_overlay(self) -> Dict[str, float]:
        """Returns the live parameter corrections applied on top of base config."""
        return dict(self._param_overlay)

    def clear_overlay(self) -> None:
        """Manual override: clear all corrections and revert to base config."""
        self._param_overlay.clear()
        logger.info("[FTD-029] Parameter overlay cleared — reverted to base config")

    # ── Q12: Export + Q13: summary ────────────────────────────────────────────

    def summary(self) -> Dict[str, Any]:
        return {
            "module":                 self.MODULE,
            "phase":                  self.PHASE,
            "enabled":                self._enabled,
            "human_stopped":          self._human_stopped,
            "session_cycles":         self._session_cycles,
            "max_cycles_per_session": MAX_CYCLES_PER_SESSION,
            "cooldown_hours":         COOLDOWN_SECONDS // 3600,
            "last_cycle_ts":          int(self._last_cycle_ts * 1000) if self._last_cycle_ts else None,
            "active_corrections":     len(self._param_overlay),
            "param_overlay":          self._param_overlay,
            "rollback_state":         self._rollback.summary(),
            "audit_summary":          self._audit.summary(),
            "recent_cycles":          [self._cycle_dict(c) for c in self._cycles[-5:]],
            "hard_limits":            HARD_LIMITS,
            "start_conditions": {
                "min_trades":         MIN_TRADES_TO_START,
                "min_system_score":   MIN_SYSTEM_SCORE_TO_START,
            },
            "snapshot_ts":            int(time.time() * 1000),
        }

    # ── Internals ─────────────────────────────────────────────────────────────

    def _apply_proposal(
        self,
        prop: Proposal,
        base_params: Dict[str, float],
        current_pnl: float,
    ) -> Dict[str, Any]:
        entry_id = f"{self._last_cycle_ts:.0f}_{prop.param[:8]}"

        # Hard-limit guard (Q14)
        if prop.param in HARD_LIMITS:
            self._audit.record(
                entry_id=entry_id, param=prop.param,
                before=prop.current, after=prop.current,
                delta_pct=0.0, reason=prop.reason, objective=prop.objective,
                confidence=prop.confidence, auto_applied=False,
                outcome=CorrectionOutcome.BLOCKED_LIMIT,
                outcome_detail=f"Parameter is in HARD_LIMITS — immutable",
            )
            return {"applied": False, "param": prop.param, "reason": "HARD_LIMIT"}

        # Bounds guard
        bounds = TUNABLE_PARAMS.get(prop.param)
        if bounds:
            lo, hi, _ = bounds
            if not (lo <= prop.proposed <= hi):
                self._audit.record(
                    entry_id=entry_id, param=prop.param,
                    before=prop.current, after=prop.current,
                    delta_pct=0.0, reason=prop.reason, objective=prop.objective,
                    confidence=prop.confidence, auto_applied=False,
                    outcome=CorrectionOutcome.BLOCKED_LIMIT,
                    outcome_detail=f"Proposed value {prop.proposed} outside bounds [{lo}, {hi}]",
                )
                return {"applied": False, "param": prop.param, "reason": "OUT_OF_BOUNDS"}

        # Apply
        self._param_overlay[prop.param] = prop.proposed
        self._audit.record(
            entry_id=entry_id, param=prop.param,
            before=prop.current, after=prop.proposed,
            delta_pct=prop.delta_pct, reason=prop.reason, objective=prop.objective,
            confidence=prop.confidence, auto_applied=prop.auto_apply,
            outcome=CorrectionOutcome.APPLIED,
            outcome_detail=f"Applied ({'auto' if prop.auto_apply else 'validated'})",
            pnl_before=current_pnl,
        )
        return {
            "applied":    True,
            "param":      prop.param,
            "before":     prop.current,
            "after":      prop.proposed,
            "delta_pct":  prop.delta_pct,
            "reason":     prop.reason,
            "objective":  prop.objective,
            "auto_apply": prop.auto_apply,
        }

    def _blocked(self, cycle_id: str, code: str, detail: str) -> Dict[str, Any]:
        return {
            "cycle_id": cycle_id,
            "module":   self.MODULE,
            "phase":    self.PHASE,
            "verdict":  "BLOCKED",
            "code":     code,
            "detail":   detail,
            "ts":       int(time.time() * 1000),
        }

    @staticmethod
    def _prop_dict(p: Proposal) -> Dict[str, Any]:
        return {
            "param": p.param, "current": p.current, "proposed": p.proposed,
            "delta_pct": p.delta_pct, "reason": p.reason,
            "objective": p.objective, "auto_apply": p.auto_apply,
        }

    @staticmethod
    def _cycle_dict(c: CorrectionCycle) -> Dict[str, Any]:
        return {
            "cycle_id": c.cycle_id,
            "verdict":  c.verdict,
            "applied":  len(c.applied),
            "blocked":  len(c.blocked),
            "rolled_back": len(c.rolled_back),
            "ts":       c.ts,
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
self_correction_engine = SelfCorrectionEngine()
