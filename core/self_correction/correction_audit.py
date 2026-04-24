"""
FTD-029 — Correction Audit Trail (Q11: mandatory logging)

Records every correction: what changed, why, before/after values, outcome.
Fully immutable append-only log — entries are never modified or deleted.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


class CorrectionOutcome(str, Enum):
    APPLIED         = "APPLIED"
    ROLLED_BACK     = "ROLLED_BACK"
    BLOCKED_LIMIT   = "BLOCKED_LIMIT"
    BLOCKED_HALTED  = "BLOCKED_HALTED"
    VALIDATION_FAIL = "VALIDATION_FAIL"
    PENDING         = "PENDING"


@dataclass
class CorrectionEntry:
    entry_id:      str
    param:         str
    before:        float
    after:         float
    delta_pct:     float
    reason:        str
    objective:     str
    confidence:    float
    auto_applied:  bool
    outcome:       CorrectionOutcome
    outcome_detail: str
    applied_ts:    int
    resolved_ts:   Optional[int] = None
    pnl_before:    Optional[float] = None
    pnl_after:     Optional[float] = None


class CorrectionAudit:
    """
    Append-only log of all correction events.
    Q11: logs what/why/before/after/result for every correction.
    Q12: summary exposed for export integration.
    """

    MODULE = "CORRECTION_AUDIT"
    PHASE  = "029"

    def __init__(self):
        self._log: List[CorrectionEntry] = []

    def record(
        self,
        entry_id: str,
        param: str,
        before: float,
        after: float,
        delta_pct: float,
        reason: str,
        objective: str,
        confidence: float,
        auto_applied: bool,
        outcome: CorrectionOutcome,
        outcome_detail: str = "",
        pnl_before: Optional[float] = None,
    ) -> CorrectionEntry:
        entry = CorrectionEntry(
            entry_id=entry_id,
            param=param,
            before=before,
            after=after,
            delta_pct=delta_pct,
            reason=reason,
            objective=objective,
            confidence=confidence,
            auto_applied=auto_applied,
            outcome=outcome,
            outcome_detail=outcome_detail,
            applied_ts=int(time.time() * 1000),
            pnl_before=pnl_before,
        )
        self._log.append(entry)
        return entry

    def resolve(self, entry_id: str, outcome: CorrectionOutcome, pnl_after: float, detail: str = "") -> None:
        for e in self._log:
            if e.entry_id == entry_id and e.resolved_ts is None:
                e.outcome       = outcome
                e.outcome_detail = detail
                e.pnl_after     = pnl_after
                e.resolved_ts   = int(time.time() * 1000)
                break

    def recent(self, n: int = 20) -> List[Dict[str, Any]]:
        return [self._serialise(e) for e in self._log[-n:]]

    def summary(self) -> Dict[str, Any]:
        total     = len(self._log)
        applied   = sum(1 for e in self._log if e.outcome == CorrectionOutcome.APPLIED)
        rolled    = sum(1 for e in self._log if e.outcome == CorrectionOutcome.ROLLED_BACK)
        blocked   = sum(1 for e in self._log if e.outcome in (
            CorrectionOutcome.BLOCKED_LIMIT, CorrectionOutcome.BLOCKED_HALTED,
            CorrectionOutcome.VALIDATION_FAIL,
        ))
        return {
            "module":         self.MODULE,
            "phase":          self.PHASE,
            "total_entries":  total,
            "applied":        applied,
            "rolled_back":    rolled,
            "blocked":        blocked,
            "recent":         self.recent(5),
            "snapshot_ts":    int(time.time() * 1000),
        }

    @staticmethod
    def _serialise(e: CorrectionEntry) -> Dict[str, Any]:
        d = asdict(e)
        d["outcome"] = e.outcome.value
        return d
