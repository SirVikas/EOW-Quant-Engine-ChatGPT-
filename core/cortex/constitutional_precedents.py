"""
PHOENIX CORTEX — Constitutional Precedents Registry  [CX-GAP-02]

A constitutional principle without precedent is untested theory.
A precedent without a constitution is ungrounded practice.

The Precedents Registry binds them: each precedent is a decided case
that interprets one or more constitutional articles in a specific context.
Future governance decisions that touch the same context are bound by these precedents.

Precedent status:
  BINDING   — future decisions in the same context cannot contradict this
  ADVISORY  — strong guidance, but not an absolute constraint
  SUPERSEDED — replaced by a newer precedent (the old record is preserved)

Source precedent: ATR Root Cause Investigation (from IMRAF record 118).
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ConstitutionalPrecedent:
    precedent_id: str
    title: str
    article_ids: List[str]         # which articles this interprets
    case_description: str          # what happened
    verdict: str                   # the institutional ruling
    precedent_type: str            # BINDING | ADVISORY
    decided_by: str                # human authority who decided
    context_tags: List[str]        # for lookup (e.g. ["atr", "regime"])
    status: str = "ACTIVE"         # ACTIVE | SUPERSEDED
    superseded_by: str = ""
    decided_at: float = field(default_factory=time.time)
    imraf_record: Optional[int] = None


class ConstitutionalPrecedentsRegistry:
    """
    Registry of decided constitutional cases.
    Future investigations and governance checks query this before ruling.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._precedents: Dict[str, ConstitutionalPrecedent] = {}
        self._bootstrap_founding_precedents()

    # ── Recording ─────────────────────────────────────────────────────────────

    def record(
        self,
        precedent_id: str,
        title: str,
        article_ids: List[str],
        case_description: str,
        verdict: str,
        precedent_type: str,
        decided_by: str,
        context_tags: Optional[List[str]] = None,
        imraf_record: Optional[int] = None,
    ) -> ConstitutionalPrecedent:
        with self._lock:
            if precedent_id in self._precedents:
                raise ValueError(f"Precedent {precedent_id} already exists. Use supersede() to replace.")
        p = ConstitutionalPrecedent(
            precedent_id=precedent_id,
            title=title,
            article_ids=article_ids,
            case_description=case_description,
            verdict=verdict,
            precedent_type=precedent_type,
            decided_by=decided_by,
            context_tags=context_tags or [],
            imraf_record=imraf_record,
        )
        with self._lock:
            self._precedents[precedent_id] = p
        self._record_imraf(p)
        return p

    def supersede(
        self,
        old_precedent_id: str,
        new_precedent_id: str,
        new_title: str,
        article_ids: List[str],
        case_description: str,
        verdict: str,
        decided_by: str,
        context_tags: Optional[List[str]] = None,
    ) -> ConstitutionalPrecedent:
        with self._lock:
            old = self._precedents.get(old_precedent_id)
            if old:
                old.status = "SUPERSEDED"
                old.superseded_by = new_precedent_id
        return self.record(
            precedent_id=new_precedent_id,
            title=new_title,
            article_ids=article_ids,
            case_description=case_description,
            verdict=verdict,
            precedent_type="BINDING",
            decided_by=decided_by,
            context_tags=context_tags,
        )

    # ── Lookup ────────────────────────────────────────────────────────────────

    def find_by_context(self, tags: List[str], article_id: Optional[str] = None) -> List[dict]:
        """Find active precedents matching tags or article."""
        with self._lock:
            items = [p for p in self._precedents.values() if p.status == "ACTIVE"]
        matches = []
        for p in items:
            if article_id and article_id in p.article_ids:
                matches.append(p)
                continue
            if any(t in p.context_tags for t in tags):
                matches.append(p)
        return [self._serialise(p) for p in matches]

    def binding_for_article(self, article_id: str) -> List[dict]:
        with self._lock:
            items = [
                p for p in self._precedents.values()
                if article_id in p.article_ids
                and p.precedent_type == "BINDING"
                and p.status == "ACTIVE"
            ]
        return [self._serialise(p) for p in items]

    def get(self, precedent_id: str) -> Optional[dict]:
        with self._lock:
            p = self._precedents.get(precedent_id)
        return self._serialise(p) if p else None

    def all_precedents(self, include_superseded: bool = False) -> List[dict]:
        with self._lock:
            items = list(self._precedents.values())
        if not include_superseded:
            items = [p for p in items if p.status == "ACTIVE"]
        return [self._serialise(p) for p in sorted(items, key=lambda x: x.decided_at, reverse=True)]

    def summary(self) -> dict:
        with self._lock:
            total = len(self._precedents)
            active = sum(1 for p in self._precedents.values() if p.status == "ACTIVE")
            binding = sum(1 for p in self._precedents.values() if p.precedent_type == "BINDING" and p.status == "ACTIVE")
        return {
            "total_precedents": total,
            "active":  active,
            "binding": binding,
            "advisory": active - binding,
            "superseded": total - active,
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _bootstrap_founding_precedents(self) -> None:
        p = ConstitutionalPrecedent(
            precedent_id="PREC-001",
            title="ATR Causation — Burden of Proof on Investigator",
            article_ids=["ARTICLE-008"],
            case_description=(
                "An investigation attributed losses to ATR calculation errors. "
                "Counterfactual analysis showed ATR values were correct — losses "
                "were caused by regime mismatch not detected at entry."
            ),
            verdict=(
                "ATR is not the primary cause of losses in this codebase. "
                "Any future investigation naming ATR as primary cause must first "
                "provide counterfactual evidence that removing ATR would have "
                "prevented the loss (ARTICLE-008 compliance)."
            ),
            precedent_type="BINDING",
            decided_by="INSTITUTIONAL_REVIEW",
            context_tags=["atr", "regime", "counterfactual", "root_cause"],
            imraf_record=118,
        )
        self._precedents[p.precedent_id] = p

    def _record_imraf(self, p: ConstitutionalPrecedent) -> None:
        try:
            from core.observatory.nexus_bridge import _imraf
            im = _imraf()
            if im:
                im.record_knowledge(
                    title=f"[PRECEDENT] {p.precedent_id}: {p.title}",
                    content=f"Articles: {p.article_ids} | Verdict: {p.verdict[:200]}",
                    category="constitutional_precedent",
                    tags=["precedent", p.precedent_type] + p.context_tags,
                )
        except Exception:
            pass

    @staticmethod
    def _serialise(p: ConstitutionalPrecedent) -> dict:
        return {
            "precedent_id":    p.precedent_id,
            "title":           p.title,
            "article_ids":     p.article_ids,
            "case_description": p.case_description,
            "verdict":         p.verdict,
            "precedent_type":  p.precedent_type,
            "decided_by":      p.decided_by,
            "context_tags":    p.context_tags,
            "status":          p.status,
            "superseded_by":   p.superseded_by,
            "decided_at":      p.decided_at,
            "imraf_record":    p.imraf_record,
        }


# Singleton
constitutional_precedents_registry = ConstitutionalPrecedentsRegistry()
