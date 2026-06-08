"""
Governance Intelligence Engine.

Stateless scans over IMRAF records to detect contradictions, stale decisions,
and assumption drift. No persistent DB — computes fresh each call.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

import logging
logger = logging.getLogger(__name__)

_MS_PER_DAY = 86_400_000


@dataclass
class ContradictionFinding:
    param_name: str
    decision_a: dict
    decision_b: dict
    description: str
    severity: str  # LOW, MEDIUM, HIGH


@dataclass
class StaleFinding:
    record_id: int
    title: str
    category: str
    age_days: int
    last_referenced: str
    recommendation: str


@dataclass
class AssumptionFinding:
    assumption: str
    assumed_value: str
    current_concern: str
    source_record: str
    severity: str  # LOW, MEDIUM, HIGH, RESOLVED


_TRACKED_ASSUMPTIONS: List[AssumptionFinding] = [
    AssumptionFinding(
        assumption="avg winning trade = 0.09R",
        assumed_value="0.09R",
        current_concern="BREAKEVEN_TRIGGER_R=0.40 was set based on this assumption. If avg win has changed, BE trigger may need retuning.",
        source_record="FTD-037 + config.py comment",
        severity="HIGH",
    ),
    AssumptionFinding(
        assumption="TRENDING band floor at 46.0 stabilizes bands in 46-50 range",
        assumed_value="46.0",
        current_concern="Diagnostic shows TRENDING survival rate 86% >> 35% target. Floor raised from 44→46 hasn't stabilized bands — governor stuck at floor. Now lowered to 42.",
        source_record="adaptive_rsi_governor.py comment",
        severity="MEDIUM",
    ),
    AssumptionFinding(
        assumption="GENOME_MIN_AVG_R=0.50 only promotes DNA with meaningful avg R",
        assumed_value="0.50",
        current_concern="Fixed 2026-06-08: with 50% WR and 1.0R avg loss, avg_R>=0.50 requires avg_win>=2.0R. Gate was unreachable. Lowered to 0.20.",
        source_record="config.py GENOME_MIN_AVG_R comment",
        severity="RESOLVED",
    ),
    AssumptionFinding(
        assumption="LCC_PAUSE_MINUTES=30 is optimal cooldown duration",
        assumed_value="30 min",
        current_concern="32% of session skips are LCC_PAUSED (459 skips). Pause may be too long for LATE session volatility patterns.",
        source_record="config.py LCC_PAUSE_MINUTES",
        severity="MEDIUM",
    ),
    AssumptionFinding(
        assumption="PARTIAL_TP_R=1.5 is reachable",
        assumed_value="1.5R",
        current_concern="Lowered from 3.0 to 1.5. Peak-R analysis shows few trades exceed 1.5R. May still be too high for current market conditions.",
        source_record="config.py PARTIAL_TP_R",
        severity="LOW",
    ),
]

# Keywords that indicate parameter direction changes
_RAISE_KEYWORDS = ["raised", "increased", "bumped", "higher", "up to", "from.*to"]
_LOWER_KEYWORDS = ["lowered", "decreased", "reduced", "lower", "down to"]


class GovernanceIntelligenceEngine:

    def scan_contradictions(self) -> List[ContradictionFinding]:
        try:
            from core.institutional_memory.imraf_engine import imraf
        except ImportError:
            return []

        findings: List[ContradictionFinding] = []
        try:
            decisions = imraf.timeline(category="DECISION", limit=200)
            decisions += imraf.timeline(category="GOVERNANCE", limit=100)
        except Exception as exc:
            logger.warning("GovernanceIntelligenceEngine.scan_contradictions error: %s", exc)
            return []

        # Group by param keywords appearing in title
        param_records: Dict[str, list] = {}
        for rec in decisions:
            title_lower = rec.title.lower()
            for word in title_lower.split():
                if len(word) > 4 and word.isalpha():
                    param_records.setdefault(word, []).append(rec)

        import re
        for param, recs in param_records.items():
            if len(recs) < 2:
                continue
            raised = [r for r in recs if any(kw in r.title.lower() for kw in ["raised", "increased", "bumped", "higher"])]
            lowered = [r for r in recs if any(kw in r.title.lower() for kw in ["lowered", "decreased", "reduced", "lower"])]
            if raised and lowered:
                a = raised[0]
                b = lowered[0]
                findings.append(ContradictionFinding(
                    param_name=param,
                    decision_a={"id": a.id, "title": a.title, "ts": a.ts},
                    decision_b={"id": b.id, "title": b.title, "ts": b.ts},
                    description=f"Param '{param}' was both raised and lowered across decisions — possible reversal confusion.",
                    severity="MEDIUM",
                ))

        # Deduplicate by param_name
        seen: set = set()
        deduped: List[ContradictionFinding] = []
        for f in findings:
            if f.param_name not in seen:
                seen.add(f.param_name)
                deduped.append(f)

        return deduped[:20]

    def scan_stale_decisions(self, max_age_days: int = 90) -> List[StaleFinding]:
        try:
            from core.institutional_memory.imraf_engine import imraf
        except ImportError:
            return []

        findings: List[StaleFinding] = []
        now_ms = int(time.time() * 1000)
        cutoff_ms = now_ms - (max_age_days * _MS_PER_DAY)

        try:
            decisions = imraf.get_all(category="DECISION")
            decisions += imraf.get_all(category="GOVERNANCE")
        except Exception as exc:
            logger.warning("GovernanceIntelligenceEngine.scan_stale_decisions error: %s", exc)
            return []

        for rec in decisions:
            if rec.ts >= cutoff_ms:
                continue
            age_days = int((now_ms - rec.ts) / _MS_PER_DAY)
            findings.append(StaleFinding(
                record_id=rec.id,
                title=rec.title,
                category=rec.category,
                age_days=age_days,
                last_referenced="unknown",
                recommendation=f"Review whether this decision ({rec.title}) is still current — {age_days} days old.",
            ))

        return findings[:20]

    def scan_assumptions(self) -> List[AssumptionFinding]:
        return list(_TRACKED_ASSUMPTIONS)

    def generate_cleanup_report(self) -> dict:
        contradictions = self.scan_contradictions()
        stale = self.scan_stale_decisions()
        assumptions = self.scan_assumptions()

        # Count by severity
        all_severities: List[str] = []
        for c in contradictions:
            all_severities.append(c.severity)
        for s in stale:
            all_severities.append("LOW")
        for a in assumptions:
            if a.severity != "RESOLVED":
                all_severities.append(a.severity)

        critical_count = all_severities.count("CRITICAL")
        high_count = all_severities.count("HIGH")
        medium_count = all_severities.count("MEDIUM")
        low_count = all_severities.count("LOW")

        health_score = max(0, 100 - critical_count * 20 - high_count * 10 - medium_count * 5 - low_count * 2)

        actions: List[str] = []
        if high_count:
            actions.append(f"Investigate {high_count} HIGH severity assumptions — these may affect live trading parameters.")
        if contradictions:
            actions.append(f"Resolve {len(contradictions)} potential parameter contradictions in IMRAF DECISION records.")
        if stale:
            actions.append(f"Review {len(stale)} decisions older than 90 days for continued relevance.")
        if not actions:
            actions.append("No urgent governance actions required.")

        return {
            "contradictions": [asdict(c) for c in contradictions],
            "stale_decisions": [asdict(s) for s in stale],
            "assumption_violations": [asdict(a) for a in assumptions],
            "total_issues": len(contradictions) + len(stale) + sum(1 for a in assumptions if a.severity not in ("RESOLVED", "LOW")),
            "critical_count": critical_count,
            "high_count": high_count,
            "recommended_actions": actions,
            "governance_health_score": health_score,
        }

    def get_stats(self) -> dict:
        report = self.generate_cleanup_report()
        return {
            "health_score": report["governance_health_score"],
            "total_issues": report["total_issues"],
            "high_count": report["high_count"],
            "scan_ts": int(time.time() * 1000),
        }
