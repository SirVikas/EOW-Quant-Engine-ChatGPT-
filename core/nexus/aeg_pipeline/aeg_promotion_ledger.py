"""
PHOENIX AEG — Promotion History Ledger  [GAP-EAP-03]

Immutable ledger of all AEG promotion decisions:
  - Promotions (sandbox → live)
  - Demotions (live → sandbox or suspended)
  - Rollbacks (forced removal from live)
  - Reinstatements (suspension lifted → re-entry)

Tracks outcomes so we can measure:
  - Promotion success rate over time
  - Average time from sandbox to first promotion
  - Rollback frequency per rec_type
  - Reinstatement success rate (did it hold after reinstatement?)
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


EVENT_TYPES = {"PROMOTION", "DEMOTION", "ROLLBACK", "REINSTATEMENT", "SUSPENSION"}


@dataclass
class LedgerEntry:
    entry_id: str
    rec_type: str
    event_type: str           # PROMOTION / DEMOTION / ROLLBACK / REINSTATEMENT / SUSPENSION
    actor: str
    sandbox_accuracy_at_event: Optional[float]
    trust_score_at_event: Optional[float]
    reason: str
    outcome: str = "PENDING"  # PENDING / SUCCESS / FAILED / REVERTED
    recorded_at: float = field(default_factory=time.time)
    resolved_at: float = 0.0
    notes: str = ""


class AEGPromotionLedger:
    """
    Immutable historical record of all AEG promotion lifecycle events.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._entries: List[LedgerEntry] = []
        self._seed_from_live_state()

    def _seed_from_live_state(self) -> None:
        """Snapshot current pipeline state into the ledger at startup."""
        try:
            from core.nexus.aeg_pipeline.aeg_promotion_engine import aeg_promotion_engine as _ape
            summary = _ape.summary()
            for entry_dict in summary.get("live_entries", []):
                rt = entry_dict.get("rec_type", "")
                if rt:
                    self._record(LedgerEntry(
                        entry_id=f"LEDGER-INIT-{rt[:8]}-{int(time.time()*1000)}",
                        rec_type=rt,
                        event_type="PROMOTION",
                        actor="SYSTEM_INIT",
                        sandbox_accuracy_at_event=entry_dict.get("accuracy"),
                        trust_score_at_event=None,
                        reason="Live state at ledger initialisation",
                        outcome="SUCCESS",
                    ))
        except Exception:
            pass

    def _record(self, entry: LedgerEntry) -> None:
        with self._lock:
            self._entries.append(entry)

    # ── Record Events ─────────────────────────────────────────────────────────

    def record_promotion(self, rec_type: str, actor: str = "SYSTEM",
                         sandbox_accuracy: Optional[float] = None,
                         trust_score: Optional[float] = None,
                         notes: str = "") -> LedgerEntry:
        entry = LedgerEntry(
            entry_id=f"LEDGER-PROM-{rec_type[:8]}-{int(time.time()*1000)}",
            rec_type=rec_type, event_type="PROMOTION", actor=actor,
            sandbox_accuracy_at_event=sandbox_accuracy,
            trust_score_at_event=trust_score,
            reason="Sandbox accuracy and trust thresholds met",
            outcome="PENDING", notes=notes,
        )
        self._record(entry)
        return entry

    def record_rollback(self, rec_type: str, reason: str, actor: str = "SYSTEM",
                        sandbox_accuracy: Optional[float] = None) -> LedgerEntry:
        entry = LedgerEntry(
            entry_id=f"LEDGER-ROLL-{rec_type[:8]}-{int(time.time()*1000)}",
            rec_type=rec_type, event_type="ROLLBACK", actor=actor,
            sandbox_accuracy_at_event=sandbox_accuracy,
            trust_score_at_event=None,
            reason=reason, outcome="APPLIED",
        )
        self._record(entry)
        # Mark any pending promotion for this rec_type as REVERTED
        with self._lock:
            for e in self._entries:
                if e.rec_type == rec_type and e.event_type == "PROMOTION" and e.outcome == "PENDING":
                    e.outcome = "REVERTED"
                    e.resolved_at = time.time()
        return entry

    def record_reinstatement(self, rec_type: str, actor: str = "SYSTEM",
                             notes: str = "") -> LedgerEntry:
        entry = LedgerEntry(
            entry_id=f"LEDGER-REIN-{rec_type[:8]}-{int(time.time()*1000)}",
            rec_type=rec_type, event_type="REINSTATEMENT", actor=actor,
            sandbox_accuracy_at_event=None, trust_score_at_event=None,
            reason="Suspension period complete", outcome="PENDING", notes=notes,
        )
        self._record(entry)
        return entry

    def resolve_entry(self, entry_id: str, outcome: str) -> dict:
        with self._lock:
            for e in self._entries:
                if e.entry_id == entry_id:
                    e.outcome = outcome
                    e.resolved_at = time.time()
                    return {"resolved": True, "entry_id": entry_id, "outcome": outcome}
        return {"error": f"Entry '{entry_id}' not found"}

    # ── Analytics ─────────────────────────────────────────────────────────────

    def for_rec_type(self, rec_type: str) -> List[dict]:
        with self._lock:
            entries = [e for e in self._entries if e.rec_type == rec_type]
        return [self._ser(e) for e in sorted(entries, key=lambda x: x.recorded_at, reverse=True)]

    def by_event_type(self, event_type: str) -> List[dict]:
        with self._lock:
            entries = [e for e in self._entries if e.event_type == event_type]
        return [self._ser(e) for e in sorted(entries, key=lambda x: x.recorded_at, reverse=True)]

    def promotion_success_rate(self) -> dict:
        with self._lock:
            promotions = [e for e in self._entries if e.event_type == "PROMOTION"]
        total = len(promotions)
        successful = sum(1 for e in promotions if e.outcome == "SUCCESS")
        reverted   = sum(1 for e in promotions if e.outcome == "REVERTED")
        pending    = sum(1 for e in promotions if e.outcome == "PENDING")
        return {
            "total_promotions": total,
            "successful":       successful,
            "reverted":         reverted,
            "pending":          pending,
            "success_rate":     round(successful / max(1, total - pending), 3) if total > pending else None,
        }

    def summary(self) -> dict:
        with self._lock:
            entries = list(self._entries)
        by_type: Dict[str, int] = {}
        by_rec: Dict[str, List[str]] = {}
        for e in entries:
            by_type[e.event_type] = by_type.get(e.event_type, 0) + 1
            by_rec.setdefault(e.rec_type, []).append(e.event_type)

        # Rec types with rollbacks
        rolled_back = [rt for rt, evs in by_rec.items() if "ROLLBACK" in evs]
        reinstated  = [rt for rt, evs in by_rec.items() if "REINSTATEMENT" in evs]

        psr = self.promotion_success_rate()
        return {
            "total_entries":      len(entries),
            "by_event_type":      by_type,
            "unique_rec_types":   len(by_rec),
            "rolled_back_types":  rolled_back,
            "reinstated_types":   reinstated,
            "promotion_success":  psr,
            "generated_at":       time.time(),
        }

    @staticmethod
    def _ser(e: LedgerEntry) -> dict:
        return {
            "entry_id":                    e.entry_id,
            "rec_type":                    e.rec_type,
            "event_type":                  e.event_type,
            "actor":                       e.actor,
            "sandbox_accuracy_at_event":   e.sandbox_accuracy_at_event,
            "trust_score_at_event":        e.trust_score_at_event,
            "reason":                      e.reason,
            "outcome":                     e.outcome,
            "recorded_at":                 e.recorded_at,
            "resolved_at":                 e.resolved_at or None,
            "notes":                       e.notes,
        }


# Singleton
aeg_promotion_ledger = AEGPromotionLedger()
