"""
Governance Intelligence Engine.

Stateless scans over IMRAF records to detect contradictions, stale decisions,
and assumption drift. No persistent DB — computes fresh each call.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any

import logging
logger = logging.getLogger(__name__)

_MS_PER_DAY = 86_400_000

# Known components — fallback when KGE MODULE nodes are unavailable
_KNOWN_COMPONENTS = [
    "trade_manager", "risk_engine", "alpha_context_memory", "data_lake",
    "pnl_calc", "genome_engine", "rl_engine", "signal_ecology",
    "loss_cluster", "safe_mode", "adaptive_scorer", "adaptive_rsi_governor",
    "regime_cartography", "trade_flow_monitor",
]


@dataclass
class DecisionLifecycle:
    decision_id: str
    state: str        # PROPOSED | APPROVED | ACTIVE | DEPRECATED | SUPERSEDED
    component: str
    version_introduced: str
    version_deprecated: str = ""
    superseded_by: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


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
            title_lower = (rec.get("title") or rec.get("search_text") or rec.get("data","")).lower()
            for word in title_lower.split():
                if len(word) > 4 and word.isalpha():
                    param_records.setdefault(word, []).append(rec)

        import re
        for param, recs in param_records.items():
            if len(recs) < 2:
                continue
            raised = [r for r in recs if any(kw in (r.get("title") or r.get("search_text","")).lower() for kw in ["raised", "increased", "bumped", "higher"])]
            lowered = [r for r in recs if any(kw in (r.get("title") or r.get("search_text","")).lower() for kw in ["lowered", "decreased", "reduced", "lower"])]
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
            decisions = imraf.timeline(category="DECISION", limit=500)
            decisions += imraf.timeline(category="GOVERNANCE", limit=100)
        except Exception as exc:
            logger.warning("GovernanceIntelligenceEngine.scan_stale_decisions error: %s", exc)
            return []

        for rec in decisions:
            _rec_ts = rec.get("ts", 0) if isinstance(rec, dict) else getattr(rec, "ts", 0)
            if _rec_ts >= cutoff_ms:
                continue
            age_days = int((now_ms - _rec_ts) / _MS_PER_DAY)
            findings.append(StaleFinding(
                record_id=rec.get("id",0) if isinstance(rec,dict) else getattr(rec,"id",0),
                title=rec.get("title","") if isinstance(rec,dict) else getattr(rec,"title",""),
                category=rec.get("category","") if isinstance(rec,dict) else getattr(rec,"category",""),
                age_days=age_days,
                last_referenced="unknown",
                recommendation=f"Review whether this decision is still current — {age_days} days old.",
            ))

        return findings[:20]

    def scan_assumptions(self) -> List[AssumptionFinding]:
        return list(_TRACKED_ASSUMPTIONS)

    # ── Decision Lifecycle State Machine ─────────────────────────────────────

    def build_lifecycle_registry(self) -> dict:
        """
        Fetch DECISION records from IMRAF and infer lifecycle state for each.
        Returns summary with total, by_state, and registry list.
        """
        try:
            from core.institutional_memory.imraf_engine import imraf
        except ImportError:
            return {"total": 0, "by_state": {}, "registry": []}

        try:
            records = imraf.timeline(category="DECISION", limit=500)
        except Exception as exc:
            logger.warning("build_lifecycle_registry: IMRAF error: %s", exc)
            return {"total": 0, "by_state": {}, "registry": []}

        registry: List[DecisionLifecycle] = []
        for rec in records:
            # rec may be dict or object depending on IMRAF version in use
            if isinstance(rec, dict):
                rec_id = str(rec.get("id", ""))
                title = (rec.get("title") or "").lower()
                data = rec.get("data", {})
                engine_ver = rec.get("engine_ver", "") or ""
                tags = rec.get("tags", [])
            else:
                rec_id = str(getattr(rec, "id", ""))
                title = (getattr(rec, "title", "") or "").lower()
                data = getattr(rec, "data", {})
                engine_ver = getattr(rec, "engine_ver", "") or ""
                tags = getattr(rec, "tags", [])

            component = ""
            if isinstance(data, dict):
                component = data.get("component", "") or ""

            # Infer state from content
            if "disabled" in title or "deprecated" in title:
                state = "DEPRECATED"
            elif "re-enabled" in title or "reverted" in title:
                state = "ACTIVE"
            elif "superseded" in title or "replaced by" in title:
                state = "SUPERSEDED"
            else:
                state = "ACTIVE"

            registry.append(DecisionLifecycle(
                decision_id=rec_id,
                state=state,
                component=component or "unknown",
                version_introduced=engine_ver,
            ))

        by_state: Dict[str, int] = {}
        for dl in registry:
            by_state[dl.state] = by_state.get(dl.state, 0) + 1

        return {
            "total": len(registry),
            "by_state": by_state,
            "registry": [dl.to_dict() for dl in registry],
        }

    # ── Contradiction Escalation ──────────────────────────────────────────────

    def detect_real_contradictions(self) -> List[dict]:
        """
        Detect contradictions in DECISION records pulled live from IMRAF.

        Groups records by component metadata field, then looks for pairs
        with opposite direction keywords or conflicting numeric parameter values.
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

        groups: Dict[str, list] = {}
        for rec in records:
            if isinstance(rec, dict):
                data = rec.get("data", {})
                component = data.get("component", "") if isinstance(data, dict) else ""
                title = rec.get("title", "") or ""
            else:
                data = getattr(rec, "data", {})
                component = data.get("component", "") if isinstance(data, dict) else ""
                title = getattr(rec, "title", "") or ""
            if not component:
                component = "unknown"
            groups.setdefault(component, []).append({"title": title, "raw": rec})

        _OPPOSITE_PAIRS = [
            ("enabled", "disabled"),
            ("raised", "lowered"),
            ("increased", "decreased"),
            ("activated", "deactivated"),
            ("added", "removed"),
        ]

        findings: list = []
        for component, recs in groups.items():
            if len(recs) < 2:
                continue
            for i in range(len(recs)):
                for j in range(i + 1, len(recs)):
                    title_a = recs[i]["title"].lower()
                    title_b = recs[j]["title"].lower()
                    for kw_pos, kw_neg in _OPPOSITE_PAIRS:
                        if kw_pos in title_a and kw_neg in title_b:
                            severity = "HIGH" if kw_pos in ("enabled", "activated") else "MEDIUM"
                            findings.append({
                                "component": component,
                                "contradiction_type": f"{kw_pos}/{kw_neg} conflict",
                                "fact_a": recs[i]["title"],
                                "fact_b": recs[j]["title"],
                                "severity": severity,
                            })
                            break
                        if kw_neg in title_a and kw_pos in title_b:
                            severity = "HIGH" if kw_pos in ("enabled", "activated") else "MEDIUM"
                            findings.append({
                                "component": component,
                                "contradiction_type": f"{kw_neg}/{kw_pos} conflict",
                                "fact_a": recs[i]["title"],
                                "fact_b": recs[j]["title"],
                                "severity": severity,
                            })
                            break

                    param_vals_a = {m.group(1).lower(): m.group(2)
                                    for m in re.finditer(r"(\w+)=(\d+\.?\d*)", title_a)}
                    param_vals_b = {m.group(1).lower(): m.group(2)
                                    for m in re.finditer(r"(\w+)=(\d+\.?\d*)", title_b)}
                    for param, val_a in param_vals_a.items():
                        if param in param_vals_b and param_vals_b[param] != val_a:
                            findings.append({
                                "component": component,
                                "contradiction_type": f"parameter value conflict: {param}",
                                "fact_a": recs[i]["title"],
                                "fact_b": recs[j]["title"],
                                "severity": "MEDIUM",
                            })

        seen: set = set()
        deduped: list = []
        for f in findings:
            key = (f["component"], f["fact_a"][:60], f["contradiction_type"])
            if key not in seen:
                seen.add(key)
                deduped.append(f)

        return deduped[:30]

    def escalate_contradictions_to_imraf(self) -> int:
        """
        For each HIGH/MEDIUM contradiction found, archive as INCIDENT if not
        already present in IMRAF. Returns count of new incidents created.
        """
        contradictions = self.detect_real_contradictions()
        if not contradictions:
            return 0

        try:
            from core.institutional_memory.imraf_engine import imraf, Category
        except ImportError:
            return 0

        created = 0
        for c in contradictions:
            if c["severity"] not in ("HIGH", "MEDIUM"):
                continue
            component = c["component"]
            contradiction_type = c["contradiction_type"]
            # Idempotency check — skip if already archived
            search_key = f"GOVERNANCE_ALERT: Contradiction detected in {component}"
            existing = imraf.search(query=search_key, limit=1)
            if existing:
                continue
            content = f"GOVERNANCE_ALERT: Contradiction detected in {component} — {contradiction_type}"
            try:
                imraf.record(
                    category=Category.INCIDENT,
                    title=content[:200],
                    data={"content": content, "component": component,
                          "contradiction_type": contradiction_type,
                          "severity": c["severity"]},
                    tags=["governance", "contradiction", "alert", component],
                )
                created += 1
            except Exception as exc:
                logger.warning("escalate_contradictions_to_imraf: record failed: %s", exc)

        return created

    # ── Governance Coverage Report ────────────────────────────────────────────

    def governance_coverage_report(self) -> dict:
        """
        Groups DECISION + GOVERNANCE records by component and computes coverage
        against the known component list (from KGE MODULE nodes if available,
        else the hardcoded 14-component list).
        """
        try:
            from core.institutional_memory.imraf_engine import imraf
        except ImportError:
            return {
                "covered_components": 0, "uncovered_components": len(_KNOWN_COMPONENTS),
                "coverage_pct": 0.0, "covered": [], "uncovered": list(_KNOWN_COMPONENTS),
                "lifecycle_summary": {},
            }

        try:
            records = imraf.timeline(category="DECISION", limit=500)
            records += imraf.timeline(category="GOVERNANCE", limit=200)
        except Exception as exc:
            logger.warning("governance_coverage_report: IMRAF error: %s", exc)
            records = []

        covered_set: set = set()
        for rec in records:
            if isinstance(rec, dict):
                data = rec.get("data", {})
            else:
                data = getattr(rec, "data", {})
            component = ""
            if isinstance(data, dict):
                component = data.get("component", "") or ""
            if component and component != "unknown":
                covered_set.add(component)

        # Try KGE MODULE nodes first
        all_components = list(_KNOWN_COMPONENTS)
        try:
            from core.nexus.kge.kge_engine import kge
            with kge._connect() as con:
                rows = con.execute(
                    "SELECT node_id FROM kg_nodes WHERE node_type='MODULE'"
                ).fetchall()
            if rows:
                all_components = [r[0].split(":")[-1] for r in rows]
        except Exception:
            pass

        uncovered = [c for c in all_components if c not in covered_set]
        covered_list = [c for c in all_components if c in covered_set]
        coverage_pct = round(len(covered_list) / len(all_components) * 100, 2) if all_components else 0.0

        lifecycle = self.build_lifecycle_registry()
        lifecycle_summary = lifecycle.get("by_state", {})

        return {
            "covered_components": len(covered_list),
            "uncovered_components": len(uncovered),
            "coverage_pct": coverage_pct,
            "covered": covered_list,
            "uncovered": uncovered,
            "lifecycle_summary": lifecycle_summary,
        }

    def generate_report(self) -> dict:
        """
        Full governance report: base cleanup report extended with lifecycle,
        coverage, and escalated contradiction metrics.
        """
        base = self.generate_cleanup_report()
        coverage = self.governance_coverage_report()
        escalated = self.escalate_contradictions_to_imraf()

        return {
            **base,
            "lifecycle_summary": coverage["lifecycle_summary"],
            "coverage_pct": coverage["coverage_pct"],
            "escalated_contradictions": escalated,
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
