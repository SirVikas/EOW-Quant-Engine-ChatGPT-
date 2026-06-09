"""
PHOENIX CORTEX — Constitutional Commentary Layer  [GAP-010]

Legal-style commentary for each constitutional article:
  - Meaning: what does this article actually mean?
  - Interpretation: how is it applied in edge cases?
  - Scope: what falls inside / outside this article?
  - Exceptions: known carved-out scenarios
  - Case Law References: precedents that interpret this article

This is the equivalent of legal annotations that accumulate
as the constitution is interpreted through real governance decisions.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ArticleCommentary:
    article_id: str
    meaning: str
    interpretation: str
    scope_inside: List[str]
    scope_outside: List[str]
    exceptions: List[str]
    case_law_refs: List[str]
    authored_by: str = "SYSTEM"
    created_at: float = field(default_factory=time.time)
    last_updated_at: float = field(default_factory=time.time)
    amendment_notes: List[str] = field(default_factory=list)


@dataclass
class CommentaryAnnotation:
    annotation_id: str
    article_id: str
    annotation_type: str    # "INTERPRETATION" / "EXCEPTION" / "SCOPE" / "CASE_LAW"
    content: str
    source: str             # case_id, amendment_id, "HUMAN:<name>", "AEG"
    added_at: float = field(default_factory=time.time)


# Founding commentary seeded at initialization
_FOUNDING_COMMENTARY = {
    "ARTICLE-001": {
        "meaning": "Risk management is the supreme constitutional principle. No other principle can override it.",
        "interpretation": "When any governance decision conflicts with risk management, risk management wins unconditionally.",
        "scope_inside": ["Position sizing", "Stop loss enforcement", "Drawdown limits", "Leverage caps"],
        "scope_outside": ["Recommendation quality metrics", "Investigation methodology", "Attribution accuracy"],
        "exceptions": ["None — ARTICLE-001 is unamendable to reduce its strength"],
        "case_law_refs": ["COURT-FOUNDING-001", "CL-FOUNDING-001"],
    },
    "ARTICLE-002": {
        "meaning": "Every governance decision must be backed by verifiable evidence, not assumption.",
        "interpretation": "Evidence must exist before a claim is made — not gathered afterwards to justify it.",
        "scope_inside": ["Trade attribution", "Strategy performance claims", "Risk factor identification"],
        "scope_outside": ["Emergency risk actions (which fall under ARTICLE-001)"],
        "exceptions": ["Time-critical risk events may proceed under ARTICLE-001 and be evidenced retroactively"],
        "case_law_refs": [],
    },
    "ARTICLE-003": {
        "meaning": "Before attributing outcomes to a strategy, the counterfactual must be modelled.",
        "interpretation": "Would the same outcome have occurred without the strategy? If yes, the attribution is invalid.",
        "scope_inside": ["Strategy blame", "Strategy exoneration", "Performance attribution"],
        "scope_outside": ["Market-wide events (systematic risk by definition has no strategy counterfactual)"],
        "exceptions": ["ATR exoneration precedent (CASE-001): ATR cannot be blamed for volatility it measures"],
        "case_law_refs": ["CASE-001", "PREC-001"],
    },
    "ARTICLE-004": {
        "meaning": "Observatory analysis is scoped to observable market and system behavior only.",
        "interpretation": "Observatory cannot make governance decisions — it can only make observations and recommendations.",
        "scope_inside": ["Market data analysis", "Strategy behavior observation", "Recommendation generation"],
        "scope_outside": ["Constitutional amendments", "Governance rulings", "Risk limit changes"],
        "exceptions": ["None defined — scope limitation is absolute"],
        "case_law_refs": ["COURT-FOUNDING-001"],
    },
}


class ConstitutionalCommentary:
    """
    Living commentary layer — annotations accumulate as the constitution is interpreted.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._commentaries: Dict[str, ArticleCommentary] = {}
        self._annotations: List[CommentaryAnnotation] = []
        self._seed_founding()

    def _seed_founding(self) -> None:
        for article_id, data in _FOUNDING_COMMENTARY.items():
            c = ArticleCommentary(
                article_id=article_id,
                meaning=data["meaning"],
                interpretation=data["interpretation"],
                scope_inside=data["scope_inside"],
                scope_outside=data["scope_outside"],
                exceptions=data["exceptions"],
                case_law_refs=data["case_law_refs"],
                authored_by="SYSTEM",
                created_at=time.time() - 86400 * 365,
                last_updated_at=time.time() - 86400 * 365,
            )
            self._commentaries[article_id] = c

    # ── Commentary Management ─────────────────────────────────────────────────

    def get_commentary(self, article_id: str) -> Optional[dict]:
        with self._lock:
            c = self._commentaries.get(article_id)
        if not c:
            return None
        annotations = [a for a in self._annotations if a.article_id == article_id]
        return {**self._ser(c), "annotations": [self._ser_ann(a) for a in annotations]}

    def all_commentaries(self) -> List[dict]:
        with self._lock:
            items = list(self._commentaries.values())
        return [self.get_commentary(c.article_id) for c in items]

    def add_annotation(
        self,
        article_id: str,
        annotation_type: str,
        content: str,
        source: str = "SYSTEM",
    ) -> CommentaryAnnotation:
        ann = CommentaryAnnotation(
            annotation_id=f"ANN-{article_id}-{int(time.time()*1000)}",
            article_id=article_id,
            annotation_type=annotation_type,
            content=content,
            source=source,
        )
        with self._lock:
            self._annotations.append(ann)
            if article_id in self._commentaries:
                self._commentaries[article_id].last_updated_at = time.time()
        return ann

    def update_commentary(
        self,
        article_id: str,
        field_name: str,
        value,
        updated_by: str = "SYSTEM",
    ) -> dict:
        with self._lock:
            c = self._commentaries.get(article_id)
        if not c:
            return {"error": f"No commentary for '{article_id}'"}
        if hasattr(c, field_name):
            setattr(c, field_name, value)
            c.last_updated_at = time.time()
            c.amendment_notes.append(
                f"[{time.strftime('%Y-%m-%d')}] {field_name} updated by {updated_by}"
            )
            return {"updated": True, "article_id": article_id, "field": field_name}
        return {"error": f"Unknown field '{field_name}'"}

    def search(self, query: str) -> List[dict]:
        query = query.lower()
        results = []
        with self._lock:
            for c in self._commentaries.values():
                if (query in c.meaning.lower() or
                        query in c.interpretation.lower() or
                        any(query in s.lower() for s in c.scope_inside + c.scope_outside + c.exceptions)):
                    results.append(c.article_id)
        return [self.get_commentary(aid) for aid in results]

    @staticmethod
    def _ser(c: ArticleCommentary) -> dict:
        return {
            "article_id":      c.article_id,
            "meaning":         c.meaning,
            "interpretation":  c.interpretation,
            "scope_inside":    c.scope_inside,
            "scope_outside":   c.scope_outside,
            "exceptions":      c.exceptions,
            "case_law_refs":   c.case_law_refs,
            "authored_by":     c.authored_by,
            "created_at":      c.created_at,
            "last_updated_at": c.last_updated_at,
            "amendment_notes": c.amendment_notes,
        }

    @staticmethod
    def _ser_ann(a: CommentaryAnnotation) -> dict:
        return {
            "annotation_id":   a.annotation_id,
            "article_id":      a.article_id,
            "annotation_type": a.annotation_type,
            "content":         a.content,
            "source":          a.source,
            "added_at":        a.added_at,
        }


# Singleton
constitutional_commentary = ConstitutionalCommentary()
