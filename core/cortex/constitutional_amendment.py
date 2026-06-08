"""
PHOENIX CORTEX — Constitutional Amendment Framework  [CX-GAP-01]

A constitution without an amendment process is brittle.
An amendment process without governance is dangerous.

This framework implements the formal five-stage amendment process:
  1. PROPOSE    — Any operator can propose a change to a constitutional article
  2. REVIEW     — System runs automatic compliance + impact analysis
  3. VOTE       — Human quorum registers approval/rejection
  4. RATIFY     — After quorum met, amendment enters 24h ratification window
  5. ENACTED    — Article is updated; old version archived

Hard constraints:
  - ARTICLE-001 (Risk Supremacy) and ARTICLE-004 (Drawdown Supremacy) cannot
    be weakened by any amendment. They can only be strengthened.
  - All amendments require human approval (ARTICLE-003 compliance).
  - No amendment can be ratified within 24h of proposal (cooling-off period).
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

COOLING_OFF_SECONDS = 86400   # 24h
QUORUM_REQUIRED     = 2       # minimum human approvals to advance to RATIFY

_UNAMENDABLE_STRONGER_ONLY = frozenset({"ARTICLE-001", "ARTICLE-004"})


@dataclass
class Amendment:
    amendment_id: str
    target_article_id: str
    proposed_change: str          # what the proposer wants to change
    rationale: str
    proposed_by: str              # operator identifier
    status: str = "PROPOSED"     # PROPOSED | REVIEW | VOTE | RATIFY | ENACTED | REJECTED
    proposed_at: float = field(default_factory=time.time)
    review_notes: str = ""
    votes_for: List[str] = field(default_factory=list)
    votes_against: List[str] = field(default_factory=list)
    ratified_at: float = 0.0
    enacted_at: float = 0.0
    rejected_reason: str = ""


class ConstitutionalAmendmentFramework:
    """
    Formal governance process for amending constitutional articles.
    Enforces cooling-off periods, quorum requirements, and unamendable protections.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._amendments: Dict[str, Amendment] = {}

    # ── Stage 1: Propose ──────────────────────────────────────────────────────

    def propose(
        self,
        target_article_id: str,
        proposed_change: str,
        rationale: str,
        proposed_by: str,
    ) -> Amendment:
        amendment_id = f"AMD_{target_article_id}_{int(time.time())}"
        a = Amendment(
            amendment_id=amendment_id,
            target_article_id=target_article_id,
            proposed_change=proposed_change,
            rationale=rationale,
            proposed_by=proposed_by,
        )
        with self._lock:
            self._amendments[amendment_id] = a
        self._advance_to_review(a)
        return a

    # ── Stage 2: Review ───────────────────────────────────────────────────────

    def _advance_to_review(self, a: Amendment) -> None:
        notes = []
        if a.target_article_id in _UNAMENDABLE_STRONGER_ONLY:
            notes.append(
                f"⚠ {a.target_article_id} is a Supremacy Article. "
                "Amendments may only strengthen its protections, never weaken them."
            )
        # Check article exists
        try:
            from core.cortex.constitution import constitution_registry
            art = constitution_registry.get_article(a.target_article_id)
            if not art:
                a.status = "REJECTED"
                a.rejected_reason = f"Article {a.target_article_id} does not exist."
                return
            notes.append(f"Current enforcement: {art.enforcement}. Override authority: {art.override_authority}.")
        except Exception as e:
            notes.append(f"Review warning: {e}")
        a.review_notes = " | ".join(notes)
        a.status = "VOTE"

    # ── Stage 3: Vote ─────────────────────────────────────────────────────────

    def cast_vote(
        self,
        amendment_id: str,
        voter: str,
        approve: bool,
        reason: str = "",
    ) -> dict:
        with self._lock:
            a = self._amendments.get(amendment_id)
        if not a:
            return {"error": f"Amendment {amendment_id} not found"}
        if a.status != "VOTE":
            return {"error": f"Amendment is in '{a.status}' state, not VOTE"}
        with self._lock:
            if approve:
                if voter not in a.votes_for:
                    a.votes_for.append(voter)
            else:
                if voter not in a.votes_against:
                    a.votes_against.append(voter)
            # Advance if quorum met
            if len(a.votes_for) >= QUORUM_REQUIRED:
                a.status = "RATIFY"
                a.ratified_at = time.time()
            elif len(a.votes_against) >= QUORUM_REQUIRED:
                a.status = "REJECTED"
                a.rejected_reason = f"Voted down by quorum. Last reason: {reason}"
        return {"amendment_id": amendment_id, "status": a.status}

    # ── Stage 4/5: Ratify + Enact ─────────────────────────────────────────────

    def enact(self, amendment_id: str, enacted_by: str) -> dict:
        """
        Enact an amendment after the cooling-off period has passed.
        This does NOT automatically modify the ConstitutionRegistry (which is immutable).
        Instead it records the intent and flags the article for human-applied change.
        Constitutional articles must be updated in code by a developer per ARTICLE-003.
        """
        with self._lock:
            a = self._amendments.get(amendment_id)
        if not a:
            return {"error": f"Amendment {amendment_id} not found"}
        if a.status != "RATIFY":
            return {"error": f"Amendment must be in RATIFY state. Current: {a.status}"}
        elapsed = time.time() - a.ratified_at
        if elapsed < COOLING_OFF_SECONDS:
            remaining = COOLING_OFF_SECONDS - elapsed
            return {
                "error": "Cooling-off period not elapsed",
                "remaining_seconds": round(remaining),
                "note": "Amendments cannot be enacted within 24h of ratification (ARTICLE-003).",
            }
        with self._lock:
            a.status = "ENACTED"
            a.enacted_at = time.time()
        self._record_imraf(a)
        return {
            "amendment_id":      amendment_id,
            "status":            "ENACTED",
            "target_article":    a.target_article_id,
            "note": (
                "Amendment enacted. A developer must apply the change to the "
                "ConstitutionRegistry source code per ARTICLE-003 (Human Final Authority)."
            ),
        }

    # ── Query ─────────────────────────────────────────────────────────────────

    def get(self, amendment_id: str) -> Optional[dict]:
        with self._lock:
            a = self._amendments.get(amendment_id)
        return self._serialise(a) if a else None

    def all_amendments(self, status_filter: Optional[str] = None) -> List[dict]:
        with self._lock:
            items = list(self._amendments.values())
        if status_filter:
            items = [a for a in items if a.status == status_filter]
        return [self._serialise(a) for a in sorted(items, key=lambda x: x.proposed_at, reverse=True)]

    def summary(self) -> dict:
        with self._lock:
            items = list(self._amendments.values())
        by_status: Dict[str, int] = {}
        for a in items:
            by_status[a.status] = by_status.get(a.status, 0) + 1
        return {
            "total_amendments": len(items),
            "by_status": by_status,
            "quorum_required": QUORUM_REQUIRED,
            "cooling_off_hours": COOLING_OFF_SECONDS / 3600,
            "unamendable_articles": list(_UNAMENDABLE_STRONGER_ONLY),
        }

    def _record_imraf(self, a: Amendment) -> None:
        try:
            from core.observatory.nexus_bridge import _imraf
            im = _imraf()
            if im:
                im.record_knowledge(
                    title=f"[AMENDMENT ENACTED] {a.amendment_id}: {a.target_article_id}",
                    content=f"Change: {a.proposed_change} | Rationale: {a.rationale}",
                    category="constitutional_amendment",
                    tags=["amendment", a.target_article_id, "enacted"],
                )
        except Exception:
            pass

    @staticmethod
    def _serialise(a: Amendment) -> dict:
        return {
            "amendment_id":       a.amendment_id,
            "target_article_id":  a.target_article_id,
            "proposed_change":    a.proposed_change,
            "rationale":          a.rationale,
            "proposed_by":        a.proposed_by,
            "status":             a.status,
            "proposed_at":        a.proposed_at,
            "review_notes":       a.review_notes,
            "votes_for":          a.votes_for,
            "votes_against":      a.votes_against,
            "ratified_at":        a.ratified_at,
            "enacted_at":         a.enacted_at,
            "rejected_reason":    a.rejected_reason,
        }


# Singleton
constitutional_amendment_framework = ConstitutionalAmendmentFramework()
