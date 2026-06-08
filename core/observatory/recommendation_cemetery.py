"""
PHOENIX OBSERVATORY-X — Recommendation Cemetery  [OX-GAP-02]

Institutional systems preserve failures as first-class knowledge.
The Cemetery archives every recommendation that was:
  - REJECTED   : human explicitly declined to act
  - FAILED     : was applied but measurably worsened metrics
  - HARMFUL    : caused direct damage before being reversed
  - EXPIRED    : monitoring window elapsed with no outcome recorded

This prevents the system from repeating the same bad recommendations.
Future recommendation generation checks the cemetery before proposing.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


BURIAL_REASONS = frozenset({"rejected", "failed", "harmful", "expired"})


@dataclass
class BuriedRecommendation:
    rec_id: str
    rec_type: str
    title: str
    action: str
    investigation_id: str
    burial_reason: str        # rejected | failed | harmful | expired
    burial_note: str          # human or system explanation
    buried_at: float = field(default_factory=time.time)
    harm_score: float = 0.0   # 0–10, filled for harmful/failed
    revived: bool = False     # can be revived by human override


class RecommendationCemetery:
    """
    Archive of recommendations that must not be repeated without new evidence.
    Before generating a new recommendation of the same type for the same module/scope,
    the system checks the cemetery for recent burials.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._buried: Dict[str, BuriedRecommendation] = {}   # rec_id → burial

    # ── Burial ────────────────────────────────────────────────────────────────

    def bury(
        self,
        rec_id: str,
        rec_type: str,
        title: str,
        action: str,
        investigation_id: str,
        reason: str,
        note: str,
        harm_score: float = 0.0,
    ) -> BuriedRecommendation:
        if reason not in BURIAL_REASONS:
            raise ValueError(f"Invalid burial reason '{reason}'. Must be one of {BURIAL_REASONS}")
        burial = BuriedRecommendation(
            rec_id=rec_id,
            rec_type=rec_type,
            title=title,
            action=action,
            investigation_id=investigation_id,
            burial_reason=reason,
            burial_note=note,
            harm_score=min(10.0, max(0.0, harm_score)),
        )
        with self._lock:
            self._buried[rec_id] = burial
        self._record_imraf(burial)
        return burial

    def revive(self, rec_id: str, revival_justification: str) -> bool:
        """Mark a buried recommendation as revived (human override with justification)."""
        with self._lock:
            b = self._buried.get(rec_id)
            if b:
                b.revived = True
                b.burial_note += f" | REVIVED: {revival_justification}"
                return True
        return False

    # ── Cemetery Check ────────────────────────────────────────────────────────

    def is_buried(self, rec_id: str) -> bool:
        with self._lock:
            b = self._buried.get(rec_id)
        return b is not None and not b.revived

    def recent_failures_for_type(self, rec_type: str, window_days: float = 30.0) -> List[dict]:
        """Return non-revived burials for a given rec_type within the time window."""
        cutoff = time.time() - window_days * 86400
        with self._lock:
            items = [
                b for b in self._buried.values()
                if b.rec_type == rec_type
                and not b.revived
                and b.buried_at >= cutoff
            ]
        return [self._serialise(b) for b in items]

    # ── Query ─────────────────────────────────────────────────────────────────

    def get(self, rec_id: str) -> Optional[dict]:
        with self._lock:
            b = self._buried.get(rec_id)
        return self._serialise(b) if b else None

    def all_buried(
        self,
        reason_filter: Optional[str] = None,
        include_revived: bool = False,
    ) -> List[dict]:
        with self._lock:
            items = list(self._buried.values())
        if reason_filter:
            items = [b for b in items if b.burial_reason == reason_filter]
        if not include_revived:
            items = [b for b in items if not b.revived]
        return [self._serialise(b) for b in sorted(items, key=lambda x: x.buried_at, reverse=True)]

    def summary(self) -> dict:
        with self._lock:
            all_b = list(self._buried.values())
        by_reason: Dict[str, int] = {}
        for b in all_b:
            by_reason[b.burial_reason] = by_reason.get(b.burial_reason, 0) + 1
        active = [b for b in all_b if not b.revived]
        return {
            "total_buried":   len(all_b),
            "active_burials": len(active),
            "revived":        len(all_b) - len(active),
            "by_reason":      by_reason,
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _record_imraf(self, b: BuriedRecommendation) -> None:
        try:
            from core.observatory.nexus_bridge import _imraf
            im = _imraf()
            if im:
                im.record_knowledge(
                    title=f"[CEMETERY] {b.burial_reason.upper()}: {b.rec_type} — {b.title}",
                    content=f"Buried: {b.burial_note}",
                    category="recommendation_failure",
                    tags=["cemetery", b.burial_reason, b.rec_type],
                )
        except Exception:
            pass

    @staticmethod
    def _serialise(b: BuriedRecommendation) -> dict:
        return {
            "rec_id":           b.rec_id,
            "rec_type":         b.rec_type,
            "title":            b.title,
            "action":           b.action,
            "investigation_id": b.investigation_id,
            "burial_reason":    b.burial_reason,
            "burial_note":      b.burial_note,
            "harm_score":       b.harm_score,
            "buried_at":        b.buried_at,
            "revived":          b.revived,
        }


# Singleton
recommendation_cemetery = RecommendationCemetery()
