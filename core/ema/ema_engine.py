"""
FTD-EMA-001 — Enterprise Memory Architecture

Unified institutional intelligence layer that binds IMRAF (memory),
DIAL (developer intelligence), and AEOS (context assembly) into a single
vendor-neutral interface consumable by any AI system, human developer,
auditor, maintainer, researcher, or autonomous agent.

Core principle:
    AI Memory is temporary.
    Institutional Memory is permanent.
    PHOENIX must never depend on a specific AI vendor memory implementation.
    All critical knowledge must remain owned by PHOENIX.

Architecture:
    PHOENIX Knowledge Core
          ↓
    IMRAF (Memory)
          ↓
    DIAL (Developer Intelligence)
          ↓
    AEOS (Context Assembly)
          ↓
    EMA  (Multi-AI Interface + Governance + Knowledge Graph + Health Monitor)
          ↓
    Claude / ChatGPT / Gemini / Copilot / Future Agents
"""
from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

from loguru import logger


# ── Module 3: Project Knowledge Core ─────────────────────────────────────────
# Static institutional knowledge that never changes — the permanent identity
# of the PHOENIX project.
_PROJECT_KNOWLEDGE: Dict[str, Any] = {
    "project":        "EOW Quant Engine — PHOENIX Autonomous Trading Platform",
    "classification": "Proprietary institutional trading system",
    "stack":          "Python / FastAPI / asyncio / SQLite / loguru",
    "trade_modes":    ["PAPER", "LIVE"],
    # ── PHOENIX NEXUS formal identity ───────────────────────────────────────
    "SYSTEM_NAME":    "PHOENIX NEXUS",
    "SYSTEM_DESCRIPTION": (
        "PHOENIX Institutional Intelligence Layer responsible for memory, intelligence, "
        "context assembly, governance, and future autonomous engineering guidance. "
        "NEXUS is not a module — it is the collective name for the entire institutional "
        "intelligence ecosystem: IMRAF + DIAL + AEOS + EMA + EGI (active) and "
        "KGE + HKE + AEG (pending)."
    ),
    "architecture": {
        "execution_layer": [
            "Trading Engine", "Risk Engine", "Portfolio Intelligence",
            "Reporting Layer", "Truth Engine (ETE / XTE / AAP)",
        ],
        "PHOENIX_NEXUS": {
            "active":  ["IMRAF", "DIAL", "AEOS", "EMA", "EGI"],
            "pending": ["KGE", "HKE", "AEG"],
            "adr":     "ADR-NEXUS-001",
        },
    },
    "vision":         (
        "A self-evolving, AI-guided autonomous trading engine that compounds "
        "institutional knowledge across every session, trade, and engineering change."
    ),
    "operating_principles": [
        "APP_VERSION in config.py is the single source of truth for versioning",
        "All architectural decisions must be recorded in IMRAF before implementation",
        "No code change is made without consulting DIAL regression risk first",
        "Every failure generates a lesson in IMRAF — failures teach, not just hurt",
        "AI Memory is temporary — PHOENIX institutional memory is permanent",
        "The project must be able to explain itself without relying on any AI vendor",
    ],
    "governance_rules": [
        "Force-push to main/master requires explicit user confirmation",
        "APP_VERSION bumped on every commit touching main.py, core/, or strategies/",
        "IMRAF records all FTD deliveries, architectural decisions, and governance choices",
        "All verifier results stored in IMRAF VERIFIER category after each test run",
        "DIAL Module 15 health score checked before any high-risk component modification",
    ],
    "critical_components": [
        "config.py — single source of truth for all parameters",
        "main.py — orchestration and all API endpoints",
        "core/data_lake.py — trade persistence",
        "core/trade_manager.py — position lifecycle (HIGH RISK)",
        "core/risk_engine.py — capital protection (HIGH RISK)",
        "core/genome_engine.py — strategy evolution",
        "core/signal_ecology/alpha_context_memory.py — context amplification",
        "core/institutional_memory/imraf_engine.py — institutional knowledge",
        "core/developer_intelligence/dial_engine.py — engineering intelligence",
        "core/aeos/aeos_engine.py — autonomous context assembly",
        "core/ema/ema_engine.py — enterprise memory architecture",
    ],
    "known_permanent_risks": [
        "Context memory key must use strategy_id not strategy_type (fixed v1.53.4)",
        "Phase-H startup with >4k trades blocks event loop (fixed v1.53.2)",
        "Trailing stop must stay tighter than breakeven price (fixed v1.53.0)",
        "RSI governor only gates PAPER_SPEED signals — primary signals bypass it",
        "Backfill must not double-count if JSON persistence already loaded state",
    ],
    "ftd_registry": [
        "FTD-IMR-001: Institutional Memory & Research Archive Framework",
        "FTD-DIAL-001: Developer Intelligence Assist Layer",
        "FTD-AEOS-001: Autonomous Engineering Operating System",
        "FTD-EMA-001: Enterprise Memory Architecture",
        "FTD-EGI-001: Engineering Governance Integrity Program",
        "FTD-KGE-001: Knowledge Graph Expansion Program (PENDING — NEXT)",
        "FTD-HKE-001: Historical Knowledge Extraction Program (PENDING)",
        "FTD-AEG-001: Autonomous Engineering Governance (PENDING — BLOCKED until KGE+HKE)",
        "FTD-ETE-001: Entry Truth Engine Activation Program (PENDING — Phase-2 after 500+ trades)",
        "FTD-XTE-001: Exit Truth Engine Activation Program (PENDING — after ETE Phase-3)",
    ],
    "nexus": {
        "name":        "PHOENIX NEXUS",
        "version":     "1.0.0",
        "definition":  "Central knowledge and intelligence nexus — connects all institutional layers.",
        "active":      ["IMRAF", "DIAL", "AEOS", "EMA", "EGI"],
        "pending":     ["KGE", "HKE", "AEG"],
        "imraf_record": 111,
    },
}

# ── Module 6: Architecture Knowledge Graph (entity registry) ─────────────────
# Links modules ↔ FTDs ↔ incidents ↔ strategies ↔ verifiers ↔ governance
_KNOWLEDGE_GRAPH: Dict[str, Dict[str, List[str]]] = {
    "trade_manager": {
        "related_ftds":       ["FTD-IMR-001", "FTD-DIAL-001"],
        "related_incidents":  ["TSL below breakeven", "BE trigger mismatch"],
        "related_strategies": ["ALPHA_PBE_v1", "TrendFollowing"],
        "related_verifiers":  ["tests/test_live_process_access.py"],
        "related_modules":    ["risk_engine", "pnl_calc", "data_lake"],
        "governance_links":   ["TRAIL_ATR_MULT fixed to 0.60"],
    },
    "risk_engine": {
        "related_ftds":       ["FTD-IMR-001"],
        "related_incidents":  ["WebSocket gap on risk_engine tick"],
        "related_strategies": [],
        "related_verifiers":  ["tests/test_live_process_access.py"],
        "related_modules":    ["portfolio_layer", "lean_gate", "equity_snapshot"],
        "governance_links":   ["MAX_DRAWDOWN_HALT=0.15"],
    },
    "alpha_context_memory": {
        "related_ftds":       ["FTD-DIAL-001"],
        "related_incidents":  ["Context memory key mismatch v1.53.3"],
        "related_strategies": ["ALPHA_PBE_v1"],
        "related_verifiers":  ["tests/developer_intelligence/test_dial.py"],
        "related_modules":    ["opportunity_ecology", "signal_flow"],
        "governance_links":   ["strategy_id not strategy_type as lookup key"],
    },
    "imraf_engine": {
        "related_ftds":       ["FTD-IMR-001"],
        "related_incidents":  [],
        "related_strategies": [],
        "related_verifiers":  ["tests/institutional_memory/test_imraf.py"],
        "related_modules":    ["dial_engine", "aeos_engine", "ema_engine"],
        "governance_links":   ["SQLite WAL mode", "data/institutional_memory.db"],
    },
    "dial_engine": {
        "related_ftds":       ["FTD-DIAL-001"],
        "related_incidents":  [],
        "related_strategies": [],
        "related_verifiers":  ["tests/developer_intelligence/test_dial.py"],
        "related_modules":    ["imraf_engine", "aeos_engine"],
        "governance_links":   [],
    },
    "aeos_engine": {
        "related_ftds":       ["FTD-AEOS-001"],
        "related_incidents":  [],
        "related_strategies": [],
        "related_verifiers":  ["tests/aeos/test_aeos.py"],
        "related_modules":    ["dial_engine", "imraf_engine", "ema_engine"],
        "governance_links":   [],
    },
    "ema_engine": {
        "related_ftds":       ["FTD-EMA-001"],
        "related_incidents":  [],
        "related_strategies": [],
        "related_verifiers":  ["tests/enterprise_memory/test_ema.py"],
        "related_modules":    ["aeos_engine", "dial_engine", "imraf_engine"],
        "governance_links":   ["Multi-AI compatibility", "Vendor neutrality"],
    },
    "data_lake": {
        "related_ftds":       ["FTD-IMR-001"],
        "related_incidents":  ["Phase-H startup timeout"],
        "related_strategies": [],
        "related_verifiers":  ["tests/test_live_process_access.py"],
        "related_modules":    ["pnl_calc", "trade_manager", "genome_engine"],
        "governance_links":   ["SQLite WAL mode", "limit=500 on boot backfill"],
    },
}

# ── Module 11: Multi-AI Compatibility — supported consumers ──────────────────
_AI_CONSUMERS = ["Claude", "ChatGPT", "Gemini", "Copilot", "Cursor",
                 "Windsurf", "InternalAgent", "Future"]


class EMAEngine:
    """
    Enterprise Memory Architecture Engine.

    Orchestrates all 14 EMA modules over IMRAF + DIAL + AEOS.
    Produces vendor-neutral AI context packages and governs institutional
    knowledge integrity.
    Thread-safe singleton.
    """

    def __init__(self):
        self._lock        = threading.RLock()
        self._boot_ts     = int(time.time() * 1000)
        self._query_count = 0
        self._audit_log:  List[Dict[str, Any]] = []
        self._dial   = None
        self._imraf  = None
        self._aeos   = None
        self._available   = False
        self._load_subsystems()

    # ── Internal ─────────────────────────────────────────────────────────────

    def _load_subsystems(self) -> None:
        try:
            from core.developer_intelligence.dial_engine import dial
            from core.institutional_memory.imraf_engine import imraf
            from core.aeos.aeos_engine import aeos
            self._dial  = dial
            self._imraf = imraf
            self._aeos  = aeos
            self._available = True
            logger.info("[EMA] Enterprise Memory Architecture ready — IMRAF+DIAL+AEOS connected")
        except Exception as exc:
            logger.warning(f"[EMA] Subsystem load failed — degraded mode: {exc}")

    def _audit(self, module: str, action: str, detail: str = "") -> None:
        entry = {
            "ts":     int(time.time() * 1000),
            "module": module,
            "action": action,
            "detail": detail,
        }
        with self._lock:
            self._audit_log.append(entry)
            self._query_count += 1
        # Keep last 1000 entries in memory
        if len(self._audit_log) > 1000:
            self._audit_log = self._audit_log[-1000:]

    # ── Module 1: AI Memory Abstraction Layer ─────────────────────────────────

    def get_ai_abstraction_status(self) -> Dict[str, Any]:
        """
        Confirms vendor independence: any AI system can consume PHOENIX knowledge
        through standardised EMA APIs without requiring vendor-specific memory.
        """
        self._audit("Module1_AI_Abstraction", "status_check")
        return {
            "principle":        "AI Memory is temporary. Institutional Memory is permanent.",
            "vendor_independence": True,
            "supported_consumers": _AI_CONSUMERS,
            "knowledge_owner":  "PHOENIX — not any AI vendor",
            "retrieval_guarantee": (
                "All knowledge is retrievable via /api/ema/* endpoints without "
                "any AI session context, memory, or vendor-specific feature."
            ),
            "standard_interfaces": [
                "GET /api/ema/context-package — full AI briefing",
                "GET /api/ema/project-knowledge — permanent project facts",
                "GET /api/ema/knowledge-graph/{module} — entity relationships",
                "GET /api/ema/roadmap — current project state",
                "GET /api/ema/dashboard — engineering intelligence summary",
                "GET /api/ema/health — knowledge quality metrics",
                "GET /api/ema/governance/audit — audit trail",
            ],
        }

    # ── Module 2 + 8: Context Assembly + Autonomous Engineering Context ────────

    def generate_ai_context_package(
        self,
        task: str,
        module: Optional[str] = None,
        ai_consumer: str = "Generic",
    ) -> Dict[str, Any]:
        """
        Generate a complete, vendor-neutral engineering context package
        for any AI consumer. Delegates heavy lifting to AEOS, then wraps
        in EMA governance metadata.

        Module 2 (Context Assembly) + Module 8 (Autonomous Engineering Package).
        """
        self._audit("Module2_ContextAssembly", "generate_package",
                    f"consumer={ai_consumer} task={task[:40]}")

        pkg: Dict[str, Any] = {
            "ema_version":    "EMA-001",
            "ai_consumer":    ai_consumer,
            "task":           task,
            "module":         module or "GENERAL",
            "generated_ts":   int(time.time() * 1000),
            "vendor_neutral": True,
        }

        if not self._available:
            pkg["status"] = "DEGRADED"
            return pkg

        # Section 1: Project Overview (Module 3)
        pkg["project_overview"] = {
            "name":    _PROJECT_KNOWLEDGE["project"],
            "stack":   _PROJECT_KNOWLEDGE["stack"],
            "vision":  _PROJECT_KNOWLEDGE["vision"],
            "principles": _PROJECT_KNOWLEDGE["operating_principles"][:3],
        }

        # Section 2: Current Roadmap Stage (Module 7)
        roadmap = self._aeos.get_roadmap_guidance()
        pkg["roadmap_state"] = {
            "open_incidents":    roadmap.get("open_incidents", 0),
            "in_progress_ftds":  roadmap.get("in_progress_ftds", 0),
            "next_steps":        roadmap.get("recommended_next_steps", [])[:3],
            "high_risk_modules": roadmap.get("high_risk_modules", [])[:3],
        }

        # Section 3: Historical incidents + architecture for module
        if module:
            aeos_ctx = self._aeos.assemble_context(task, module)
            pkg["module_context"] = {
                "historical_incidents": aeos_ctx.get("historical_incidents", {}),
                "architecture_decisions": aeos_ctx.get("architecture_decisions", []),
                "dependency_blast_radius": aeos_ctx.get("dependency_blast_radius", {}),
                "module_health_score": aeos_ctx.get("module_health_score", {}),
                "known_risks": aeos_ctx.get("known_risks", []),
            }
            # Section 4: Knowledge Graph (Module 6)
            pkg["knowledge_graph"] = self.get_knowledge_graph(module)

        # Section 5: Similar past issues
        similar = self._dial.find_similar_issues(task, limit=3)
        pkg["similar_past_issues"] = similar

        # Section 6: Required tests / verifiers
        verifiers = {}
        if module:
            verifiers = self._aeos.recommend_verifiers(module)
        pkg["required_tests"] = verifiers.get("recommended_verifiers", [])
        pkg["verifier_run_command"] = verifiers.get("run_command", "")

        # Section 7: Open items / recommended actions
        if module:
            proposal = self._dial.generate_change_proposal(task, module)
            pkg["recommended_actions"] = proposal.get("checklist", [])
            pkg["change_proposal"]     = proposal
        else:
            pkg["recommended_actions"] = [
                "Specify a module to get targeted change proposal and verifier list",
                "Call /api/ema/context-package?task=...&module=... for full briefing",
            ]

        # Section 8: Permanent known risks
        pkg["permanent_known_risks"] = _PROJECT_KNOWLEDGE["known_permanent_risks"]

        pkg["status"] = "OK"
        return pkg

    # ── Module 3: Project Knowledge Core ─────────────────────────────────────

    def get_project_knowledge(self) -> Dict[str, Any]:
        """Return permanent project knowledge — stable institutional facts."""
        self._audit("Module3_ProjectKnowledge", "get")
        return dict(_PROJECT_KNOWLEDGE)

    # ── Module 4: FTD Knowledge Hub ───────────────────────────────────────────

    def get_ftd_hub(self, ftd_id: str = "", limit: int = 50) -> Dict[str, Any]:
        """
        Full FTD knowledge hub: retrieve FTD records from IMRAF with complete
        lifecycle metadata (status, delivery, dependencies, verifier results).
        """
        self._audit("Module4_FTDHub", "query", ftd_id)
        if not self._available:
            return {"status": "DEGRADED"}

        records = self._imraf.search(ftd_id or "ftd", category="FTD", limit=limit)
        # Also search without category filter for FTD references in other records
        cross_refs = self._imraf.search(ftd_id, limit=20) if ftd_id else []
        cross_refs = [r for r in cross_refs if r["category"] != "FTD"][:10]

        return {
            "ftd_id":      ftd_id or "ALL",
            "ftd_records": [
                {
                    "id":                r["id"],
                    "title":             r["title"],
                    "status":            r.get("data", {}).get("status", ""),
                    "delivered_by":      r.get("data", {}).get("delivered_by", ""),
                    "completion_date":   r.get("data", {}).get("completion_date", ""),
                    "dependencies":      r.get("data", {}).get("dependencies", []),
                    "verification_result": r.get("data", {}).get("verification_result", ""),
                    "rollback_history":  r.get("data", {}).get("rollback_history", []),
                    "engine_ver":        r.get("engine_ver", ""),
                    "ts":                r["ts"],
                }
                for r in records
            ],
            "cross_references": [
                {"id": r["id"], "category": r["category"], "title": r["title"]}
                for r in cross_refs
            ],
            "registry":    _PROJECT_KNOWLEDGE["ftd_registry"],
            "total_found": len(records),
        }

    # ── Module 5: Verifier Intelligence Hub ──────────────────────────────────

    def get_verifier_hub(self, component: str = "") -> Dict[str, Any]:
        """
        Verifier intelligence hub: full validation history with pass rates,
        coverage, confidence, and historical failure patterns.
        """
        self._audit("Module5_VerifierHub", "query", component)
        if not self._available:
            return {"status": "DEGRADED"}

        verifier_records = self._imraf.search(
            component or "", category="VERIFIER", limit=50
        )
        recommendation = self._aeos.recommend_verifiers(component or "general")

        return {
            "component":          component or "ALL",
            "verifier_records": [
                {
                    "id":                 r["id"],
                    "verifier_name":      r.get("data", {}).get("verifier_name", r["title"]),
                    "passed_tests":       r.get("data", {}).get("passed_tests", 0),
                    "failed_tests":       r.get("data", {}).get("failed_tests", 0),
                    "pass_rate":          r.get("data", {}).get("pass_rate", 0),
                    "coverage":           r.get("data", {}).get("coverage", 0),
                    "confidence":         r.get("data", {}).get("confidence", ""),
                    "historical_failures": r.get("data", {}).get("historical_failures", []),
                    "component":          r.get("data", {}).get("component", ""),
                    "ts":                 r["ts"],
                }
                for r in verifier_records
            ],
            "recommended_verifiers": recommendation.get("recommended_verifiers", []),
            "historically_failing":  recommendation.get("historically_failing", []),
            "run_command":           recommendation.get("run_command", ""),
            "total_records":         len(verifier_records),
        }

    # ── Module 6: Architecture Knowledge Graph ────────────────────────────────

    def get_knowledge_graph(self, module: str = "") -> Dict[str, Any]:
        """
        Return entity relationship graph for a module: FTDs, incidents,
        strategies, verifiers, governance policies, and linked modules.
        """
        self._audit("Module6_KnowledgeGraph", "query", module)
        key = module.lower().replace(".py", "").replace("core/", "").replace("/", "_")
        static_graph = _KNOWLEDGE_GRAPH.get(key, {})

        # Enrich with live IMRAF data
        live_enrichment: Dict[str, List] = {}
        if self._available and module:
            arch_recs = self._imraf.search(module, category="ARCHITECTURE", limit=5)
            live_enrichment["live_architecture_decisions"] = [
                {"id": r["id"], "title": r["title"]} for r in arch_recs
            ]
            incident_recs = self._imraf.search(module, limit=10)
            incident_recs = [r for r in incident_recs
                             if r["category"] in ("INCIDENT", "FAILURE", "BUG")]
            live_enrichment["live_incidents"] = [
                {"id": r["id"], "category": r["category"], "title": r["title"]}
                for r in incident_recs[:5]
            ]

        return {
            "module":          module or "GLOBAL",
            "entity_type":     "MODULE",
            "relationships":   static_graph,
            "live_enrichment": live_enrichment,
            "graph_stats": {
                "related_ftds":      len(static_graph.get("related_ftds", [])),
                "related_incidents": len(static_graph.get("related_incidents", [])),
                "related_modules":   len(static_graph.get("related_modules", [])),
                "related_verifiers": len(static_graph.get("related_verifiers", [])),
            },
            "all_registered_modules": list(_KNOWLEDGE_GRAPH.keys()),
        }

    # ── Module 7: Roadmap Intelligence Engine ────────────────────────────────

    def get_roadmap_state(self) -> Dict[str, Any]:
        """
        Full roadmap intelligence: current position, what was completed,
        what is pending, what is blocked, and what should happen next.
        """
        self._audit("Module7_RoadmapIntelligence", "get_state")
        if not self._available:
            return {"status": "DEGRADED"}

        roadmap = self._aeos.get_roadmap_guidance()
        plan    = self._dial.plan_next_steps(limit=10)

        # FTD completion timeline from IMRAF
        ftd_delivered = self._imraf.search("DELIVERED", category="FTD", limit=20)
        ftd_pending   = self._imraf.search("IN_PROGRESS", category="FTD", limit=10)
        ftd_planned   = self._imraf.search("PLANNED", category="FTD", limit=10)

        governance = self._imraf.timeline(category="GOVERNANCE", limit=10)

        return {
            "status":     "OK",
            "where_are_we": {
                "completed_ftds":  len(ftd_delivered),
                "in_progress_ftds": len(ftd_pending),
                "planned_ftds":    len(ftd_planned),
                "open_incidents":  plan.get("open_incidents", 0),
                "recent_regressions": plan.get("recent_regressions", 0),
            },
            "what_was_completed": [
                {"title": r["title"], "ts": r["ts"]} for r in ftd_delivered[:5]
            ],
            "what_is_pending": [
                {"title": r["title"], "ts": r["ts"]} for r in ftd_pending[:5]
            ],
            "what_should_happen_next": plan.get("recommended_next_steps", [])[:5],
            "high_risk_modules":      roadmap.get("high_risk_modules", [])[:5],
            "governance_constraints": [
                {"title": r["title"], "impact": r.get("data", {}).get("impact", "")}
                for r in governance[:5]
            ],
            "ftd_registry":           _PROJECT_KNOWLEDGE["ftd_registry"],
        }

    # ── Module 9: Decision Traceability Engine ────────────────────────────────

    def get_decision_trail(self, query: str = "", limit: int = 50) -> Dict[str, Any]:
        """
        Full decision traceability: why decisions were made, alternatives
        considered, expected vs actual outcomes.
        """
        self._audit("Module9_DecisionTraceability", "query", query)
        if not self._available:
            return {"status": "DEGRADED"}

        decisions  = self._imraf.search(query, category="DECISION", limit=limit)
        arch_decs  = self._imraf.search(query, category="ARCHITECTURE", limit=20)
        governance = self._imraf.search(query, category="GOVERNANCE", limit=20)

        return {
            "query":  query or "ALL",
            "trade_decisions": [
                {
                    "id":       r["id"],
                    "title":    r["title"],
                    "decision": r.get("data", {}).get("decision", ""),
                    "reason":   r.get("data", {}).get("reason", ""),
                    "symbol":   r.get("data", {}).get("symbol", ""),
                    "strategy": r.get("data", {}).get("strategy", ""),
                    "outcome":  r.get("data", {}).get("outcome", ""),
                    "ts":       r["ts"],
                }
                for r in decisions[:10]
            ],
            "architecture_decisions": [
                {
                    "id":           r["id"],
                    "title":        r["title"],
                    "decision":     r.get("data", {}).get("decision", ""),
                    "alternatives": r.get("data", {}).get("alternatives", []),
                    "reasoning":    r.get("data", {}).get("reasoning", ""),
                    "trade_offs":   r.get("data", {}).get("trade_offs", ""),
                    "ts":           r["ts"],
                }
                for r in arch_decs[:10]
            ],
            "governance_decisions": [
                {
                    "id":        r["id"],
                    "title":     r["title"],
                    "decision":  r.get("data", {}).get("decision", ""),
                    "rationale": r.get("data", {}).get("rationale", ""),
                    "impact":    r.get("data", {}).get("impact", ""),
                    "ts":        r["ts"],
                }
                for r in governance[:10]
            ],
            "total_decisions": len(decisions) + len(arch_decs) + len(governance),
        }

    # ── Module 10: Lessons Learned Repository ────────────────────────────────

    def get_lessons_learned(self, query: str = "", limit: int = 50) -> Dict[str, Any]:
        """
        Institutional lessons learned: issues, root causes, resolutions,
        preventions, and future recommendations.
        """
        self._audit("Module10_LessonsLearned", "query", query)
        if not self._available:
            return {"status": "DEGRADED"}

        lessons      = self._imraf.search(query or "lesson", category="KNOWLEDGE", limit=limit)
        self_improve = self._imraf.search(query, category="SELF_IMPROVE", limit=20)
        meta         = self._imraf.search(query, category="META_LEARNING", limit=20)

        return {
            "query": query or "ALL",
            "lessons": [
                {
                    "id":           r["id"],
                    "title":        r["title"],
                    "issue":        r.get("data", {}).get("issue", ""),
                    "root_cause":   r.get("data", {}).get("root_cause", ""),
                    "fix":          r.get("data", {}).get("fix", ""),
                    "prevention":   r.get("data", {}).get("prevention", ""),
                    "related_components": r.get("data", {}).get("related_components", []),
                    "ts":           r["ts"],
                }
                for r in lessons[:15]
            ],
            "self_improvements": [
                {
                    "id":               r["id"],
                    "title":            r["title"],
                    "change":           r.get("data", {}).get("change", ""),
                    "observed_impact":  r.get("data", {}).get("observed_impact", ""),
                    "outcome":          r.get("data", {}).get("outcome", ""),
                    "ts":               r["ts"],
                }
                for r in self_improve[:10]
            ],
            "meta_learning_observations": [
                {
                    "id":          r["id"],
                    "title":       r["title"],
                    "observation": r.get("data", {}).get("observation", ""),
                    "is_novel":    r.get("data", {}).get("is_novel", False),
                    "ts":          r["ts"],
                }
                for r in meta[:10]
            ],
            "total_lessons": len(lessons) + len(self_improve) + len(meta),
        }

    # ── Module 11: Multi-AI Compatibility Layer ───────────────────────────────

    def get_multi_ai_package(
        self, task: str, module: Optional[str] = None, consumer: str = "Generic"
    ) -> Dict[str, Any]:
        """
        Standardised context package formatted for any AI consumer.
        Guarantees identical knowledge regardless of which AI system receives it.
        Same input → same institutional knowledge output for Claude, ChatGPT,
        Gemini, Copilot, or any future system.
        """
        self._audit("Module11_MultiAI", "generate_package", f"consumer={consumer}")
        base = self.generate_ai_context_package(task, module, ai_consumer=consumer)
        base["compatibility_guarantee"] = (
            "This package was generated by PHOENIX EMA using vendor-neutral APIs. "
            f"The same query submitted by any AI consumer ({', '.join(_AI_CONSUMERS)}) "
            "will receive the same institutional knowledge."
        )
        base["consumer_instructions"] = {
            "Claude":         "Use /api/ema/context-package for full briefing before any task",
            "ChatGPT":        "Same endpoint — EMA is AI-vendor neutral",
            "Gemini":         "Same endpoint — EMA is AI-vendor neutral",
            "Copilot":        "Same endpoint — EMA is AI-vendor neutral",
            "Future AI":      "Same endpoint — EMA is AI-vendor neutral",
            "Human Dev":      "Use /api/ema/dashboard for management overview",
            "Auditor":        "Use /api/ema/governance/audit for full audit trail",
        }
        return base

    # ── Module 12: Institutional Memory Governance ───────────────────────────

    def get_governance_audit(self, limit: int = 100) -> Dict[str, Any]:
        """
        Full audit trail of all EMA queries, IMRAF changes, and knowledge
        access events. Provides integrity, versioning, and retention visibility.
        """
        self._audit("Module12_Governance", "audit_read")
        with self._lock:
            recent_audit = list(reversed(self._audit_log[-limit:]))

        imraf_stats = {}
        if self._available:
            imraf_stats = self._imraf.get_stats()

        return {
            "audit_trail":      recent_audit,
            "total_queries":    self._query_count,
            "imraf_integrity": {
                "total_records":  imraf_stats.get("total_records", 0),
                "by_category":    imraf_stats.get("by_category", {}),
                "db_path":        imraf_stats.get("db_path", ""),
            },
            "governance_rules":   _PROJECT_KNOWLEDGE["governance_rules"],
            "retention_policy":   "All IMRAF records are permanent. Audit log: last 1000 entries in memory.",
            "integrity_status":   "OK" if self._available else "DEGRADED",
            "audit_generated_ts": int(time.time() * 1000),
        }

    # ── Module 13: Knowledge Health Monitor ──────────────────────────────────

    def get_knowledge_health(self) -> Dict[str, Any]:
        """
        Knowledge quality metrics: coverage, completeness, freshness,
        link integrity, archive growth, and search success rate.
        """
        self._audit("Module13_HealthMonitor", "check")
        if not self._available:
            return {"status": "DEGRADED"}

        stats = self._imraf.get_stats()
        by_cat = stats.get("by_category", {})
        total  = stats.get("total_records", 0)

        # Coverage: how many of the 23 expected categories have records
        expected_categories = [
            "RESEARCH", "FAILURE", "EVOLUTION", "REGIME", "DECISION",
            "ATTRIBUTION", "KNOWLEDGE", "AI_TRAINING", "POSTMORTEM",
            "META_LEARNING", "BUG", "ARCHITECTURE", "INCIDENT", "DEPLOYMENT",
            "DEVELOPER", "REGRESSION", "EVOLUTION_TL", "OPERATIONAL",
            "SELF_IMPROVE", "FTD", "DELIVERY", "VERIFIER", "GOVERNANCE",
        ]
        covered = [c for c in expected_categories if c in by_cat and by_cat[c] > 0]
        coverage_pct = round(len(covered) / len(expected_categories) * 100, 1)

        # Freshness: check if records exist from last 24h
        ts_24h_ago = int(time.time() * 1000) - 86_400_000
        recent = self._imraf.search("", limit=1)
        is_fresh = bool(recent and recent[0]["ts"] > ts_24h_ago)

        # Link integrity: knowledge graph coverage
        graph_coverage = round(len(_KNOWLEDGE_GRAPH) / 14 * 100, 1)  # 14 expected modules

        health_score = (
            (coverage_pct * 0.4) +          # 40% weight on category coverage
            (graph_coverage * 0.3) +         # 30% weight on graph coverage
            (100.0 if is_fresh else 50.0) * 0.3  # 30% weight on freshness
        )

        return {
            "overall_health_score": round(health_score, 1),
            "health_label": (
                "EXCELLENT" if health_score >= 80 else
                "GOOD"      if health_score >= 60 else
                "FAIR"      if health_score >= 40 else "POOR"
            ),
            "metrics": {
                "coverage": {
                    "categories_with_data": len(covered),
                    "total_categories":     len(expected_categories),
                    "coverage_pct":         coverage_pct,
                    "missing_categories":   [c for c in expected_categories if c not in covered],
                },
                "completeness": {
                    "total_records":    total,
                    "by_category":      by_cat,
                    "categories_empty": len(expected_categories) - len(covered),
                },
                "freshness": {
                    "has_records_last_24h": is_fresh,
                    "most_recent_record_ts": recent[0]["ts"] if recent else 0,
                },
                "link_integrity": {
                    "knowledge_graph_modules": len(_KNOWLEDGE_GRAPH),
                    "graph_coverage_pct":      graph_coverage,
                },
                "archive_growth": {
                    "total_records": total,
                },
            },
            "recommendations": (
                [f"Add records for: {', '.join(list(c for c in expected_categories if c not in covered)[:5])}"]
                if len(covered) < len(expected_categories) else []
            ) + (
                ["No records in last 24h — confirm engine is running and recording"]
                if not is_fresh else []
            ),
            "checked_ts": int(time.time() * 1000),
        }

    # ── Module 14: Engineering Intelligence Dashboard ─────────────────────────

    def get_engineering_dashboard(self) -> Dict[str, Any]:
        """
        Management-level engineering intelligence dashboard.
        Single API call that returns the full institutional state.
        """
        self._audit("Module14_Dashboard", "get")
        if not self._available:
            return {"status": "DEGRADED"}

        stats    = self._imraf.get_stats()
        roadmap  = self._aeos.get_roadmap_guidance()
        health   = self.get_knowledge_health()
        plan     = self._dial.plan_next_steps(limit=5)

        # Incident / regression counts
        incidents   = self._imraf.search("", limit=200)
        open_bugs   = [r for r in incidents if r["category"] == "BUG"
                       and r.get("data", {}).get("status", "FIXED") != "FIXED"]
        regressions = [r for r in incidents if r["category"] == "REGRESSION"]
        total_inc   = [r for r in incidents if r["category"] in ("INCIDENT", "FAILURE")]

        # Recent decisions
        recent_decisions = self._imraf.timeline(category="ARCHITECTURE", limit=5)

        # Verifier health summary
        verifier_recs = self._imraf.search("", category="VERIFIER", limit=20)
        avg_pass_rate = (
            sum(r.get("data", {}).get("pass_rate", 0) for r in verifier_recs)
            / max(len(verifier_recs), 1)
        ) if verifier_recs else 0

        return {
            "status": "OK",
            "dashboard_ts": int(time.time() * 1000),
            "summary": {
                "total_institutional_records": stats.get("total_records", 0),
                "categories_active":           len(stats.get("by_category", {})),
                "knowledge_health_score":      health.get("overall_health_score", 0),
                "knowledge_health_label":      health.get("health_label", ""),
            },
            "incident_panel": {
                "total_incidents":   len(total_inc),
                "open_bugs":         len(open_bugs),
                "regressions":       len(regressions),
                "open_incidents":    plan.get("open_incidents", 0),
            },
            "roadmap_panel": {
                "in_progress_ftds": plan.get("in_progress_ftds", 0),
                "next_actions":     plan.get("recommended_next_steps", [])[:3],
                "high_risk_modules": roadmap.get("high_risk_modules", [])[:3],
            },
            "verifier_panel": {
                "total_verifier_runs": len(verifier_recs),
                "avg_pass_rate_pct":   round(avg_pass_rate, 1),
            },
            "knowledge_panel": {
                "coverage_pct":   health.get("metrics", {}).get("coverage", {}).get("coverage_pct", 0),
                "is_fresh":       health.get("metrics", {}).get("freshness", {}).get("has_records_last_24h", False),
                "missing_cats":   health.get("metrics", {}).get("coverage", {}).get("missing_categories", [])[:5],
            },
            "recent_decisions": [
                {"title": r["title"], "ts": r["ts"]} for r in recent_decisions
            ],
            "ftd_registry":     _PROJECT_KNOWLEDGE["ftd_registry"],
        }

    # ── Boot Summary ─────────────────────────────────────────────────────────

    def get_boot_summary(self) -> str:
        health_score = 0.0
        try:
            if self._available:
                health_score = self.get_knowledge_health().get("overall_health_score", 0)
        except Exception:
            pass
        return (
            f"available={self._available} "
            f"knowledge_health={health_score:.0f}% "
            f"graph_modules={len(_KNOWLEDGE_GRAPH)} "
            f"ai_consumers={len(_AI_CONSUMERS)}"
        )

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "module":            "EMAEngine",
                "ftd":               "EMA-001",
                "available":         self._available,
                "query_count":       self._query_count,
                "audit_log_entries": len(self._audit_log),
                "knowledge_graph_modules": len(_KNOWLEDGE_GRAPH),
                "ai_consumers":      _AI_CONSUMERS,
                "boot_ts":           self._boot_ts,
                "modules": [
                    "Module1_AI_Abstraction", "Module2_ContextAssembly",
                    "Module3_ProjectKnowledge", "Module4_FTDHub",
                    "Module5_VerifierHub", "Module6_KnowledgeGraph",
                    "Module7_RoadmapIntelligence", "Module8_AutonomousContextPackage",
                    "Module9_DecisionTraceability", "Module10_LessonsLearned",
                    "Module11_MultiAI", "Module12_Governance",
                    "Module13_HealthMonitor", "Module14_Dashboard",
                ],
            }


# ── Singleton ─────────────────────────────────────────────────────────────────
ema = EMAEngine()
