"""
Governance Intelligence Engine.

Stateless scans over IMRAF records to detect contradictions, stale decisions,
and assumption drift. No persistent DB — computes fresh each call.
"""

from __future__ import annotations

import re
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
            title_lower = (rec.get("title") or "").lower()
            for word in title_lower.split():
                if len(word) > 4 and word.isalpha():
                    param_records.setdefault(word, []).append(rec)

        for param, recs in param_records.items():
            if len(recs) < 2:
                continue
            raised = [r for r in recs if any(kw in (r.get("title") or "").lower() for kw in ["raised", "increased", "bumped", "higher"])]
            lowered = [r for r in recs if any(kw in (r.get("title") or "").lower() for kw in ["lowered", "decreased", "reduced", "lower"])]
            if raised and lowered:
                a = raised[0]
                b = lowered[0]
                findings.append(ContradictionFinding(
                    param_name=param,
                    decision_a={"id": a.get("id"), "title": a.get("title"), "ts": a.get("ts")},
                    decision_b={"id": b.get("id"), "title": b.get("title"), "ts": b.get("ts")},
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
            decisions = imraf.timeline(category="DECISION", limit=500)
            decisions += imraf.timeline(category="GOVERNANCE", limit=200)
        except Exception as exc:
            logger.warning("GovernanceIntelligenceEngine.scan_stale_decisions error: %s", exc)
            return []

        for rec in decisions:
            rec_ts = rec.get("ts", 0) or 0
            if rec_ts >= cutoff_ms:
                continue
            age_days = int((now_ms - rec_ts) / _MS_PER_DAY)
            title = rec.get("title", "")
            findings.append(StaleFinding(
                record_id=rec.get("id", 0),
                title=title,
                category=rec.get("category", ""),
                age_days=age_days,
                last_referenced="unknown",
                recommendation=f"Review whether this decision ({title}) is still current — {age_days} days old.",
            ))

        return findings[:20]

    def scan_assumptions(self) -> List[AssumptionFinding]:
        return list(_TRACKED_ASSUMPTIONS)

    # ── Real contradiction detection (live IMRAF data) ────────────────────────

    def detect_real_contradictions(self) -> List[dict]:
        """
        Detect contradictions in DECISION records pulled live from IMRAF.

        Groups records by component metadata field, then within each component
        looks for pairs with opposite direction keywords or conflicting numeric
        parameter values.

        Returns list of dicts:
          {"component": str, "contradiction_type": str, "fact_a": str,
           "fact_b": str, "severity": "HIGH"|"MEDIUM"|"LOW"}
        """
        try:
            from core.institutional_memory.imraf_engine import imraf
        except ImportError:
            return []

        try:
            records = imraf.search(query="decision", limit=500)
        except Exception as exc:
            logger.warning("detect_real_contradictions: IMRAF search failed: %s", exc)
            return []

        # Group by component extracted from the data dict
        groups: Dict[str, list] = {}
        for rec in records:
            data = rec.get("data", {})
            component = ""
            if isinstance(data, dict):
                component = data.get("component", "") or ""
            if not component:
                component = "unknown"
            groups.setdefault(component, []).append(rec)

        findings: list = []

        # Opposite keyword pairs that signal conflicting decisions
        _OPPOSITE_PAIRS = [
            ("enabled", "disabled"),
            ("raised", "lowered"),
            ("increased", "decreased"),
            ("activated", "deactivated"),
            ("added", "removed"),
        ]

        for component, recs in groups.items():
            if len(recs) < 2:
                continue

            for i in range(len(recs)):
                for j in range(i + 1, len(recs)):
                    a = recs[i]
                    b = recs[j]
                    title_a = (a.get("title") or "").lower()
                    title_b = (b.get("title") or "").lower()

                    # Check for opposite keyword pairs
                    for kw_pos, kw_neg in _OPPOSITE_PAIRS:
                        if kw_pos in title_a and kw_neg in title_b:
                            severity = "HIGH" if kw_pos in ("enabled", "activated") else "MEDIUM"
                            findings.append({
                                "component": component,
                                "contradiction_type": f"{kw_pos}/{kw_neg} conflict",
                                "fact_a": a.get("title", ""),
                                "fact_b": b.get("title", ""),
                                "severity": severity,
                            })
                            break
                        if kw_neg in title_a and kw_pos in title_b:
                            severity = "HIGH" if kw_pos in ("enabled", "activated") else "MEDIUM"
                            findings.append({
                                "component": component,
                                "contradiction_type": f"{kw_neg}/{kw_pos} conflict",
                                "fact_a": a.get("title", ""),
                                "fact_b": b.get("title", ""),
                                "severity": severity,
                            })
                            break

                    # Numeric parameter value conflicts: param=X in one vs param=Y in other
                    param_vals_a = {m.group(1).lower(): m.group(2)
                                    for m in re.finditer(r"(\w+)=(\d+\.?\d*)", title_a)}
                    param_vals_b = {m.group(1).lower(): m.group(2)
                                    for m in re.finditer(r"(\w+)=(\d+\.?\d*)", title_b)}
                    for param, val_a in param_vals_a.items():
                        if param in param_vals_b and param_vals_b[param] != val_a:
                            findings.append({
                                "component": component,
                                "contradiction_type": f"parameter value conflict: {param}",
                                "fact_a": a.get("title", ""),
                                "fact_b": b.get("title", ""),
                                "severity": "MEDIUM",
                            })

        # Deduplicate by (component, fact_a prefix, contradiction_type)
        seen: set = set()
        deduped: list = []
        for f in findings:
            key = (f["component"], f["fact_a"][:60], f["contradiction_type"])
            if key not in seen:
                seen.add(key)
                deduped.append(f)

        return deduped[:30]

    def detect_stale_assumptions(self) -> List[dict]:
        """
        Detect DECISION records whose engine_ver is more than 5 minor versions
        behind the current APP_VERSION.

        Returns list of dicts:
          {"content": str, "version": str, "age_versions": int, "component": str}
        """
        try:
            from core.institutional_memory.imraf_engine import imraf
        except ImportError:
            return []

        try:
            from config import APP_VERSION as _APP_VER
        except Exception:
            _APP_VER = "0.0.0"

        def _parse_minor(vstr: str):
            m = re.search(r"\d+\.(\d+)", vstr)
            return int(m.group(1)) if m else None

        current_minor = _parse_minor(_APP_VER)
        if current_minor is None:
            return []

        try:
            records = imraf.search(query="decision", limit=500)
        except Exception as exc:
            logger.warning("detect_stale_assumptions: IMRAF search failed: %s", exc)
            return []

        stale: list = []
        for rec in records:
            if rec.get("category") != "DECISION":
                continue
            engine_ver = rec.get("engine_ver", "")
            if not engine_ver:
                continue
            rec_minor = _parse_minor(engine_ver)
            if rec_minor is None:
                continue
            age = current_minor - rec_minor
            if age > 5:
                data = rec.get("data", {})
                component = ""
                if isinstance(data, dict):
                    component = data.get("component", "") or ""
                stale.append({
                    "content": rec.get("title", ""),
                    "version": engine_ver,
                    "age_versions": age,
                    "component": component or "unknown",
                })

        stale.sort(key=lambda x: x["age_versions"], reverse=True)
        return stale[:30]

    # ── Reports ───────────────────────────────────────────────────────────────

    def generate_report(self) -> dict:
        """
        Extended governance report that includes live contradiction detection.

        Extends generate_cleanup_report() with:
          real_contradictions      — output of detect_real_contradictions()
          stale_assumptions        — output of detect_stale_assumptions()
          real_contradiction_count — int
          stale_count              — int

        governance_health_score is adjusted downward for real contradictions
        and stale assumptions beyond those already counted in the base report.
        """
        base = self.generate_cleanup_report()
        real_contradictions = self.detect_real_contradictions()
        stale_assumptions = self.detect_stale_assumptions()

        real_count = len(real_contradictions)
        stale_count = len(stale_assumptions)

        # Each real contradiction costs 5 points; each stale assumption costs 1 point
        adjusted_score = max(0, base["governance_health_score"] - real_count * 5 - stale_count * 1)

        return {
            **base,
            "real_contradictions": real_contradictions,
            "stale_assumptions": stale_assumptions,
            "real_contradiction_count": real_count,
            "stale_count": stale_count,
            "governance_health_score": adjusted_score,
        }

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
