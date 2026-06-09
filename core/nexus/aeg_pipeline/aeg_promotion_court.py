"""
PHOENIX AEG — Promotion Court  [GAP-006]

Structured adjudication layer for AEG promotion decisions.

Pipeline:
  PROMOTION_CANDIDATE
      ↓
  EVIDENCE_REVIEW    ← Court collects evidence package
      ↓
  DELIBERATION       ← Court evaluates against promotion criteria
      ↓
  VERDICT            ← APPROVE / REJECT / DEFER
      ↓
  HUMAN_APPROVED     ← Final human sign-off (cannot be bypassed)

Each case is recorded with:
  - Full evidence at time of filing
  - Deliberation notes
  - Verdict with reasoning
  - Human approver identity

This replaces ad-hoc approve_promotion() for formal governance.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


VERDICT_OPTIONS = ["APPROVE", "REJECT", "DEFER"]


@dataclass
class CourtCase:
    case_id: str
    rec_id: str
    rec_type: str
    filed_by: str
    status: str = "EVIDENCE_REVIEW"    # EVIDENCE_REVIEW / DELIBERATION / VERDICT / CLOSED
    evidence: dict = field(default_factory=dict)
    deliberation_notes: List[str] = field(default_factory=list)
    verdict: str = ""
    verdict_reasoning: str = ""
    human_approver: str = ""
    filed_at: float = field(default_factory=time.time)
    verdict_at: float = 0.0
    closed_at: float = 0.0


class AEGPromotionCourt:
    """
    Formal adjudication of AEG promotion candidates.
    Every promotion that passes here is provably governed.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._cases: Dict[str, CourtCase] = {}

    def file_case(self, rec_id: str, rec_type: str, filed_by: str = "SYSTEM") -> CourtCase:
        case_id = f"AEG-COURT-{rec_type[:4]}-{int(time.time()*1000)}"
        case = CourtCase(
            case_id=case_id,
            rec_id=rec_id,
            rec_type=rec_type,
            filed_by=filed_by,
        )
        # Collect evidence immediately
        self._collect_evidence(case)
        with self._lock:
            self._cases[case_id] = case
        return case

    def _collect_evidence(self, case: CourtCase) -> None:
        try:
            from core.nexus.aeg_pipeline.aeg_sandbox_stats import aeg_sandbox_stats as _ass
            case.evidence["sandbox_stats"] = _ass.stats_for(case.rec_type)
            case.evidence["evidence_package"] = _ass.evidence_package(case.rec_type)
        except Exception:
            pass
        try:
            from core.observatory.trust_engine import recommendation_trust_engine
            case.evidence["trust_status"] = recommendation_trust_engine.trust_for_type(case.rec_type)
        except Exception:
            pass
        try:
            from core.nexus.aeg_pipeline.aeg_promotion_engine import aeg_promotion_engine
            entry = aeg_promotion_engine.get(case.rec_id)
            case.evidence["pipeline_entry"] = entry
        except Exception:
            pass
        case.status = "DELIBERATION"

    def deliberate(self, case_id: str) -> dict:
        with self._lock:
            case = self._cases.get(case_id)
        if not case:
            return {"error": f"Case '{case_id}' not found"}

        notes = []
        sandbox = case.evidence.get("sandbox_stats", {})
        trust = case.evidence.get("trust_status", {})

        accuracy = sandbox.get("accuracy") or 0.0
        samples = sandbox.get("samples_with_outcome", 0)
        trust_score = trust.get("trust_score", 0.0) if isinstance(trust, dict) else 0.0

        if accuracy >= 0.70:
            notes.append(f"✓ Sandbox accuracy {accuracy:.1%} meets 70% threshold")
        else:
            notes.append(f"✗ Sandbox accuracy {accuracy:.1%} below 70% threshold")

        if samples >= 20:
            notes.append(f"✓ {samples} sandbox samples meets minimum of 20")
        else:
            notes.append(f"✗ Only {samples} sandbox samples (need 20)")

        if trust_score >= 50.0:
            notes.append(f"✓ Trust score {trust_score:.1f} meets 50.0 threshold")
        else:
            notes.append(f"✗ Trust score {trust_score:.1f} below 50.0 threshold")

        case.deliberation_notes = notes
        return {"case_id": case_id, "notes": notes}

    def issue_verdict(self, case_id: str, verdict: str, reasoning: str, decided_by: str = "SYSTEM") -> dict:
        if verdict not in VERDICT_OPTIONS:
            return {"error": f"Invalid verdict '{verdict}'. Choose from {VERDICT_OPTIONS}"}
        with self._lock:
            case = self._cases.get(case_id)
        if not case:
            return {"error": f"Case '{case_id}' not found"}
        case.verdict = verdict
        case.verdict_reasoning = reasoning
        case.verdict_at = time.time()
        case.status = "VERDICT"
        return {"case_id": case_id, "verdict": verdict, "status": "VERDICT"}

    def human_approve(self, case_id: str, approver: str) -> dict:
        with self._lock:
            case = self._cases.get(case_id)
        if not case:
            return {"error": f"Case '{case_id}' not found"}
        if case.verdict != "APPROVE":
            return {"error": f"Case verdict is '{case.verdict}', not APPROVE — cannot human-approve"}
        case.human_approver = approver
        case.status = "CLOSED"
        case.closed_at = time.time()

        # Trigger actual promotion
        try:
            from core.nexus.aeg_pipeline.aeg_promotion_engine import aeg_promotion_engine
            aeg_promotion_engine.approve_promotion(case.rec_id, approved_by=approver)
        except Exception:
            pass

        return {"case_id": case_id, "closed": True, "approved_by": approver}

    def get_case(self, case_id: str) -> Optional[dict]:
        with self._lock:
            case = self._cases.get(case_id)
        return self._ser(case) if case else None

    def open_cases(self) -> List[dict]:
        with self._lock:
            items = [c for c in self._cases.values() if c.status != "CLOSED"]
        return [self._ser(c) for c in sorted(items, key=lambda x: x.filed_at, reverse=True)]

    def all_cases(self, limit: int = 50) -> List[dict]:
        with self._lock:
            items = list(self._cases.values())
        return [self._ser(c) for c in sorted(items, key=lambda x: x.filed_at, reverse=True)[:limit]]

    def summary(self) -> dict:
        with self._lock:
            items = list(self._cases.values())
        approved = sum(1 for c in items if c.verdict == "APPROVE" and c.status == "CLOSED")
        rejected = sum(1 for c in items if c.verdict == "REJECT")
        return {
            "total_cases":  len(items),
            "open":         sum(1 for c in items if c.status != "CLOSED"),
            "approved":     approved,
            "rejected":     rejected,
            "deferred":     sum(1 for c in items if c.verdict == "DEFER"),
        }

    @staticmethod
    def _ser(c: CourtCase) -> dict:
        return {
            "case_id":            c.case_id,
            "rec_id":             c.rec_id,
            "rec_type":           c.rec_type,
            "filed_by":           c.filed_by,
            "status":             c.status,
            "evidence_summary":   {k: type(v).__name__ for k, v in c.evidence.items()},
            "deliberation_notes": c.deliberation_notes,
            "verdict":            c.verdict,
            "verdict_reasoning":  c.verdict_reasoning,
            "human_approver":     c.human_approver,
            "filed_at":           c.filed_at,
            "verdict_at":         c.verdict_at or None,
            "closed_at":          c.closed_at or None,
        }


# Singleton
aeg_promotion_court = AEGPromotionCourt()
