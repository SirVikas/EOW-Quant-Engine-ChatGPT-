"""
FTD-DIAL-001 — Developer Intelligence Assist Layer (DIAL)

Transforms institutional memory (FTD-IMR-001 IMRAF) from a passive archive
into an active developer assistance system.

Serves: human developers, AI coding agents, auditors, maintainers, and future
autonomous engineering agents — providing contextual historical guidance,
regression prevention, architectural memory retrieval, dependency awareness,
onboarding intelligence, and engineering decision support.

The Institutional Memory Framework shall not operate solely as a historical
archive. It shall additionally function as an active Developer Intelligence
System capable of assisting human developers, AI developers, auditors,
maintainers, and future autonomous engineering agents through contextual
historical guidance, regression prevention, architectural memory retrieval,
dependency awareness, onboarding intelligence, and engineering decision support.
"""
from __future__ import annotations

import threading
import time
from typing import Dict, Any, List, Optional

from loguru import logger

# Dependency map: key → list of downstream modules that break if key changes
_DEPENDENCY_MAP: Dict[str, List[str]] = {
    "risk_engine":           ["portfolio_layer", "execution_layer", "signal_validation", "lean_gate"],
    "signal_ecology":        ["opportunity_ecology", "rsi_governor", "alpha_context_memory"],
    "trade_manager":         ["risk_engine", "pnl_calc", "data_lake"],
    "genome_engine":         ["strategy_engine", "data_lake", "rl_engine"],
    "rl_engine":             ["signal_ecology", "trade_manager"],
    "data_lake":             ["pnl_calc", "trade_manager", "genome_engine"],
    "pnl_calc":              ["risk_engine", "data_lake", "analytics"],
    "opportunity_ecology":   ["alpha_context_memory", "signal_density_engine"],
    "alpha_context_memory":  ["opportunity_ecology", "signal flow"],
    "adaptive_rsi_governor": ["opportunity_ecology", "signal_ecology"],
    "lean_gate":             ["execution_layer", "trade_manager"],
    "healer":                ["websocket", "data_lake", "risk_engine"],
    "main":                  ["all modules — entry point and orchestrator"],
    "imraf_engine":          ["dial_engine", "api_imraf_endpoints"],
    "dial_engine":           ["api_dial_endpoints", "autonomous_agents"],
    "strategy_engine":       ["genome_engine", "signal_flow", "pnl_calc"],
    "loss_cluster_controller": ["lean_gate", "risk_engine"],
    "equity_snapshot":       ["risk_engine", "data_lake"],
    "inverse_engine":        ["signal_flow", "strategy_engine"],
}

# Risk classification for known high-incident areas
_HIGH_RISK_COMPONENTS = frozenset({
    "risk_engine", "pnl_calc", "data_lake", "trade_manager",
    "lean_gate", "equity_snapshot", "main",
})


class DIALEngine:
    """
    Developer Intelligence Assist Layer.
    Queries IMRAF for historical context and provides active engineering guidance.
    Thread-safe.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._boot_ts = int(time.time() * 1000)
        self._imraf = None
        self._imraf_available = False
        self._query_count = 0
        self._load_imraf()

    def _load_imraf(self) -> None:
        try:
            from core.institutional_memory.imraf_engine import imraf
            self._imraf = imraf
            self._imraf_available = True
            logger.info("[DIAL] Connected to IMRAF institutional memory store")
        except Exception as exc:
            logger.warning(f"[DIAL] IMRAF unavailable — DIAL running in degraded mode: {exc}")

    def _search_imraf(self, query: str, category=None, limit: int = 20) -> List[Dict[str, Any]]:
        if not self._imraf_available:
            return []
        try:
            return self._imraf.search(query, category=category, limit=limit)
        except Exception:
            return []

    # ── Module 1: Historical Context Engine ───────────────────────────────────

    def get_historical_context(self, module_name: str) -> Dict[str, Any]:
        """
        Full historical context for a module before modification.
        Returns incident count, known weaknesses, prior failures, and related FTDs.
        """
        with self._lock:
            self._query_count += 1

        records = self._search_imraf(module_name, limit=50)
        incidents  = [r for r in records if r["category"] in ("INCIDENT", "FAILURE", "BUG")]
        arch_recs  = [r for r in records if r["category"] == "ARCHITECTURE"]
        decisions  = [r for r in records if r["category"] == "DECISION"]
        deployments = [r for r in records if r["category"] == "DEPLOYMENT"]

        # Extract known weaknesses from failure records
        weaknesses = []
        for r in incidents[:5]:
            rc = r.get("data", {}).get("root_cause", "")
            if rc and rc not in weaknesses:
                weaknesses.append(rc)

        # Check high-risk classification
        is_high_risk = module_name.lower() in _HIGH_RISK_COMPONENTS

        return {
            "module":            module_name,
            "total_records":     len(records),
            "incident_count":    len(incidents),
            "change_count":      len(decisions) + len(deployments),
            "architecture_decisions": len(arch_recs),
            "known_weaknesses":  weaknesses[:3],
            "recommended_review": "RiskValidator, TestSuite" if is_high_risk else "TestSuite",
            "risk_classification": "HIGH" if is_high_risk else "STANDARD",
            "last_incident_ts":  max((r["ts"] for r in incidents), default=0),
            "recent_records":    [
                {"id": r["id"], "category": r["category"], "title": r["title"], "ts": r["ts"]}
                for r in records[:5]
            ],
            "ts": self._boot_ts,
        }

    # ── Module 2: Similar Issue Detection Engine ───────────────────────────────

    def find_similar_issues(self, error_description: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search institutional memory for historically similar failures and their resolutions.
        Returns ranked list with similarity signals.
        """
        with self._lock:
            self._query_count += 1

        results = []
        # Search across failure-type categories — fall back to string if Category enum unavailable
        for cat_name in ("FAILURE", "INCIDENT", "BUG", "REGRESSION"):
            hits = self._search_imraf(error_description, category=cat_name, limit=limit)
            for r in hits:
                results.append({
                    "id":               r["id"],
                    "title":            r["title"],
                    "category":         r["category"],
                    "root_cause":       r.get("data", {}).get("root_cause", ""),
                    "resolution":       r.get("data", {}).get("resolution", ""),
                    "prevention":       r.get("data", {}).get("prevention", ""),
                    "similarity_signal": "keyword_match",
                    "ts":               r["ts"],
                })

        # Deduplicate by id, sort newest first
        seen = set()
        unique = []
        for r in sorted(results, key=lambda x: x["ts"], reverse=True):
            if r["id"] not in seen:
                seen.add(r["id"])
                unique.append(r)

        return unique[:limit]

    # ── Module 3: Regression Risk Engine ──────────────────────────────────────

    def check_regression_risk(self, file_or_component: str) -> Dict[str, Any]:
        """
        Assess regression risk before modifying a component.
        Combines historical incident search with hardcoded high-risk classification.
        """
        with self._lock:
            self._query_count += 1

        records = self._search_imraf(file_or_component, limit=30)
        high_severity = [
            r for r in records
            if r["category"] in ("INCIDENT", "FAILURE", "REGRESSION", "BUG")
            and r.get("data", {}).get("severity", "").upper() in ("CRITICAL", "HIGH", "ERROR")
        ]
        any_incidents = [r for r in records if r["category"] in ("INCIDENT", "FAILURE", "REGRESSION", "BUG")]

        is_core = file_or_component.lower() in _HIGH_RISK_COMPONENTS
        if high_severity or is_core:
            risk_level = "HIGH"
            recommendation = (
                "⚠ HIGH REGRESSION RISK — review all prior incidents and run full test suite. "
                "Validate with risk_engine, lean_gate, and equity_snapshot integration tests."
            )
        elif any_incidents:
            risk_level = "MEDIUM"
            recommendation = (
                "Review prior incident records before modification. "
                "Run targeted tests for affected subsystems."
            )
        else:
            risk_level = "LOW"
            recommendation = "No prior incidents found. Run standard test suite."

        return {
            "component":      file_or_component,
            "risk_level":     risk_level,
            "incident_count": len(any_incidents),
            "high_severity":  len(high_severity),
            "recommendation": recommendation,
            "incidents": [
                {"id": r["id"], "title": r["title"], "category": r["category"], "ts": r["ts"]}
                for r in any_incidents[:5]
            ],
            "is_core_component": is_core,
        }

    # ── Module 4: Architecture Memory Advisor ─────────────────────────────────

    def get_architecture_rationale(self, component: str) -> List[Dict[str, Any]]:
        """
        Retrieve why architectural decisions were made for a component.
        Includes alternatives evaluated and trade-offs documented.
        """
        with self._lock:
            self._query_count += 1

        try:
            from core.institutional_memory.imraf_engine import Category
            records = self._search_imraf(component, category=Category.ARCHITECTURE, limit=20)
        except Exception:
            records = self._search_imraf(component, limit=20)
            records = [r for r in records if r["category"] == "ARCHITECTURE"]

        return [
            {
                "id":           r["id"],
                "title":        r["title"],
                "decision":     r.get("data", {}).get("decision", ""),
                "alternatives": r.get("data", {}).get("alternatives", []),
                "reasoning":    r.get("data", {}).get("reasoning", ""),
                "trade_offs":   r.get("data", {}).get("trade_offs", ""),
                "engine_ver":   r.get("engine_ver", ""),
                "ts":           r["ts"],
            }
            for r in records
        ]

    # ── Module 5: Dependency Impact Analyzer ──────────────────────────────────

    def analyze_dependency_impact(self, component: str) -> Dict[str, Any]:
        """
        Identify downstream modules affected by a change and historical breakages.
        """
        with self._lock:
            self._query_count += 1

        # Find dependents from static map
        key = component.lower().replace(".py", "").replace("core/", "").replace("/", "_")
        direct_dependents = _DEPENDENCY_MAP.get(key, [])

        # Also check if component appears as a dependent of anything else
        reverse_deps = [
            mod for mod, deps in _DEPENDENCY_MAP.items()
            if any(component.lower() in d.lower() for d in deps)
        ]

        # Search IMRAF for historical breakages involving this component
        breakages = self._search_imraf(component, limit=15)
        breakages = [
            r for r in breakages
            if r["category"] in ("INCIDENT", "FAILURE", "REGRESSION", "BUG")
        ]

        risk = "HIGH" if (len(direct_dependents) >= 3 or component.lower() in _HIGH_RISK_COMPONENTS) else \
               "MEDIUM" if direct_dependents else "LOW"

        return {
            "component":           component,
            "direct_dependents":   direct_dependents,
            "reverse_dependencies": reverse_deps[:5],
            "historical_breakages": [
                {"id": r["id"], "title": r["title"], "ts": r["ts"]}
                for r in breakages[:5]
            ],
            "risk_assessment": risk,
            "recommendation": (
                f"Modifying {component} may affect: {', '.join(direct_dependents[:3])}. "
                f"{'Review ' + str(len(breakages)) + ' historical breakages.' if breakages else 'No prior breakages found.'}"
            ),
        }

    # ── Module 6: FTD Knowledge Engine ────────────────────────────────────────

    def get_ftd_knowledge(self, ftd_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all institutional memory records related to a specific FTD.
        """
        with self._lock:
            self._query_count += 1

        records = self._search_imraf(ftd_id, limit=30)
        return [
            {
                "id": r["id"], "category": r["category"],
                "title": r["title"], "tags": r["tags"],
                "engine_ver": r.get("engine_ver", ""), "ts": r["ts"],
            }
            for r in records
        ]

    # ── Module 7: Developer Onboarding Engine ─────────────────────────────────

    def generate_onboarding_package(self) -> Dict[str, Any]:
        """
        Structured onboarding package for new developers or AI agents.
        Summarises project architecture, risks, open items, and lessons learned.
        """
        with self._lock:
            self._query_count += 1

        imraf_stats = {}
        deployments = []
        top_incidents = []
        arch_decisions = []
        lessons = []

        if self._imraf_available:
            try:
                imraf_stats = self._imraf.get_stats()
                deployments  = self._search_imraf("boot", limit=5)
                top_incidents = self._search_imraf("", limit=10)
                top_incidents = [r for r in top_incidents if r["category"] in ("INCIDENT", "FAILURE")][:5]
                arch_decisions = self._search_imraf("", limit=10)
                arch_decisions = [r for r in arch_decisions if r["category"] == "ARCHITECTURE"][:5]
                lessons        = self._search_imraf("lesson", limit=5)
            except Exception:
                pass

        return {
            "project":          "EOW Quant Engine — PHOENIX Autonomous Trading Platform",
            "stack":            "Python / FastAPI / asyncio / SQLite / loguru",
            "trade_modes":      ["PAPER", "LIVE"],
            "key_subsystems": [
                "DataLake (SQLite trade archive)",
                "RL Engine (contextual bandit)",
                "Genome Engine (DNA evolution)",
                "Signal Ecology (RSI governor, context memory)",
                "Trade Manager (TSL, BE, partial TP)",
                "Risk Engine (drawdown, loss streak, capital)",
                "IMRAF (institutional memory)",
                "DIAL (developer intelligence)",
            ],
            "critical_files": [
                "main.py — orchestration & all API endpoints",
                "config.py — single source of truth for all parameters",
                "core/data_lake.py — trade persistence",
                "core/trade_manager.py — position lifecycle",
                "core/risk_engine.py — capital protection",
                "core/genome_engine.py — strategy evolution",
                "core/signal_ecology/alpha_context_memory.py — context amplification",
                "core/institutional_memory/imraf_engine.py — institutional knowledge",
                "core/developer_intelligence/dial_engine.py — engineering intelligence",
            ],
            "institutional_memory": imraf_stats,
            "recent_deployments": [
                {"title": r["title"], "ts": r["ts"]} for r in deployments[:3]
            ],
            "known_incidents": [
                {"title": r["title"], "category": r["category"], "ts": r["ts"]}
                for r in top_incidents
            ],
            "architecture_decisions": [
                {"title": r["title"], "ts": r["ts"]} for r in arch_decisions
            ],
            "lessons_learned": [
                {"title": r["title"], "finding": r.get("data", {}).get("finding", "")}
                for r in lessons
            ],
            "known_risks": [
                "Context memory key must use strategy_id not strategy_type (fixed v1.53.4)",
                "Phase-H startup with >4k trades blocks event loop (fixed v1.53.2)",
                "Trailing stop must stay tighter than breakeven price (fixed v1.53.0)",
                "RSI governor only gates PAPER_SPEED signals — primary signals use crash guard only",
            ],
            "generated_ts": int(time.time() * 1000),
        }

    # ── Module 8: Autonomous Developer Context Engine ─────────────────────────

    def get_autonomous_context(self, module_name: str) -> Dict[str, Any]:
        """
        Structured context package for AI coding agents working on a module.
        Combines historical context, regression risk, and architecture rationale.
        """
        ctx = self.get_historical_context(module_name)
        reg = self.check_regression_risk(module_name)
        arch = self.get_architecture_rationale(module_name)
        deps = self.analyze_dependency_impact(module_name)

        return {
            "module":               module_name,
            "ai_agent_guidance": (
                f"Module '{module_name}' has {ctx['incident_count']} historical incidents. "
                f"Regression risk: {reg['risk_level']}. "
                f"Affects {len(deps['direct_dependents'])} downstream modules. "
                f"{'⚠ HIGH RISK — review all prior incidents before modifying.' if reg['risk_level'] == 'HIGH' else 'Standard caution advised.'}"
            ),
            "historical_context":   ctx,
            "regression_risk":      reg,
            "architecture_context": arch[:3],
            "dependency_impact":    deps,
            "recommended_actions": [
                "Read all INCIDENT records for this module before modifying",
                "Run regression_risk check after each significant change",
                "Record your change via /api/imraf/search after implementation",
                "Update lessons learned if a new failure is discovered",
            ],
        }

    # ── Module 9: Code Change Memory Engine ───────────────────────────────────

    def record_code_change(
        self,
        module: str,
        description: str,
        reason: str,
        expected_outcome: str,
        author: str = "claude",
        verification_status: str = "PENDING",
    ) -> int:
        """Record an engineering change for long-term traceability."""
        if not self._imraf_available:
            return -1
        return self._imraf.record(
            category=self._imraf.Category.DEVELOPER if hasattr(self._imraf, 'Category') else "DEVELOPER",
            title=f"Change: {module} — {description[:60]}",
            data={
                "module": module, "description": description, "reason": reason,
                "expected_outcome": expected_outcome, "author": author,
                "verification_status": verification_status,
            },
            subcategory=module,
            tags=["code_change", module, author],
        )

    # ── Module 10: Lessons Learned Engine ─────────────────────────────────────

    def extract_lesson(
        self,
        issue: str,
        root_cause: str,
        fix: str,
        prevention: str,
        related_components: List[str],
    ) -> int:
        """Convert an incident into reusable institutional knowledge."""
        if not self._imraf_available:
            return -1
        return self._imraf.record(
            category=self._imraf.Category.KNOWLEDGE if hasattr(self._imraf, 'Category') else "KNOWLEDGE",
            title=f"Lesson: {issue[:60]}",
            data={
                "issue": issue, "root_cause": root_cause, "fix": fix,
                "prevention": prevention, "related_components": related_components,
            },
            subcategory="LESSON",
            tags=["lesson", "prevention"] + related_components[:3],
        )

    # ── Module 11: Engineering Decision Assistant ──────────────────────────────

    def get_engineering_recommendation(self, query: str) -> Dict[str, Any]:
        """
        Recommend based on historical precedent for a given engineering question.
        """
        with self._lock:
            self._query_count += 1

        records = self._search_imraf(query, limit=10)
        arch = [r for r in records if r["category"] == "ARCHITECTURE"]
        failures = [r for r in records if r["category"] in ("FAILURE", "INCIDENT", "BUG")]
        successes = [r for r in records if r["category"] in ("EVOLUTION", "SELF_IMPROVE", "RESEARCH")]

        confidence = "HIGH" if len(records) >= 5 else "MEDIUM" if len(records) >= 2 else "LOW"

        if failures and not successes:
            recommendation = f"Historical evidence shows {len(failures)} failure(s) for similar queries. Proceed with caution."
        elif arch:
            best = arch[0]
            recommendation = f"Architecture decision found: {best['title']}. Reasoning: {best.get('data', {}).get('reasoning', 'see record')}."
        elif records:
            recommendation = f"Found {len(records)} related records. Review historical context before proceeding."
        else:
            recommendation = "No historical precedent found. Document your decision as a new architecture record."

        return {
            "query":            query,
            "confidence":       confidence,
            "recommendation":   recommendation,
            "relevant_records": [
                {"id": r["id"], "category": r["category"], "title": r["title"], "ts": r["ts"]}
                for r in records[:5]
            ],
            "failure_warnings": [
                {"id": r["id"], "title": r["title"]} for r in failures[:3]
            ],
        }

    # ── Boot summary ───────────────────────────────────────────────────────────

    def get_boot_summary(self) -> str:
        imraf_records = 0
        if self._imraf_available:
            try:
                imraf_records = self._imraf.get_stats().get("total_records", 0)
            except Exception:
                pass
        return (
            f"imraf_available={self._imraf_available} "
            f"imraf_records={imraf_records} "
            f"dependency_map_entries={len(_DEPENDENCY_MAP)} "
            f"high_risk_components={len(_HIGH_RISK_COMPONENTS)}"
        )

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "module":                "DIALEngine",
                "ftd":                   "DIAL-001",
                "imraf_available":       self._imraf_available,
                "query_count":           self._query_count,
                "dependency_map_size":   len(_DEPENDENCY_MAP),
                "high_risk_components":  list(_HIGH_RISK_COMPONENTS),
                "boot_ts":               self._boot_ts,
            }


# ── Singleton ──────────────────────────────────────────────────────────────────
dial = DIALEngine()
