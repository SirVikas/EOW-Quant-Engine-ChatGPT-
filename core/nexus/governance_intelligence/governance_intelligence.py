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


def _rec_attr(rec: Any, attr: str, default: Any = "") -> Any:
    """Uniform attribute access for dict-or-object IMRAF records."""
    if isinstance(rec, dict):
        return rec.get(attr, default)
    return getattr(rec, attr, default)


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
            title_lower = (_rec_attr(rec, "title") or "").lower()
            for word in title_lower.split():
                if len(word) > 4 and word.isalpha():
                    param_records.setdefault(word, []).append(rec)

        for param, recs in param_records.items():
            if len(recs) < 2:
                continue
            raised = [r for r in recs if any(kw in (_rec_attr(r, "title") or "").lower() for kw in ["raised", "increased", "bumped", "higher"])]
            lowered = [r for r in recs if any(kw in (_rec_attr(r, "title") or "").lower() for kw in ["lowered", "decreased", "reduced", "lower"])]
            if raised and lowered:
                a = raised[0]
                b = lowered[0]
                findings.append(ContradictionFinding(
                    param_name=param,
                    decision_a={"id": _rec_attr(a, "id"), "title": _rec_attr(a, "title"), "ts": _rec_attr(a, "ts")},
                    decision_b={"id": _rec_attr(b, "id"), "title": _rec_attr(b, "title"), "ts": _rec_attr(b, "ts")},
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
            _rec_ts = _rec_attr(rec, "ts", 0)
            if _rec_ts >= cutoff_ms:
                continue
            age_days = int((now_ms - _rec_ts) / _MS_PER_DAY)
            findings.append(StaleFinding(
                record_id=_rec_attr(rec, "id", 0),
                title=_rec_attr(rec, "title", ""),
                category=_rec_attr(rec, "category", ""),
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
            rec_id = str(_rec_attr(rec, "id", ""))
            title = (_rec_attr(rec, "title", "") or "").lower()
            data = _rec_attr(rec, "data", {})
            engine_ver = _rec_attr(rec, "engine_ver", "") or ""

            component = ""
            if isinstance(data, dict):
                component = data.get("component", "") or ""
                # Respect explicit lifecycle state set by mark_decision_superseded
                if data.get("lifecycle_state") == "SUPERSEDED":
                    state = "SUPERSEDED"
                elif "disabled" in title or "deprecated" in title:
                    state = "DEPRECATED"
                elif "re-enabled" in title or "reverted" in title:
                    state = "ACTIVE"
                elif "superseded" in title or "replaced by" in title:
                    state = "SUPERSEDED"
                else:
                    state = "ACTIVE"
            else:
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

    # ── Contradiction Detection — Subject-Scoped ──────────────────────────────

    def detect_real_contradictions(self) -> List[dict]:
        """
        Detect genuine contradictions in DECISION/GOVERNANCE records from IMRAF.

        A contradiction exists ONLY when the SAME specific subject (strategy ID or
        parameter name) is both enabled AND disabled in records from the SAME
        component, and neither record is a sequential correction of the other.

        Sequential corrections (re-enabled, reversed, reverted) are NOT
        contradictions — they are temporal state progressions. Different strategies
        in different states (ALPHA_TCB disabled, ALPHA_PBE enabled) are also NOT
        contradictions.
        """
        try:
            from core.institutional_memory.imraf_engine import imraf
        except ImportError:
            return []

        try:
            records = imraf.timeline(category="DECISION", limit=500)
            records += imraf.timeline(category="GOVERNANCE", limit=200)
        except Exception as exc:
            logger.warning("detect_real_contradictions: IMRAF fetch failed: %s", exc)
            return []

        _DISABLE_WORDS = {"disabled", "removed", "deprecated", "deactivated"}
        _ENABLE_WORDS = {"enabled", "activated"}
        # Correction markers indicate a sequential fix, not a new independent decision.
        _CORRECTION_WORDS = {"re-enabled", "reenabled", "reverted", "reversed", "restored"}

        def _extract_subjects(title: str) -> List[str]:
            """Extract specific strategy IDs or long uppercase param names."""
            subjects: List[str] = []
            # Strategy IDs like ALPHA_TCB_v1, ALPHA_PBE_v1
            subjects += re.findall(r'ALPHA_\w+', title)
            # Uppercase parameter names >= 5 chars (e.g. BREAKEVEN_TRIGGER_R)
            subjects += re.findall(r'\b[A-Z][A-Z_]{4,}[A-Z]\b', title)
            return subjects

        def _is_superseded(rec: Any) -> bool:
            data = _rec_attr(rec, "data", {})
            return isinstance(data, dict) and data.get("lifecycle_state") == "SUPERSEDED"

        # Group records by component
        groups: Dict[str, list] = {}
        for rec in records:
            data = _rec_attr(rec, "data", {})
            component = data.get("component", "") if isinstance(data, dict) else ""
            title = _rec_attr(rec, "title", "") or ""
            rec_id = _rec_attr(rec, "id", 0)
            rec_ts = _rec_attr(rec, "ts", 0)
            if not component:
                component = "unknown"
            groups.setdefault(component, []).append({
                "id": rec_id, "title": title, "ts": rec_ts,
                "superseded": _is_superseded(rec), "raw": rec,
            })

        findings: list = []
        for component, recs in groups.items():
            if len(recs) < 2:
                continue

            # Build per-subject state map — only ACTIVE (non-superseded) records
            subject_states: Dict[str, list] = {}
            for r in recs:
                if r["superseded"]:
                    continue
                title_lower = r["title"].lower()
                subjects = _extract_subjects(r["title"])
                if not subjects:
                    continue
                is_disable = any(w in title_lower for w in _DISABLE_WORDS)
                is_enable = any(w in title_lower for w in _ENABLE_WORDS)
                is_correction = any(w in title_lower for w in _CORRECTION_WORDS)
                for subj in subjects:
                    subject_states.setdefault(subj, []).append({
                        "state": "disabled" if is_disable and not is_enable else
                                 "enabled" if is_enable else "other",
                        "is_correction": is_correction,
                        "record": r,
                    })

            # Flag only when the SAME subject has conflicting ACTIVE states and
            # no correction sequence explains the transition.
            for subj, states in subject_states.items():
                disabled_recs = [s for s in states if s["state"] == "disabled"]
                enabled_recs  = [s for s in states if s["state"] == "enabled"]
                if not disabled_recs or not enabled_recs:
                    continue
                # Sequential correction present → not a contradiction
                if any(s["is_correction"] for s in enabled_recs):
                    continue
                ra = disabled_recs[0]["record"]
                rb = enabled_recs[0]["record"]
                findings.append({
                    "component": component,
                    "subject": subj,
                    "contradiction_type": "enable/disable conflict",
                    "fact_a": ra["title"],
                    "fact_a_id": ra["id"],
                    "fact_b": rb["title"],
                    "fact_b_id": rb["id"],
                    "severity": "HIGH",
                })

        seen: set = set()
        deduped: list = []
        for f in findings:
            key = (f["component"], f["subject"])
            if key not in seen:
                seen.add(key)
                deduped.append(f)

        return deduped[:30]

    def mark_decision_superseded(self, record_id: int, superseded_by: str, reason: str) -> bool:
        """
        Mark an IMRAF record as SUPERSEDED by patching its data JSON in SQLite and
        archiving a GOVERNANCE record documenting the supersession.
        """
        try:
            from core.institutional_memory.imraf_engine import imraf, Category
        except ImportError:
            return False

        try:
            records = imraf.timeline(limit=2000)
            target = None
            for r in records:
                if _rec_attr(r, "id", 0) == record_id:
                    target = r
                    break
            if target is None:
                logger.warning("mark_decision_superseded: record %s not found", record_id)
                return False

            data = _rec_attr(target, "data", {})
            if not isinstance(data, dict):
                data = {}
            data["lifecycle_state"] = "SUPERSEDED"
            data["superseded_by"] = superseded_by
            data["superseded_reason"] = reason

            import sqlite3 as _sqlite3
            import json as _json
            from pathlib import Path
            db_path = Path("data/institutional_memory.db")
            with _sqlite3.connect(str(db_path)) as conn:
                conn.execute(
                    "UPDATE imraf_records SET data=? WHERE id=?",
                    (_json.dumps(data), record_id),
                )
                conn.commit()

            imraf.record(
                category=Category.GOVERNANCE,
                title=f"SUPERSEDED: record {record_id} → {superseded_by[:60]}",
                data={"content": reason, "superseded_record_id": record_id,
                      "superseded_by": superseded_by, "lifecycle_state": "GOVERNANCE_RESOLUTION"},
                tags=["governance", "superseded", "lifecycle"],
            )
            return True
        except Exception as exc:
            logger.warning("mark_decision_superseded: %s", exc)
            return False

    def resolve_contradiction(self, fact_a_id: int, fact_b_id: int, resolution: str) -> bool:
        """
        Resolve a contradiction between two IMRAF records.
        The older record is marked SUPERSEDED by the newer one, and a GOVERNANCE
        record documents the resolution.
        """
        try:
            from core.institutional_memory.imraf_engine import imraf, Category
        except ImportError:
            return False

        try:
            records = imraf.timeline(limit=2000)
            rec_map: Dict[int, Any] = {_rec_attr(r, "id", 0): r for r in records}

            rec_a = rec_map.get(fact_a_id)
            rec_b = rec_map.get(fact_b_id)
            if rec_a is None or rec_b is None:
                return False

            ts_a = _rec_attr(rec_a, "ts", 0)
            ts_b = _rec_attr(rec_b, "ts", 0)
            older_id = fact_a_id if ts_a <= ts_b else fact_b_id
            newer_title = (_rec_attr(rec_b, "title", "") if ts_a <= ts_b else _rec_attr(rec_a, "title", "")) or ""

            ok = self.mark_decision_superseded(older_id, newer_title[:80], resolution)
            if ok:
                try:
                    imraf.record(
                        category=Category.GOVERNANCE,
                        title=f"CONTRADICTION_RESOLVED: records {fact_a_id}/{fact_b_id}",
                        data={"content": resolution, "fact_a_id": fact_a_id,
                              "fact_b_id": fact_b_id, "older_superseded": older_id},
                        tags=["governance", "contradiction_resolved"],
                    )
                except Exception:
                    pass
            return ok
        except Exception as exc:
            logger.warning("resolve_contradiction: %s", exc)
            return False

    def auto_resolve_sequential_contradictions(self) -> int:
        """
        Find sequential correction pairs (re-enabled/reversed records) and mark
        the earlier record as SUPERSEDED so detect_real_contradictions() won't flag
        them. Returns count of auto-resolved pairs.
        """
        try:
            from core.institutional_memory.imraf_engine import imraf
        except ImportError:
            return 0

        _CORRECTION_WORDS = ["re-enabled", "reenabled", "reverted", "reversed", "restored"]
        _ALPHA_RE = re.compile(r'ALPHA_\w+')

        try:
            records = imraf.timeline(category="DECISION", limit=500)
        except Exception:
            return 0

        resolved = 0
        # Group by component
        groups: Dict[str, list] = {}
        for rec in records:
            data = _rec_attr(rec, "data", {})
            component = data.get("component", "") if isinstance(data, dict) else ""
            if not component:
                component = "unknown"
            if isinstance(data, dict) and data.get("lifecycle_state") == "SUPERSEDED":
                continue
            groups.setdefault(component, []).append({
                "id": _rec_attr(rec, "id", 0),
                "title": _rec_attr(rec, "title", "") or "",
                "ts": _rec_attr(rec, "ts", 0),
            })

        for _component, recs in groups.items():
            for rec in recs:
                title_lower = rec["title"].lower()
                if not any(cw in title_lower for cw in _CORRECTION_WORDS):
                    continue
                subjects = _ALPHA_RE.findall(rec["title"])
                if not subjects:
                    continue
                for subj in subjects:
                    for older in recs:
                        if older["id"] == rec["id"] or subj not in older["title"]:
                            continue
                        if older["ts"] >= rec["ts"]:
                            continue
                        ok = self.mark_decision_superseded(
                            older["id"],
                            rec["title"][:80],
                            f"Sequential correction: '{rec['title'][:80]}' supersedes this record",
                        )
                        if ok:
                            resolved += 1

        return resolved

    def detect_stale_assumptions(self) -> List[dict]:
        """
        Return DECISION records whose version is 5+ minor versions old vs APP_VERSION.
        """
        stale: List[dict] = []
        try:
            from core.institutional_memory.imraf_engine import imraf
            from config import APP_VERSION
            records = imraf.timeline(category=None, limit=1000)
        except Exception:
            return stale

        try:
            current_minor = int(APP_VERSION.split(".")[1]) if "." in APP_VERSION else 59
        except Exception:
            current_minor = 59

        for rec in records:
            content = ""
            data = _rec_attr(rec, "data", {})
            if isinstance(data, dict):
                content = data.get("content", "") or ""
            ver_matches = re.findall(r"v?(\d+)\.(\d+)\.\d+", content)
            for _major, minor_s in ver_matches:
                try:
                    minor = int(minor_s)
                    if current_minor - minor >= 5:
                        stale.append({
                            "content": content[:120],
                            "version": f"v{_major}.{minor_s}",
                            "age_versions": current_minor - minor,
                            "component": data.get("component", "") if isinstance(data, dict) else "",
                        })
                        break
                except Exception:
                    pass
        return stale[:20]

    def escalate_contradictions_to_imraf(self) -> int:
        """
        For each HIGH/MEDIUM contradiction, archive as INCIDENT if not already
        present in IMRAF. Returns count of new incidents created.
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
        against the known component list.
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
            data = _rec_attr(rec, "data", {})
            component = data.get("component", "") if isinstance(data, dict) else ""
            if component and component != "unknown":
                covered_set.add(component)

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
        Full governance report: cleanup + lifecycle + real contradictions +
        stale assumptions + coverage + AEG-readiness fields.
        """
        base = self.generate_cleanup_report()
        coverage = self.governance_coverage_report()
        escalated = self.escalate_contradictions_to_imraf()
        real_contradictions = self.detect_real_contradictions()
        stale_assumptions = self.detect_stale_assumptions()

        return {
            **base,
            "lifecycle_summary": coverage.get("lifecycle_summary", {}),
            "coverage_pct": coverage.get("coverage_pct", 0.0),
            "escalated_contradictions": escalated,
            "real_contradictions": real_contradictions,
            "real_contradiction_count": len(real_contradictions),
            "stale_assumptions": stale_assumptions,
            "stale_count": len(stale_assumptions),
        }

    def generate_cleanup_report(self) -> dict:
        contradictions = self.scan_contradictions()
        stale = self.scan_stale_decisions()
        assumptions = self.scan_assumptions()

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
