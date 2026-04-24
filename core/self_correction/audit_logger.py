"""
FTD-029 Part 9 — Audit Logger (Q11: mandatory, append-only)

Immutable record of every correction:
  - change_id
  - issue_detected (type + severity)
  - rationale
  - before / after
  - confidence
  - validation_result (post-correction FTD-028 score)
  - final_state: KEPT | ROLLED_BACK | BLOCKED
"""
from __future__ import annotations
import json
import pathlib
import time
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


CORRECTIONS_LOG_PATH = pathlib.Path("reports/self_correction/corrections_log.json")
LAST_CORRECTION_PATH = pathlib.Path("reports/self_correction/last_correction.md")


class FinalState(str, Enum):
    KEPT        = "KEPT"
    ROLLED_BACK = "ROLLED_BACK"
    BLOCKED     = "BLOCKED"


@dataclass
class AuditEntry:
    entry_id:          str
    change_id:         str
    issue_type:        str
    issue_severity:    str
    affected_module:   str
    rationale:         str
    parameter:         str
    value_before:      float
    value_after:       float
    delta_pct:         float
    confidence:        float
    pre_score:         float
    post_score:        Optional[float]
    rollback_trigger:  Optional[str]
    final_state:       FinalState
    applied_ts:        int
    resolved_ts:       Optional[int] = None


class AuditLogger:
    """
    Append-only correction audit trail with file persistence.
    Q11: every correction logged with full context.
    Q12: summary exportable for FTD-025A report.
    """

    MODULE = "AUDIT_LOGGER"
    PHASE  = "029"

    def __init__(self):
        self._entries: List[AuditEntry] = []
        self._last_entry: Optional[AuditEntry] = None

    def log_applied(
        self,
        change_id:       str,
        issue_type:      str,
        issue_severity:  str,
        affected_module: str,
        rationale:       str,
        parameter:       str,
        value_before:    float,
        value_after:     float,
        delta_pct:       float,
        confidence:      float,
        pre_score:       float,
    ) -> AuditEntry:
        entry = AuditEntry(
            entry_id=f"AUD_{change_id}",
            change_id=change_id,
            issue_type=issue_type,
            issue_severity=issue_severity,
            affected_module=affected_module,
            rationale=rationale,
            parameter=parameter,
            value_before=round(value_before, 6),
            value_after=round(value_after, 6),
            delta_pct=round(delta_pct, 4),
            confidence=round(confidence, 2),
            pre_score=round(pre_score, 2),
            post_score=None,
            rollback_trigger=None,
            final_state=FinalState.KEPT,   # optimistically KEPT until resolved
            applied_ts=int(time.time() * 1000),
        )
        self._entries.append(entry)
        self._last_entry = entry
        self._persist()
        return entry

    def log_blocked(
        self,
        change_id: str,
        parameter: str,
        reason:    str,
        confidence: float,
        pre_score:  float,
    ) -> AuditEntry:
        entry = AuditEntry(
            entry_id=f"AUD_{change_id}_BLK",
            change_id=change_id,
            issue_type="BLOCKED",
            issue_severity="INFO",
            affected_module="policy_guard",
            rationale=reason,
            parameter=parameter,
            value_before=0.0,
            value_after=0.0,
            delta_pct=0.0,
            confidence=confidence,
            pre_score=pre_score,
            post_score=None,
            rollback_trigger=None,
            final_state=FinalState.BLOCKED,
            applied_ts=int(time.time() * 1000),
        )
        self._entries.append(entry)
        self._persist()
        return entry

    def resolve(
        self,
        change_id:       str,
        post_score:      float,
        final_state:     FinalState,
        rollback_trigger: Optional[str] = None,
    ) -> None:
        for e in self._entries:
            if e.change_id == change_id and e.resolved_ts is None:
                e.post_score       = round(post_score, 2)
                e.final_state      = final_state
                e.rollback_trigger = rollback_trigger
                e.resolved_ts      = int(time.time() * 1000)
                self._last_entry   = e
                break
        self._persist()
        self._write_last_correction_md()

    def recent(self, n: int = 20) -> List[Dict[str, Any]]:
        return [self._ser(e) for e in self._entries[-n:]]

    def last_change(self) -> Optional[Dict[str, Any]]:
        return self._ser(self._last_entry) if self._last_entry else None

    def summary(self) -> Dict[str, Any]:
        total   = len(self._entries)
        kept    = sum(1 for e in self._entries if e.final_state == FinalState.KEPT)
        rolled  = sum(1 for e in self._entries if e.final_state == FinalState.ROLLED_BACK)
        blocked = sum(1 for e in self._entries if e.final_state == FinalState.BLOCKED)
        return {
            "module":        self.MODULE,
            "phase":         self.PHASE,
            "total_entries": total,
            "kept":          kept,
            "rolled_back":   rolled,
            "blocked":       blocked,
            "last_change":   self.last_change(),
            "snapshot_ts":   int(time.time() * 1000),
        }

    # ── Persistence ───────────────────────────────────────────────────────────

    def _persist(self) -> None:
        try:
            CORRECTIONS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            data = [self._ser(e) for e in self._entries]
            CORRECTIONS_LOG_PATH.write_text(json.dumps(data, indent=2, default=str))
        except Exception:
            pass

    def _write_last_correction_md(self) -> None:
        if not self._last_entry:
            return
        e = self._last_entry
        try:
            LAST_CORRECTION_PATH.parent.mkdir(parents=True, exist_ok=True)
            md = f"""# FTD-029 — Last Correction

**change_id:** {e.change_id}
**parameter:** {e.parameter}
**before:** {e.value_before} → **after:** {e.value_after} (Δ {e.delta_pct:.2%})
**issue:** {e.issue_type} ({e.issue_severity}) — module: {e.affected_module}
**rationale:** {e.rationale}
**confidence:** {e.confidence:.1f}
**pre_score:** {e.pre_score:.1f} | **post_score:** {e.post_score or 'pending'}
**final_state:** {e.final_state.value}
**rollback_trigger:** {e.rollback_trigger or 'none'}
**applied_ts:** {e.applied_ts}
"""
            LAST_CORRECTION_PATH.write_text(md)
        except Exception:
            pass

    @staticmethod
    def _ser(e: AuditEntry) -> Dict[str, Any]:
        d = asdict(e)
        d["final_state"] = e.final_state.value
        return d
