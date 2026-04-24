"""
FTD-029 Part 3 — Policy Guard

Single gate that must pass ALL conditions before any correction is applied.
Implements Q4, Q7, Q8, Q14, Q15.
"""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from core.self_correction.correction_proposal import HARD_LIMITS


# ── Thresholds (locked) ───────────────────────────────────────────────────────
MIN_TRADES            = 30
MIN_SYSTEM_SCORE      = 70.0
MIN_AI_BRAIN_SCORE    = 70.0
MIN_META_SCORE        = 70.0
CRITICAL_BYPASS_SCORE = 50.0   # system_score < 50 → bypass cooldown (Q7 Part 7)


class PolicyGuard:
    """
    Enforces all correction gates in one place.
    Returns a structured decision with blocking reasons.
    """

    MODULE = "POLICY_GUARD"
    PHASE  = "029"

    def check(
        self,
        n_trades:            int,
        ftd027_passed:       bool,
        ftd028_score:        float,
        ai_brain_score:      float,
        meta_score:          float,
        in_cooldown:         bool,
        risk_halted:         bool,
        human_stopped:       bool,
        rollback_stop:       bool,
        disabled:            bool,
        proposed_params:     Optional[Dict[str, Any]] = None,
        system_score:        Optional[float] = None,
        risk_violated:       bool = False,
        contradiction_critical: bool = False,
    ) -> Dict[str, Any]:
        """
        Returns:
            allowed: bool
            bypass_cooldown: bool  (critical bypass — Q7 Part 7)
            blocking_reasons: list[str]
        """
        blocking: List[str] = []
        bypass_cooldown = False

        # ── Hard stops (Q8) ──────────────────────────────────────────────────
        if disabled:
            blocking.append("DISABLED: auto-correction is turned off")
        if human_stopped:
            blocking.append("HUMAN_OVERRIDE: stopped by human override")
        if rollback_stop:
            blocking.append("CONSECUTIVE_FAIL_STOP: 3 rollback failures reached (Q10)")
        if risk_halted:
            blocking.append("RISK_ENGINE_VETO: risk engine halt active (Q8)")

        # ── Start conditions (Q15) ────────────────────────────────────────────
        if n_trades < MIN_TRADES:
            blocking.append(f"INSUFFICIENT_TRADES: {n_trades} < {MIN_TRADES} (Q15)")

        # ── Dual validation (Q4) ──────────────────────────────────────────────
        if not ftd027_passed:
            blocking.append("FTD027_FAIL: FTD-027 validation did not pass (Q4)")
        if ftd028_score < MIN_SYSTEM_SCORE:
            blocking.append(f"FTD028_SCORE_LOW: {ftd028_score:.1f} < {MIN_SYSTEM_SCORE} (Q4)")

        # ── Dual authority (Q7) ───────────────────────────────────────────────
        if ai_brain_score < MIN_AI_BRAIN_SCORE:
            blocking.append(f"AI_BRAIN_SCORE_LOW: {ai_brain_score:.1f} < {MIN_AI_BRAIN_SCORE} (Q7)")
        if meta_score < MIN_META_SCORE:
            blocking.append(f"META_SCORE_LOW: {meta_score:.1f} < {MIN_META_SCORE} (Q7)")

        # ── Cooldown — may be bypassed for critical issues (Q6 / Part 7) ──────
        eff_score = system_score if system_score is not None else ftd028_score
        critical_bypass_triggered = (
            risk_violated
            or contradiction_critical
            or eff_score < CRITICAL_BYPASS_SCORE
        )
        if in_cooldown and not critical_bypass_triggered:
            blocking.append("COOLDOWN: correction cooldown active (Q6)")
        elif in_cooldown and critical_bypass_triggered:
            bypass_cooldown = True   # allowed: bypass for critical

        # ── Hard-limit guard (Q14) ────────────────────────────────────────────
        if proposed_params:
            for param in proposed_params:
                if param in HARD_LIMITS:
                    blocking.append(f"HARD_LIMIT: '{param}' is immutable (Q14)")

        allowed = len(blocking) == 0
        return {
            "module":           self.MODULE,
            "phase":            self.PHASE,
            "allowed":          allowed,
            "bypass_cooldown":  bypass_cooldown,
            "blocking_reasons": blocking,
            "snapshot_ts":      int(time.time() * 1000),
        }
