"""
AEOS — Autonomous Engineering Operating System
FTD-AEOS-001

Top-level orchestration layer that sits above IMRAF (institutional memory) and
DIAL (developer intelligence). Assembles complete context packages for autonomous
AI engineering agents, provides roadmap guidance, forecasts change impact, and
recommends verifiers.

Architecture:
    IMRAF (raw memory store)
        ↓
    DIAL (active intelligence methods)
        ↓
    AEOS (full context assembly + autonomous guidance)
"""
from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

from loguru import logger


class AEOSEngine:
    """
    Autonomous Engineering Operating System.
    Coordinates DIAL + IMRAF to produce complete AI-agent briefings.
    Thread-safe singleton.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._boot_ts = int(time.time() * 1000)
        self._assembly_count = 0
        self._dial = None
        self._imraf = None
        self._available = False
        self._load_subsystems()

    def _load_subsystems(self) -> None:
        try:
            from core.developer_intelligence.dial_engine import dial
            from core.institutional_memory.imraf_engine import imraf
            self._dial = dial
            self._imraf = imraf
            self._available = True
            logger.info("[AEOS] Connected to DIAL + IMRAF subsystems")
        except Exception as exc:
            logger.warning(f"[AEOS] Subsystem load failed — degraded mode: {exc}")

    # ── Context Assembly Engine ────────────────────────────────────────────────

    def assemble_context(self, task: str, module: Optional[str] = None) -> Dict[str, Any]:
        """
        Assemble a complete AI-agent engineering briefing for a given task.

        Combines:
        - Current task description
        - Historical incidents for the module
        - Related FTDs
        - Architecture decisions
        - Dependencies and blast radius
        - Known risks
        - Roadmap position
        - Verifier history
        - Recommended next actions
        """
        with self._lock:
            self._assembly_count += 1

        result: Dict[str, Any] = {
            "task":              task,
            "module":            module or "GENERAL",
            "assembled_ts":      int(time.time() * 1000),
            "aeos_version":      "1.0.0",
        }

        if not self._available:
            result["status"] = "DEGRADED"
            result["message"] = "DIAL/IMRAF unavailable"
            return result

        # 1. Historical incidents for module
        historical = {}
        if module:
            historical = self._dial.get_historical_context(module)
        result["historical_incidents"] = historical

        # 2. Similar issues to the task
        similar = self._dial.find_similar_issues(task, limit=5)
        result["similar_past_issues"] = similar

        # 3. Related FTDs from IMRAF
        ftd_records = []
        if self._imraf:
            ftd_records = self._imraf.search(task, category="FTD", limit=5)
            if not ftd_records and module:
                ftd_records = self._imraf.search(module, category="FTD", limit=5)
        result["related_ftds"] = [
            {"id": r["id"], "title": r["title"],
             "status": r.get("data", {}).get("status", ""),
             "ts": r["ts"]}
            for r in ftd_records
        ]

        # 4. Architecture decisions
        arch = []
        if module:
            arch = self._dial.get_architecture_rationale(module)
        result["architecture_decisions"] = arch[:3]

        # 5. Dependency blast radius
        dep_impact = {}
        if module:
            dep_impact = self._dial.analyze_dependency_impact(module)
        result["dependency_blast_radius"] = dep_impact

        # 6. Known risks (static + from health score)
        known_risks = []
        if module:
            health = self._dial.get_module_health_score(module)
            known_risks = health.get("top_risk_factors", [])
            result["module_health_score"] = health
        result["known_risks"] = known_risks

        # 7. Roadmap / governance decisions from IMRAF
        governance = []
        if self._imraf:
            gov_records = self._imraf.search(task, category="GOVERNANCE", limit=5)
            if not gov_records and module:
                gov_records = self._imraf.search(module, category="GOVERNANCE", limit=5)
            governance = [
                {"title": r["title"],
                 "decision": r.get("data", {}).get("decision", ""),
                 "impact": r.get("data", {}).get("impact", "")}
                for r in gov_records
            ]
        result["roadmap_constraints"] = governance

        # 8. Verifier history from IMRAF
        verifier_history = []
        if self._imraf:
            vr = self._imraf.search(module or task, category="VERIFIER", limit=5)
            verifier_history = [
                {"name": r.get("data", {}).get("verifier_name", r["title"]),
                 "pass_rate": r.get("data", {}).get("pass_rate", 0),
                 "confidence": r.get("data", {}).get("confidence", ""),
                 "ts": r["ts"]}
                for r in vr
            ]
        result["verifier_history"] = verifier_history

        # 9. Change proposal if module given
        if module:
            result["change_proposal"] = self._dial.generate_change_proposal(task, module)

        # 10. Recommended next actions (synthesised)
        result["recommended_actions"] = self._synthesize_actions(result)

        result["status"] = "OK"
        return result

    def _synthesize_actions(self, ctx: Dict[str, Any]) -> List[str]:
        actions = []
        hist = ctx.get("historical_incidents", {})
        if hist.get("incident_count", 0) > 0:
            actions.append(f"Review {hist['incident_count']} historical incidents before modifying this module")
        if ctx.get("similar_past_issues"):
            top = ctx["similar_past_issues"][0]
            actions.append(f"Similar issue found: '{top['title']}' — check its resolution first")
        dep = ctx.get("dependency_blast_radius", {})
        if dep.get("direct_dependents"):
            actions.append(f"Blast radius: {len(dep['direct_dependents'])} downstream modules — test all after change")
        if ctx.get("roadmap_constraints"):
            actions.append(f"Governance constraint active — review before proceeding")
        proposal = ctx.get("change_proposal", {})
        if proposal.get("required_verifiers"):
            actions.append(f"Run verifiers: {', '.join(proposal['required_verifiers'])}")
        actions.append("Record change in IMRAF with record_code_change() after implementation")
        return actions

    # ── Roadmap Guidance Engine ────────────────────────────────────────────────

    def get_roadmap_guidance(self) -> Dict[str, Any]:
        """
        Return prioritised next-step guidance based on current IMRAF state.
        Synthesises open incidents, in-progress FTDs, governance constraints, and health scores.
        """
        if not self._available:
            return {"status": "DEGRADED"}

        with self._lock:
            self._assembly_count += 1

        # Next steps from DIAL planning assistant
        next_steps = self._dial.plan_next_steps(limit=7)

        # Module health ranking
        high_risk_modules = []
        for mod in ["trade_manager", "risk_engine", "data_lake", "alpha_context_memory",
                    "pnl_calc", "lean_gate", "imraf_engine", "dial_engine"]:
            score = self._dial.get_module_health_score(mod)
            if score["risk_score"] >= 3.0:
                high_risk_modules.append({
                    "module": mod,
                    "risk_score": score["risk_score"],
                    "risk_label": score["risk_label"],
                    "developer_attention": score["developer_attention"],
                })
        high_risk_modules.sort(key=lambda x: x["risk_score"], reverse=True)

        # Governance constraints from IMRAF
        governance = []
        if self._imraf:
            gov_records = self._imraf.timeline(category="GOVERNANCE", limit=5)
            governance = [
                {"title": r["title"], "impact": r.get("data", {}).get("impact", "")}
                for r in gov_records
            ]

        return {
            "status":                "OK",
            "recommended_next_steps": next_steps.get("recommended_next_steps", []),
            "high_risk_modules":     high_risk_modules[:5],
            "governance_constraints": governance,
            "open_incidents":        next_steps.get("open_incidents", 0),
            "in_progress_ftds":      next_steps.get("in_progress_ftds", 0),
            "generated_ts":          int(time.time() * 1000),
        }

    # ── Change Impact Forecaster ───────────────────────────────────────────────

    def forecast_change_impact(self, component: str, change_description: str) -> Dict[str, Any]:
        """
        Forecast the full impact of a proposed change before making it.
        Combines static dependency graph, historical breakage data, and regression history.
        """
        if not self._available:
            return {"status": "DEGRADED"}

        with self._lock:
            self._assembly_count += 1

        dep_impact  = self._dial.analyze_dependency_impact(component)
        reg_risk    = self._dial.check_regression_risk(component)
        health      = self._dial.get_module_health_score(component)
        proposal    = self._dial.generate_change_proposal(change_description, component)

        # Second-order effects: check health of all direct dependents
        second_order_risks = []
        for dep in dep_impact.get("direct_dependents", [])[:4]:
            dep_health = self._dial.get_module_health_score(dep)
            if dep_health["risk_score"] >= 4.0:
                second_order_risks.append({
                    "module": dep,
                    "risk_score": dep_health["risk_score"],
                    "note": f"Changing {component} could trigger regression in {dep} (score {dep_health['risk_score']})",
                })

        overall_risk = reg_risk["risk_level"]
        if second_order_risks and overall_risk != "HIGH":
            overall_risk = "MEDIUM"

        return {
            "component":            component,
            "change_description":   change_description,
            "overall_risk":         overall_risk,
            "direct_impact": {
                "dependents":         dep_impact.get("direct_dependents", []),
                "historical_breakages": len(dep_impact.get("historical_breakages", [])),
            },
            "second_order_risks":   second_order_risks,
            "module_health":        {
                "risk_score":  health["risk_score"],
                "risk_label":  health["risk_label"],
                "regression_count": health["regression_count"],
            },
            "required_verifiers":   proposal.get("required_verifiers", []),
            "pre_change_checklist": [
                f"Review {reg_risk['incident_count']} historical incident(s) for {component}",
                f"Check {len(dep_impact.get('direct_dependents', []))} downstream modules for compatibility",
                "Run full verifier suite BEFORE making the change",
            ] + [r["note"] for r in second_order_risks],
            "forecasted_ts": int(time.time() * 1000),
        }

    # ── Verifier Recommendation Engine ────────────────────────────────────────

    def recommend_verifiers(self, component: str) -> Dict[str, Any]:
        """
        Recommend specific test files and verifiers to run for a component.
        Combines static knowledge with IMRAF verifier history.
        """
        if not self._available:
            return {"status": "DEGRADED"}

        with self._lock:
            self._assembly_count += 1

        # Static verifier knowledge base
        _VERIFIER_MAP: Dict[str, List[str]] = {
            "trade_manager":        ["tests/test_live_process_access.py",
                                     "tests/developer_intelligence/test_dial.py"],
            "risk_engine":          ["tests/test_live_process_access.py"],
            "data_lake":            ["tests/test_live_process_access.py"],
            "alpha_context_memory": ["tests/developer_intelligence/test_dial.py"],
            "genome_engine":        ["tests/test_live_process_access.py"],
            "imraf_engine":         ["tests/institutional_memory/test_imraf.py"],
            "dial_engine":          ["tests/developer_intelligence/test_dial.py"],
            "aeos_engine":          ["tests/aeos/test_aeos.py"],
            "signal_ecology":       ["tests/test_live_process_access.py"],
            "pnl_calc":             ["tests/test_live_process_access.py"],
        }

        key = component.lower().replace(".py", "").replace("core/", "").replace("/", "_")
        static_verifiers = _VERIFIER_MAP.get(key, ["tests/test_live_process_access.py"])

        # Check IMRAF for historical verifier runs on this component
        historical_verifiers = []
        if self._imraf:
            vr = self._imraf.search(component, category="VERIFIER", limit=10)
            historical_verifiers = [
                {"name": r.get("data", {}).get("verifier_name", ""),
                 "pass_rate": r.get("data", {}).get("pass_rate", 0),
                 "last_run_ts": r["ts"]}
                for r in vr
            ]

        # Flag any historically failing verifiers
        failing = [v for v in historical_verifiers if v["pass_rate"] < 90]

        return {
            "component":             component,
            "recommended_verifiers": static_verifiers,
            "historical_runs":       historical_verifiers[:5],
            "historically_failing":  failing,
            "run_command":           f"python -m pytest {' '.join(static_verifiers)} -v",
            "priority": "HIGH" if failing else "STANDARD",
        }

    # ── Stats & Boot ──────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "module":           "AEOSEngine",
                "ftd":              "AEOS-001",
                "available":        self._available,
                "assembly_count":   self._assembly_count,
                "boot_ts":          self._boot_ts,
                "subsystems":       ["IMRAF", "DIAL"],
                "capabilities": [
                    "context_assembly",
                    "roadmap_guidance",
                    "change_impact_forecast",
                    "verifier_recommendation",
                ],
            }

    def get_boot_summary(self) -> str:
        return (
            f"available={self._available} "
            f"assembly_count={self._assembly_count} "
            f"subsystems=IMRAF+DIAL"
        )


# ── Singleton ─────────────────────────────────────────────────────────────────
aeos = AEOSEngine()
