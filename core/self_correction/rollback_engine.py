"""
FTD-029 — Rollback Engine (Q5: all triggers)

Triggers rollback when:
  - Performance drop > 5% after correction
  - Risk violation detected
  - FTD-028 validation fails post-correction
"""
from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


PERF_DROP_THRESHOLD   = 0.05    # >5% PnL regression triggers rollback
MAX_CONSECUTIVE_FAILS = 3       # Q10: 3 consecutive failures → stop auto-correction


@dataclass
class RollbackEvent:
    entry_id:    str
    param:       str
    restored_to: float
    trigger:     str          # PERF_DROP | RISK_VIOLATION | VALIDATION_FAIL
    detail:      str
    ts:          int


class RollbackEngine:
    """
    Monitors active corrections and triggers rollback on any failure condition.
    Tracks consecutive failures to enforce Q10 (stop + safe mode + alert).
    """

    MODULE = "ROLLBACK_ENGINE"
    PHASE  = "029"

    def __init__(self):
        self._events:         List[RollbackEvent] = []
        self._consecutive_fails: int = 0
        self._stopped:        bool = False

    # ── Public API ────────────────────────────────────────────────────────────

    def check(
        self,
        entry_id: str,
        param: str,
        value_before: float,
        pnl_before: float,
        pnl_after: float,
        risk_violated: bool,
        validation_passed: bool,
    ) -> Optional[RollbackEvent]:
        """
        Returns a RollbackEvent if any rollback trigger fires, else None.
        Caller is responsible for restoring the parameter when rollback occurs.
        """
        trigger = self._detect_trigger(pnl_before, pnl_after, risk_violated, validation_passed)
        if trigger is None:
            self._consecutive_fails = 0   # reset on success
            return None

        event = RollbackEvent(
            entry_id=entry_id,
            param=param,
            restored_to=value_before,
            trigger=trigger,
            detail=self._detail(pnl_before, pnl_after, risk_violated, validation_passed),
            ts=int(time.time() * 1000),
        )
        self._events.append(event)
        self._consecutive_fails += 1

        if self._consecutive_fails >= MAX_CONSECUTIVE_FAILS:
            self._stopped = True

        return event

    def should_stop(self) -> bool:
        """Q10: returns True after MAX_CONSECUTIVE_FAILS rollbacks."""
        return self._stopped

    def reset_stop(self) -> None:
        """Human override (Q8) can reset the stop state."""
        self._stopped = False
        self._consecutive_fails = 0

    def recent_rollbacks(self, n: int = 10) -> List[Dict[str, Any]]:
        return [
            {
                "entry_id":    e.entry_id,
                "param":       e.param,
                "restored_to": e.restored_to,
                "trigger":     e.trigger,
                "detail":      e.detail,
                "ts":          e.ts,
            }
            for e in self._events[-n:]
        ]

    def summary(self) -> Dict[str, Any]:
        return {
            "module":             self.MODULE,
            "phase":              self.PHASE,
            "total_rollbacks":    len(self._events),
            "consecutive_fails":  self._consecutive_fails,
            "auto_correction_stopped": self._stopped,
            "recent_rollbacks":   self.recent_rollbacks(3),
            "snapshot_ts":        int(time.time() * 1000),
        }

    # ── Internals ─────────────────────────────────────────────────────────────

    def _detect_trigger(
        self,
        pnl_before: float,
        pnl_after: float,
        risk_violated: bool,
        validation_passed: bool,
    ) -> Optional[str]:
        if risk_violated:
            return "RISK_VIOLATION"
        if not validation_passed:
            return "VALIDATION_FAIL"
        if pnl_before != 0 and pnl_after < pnl_before:
            drop = (pnl_before - pnl_after) / abs(pnl_before)
            if drop > PERF_DROP_THRESHOLD:
                return "PERF_DROP"
        return None

    @staticmethod
    def _detail(pnl_before: float, pnl_after: float, risk_violated: bool, validation_passed: bool) -> str:
        if risk_violated:
            return "Risk engine veto: risk violation detected after correction"
        if not validation_passed:
            return "Post-correction FTD-028 validation failed"
        if pnl_before != 0:
            drop = (pnl_before - pnl_after) / abs(pnl_before) if pnl_before else 0
            return f"PnL regression {pnl_before:.4f}→{pnl_after:.4f} ({drop:.2%} drop)"
        return "Rollback triggered"
