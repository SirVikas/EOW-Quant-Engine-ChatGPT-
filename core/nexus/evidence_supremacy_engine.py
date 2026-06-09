"""
PHOENIX NEXUS — Evidence Supremacy Automation Engine  [GAP-017]

Enforces the Evidence Supremacy Doctrine automatically:

  "No governance decision is made without verifiable evidence."

The engine intercepts governance proposals and:
  1. Checks whether sufficient evidence exists in the Trust Evidence Warehouse
  2. Checks whether the accuracy threshold is met for the relevant pillar
  3. Issues PERMIT / HOLD / BLOCK verdict
  4. Records every enforcement decision for audit

BLOCK scenarios:
  - Proposed trust promotion with insufficient evidence count
  - AEG promotion with sandbox accuracy below threshold
  - Amendment proposal without governance replay evidence
  - Constitutional change without court precedent

This closes the governance loop:
  Evidence must precede action — not follow it.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


VERDICT_PERMIT = "PERMIT"
VERDICT_HOLD   = "HOLD"
VERDICT_BLOCK  = "BLOCK"

EVIDENCE_FLOOR_FOR_TRUST_PROMOTION = 10
ACCURACY_FLOOR_FOR_AEG_PROMOTION   = 0.70
EVIDENCE_FLOOR_FOR_AMENDMENT       = 5     # governance replay events required


@dataclass
class SupremacyVerdict:
    check_id: str
    action_type: str         # "TRUST_PROMOTION" / "AEG_PROMOTION" / "AMENDMENT" / "RULING"
    subject_id: str
    verdict: str             # PERMIT / HOLD / BLOCK
    reasons: List[str]
    evidence_count: int
    evidence_required: int
    checked_at: float = field(default_factory=time.time)
    overridden_by: str = ""
    override_at: float = 0.0


class EvidenceSupremacyEngine:
    """
    Doctrine enforcement — every governance action must pass through here.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._verdicts: List[SupremacyVerdict] = []

    # ── Core Check API ─────────────────────────────────────────────────────────

    def check_trust_promotion(self, pillar: str, to_rung: str) -> SupremacyVerdict:
        reasons = []
        evidence_count = 0
        required = EVIDENCE_FLOOR_FOR_TRUST_PROMOTION

        try:
            from core.trust.trust_evidence_warehouse import trust_evidence_warehouse as _tew
            audit = _tew.pillar_audit(pillar)
            evidence_count = audit.get("total", 0)
            accuracy = audit.get("accuracy", 0.0) or 0.0
            if evidence_count < required:
                reasons.append(f"Insufficient evidence: {evidence_count} < {required} required")
            else:
                reasons.append(f"Evidence sufficient: {evidence_count} records")
            if accuracy < 0.50:
                reasons.append(f"Accuracy {accuracy:.1%} below 50% floor for promotion")
        except Exception as e:
            reasons.append(f"Evidence check failed: {e}")

        verdict = VERDICT_BLOCK if reasons and any("Insufficient" in r or "below" in r for r in reasons) else VERDICT_PERMIT
        return self._record(
            action_type="TRUST_PROMOTION",
            subject_id=f"{pillar}→{to_rung}",
            verdict=verdict,
            reasons=reasons,
            evidence_count=evidence_count,
            evidence_required=required,
        )

    def check_aeg_promotion(self, rec_type: str) -> SupremacyVerdict:
        reasons = []
        evidence_count = 0
        required = 20

        try:
            from core.nexus.aeg_pipeline.aeg_sandbox_stats import aeg_sandbox_stats as _ass
            stats = _ass.stats_for(rec_type)
            evidence_count = stats.get("samples_with_outcome", 0)
            accuracy = stats.get("accuracy") or 0.0
            if evidence_count < required:
                reasons.append(f"Sandbox samples {evidence_count} < {required} minimum")
            if accuracy < ACCURACY_FLOOR_FOR_AEG_PROMOTION:
                reasons.append(f"Sandbox accuracy {accuracy:.1%} < {ACCURACY_FLOOR_FOR_AEG_PROMOTION:.0%}")
            if not reasons:
                reasons.append(f"Evidence sufficient: {evidence_count} samples at {accuracy:.1%} accuracy")
        except Exception as e:
            reasons.append(f"AEG evidence check failed: {e}")

        verdict = VERDICT_BLOCK if any("minimum" in r or "accuracy" in r.lower() and "<" in r for r in reasons) else VERDICT_PERMIT
        return self._record(
            action_type="AEG_PROMOTION",
            subject_id=rec_type,
            verdict=verdict,
            reasons=reasons,
            evidence_count=evidence_count,
            evidence_required=required,
        )

    def check_amendment(self, article_id: str, amendment_type: str) -> SupremacyVerdict:
        reasons = []
        evidence_count = 0
        required = EVIDENCE_FLOOR_FOR_AMENDMENT

        try:
            from core.cortex.governance_replay import governance_replay
            timeline = governance_replay.replay_timeline(limit=500)
            evidence_count = sum(1 for e in timeline if article_id in str(e.get("context", "")))
            if evidence_count < required:
                reasons.append(f"Governance replay evidence: {evidence_count} < {required} required for amendment")
            else:
                reasons.append(f"Amendment evidence sufficient: {evidence_count} governance events")
        except Exception as e:
            reasons.append(f"Amendment evidence check failed: {e}")

        # Unamendable article check
        if article_id in ("ARTICLE-001", "ARTICLE-004") and "strengthen" not in amendment_type.lower():
            reasons.append(f"{article_id} is unamendable in weakening direction — BLOCK")
            verdict = VERDICT_BLOCK
        elif any("< required" in r for r in reasons):
            verdict = VERDICT_HOLD
        else:
            verdict = VERDICT_PERMIT

        return self._record(
            action_type="AMENDMENT",
            subject_id=f"{article_id}:{amendment_type}",
            verdict=verdict,
            reasons=reasons,
            evidence_count=evidence_count,
            evidence_required=required,
        )

    def check_governance_ruling(self, case_id: str, article_ids: List[str]) -> SupremacyVerdict:
        reasons = []
        evidence_count = 0
        required = 1

        try:
            from core.cortex.constitutional_court import constitutional_court
            case = constitutional_court.get_case(case_id)
            if case:
                evidence_count = len(case.get("evidence", {}))
                if evidence_count >= required:
                    reasons.append(f"Case evidence present: {evidence_count} items")
                else:
                    reasons.append("Case has no supporting evidence — BLOCK")
            else:
                reasons.append(f"Case '{case_id}' not found — BLOCK")
        except Exception as e:
            reasons.append(f"Ruling evidence check failed: {e}")

        verdict = VERDICT_BLOCK if any("BLOCK" in r for r in reasons) else VERDICT_PERMIT
        return self._record(
            action_type="RULING",
            subject_id=case_id,
            verdict=verdict,
            reasons=reasons,
            evidence_count=evidence_count,
            evidence_required=required,
        )

    def override_verdict(self, check_id: str, overridden_by: str) -> dict:
        with self._lock:
            v = next((x for x in self._verdicts if x.check_id == check_id), None)
        if not v:
            return {"error": f"Verdict '{check_id}' not found"}
        v.overridden_by = overridden_by
        v.override_at = time.time()
        v.verdict = VERDICT_PERMIT
        v.reasons.append(f"[OVERRIDE by {overridden_by}]")
        return {"overridden": True, "check_id": check_id}

    # ── Query ─────────────────────────────────────────────────────────────────

    def recent_verdicts(self, limit: int = 50) -> List[dict]:
        with self._lock:
            items = list(self._verdicts)
        return [self._ser(v) for v in sorted(items, key=lambda x: x.checked_at, reverse=True)[:limit]]

    def blocked_actions(self) -> List[dict]:
        with self._lock:
            items = [v for v in self._verdicts if v.verdict == VERDICT_BLOCK and not v.overridden_by]
        return [self._ser(v) for v in sorted(items, key=lambda x: x.checked_at, reverse=True)]

    def summary(self) -> dict:
        with self._lock:
            items = list(self._verdicts)
        by_verdict: Dict[str, int] = {}
        for v in items:
            by_verdict[v.verdict] = by_verdict.get(v.verdict, 0) + 1
        return {
            "total_checks":    len(items),
            "by_verdict":      by_verdict,
            "overridden":      sum(1 for v in items if v.overridden_by),
            "doctrine":        "Evidence must precede action — not follow it",
            "active_blocks":   sum(1 for v in items if v.verdict == VERDICT_BLOCK and not v.overridden_by),
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _record(
        self,
        action_type: str,
        subject_id: str,
        verdict: str,
        reasons: List[str],
        evidence_count: int,
        evidence_required: int,
    ) -> SupremacyVerdict:
        v = SupremacyVerdict(
            check_id=f"ESE-{action_type[:3]}-{int(time.time()*1000)}",
            action_type=action_type,
            subject_id=subject_id,
            verdict=verdict,
            reasons=reasons,
            evidence_count=evidence_count,
            evidence_required=evidence_required,
        )
        with self._lock:
            self._verdicts.append(v)
            if len(self._verdicts) > 10_000:
                self._verdicts = self._verdicts[-10_000:]
        return v

    @staticmethod
    def _ser(v: SupremacyVerdict) -> dict:
        return {
            "check_id":         v.check_id,
            "action_type":      v.action_type,
            "subject_id":       v.subject_id,
            "verdict":          v.verdict,
            "reasons":          v.reasons,
            "evidence_count":   v.evidence_count,
            "evidence_required": v.evidence_required,
            "checked_at":       v.checked_at,
            "overridden_by":    v.overridden_by,
            "override_at":      v.override_at or None,
        }


# Singleton
evidence_supremacy_engine = EvidenceSupremacyEngine()
