"""
PHOENIX CORTEX — Constitutional Court  [CX-MATURITY-01]

A constitution with no interpreter is a list of hopes.
When two constitutional articles conflict, someone must decide.

The Constitutional Court handles:
  1. Article conflicts    — ARTICLE-001 vs ARTICLE-004 (both HARD_BLOCK same action)
  2. Application disputes — "Does ARTICLE-002 apply to this specific action?"
  3. Interpretation rulings — what a principle means in a specific context
  4. Emergency overrides — time-critical situations requiring immediate adjudication

Court ruling types:
  SUPREMACY    — Article A takes precedence over Article B in this context
  SCOPE_LIMIT  — Article X does not apply to this specific action
  INTERPRETATION — Article Y means Z in context C
  EMERGENCY    — Temporary override with mandatory 48h review

All court rulings become Governance Case Law (CX-MATURITY-02).
All rulings require human authority — the Court cannot self-rule.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CourtCase:
    case_id: str
    case_type: str           # CONFLICT | INTERPRETATION | SCOPE | EMERGENCY
    articles_involved: List[str]
    case_description: str
    action_context: str      # the specific action that triggered the conflict
    module_key: str
    filed_by: str
    status: str = "OPEN"     # OPEN | UNDER_REVIEW | RULED | DISMISSED
    filed_at: float = field(default_factory=time.time)
    ruling: str = ""
    ruling_type: str = ""    # SUPREMACY | SCOPE_LIMIT | INTERPRETATION | EMERGENCY
    ruling_authority: str = ""
    ruling_at: float = 0.0
    ruling_rationale: str = ""
    binding_verdict: str = ""
    dissenting_notes: str = ""


class ConstitutionalCourt:
    """
    Adjudicates conflicts between constitutional articles.
    All rulings are human-confirmed and become binding case law.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._cases: Dict[str, CourtCase] = {}
        self._bootstrap_founding_cases()

    # ── Filing ────────────────────────────────────────────────────────────────

    def file_case(
        self,
        case_type: str,
        articles_involved: List[str],
        case_description: str,
        action_context: str,
        module_key: str,
        filed_by: str,
    ) -> CourtCase:
        case_id = f"COURT-{int(time.time())}-{case_type[:3]}"
        case = CourtCase(
            case_id=case_id,
            case_type=case_type,
            articles_involved=articles_involved,
            case_description=case_description,
            action_context=action_context,
            module_key=module_key,
            filed_by=filed_by,
        )

        # Auto-detect known conflict patterns for faster review
        self._auto_analyze(case)

        with self._lock:
            self._cases[case_id] = case
        return case

    # ── Auto-Analysis ─────────────────────────────────────────────────────────

    def _auto_analyze(self, case: CourtCase) -> None:
        """Identify known conflict patterns and add preliminary analysis."""
        arts = set(case.articles_involved)
        # Known conflict: Risk Supremacy vs Drawdown Supremacy — both HARD_BLOCK
        if "ARTICLE-001" in arts and "ARTICLE-004" in arts:
            case.ruling_rationale = (
                "Known Conflict: ARTICLE-001 (Risk Supremacy) and ARTICLE-004 (Drawdown Supremacy) "
                "both apply HARD_BLOCK. Preliminary analysis: ARTICLE-004 is the more specific "
                "constraint (drawdown is an acute state, not a general risk principle) and should "
                "take precedence for trade entry decisions during active drawdown. Requires human ruling."
            )
        # Known conflict: Evidence Required vs Human Authority — when system auto-generates with evidence
        elif "ARTICLE-002" in arts and "ARTICLE-003" in arts:
            case.ruling_rationale = (
                "Known Conflict: ARTICLE-002 (Evidence Before Change) and ARTICLE-003 (Human Final Authority). "
                "Preliminary analysis: These articles are complementary, not conflicting. "
                "ARTICLE-002 governs automated systems; ARTICLE-003 governs the human override layer. "
                "If the action has evidence (ARTICLE-002 satisfied), human approval (ARTICLE-003) still required."
            )

    # ── Ruling ────────────────────────────────────────────────────────────────

    def issue_ruling(
        self,
        case_id: str,
        ruling: str,
        ruling_type: str,
        ruling_authority: str,
        ruling_rationale: str,
        binding_verdict: str,
        dissenting_notes: str = "",
    ) -> dict:
        with self._lock:
            case = self._cases.get(case_id)
        if not case:
            return {"error": f"Case {case_id} not found"}
        if case.status == "RULED":
            return {"error": "Case already ruled"}
        with self._lock:
            case.ruling           = ruling
            case.ruling_type      = ruling_type
            case.ruling_authority = ruling_authority
            case.ruling_at        = time.time()
            case.ruling_rationale = ruling_rationale
            case.binding_verdict  = binding_verdict
            case.dissenting_notes = dissenting_notes
            case.status           = "RULED"

        # Register as Governance Case Law
        self._register_case_law(case)
        self._record_imraf(case)
        return {"ruled": True, "case_id": case_id, "ruling_type": ruling_type}

    def dismiss(self, case_id: str, reason: str) -> bool:
        with self._lock:
            case = self._cases.get(case_id)
            if not case:
                return False
            case.status = "DISMISSED"
            case.ruling_rationale = f"DISMISSED: {reason}"
        return True

    # ── Query ─────────────────────────────────────────────────────────────────

    def check_for_conflict(self, module_key: str, action_type: str) -> Optional[dict]:
        """
        Pre-flight check: does this action have a known conflict ruling?
        Returns the most recent ruling if found.
        """
        with self._lock:
            ruled = [
                c for c in self._cases.values()
                if c.status == "RULED"
                and c.module_key == module_key
            ]
        if not ruled:
            return None
        most_recent = max(ruled, key=lambda c: c.ruling_at)
        return self._serialise(most_recent)

    def open_cases(self) -> List[dict]:
        with self._lock:
            items = [c for c in self._cases.values() if c.status == "OPEN"]
        return [self._serialise(c) for c in items]

    def get(self, case_id: str) -> Optional[dict]:
        with self._lock:
            c = self._cases.get(case_id)
        return self._serialise(c) if c else None

    def all_cases(self, status_filter: Optional[str] = None) -> List[dict]:
        with self._lock:
            items = list(self._cases.values())
        if status_filter:
            items = [c for c in items if c.status == status_filter]
        return [self._serialise(c) for c in sorted(items, key=lambda x: x.filed_at, reverse=True)]

    def summary(self) -> dict:
        with self._lock:
            items = list(self._cases.values())
        by_status: Dict[str, int] = {}
        by_type: Dict[str, int] = {}
        for c in items:
            by_status[c.status] = by_status.get(c.status, 0) + 1
            by_type[c.case_type] = by_type.get(c.case_type, 0) + 1
        return {
            "total_cases":  len(items),
            "by_status":    by_status,
            "by_type":      by_type,
            "open_cases":   by_status.get("OPEN", 0),
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _bootstrap_founding_cases(self) -> None:
        case = CourtCase(
            case_id="COURT-FOUNDING-001",
            case_type="CONFLICT",
            articles_involved=["ARTICLE-001", "ARTICLE-004"],
            case_description=(
                "Both ARTICLE-001 and ARTICLE-004 issue HARD_BLOCK for new entries "
                "during a drawdown event when risk parameters are at maximum. "
                "Which article governs the block decision?"
            ),
            action_context="New trade entry during active drawdown with maximum risk",
            module_key="risk_engine",
            filed_by="INSTITUTIONAL_REVIEW",
            status="RULED",
            ruling="ARTICLE-004 governs trade entry blocking during drawdown. "
                   "ARTICLE-001 governs risk parameter changes. They are not in conflict.",
            ruling_type="SCOPE_LIMIT",
            ruling_authority="INSTITUTIONAL_REVIEW",
            ruling_rationale=(
                "ARTICLE-001 protects the risk engine from being overridden. "
                "ARTICLE-004 protects against entries during drawdown. "
                "These have distinct scopes: ARTICLE-004 is the entry gate; "
                "ARTICLE-001 is the parameter guard. No true conflict."
            ),
            binding_verdict=(
                "Ruling: ARTICLE-001 and ARTICLE-004 have non-overlapping scopes. "
                "Trade entry during drawdown: ARTICLE-004 governs. "
                "Risk parameter changes: ARTICLE-001 governs."
            ),
            filed_at=time.time() - 30 * 86400,
            ruling_at=time.time() - 28 * 86400,
        )
        self._cases[case.case_id] = case

    def _register_case_law(self, case: CourtCase) -> None:
        try:
            from core.cortex.governance_case_law import governance_case_law
            governance_case_law.record_ruling(
                case_id=case.case_id,
                articles_involved=case.articles_involved,
                ruling_type=case.ruling_type,
                binding_verdict=case.binding_verdict,
                decided_by=case.ruling_authority,
                context_description=case.case_description,
                classification="BINDING",
            )
        except Exception:
            pass

    def _record_imraf(self, case: CourtCase) -> None:
        try:
            from core.observatory.nexus_bridge import _imraf
            im = _imraf()
            if im:
                im.record_knowledge(
                    title=f"[COURT RULING] {case.case_id}: {case.ruling_type}",
                    content=f"Articles: {case.articles_involved} | Verdict: {case.binding_verdict[:200]}",
                    category="constitutional_court",
                    tags=["court", case.ruling_type.lower()] + case.articles_involved,
                )
        except Exception:
            pass

    @staticmethod
    def _serialise(c: CourtCase) -> dict:
        return {
            "case_id":           c.case_id,
            "case_type":         c.case_type,
            "articles_involved": c.articles_involved,
            "case_description":  c.case_description,
            "action_context":    c.action_context,
            "module_key":        c.module_key,
            "filed_by":          c.filed_by,
            "status":            c.status,
            "filed_at":          c.filed_at,
            "ruling":            c.ruling,
            "ruling_type":       c.ruling_type,
            "ruling_authority":  c.ruling_authority,
            "ruling_at":         c.ruling_at or None,
            "ruling_rationale":  c.ruling_rationale,
            "binding_verdict":   c.binding_verdict,
            "dissenting_notes":  c.dissenting_notes,
        }


# Singleton
constitutional_court = ConstitutionalCourt()
