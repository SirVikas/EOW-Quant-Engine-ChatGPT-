"""
PHOENIX CORTEX — Governance Case Law  [CX-MATURITY-02]

Precedents exist. Now they need legal weight.

Case Law classification:
  BINDING      — all future decisions in this context must follow this ruling
  PERSUASIVE   — strong guidance that may be overridden with justification
  ARCHIVED     — historical record, no longer active governance
  OVERRULED    — superseded by a newer ruling on the same matter

A case is OVERRULED when a higher-authority ruling contradicts it —
the old case remains in the registry as institutional memory, but is
flagged as no longer governing.

Case Law differs from Constitutional Precedents:
  - Constitutional Precedents are about what the constitution MEANS
  - Case Law is about what HAPPENED when it was applied in practice

Sources of Case Law:
  - Court rulings (CX-MATURITY-01)
  - Amendment proceedings
  - Governance replay analysis
  - Operator decisions that established a pattern
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CaseLawRecord:
    record_id: str
    case_id: str              # source case (court case or investigation)
    articles_involved: List[str]
    ruling_type: str          # SUPREMACY | SCOPE_LIMIT | INTERPRETATION | EMERGENCY
    binding_verdict: str
    decided_by: str
    context_description: str
    classification: str = "BINDING"   # BINDING | PERSUASIVE | ARCHIVED | OVERRULED
    overruled_by: str = ""
    created_at: float = field(default_factory=time.time)
    citation_count: int = 0   # how many times this ruling has been cited


class GovernanceCaseLaw:
    """
    Registry of governance case law — classified decisions that govern future rulings.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: Dict[str, CaseLawRecord] = {}
        self._bootstrap_founding_case_law()

    # ── Recording ─────────────────────────────────────────────────────────────

    def record_ruling(
        self,
        case_id: str,
        articles_involved: List[str],
        ruling_type: str,
        binding_verdict: str,
        decided_by: str,
        context_description: str,
        classification: str = "BINDING",
    ) -> CaseLawRecord:
        record_id = f"CL_{case_id}_{int(time.time())}"
        rec = CaseLawRecord(
            record_id=record_id,
            case_id=case_id,
            articles_involved=articles_involved,
            ruling_type=ruling_type,
            binding_verdict=binding_verdict,
            decided_by=decided_by,
            context_description=context_description,
            classification=classification,
        )
        with self._lock:
            self._records[record_id] = rec
        return rec

    def overrule(
        self,
        record_id: str,
        overruled_by_case_id: str,
        new_record_id: str,
        new_binding_verdict: str,
        decided_by: str,
        context_description: str,
    ) -> CaseLawRecord:
        with self._lock:
            old = self._records.get(record_id)
            if old:
                old.classification = "OVERRULED"
                old.overruled_by = overruled_by_case_id
        return self.record_ruling(
            case_id=overruled_by_case_id,
            articles_involved=old.articles_involved if old else [],
            ruling_type="INTERPRETATION",
            binding_verdict=new_binding_verdict,
            decided_by=decided_by,
            context_description=context_description,
            classification="BINDING",
        )

    def cite(self, record_id: str) -> bool:
        with self._lock:
            rec = self._records.get(record_id)
            if rec:
                rec.citation_count += 1
                return True
        return False

    def reclassify(self, record_id: str, new_classification: str) -> bool:
        if new_classification not in ("BINDING", "PERSUASIVE", "ARCHIVED", "OVERRULED"):
            return False
        with self._lock:
            rec = self._records.get(record_id)
            if rec:
                rec.classification = new_classification
                return True
        return False

    # ── Query ─────────────────────────────────────────────────────────────────

    def find_governing(self, articles: List[str], context: str = "") -> List[dict]:
        """Find BINDING case law for given articles."""
        with self._lock:
            items = [
                r for r in self._records.values()
                if r.classification == "BINDING"
                and any(a in r.articles_involved for a in articles)
            ]
        return [self._serialise(r) for r in sorted(items, key=lambda x: x.created_at, reverse=True)]

    def most_cited(self, n: int = 10) -> List[dict]:
        with self._lock:
            items = sorted(self._records.values(), key=lambda x: x.citation_count, reverse=True)
        return [self._serialise(r) for r in items[:n]]

    def get(self, record_id: str) -> Optional[dict]:
        with self._lock:
            r = self._records.get(record_id)
        return self._serialise(r) if r else None

    def all_records(self, classification_filter: Optional[str] = None) -> List[dict]:
        with self._lock:
            items = list(self._records.values())
        if classification_filter:
            items = [r for r in items if r.classification == classification_filter]
        return [self._serialise(r) for r in sorted(items, key=lambda x: x.created_at, reverse=True)]

    def summary(self) -> dict:
        with self._lock:
            items = list(self._records.values())
        by_class: Dict[str, int] = {}
        for r in items:
            by_class[r.classification] = by_class.get(r.classification, 0) + 1
        return {
            "total_records":  len(items),
            "by_classification": by_class,
            "binding":   by_class.get("BINDING", 0),
            "persuasive": by_class.get("PERSUASIVE", 0),
            "archived":  by_class.get("ARCHIVED", 0),
            "overruled": by_class.get("OVERRULED", 0),
        }

    def _bootstrap_founding_case_law(self) -> None:
        # From COURT-FOUNDING-001
        founding = CaseLawRecord(
            record_id="CL-FOUNDING-001",
            case_id="COURT-FOUNDING-001",
            articles_involved=["ARTICLE-001", "ARTICLE-004"],
            ruling_type="SCOPE_LIMIT",
            binding_verdict=(
                "ARTICLE-001 governs risk parameter changes. "
                "ARTICLE-004 governs trade entry during drawdown. "
                "These are non-overlapping scopes — no conflict."
            ),
            decided_by="INSTITUTIONAL_REVIEW",
            context_description="Risk Supremacy vs Drawdown Supremacy scope adjudication",
            classification="BINDING",
            created_at=time.time() - 28 * 86400,
            citation_count=0,
        )
        self._records[founding.record_id] = founding

    @staticmethod
    def _serialise(r: CaseLawRecord) -> dict:
        return {
            "record_id":          r.record_id,
            "case_id":            r.case_id,
            "articles_involved":  r.articles_involved,
            "ruling_type":        r.ruling_type,
            "binding_verdict":    r.binding_verdict,
            "decided_by":         r.decided_by,
            "context_description": r.context_description,
            "classification":     r.classification,
            "overruled_by":       r.overruled_by,
            "created_at":         r.created_at,
            "citation_count":     r.citation_count,
        }


# Singleton
governance_case_law = GovernanceCaseLaw()
