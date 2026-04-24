"""
FTD-029 Part 8 — Rollback Manager

After applying changes, re-validates using FTD-028 signals.
Decides: KEEP (improved) or ROLLBACK (degraded).

Triggers (Q5):
  - PERF_DROP:       PnL regressed > 5%
  - VALIDATION_FAIL: post-correction FTD-028 score dropped
  - RISK_VIOLATION:  risk engine detected a violation after change

Failure handling (Q10):
  - 3 consecutive rollbacks → set stopped=True, request safe mode + alert
"""
from __future__ import annotations
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


PERF_DROP_THRESHOLD     = 0.05   # >5% PnL regression
SCORE_DROP_THRESHOLD    = 5.0    # system_score dropped >5 pts → fail
MAX_CONSECUTIVE_ROLLBACKS = 3


class RollbackTrigger(str, Enum):
    PERF_DROP       = "PERF_DROP"
    VALIDATION_FAIL = "VALIDATION_FAIL"
    RISK_VIOLATION  = "RISK_VIOLATION"


class RollbackDecision(str, Enum):
    KEEP     = "KEEP"
    ROLLBACK = "ROLLBACK"


@dataclass
class RollbackEvent:
    change_id:    str
    parameter:    str
    restored_to:  float
    trigger:      RollbackTrigger
    detail:       str
    ts:           int


class RollbackManager:
    """
    Post-correction re-validation and rollback decision engine.
    """

    MODULE = "ROLLBACK_MANAGER"
    PHASE  = "029"

    def __init__(self):
        self._events:             List[RollbackEvent] = []
        self._consecutive_fails:  int  = 0
        self._stopped:            bool = False

    def evaluate(
        self,
        change_id:        str,
        parameter:        str,
        value_before:     float,
        pnl_before:       float,
        pnl_after:        float,
        score_before:     float,
        score_after:      float,
        risk_violated:    bool,
        validation_passed: bool,
    ) -> Dict[str, Any]:
        """
        Returns decision (KEEP/ROLLBACK), trigger if any, and whether engine should stop.
        """
        trigger = self._detect(pnl_before, pnl_after, score_before, score_after,
                               risk_violated, validation_passed)

        if trigger is None:
            self._consecutive_fails = 0
            return {
                "change_id": change_id,
                "decision":  RollbackDecision.KEEP.value,
                "trigger":   None,
                "detail":    "All post-correction checks passed",
                "stop_engine": False,
            }

        # Rollback triggered
        event = RollbackEvent(
            change_id=change_id,
            parameter=parameter,
            restored_to=value_before,
            trigger=trigger,
            detail=self._detail(trigger, pnl_before, pnl_after, score_before, score_after),
            ts=int(time.time() * 1000),
        )
        self._events.append(event)
        self._consecutive_fails += 1

        if self._consecutive_fails >= MAX_CONSECUTIVE_ROLLBACKS:
            self._stopped = True

        return {
            "change_id":    change_id,
            "decision":     RollbackDecision.ROLLBACK.value,
            "trigger":      trigger.value,
            "restored_to":  value_before,
            "detail":       event.detail,
            "stop_engine":  self._stopped,
        }

    def should_stop(self) -> bool:
        return self._stopped

    def reset(self) -> None:
        self._stopped = False
        self._consecutive_fails = 0

    def recent_rollbacks(self, n: int = 10) -> List[Dict[str, Any]]:
        return [
            {
                "change_id":   e.change_id,
                "parameter":   e.parameter,
                "restored_to": e.restored_to,
                "trigger":     e.trigger.value,
                "detail":      e.detail,
                "ts":          e.ts,
            }
            for e in self._events[-n:]
        ]

    def summary(self) -> Dict[str, Any]:
        return {
            "module":               self.MODULE,
            "phase":                self.PHASE,
            "total_rollbacks":      len(self._events),
            "consecutive_fails":    self._consecutive_fails,
            "max_before_stop":      MAX_CONSECUTIVE_ROLLBACKS,
            "engine_stopped":       self._stopped,
            "recent_rollbacks":     self.recent_rollbacks(3),
            "snapshot_ts":          int(time.time() * 1000),
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _detect(
        self,
        pnl_before: float, pnl_after: float,
        score_before: float, score_after: float,
        risk_violated: bool, validation_passed: bool,
    ) -> Optional[RollbackTrigger]:
        if risk_violated:
            return RollbackTrigger.RISK_VIOLATION
        if not validation_passed:
            return RollbackTrigger.VALIDATION_FAIL
        if (score_before - score_after) > SCORE_DROP_THRESHOLD:
            return RollbackTrigger.VALIDATION_FAIL
        if pnl_before != 0:
            drop = (pnl_before - pnl_after) / abs(pnl_before)
            if drop > PERF_DROP_THRESHOLD:
                return RollbackTrigger.PERF_DROP
        return None

    @staticmethod
    def _detail(
        trigger: RollbackTrigger,
        pnl_before: float, pnl_after: float,
        score_before: float, score_after: float,
    ) -> str:
        if trigger == RollbackTrigger.RISK_VIOLATION:
            return "Risk engine flagged violation after correction"
        if trigger == RollbackTrigger.VALIDATION_FAIL:
            return f"System score dropped {score_before:.1f}→{score_after:.1f} after correction"
        drop = (pnl_before - pnl_after) / abs(pnl_before) if pnl_before else 0
        return f"PnL regression: {pnl_before:.4f}→{pnl_after:.4f} ({drop:.2%} drop)"
