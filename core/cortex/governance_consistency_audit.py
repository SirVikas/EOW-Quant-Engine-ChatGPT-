"""
PHOENIX CORTEX — Governance Consistency Audit  [GAP-R6 / GAP-I]

Monthly governance audit that answers:
  "Did similar cases receive similar rulings?"
  "Are constitutional precedents being applied consistently?"
  "Is there drift in how articles are being interpreted?"

Produces monthly governance consistency reports covering:
  - Court ruling consistency (same article → same verdict?)
  - Case law application frequency
  - Stress test pass-rate trend
  - Amendment rate and impact
  - Conflict resolution consistency

Consistency scoring:
  HIGH       (≥85%)  — rulings are highly predictable from articles
  MODERATE   (60–85%) — some inconsistency, review recommended
  LOW        (<60%)  — inconsistency detected, constitutional review needed
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class GovernanceAuditReport:
    report_id: str
    period_label: str          # "2026-06", "2026-Q2", etc.
    period_start: float
    period_end: float
    total_governance_events: int
    court_cases: int
    court_rulings: int
    consistency_score: float   # 0–100
    consistency_label: str
    precedents_cited: int
    amendments_proposed: int
    amendments_enacted: int
    stress_test_pass_rate: Optional[float]
    conflict_events: int
    issues: List[str]
    generated_at: float = field(default_factory=time.time)


class GovernanceConsistencyAudit:
    """
    Generates monthly governance consistency reports across all CORTEX modules.
    """

    def __init__(self) -> None:
        self._reports: List[GovernanceAuditReport] = []

    def generate_report(self, period_label: Optional[str] = None, lookback_days: int = 30) -> GovernanceAuditReport:
        now = time.time()
        start = now - lookback_days * 86400
        label = period_label or time.strftime("%Y-%m")

        court_cases, court_rulings, precedents, amendments_proposed, amendments_enacted, conflicts = 0, 0, 0, 0, 0, 0
        total_events = 0
        issues = []
        stress_pass_rate = None

        try:
            from core.cortex.constitutional_court import constitutional_court
            cases = constitutional_court.all_cases()
            recent = [c for c in cases if c.get("filed_at", 0) >= start]
            court_cases = len(recent)
            court_rulings = sum(1 for c in recent if c.get("verdict"))
            # Consistency check: same article → same verdict?
            article_verdicts: Dict[str, List[str]] = {}
            for c in recent:
                for ev in c.get("evidence_summary", {}).keys():
                    if ev.startswith("ARTICLE"):
                        article_verdicts.setdefault(ev, []).append(c.get("verdict", ""))
            inconsistencies = []
            for art, verdicts in article_verdicts.items():
                unique = set(v for v in verdicts if v)
                if len(unique) > 1:
                    inconsistencies.append(f"{art}: mixed verdicts {unique}")
            if inconsistencies:
                issues.extend(inconsistencies)
        except Exception as e:
            issues.append(f"Court data unavailable: {e}")

        try:
            from core.cortex.governance_case_law import governance_case_law
            all_caselaw = governance_case_law.all_case_law()
            precedents = sum(1 for cl in all_caselaw if cl.get("recorded_at", 0) >= start)
        except Exception:
            pass

        try:
            from core.cortex.constitutional_amendment import constitutional_amendment
            all_amend = constitutional_amendment.all_amendments()
            amendments_proposed = sum(1 for a in all_amend if a.get("proposed_at", 0) >= start)
            amendments_enacted  = sum(1 for a in all_amend if a.get("stage") == "ENACTED" and a.get("proposed_at", 0) >= start)
        except Exception:
            pass

        try:
            from core.cortex.governance_stress_test import governance_stress_test
            latest = governance_stress_test.latest_run()
            if latest:
                stress_pass_rate = latest.get("consistency_score", 0) / 100.0
                if stress_pass_rate < 0.70:
                    issues.append(f"Stress test pass rate low: {stress_pass_rate:.0%}")
        except Exception:
            pass

        try:
            from core.cortex.governance_replay import governance_replay
            timeline = governance_replay.replay_timeline(limit=1000)
            conflicts = sum(1 for e in timeline if "conflict" in str(e.get("context", "")).lower() and e.get("timestamp", 0) >= start)
        except Exception:
            pass

        total_events = court_cases + precedents + amendments_proposed + conflicts

        # Consistency score heuristic
        if total_events == 0:
            score = 100.0
        else:
            deductions = len(issues) * 8
            if amendments_enacted > 2:
                deductions += 10
            score = max(0.0, 100.0 - deductions)
            if stress_pass_rate is not None:
                score = (score + stress_pass_rate * 100) / 2

        label_str = "HIGH" if score >= 85 else ("MODERATE" if score >= 60 else "LOW")

        report = GovernanceAuditReport(
            report_id=f"GAR-{label.replace('-', '')}-{int(now)}",
            period_label=label,
            period_start=start,
            period_end=now,
            total_governance_events=total_events,
            court_cases=court_cases,
            court_rulings=court_rulings,
            consistency_score=round(score, 1),
            consistency_label=label_str,
            precedents_cited=precedents,
            amendments_proposed=amendments_proposed,
            amendments_enacted=amendments_enacted,
            stress_test_pass_rate=stress_pass_rate,
            conflict_events=conflicts,
            issues=issues,
        )
        self._reports.append(report)
        return report

    def latest_report(self) -> Optional[dict]:
        if not self._reports:
            return None
        return self._ser(self._reports[-1])

    def all_reports(self) -> List[dict]:
        return [self._ser(r) for r in reversed(self._reports)]

    def trend(self) -> dict:
        if len(self._reports) < 2:
            return {"note": "Need at least 2 reports for trend"}
        scores = [r.consistency_score for r in self._reports[-6:]]
        return {
            "reports":    len(self._reports),
            "recent_scores": scores,
            "trend":      "IMPROVING" if scores[-1] > scores[0] else ("DEGRADING" if scores[-1] < scores[0] else "STABLE"),
        }

    @staticmethod
    def _ser(r: GovernanceAuditReport) -> dict:
        return {
            "report_id":              r.report_id,
            "period_label":           r.period_label,
            "period_start":           r.period_start,
            "period_end":             r.period_end,
            "total_governance_events": r.total_governance_events,
            "court_cases":            r.court_cases,
            "court_rulings":          r.court_rulings,
            "consistency_score":      r.consistency_score,
            "consistency_label":      r.consistency_label,
            "precedents_cited":       r.precedents_cited,
            "amendments_proposed":    r.amendments_proposed,
            "amendments_enacted":     r.amendments_enacted,
            "stress_test_pass_rate":  r.stress_test_pass_rate,
            "conflict_events":        r.conflict_events,
            "issues":                 r.issues,
            "generated_at":           r.generated_at,
        }


# Singleton
governance_consistency_audit = GovernanceConsistencyAudit()
