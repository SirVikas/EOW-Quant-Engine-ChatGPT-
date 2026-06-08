"""
PHOENIX CORTEX — Module Registry  [CX-1]

The Module Registry is the foundation of CORTEX.  It catalogs every module in
the PHOENIX ecosystem, giving CORTEX the authoritative answer to:

  "What modules exist, what do they do, and which tier are they?"

Each ModuleDefinition records:
  - identity      : key, name, file path, category
  - tier          : A (direct PnL) | B (indirect PnL) | C (observability) | D (infra)
  - role          : signal | risk | execution | capital | governance | learning |
                    intelligence | reporting | infrastructure | utilities
  - state         : active | inactive | experimental | deprecated
  - i/o contract  : what data it consumes and what it produces
  - influence     : initial influence weight in the CORTEX matrix (0–100)
  - critical      : True if module failure should halt trading

The registry ships a built-in catalog of all Tier-A and Tier-B modules
identified in the architecture census (qFTD-PHOENIX-OBSX-CORTEX-001).
Tier-C/D modules are auto-discovered from the filesystem at boot.

Thread-safe singleton.
"""
from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


_CORE_ROOT = Path(__file__).resolve().parents[2] / "core"

# ── Tier / Role Constants ─────────────────────────────────────────────────────

TIER_A = "A"   # Direct PnL impact
TIER_B = "B"   # Indirect PnL impact
TIER_C = "C"   # Observability
TIER_D = "D"   # Infrastructure

ROLE_SIGNAL      = "signal"
ROLE_RISK        = "risk"
ROLE_EXECUTION   = "execution"
ROLE_CAPITAL     = "capital"
ROLE_GOVERNANCE  = "governance"
ROLE_LEARNING    = "learning"
ROLE_INTELLIGENCE= "intelligence"
ROLE_REPORTING   = "reporting"
ROLE_INFRA       = "infrastructure"
ROLE_UTILITIES   = "utilities"

STATE_ACTIVE      = "active"
STATE_INACTIVE    = "inactive"
STATE_EXPERIMENTAL= "experimental"
STATE_DEPRECATED  = "deprecated"


# ── Data Model ────────────────────────────────────────────────────────────────

@dataclass
class ModuleDefinition:
    key: str                          # Unique identifier
    name: str                         # Human label
    file_path: str                    # Relative to project root
    tier: str                         # A | B | C | D
    role: str                         # signal | risk | ...
    state: str                        # active | inactive | ...
    consumes: List[str]               # Logical inputs (e.g. "market_data", "trade_signals")
    produces: List[str]               # Logical outputs (e.g. "trade_signals", "position_size")
    influence_weight: float           # Initial CORTEX influence weight 0–100
    critical: bool                    # Trading halts if this module fails
    description: str = ""
    dependencies: List[str] = field(default_factory=list)  # Other module keys
    fdt_ref: str = ""                 # FTD reference that created this module
    registered_at: float = field(default_factory=time.time)
    auto_discovered: bool = False


# ── Registry ──────────────────────────────────────────────────────────────────

class CortexModuleRegistry:
    """CORTEX central module catalog."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._catalog: Dict[str, ModuleDefinition] = {}
        self._bootstrap_tier_ab()
        self._autodiscover_tier_cd()

    # ── Public API ────────────────────────────────────────────────────────────

    def register(self, defn: ModuleDefinition) -> None:
        with self._lock:
            self._catalog[defn.key] = defn

    def get(self, key: str) -> Optional[ModuleDefinition]:
        with self._lock:
            return self._catalog.get(key)

    def all(self) -> List[ModuleDefinition]:
        with self._lock:
            return list(self._catalog.values())

    def by_tier(self, tier: str) -> List[ModuleDefinition]:
        with self._lock:
            return [m for m in self._catalog.values() if m.tier == tier]

    def by_role(self, role: str) -> List[ModuleDefinition]:
        with self._lock:
            return [m for m in self._catalog.values() if m.role == role]

    def critical_modules(self) -> List[ModuleDefinition]:
        with self._lock:
            return [m for m in self._catalog.values() if m.critical]

    def summary(self) -> dict:
        with self._lock:
            mods = list(self._catalog.values())
        by_tier: Dict[str, int] = {}
        by_role: Dict[str, int] = {}
        by_state: Dict[str, int] = {}
        for m in mods:
            by_tier[m.tier]   = by_tier.get(m.tier, 0) + 1
            by_role[m.role]   = by_role.get(m.role, 0) + 1
            by_state[m.state] = by_state.get(m.state, 0) + 1
        return {
            "total_modules":    len(mods),
            "critical_modules": sum(1 for m in mods if m.critical),
            "by_tier":          by_tier,
            "by_role":          by_role,
            "by_state":         by_state,
            "auto_discovered":  sum(1 for m in mods if m.auto_discovered),
        }

    # ── Built-in Tier A / B Catalog ───────────────────────────────────────────

    def _bootstrap_tier_ab(self) -> None:
        _CATALOG: List[ModuleDefinition] = [
            # ── TIER A: Direct PnL Impact ─────────────────────────────────────
            ModuleDefinition(
                key="strategy_engine", name="Strategy Engine",
                file_path="strategies/alpha_engine.py",
                tier=TIER_A, role=ROLE_SIGNAL, state=STATE_ACTIVE,
                consumes=["market_data", "regime_state", "genome_dna"],
                produces=["trade_signals"],
                influence_weight=25.0, critical=True,
                description="Primary alpha signal generator using genome-evolved strategies",
                fdt_ref="FTD-REF-026",
            ),
            ModuleDefinition(
                key="risk_engine", name="Risk Engine",
                file_path="core/risk_engine.py",
                tier=TIER_A, role=ROLE_RISK, state=STATE_ACTIVE,
                consumes=["trade_signals", "pnl_state", "drawdown_state"],
                produces=["risk_approval", "risk_rejection"],
                influence_weight=30.0, critical=True,
                description="Live risk gate — primary PnL protection layer",
                fdt_ref="FTD-REF-023",
            ),
            ModuleDefinition(
                key="risk_controller", name="Risk Controller",
                file_path="core/risk_controller.py",
                tier=TIER_A, role=ROLE_RISK, state=STATE_ACTIVE,
                consumes=["pnl_state", "open_positions"],
                produces=["drawdown_state", "risk_limits"],
                influence_weight=28.0, critical=True,
                description="Drawdown and risk limit enforcement",
                dependencies=["risk_engine"],
            ),
            ModuleDefinition(
                key="execution_engine", name="Execution Engine",
                file_path="core/execution_engine.py",
                tier=TIER_A, role=ROLE_EXECUTION, state=STATE_ACTIVE,
                consumes=["risk_approval", "trade_signals"],
                produces=["executed_trades", "order_fills"],
                influence_weight=20.0, critical=True,
                description="Trade execution orchestration",
                fdt_ref="FTD-REF-023",
            ),
            ModuleDefinition(
                key="capital_allocator", name="Capital Allocator",
                file_path="core/capital_allocator.py",
                tier=TIER_A, role=ROLE_CAPITAL, state=STATE_ACTIVE,
                consumes=["trade_scorer_output", "pnl_state"],
                produces=["position_size"],
                influence_weight=22.0, critical=True,
                description="Score-based position sizing (Phase 4)",
                fdt_ref="FTD-REF-024",
            ),
            ModuleDefinition(
                key="trade_manager", name="Trade Manager",
                file_path="core/trade_manager.py",
                tier=TIER_A, role=ROLE_EXECUTION, state=STATE_ACTIVE,
                consumes=["executed_trades", "market_data"],
                produces=["managed_positions", "exit_signals"],
                influence_weight=20.0, critical=True,
                description="Position lifecycle management (entry→exit)",
                fdt_ref="FTD-REF-024",
            ),
            ModuleDefinition(
                key="trade_scorer", name="Trade Scorer",
                file_path="core/trade_scorer.py",
                tier=TIER_A, role=ROLE_SIGNAL, state=STATE_ACTIVE,
                consumes=["trade_signals", "market_context"],
                produces=["alpha_quality_scores"],
                influence_weight=18.0, critical=False,
                description="Alpha quality gate — scores signals before sizing",
                fdt_ref="FTD-REF-024",
            ),
            ModuleDefinition(
                key="signal_filter", name="Signal Filter",
                file_path="core/signal_filter.py",
                tier=TIER_A, role=ROLE_SIGNAL, state=STATE_ACTIVE,
                consumes=["trade_signals", "market_context"],
                produces=["filtered_signals"],
                influence_weight=20.0, critical=False,
                description="Signal quality gating layer",
            ),
            ModuleDefinition(
                key="profit_guard", name="Profit Guard",
                file_path="core/profit_guard.py",
                tier=TIER_A, role=ROLE_RISK, state=STATE_ACTIVE,
                consumes=["pnl_state", "open_positions"],
                produces=["profit_protection_signals"],
                influence_weight=15.0, critical=False,
                description="Profit protection — locks in gains",
                fdt_ref="FTD-REF-026",
            ),
            ModuleDefinition(
                key="drawdown_controller", name="Drawdown Controller",
                file_path="core/drawdown_controller.py",
                tier=TIER_A, role=ROLE_RISK, state=STATE_ACTIVE,
                consumes=["pnl_state", "drawdown_state"],
                produces=["dd_circuit_breaker"],
                influence_weight=25.0, critical=True,
                description="Drawdown circuit breaker (Phase 5)",
            ),
            ModuleDefinition(
                key="ev_engine", name="EV Engine",
                file_path="core/ev_engine.py",
                tier=TIER_A, role=ROLE_SIGNAL, state=STATE_ACTIVE,
                consumes=["trade_signals", "win_rate_history"],
                produces=["ev_gate_decision"],
                influence_weight=18.0, critical=False,
                description="Expected value gate — rejects negative-EV trades",
            ),
            ModuleDefinition(
                key="global_gate_controller", name="Global Gate Controller",
                file_path="core/gating/global_gate_controller.py",
                tier=TIER_A, role=ROLE_GOVERNANCE, state=STATE_ACTIVE,
                consumes=["all_gate_signals"],
                produces=["trade_permission"],
                influence_weight=35.0, critical=True,
                description="Master permission authority — Phase 6.6 hard gating",
                fdt_ref="Phase 6.6",
                dependencies=["risk_engine", "drawdown_controller"],
            ),
            ModuleDefinition(
                key="pre_trade_gate", name="Pre-Trade Gate",
                file_path="core/gating/pre_trade_gate.py",
                tier=TIER_A, role=ROLE_GOVERNANCE, state=STATE_ACTIVE,
                consumes=["trade_candidates", "risk_state"],
                produces=["trade_permission"],
                influence_weight=30.0, critical=True,
                description="Per-trade validation before execution",
            ),
            ModuleDefinition(
                key="capital_flow_engine", name="Capital Flow Engine",
                file_path="core/capital_flow_engine.py",
                tier=TIER_A, role=ROLE_CAPITAL, state=STATE_ACTIVE,
                consumes=["pnl_state", "position_state"],
                produces=["capital_allocation"],
                influence_weight=20.0, critical=False,
                fdt_ref="FTD-038/039",
            ),
            ModuleDefinition(
                key="consistency_engine", name="Consistency Engine",
                file_path="core/consistency_engine.py",
                tier=TIER_A, role=ROLE_RISK, state=STATE_ACTIVE,
                consumes=["all_module_outputs"],
                produces=["consistency_score", "consistency_violations"],
                influence_weight=22.0, critical=False,
                fdt_ref="FTD-040",
            ),
            # ── TIER B: Indirect PnL Impact ───────────────────────────────────
            ModuleDefinition(
                key="regime_detector", name="Regime Detector",
                file_path="core/regime_detector.py",
                tier=TIER_B, role=ROLE_SIGNAL, state=STATE_ACTIVE,
                consumes=["market_data", "volatility_data"],
                produces=["regime_state"],
                influence_weight=20.0, critical=False,
                description="Market regime identification",
            ),
            ModuleDefinition(
                key="regime_ai", name="Regime AI",
                file_path="core/regime_ai.py",
                tier=TIER_B, role=ROLE_INTELLIGENCE, state=STATE_ACTIVE,
                consumes=["market_data", "regime_state"],
                produces=["ai_regime_classification"],
                influence_weight=15.0, critical=False,
                description="AI-enhanced regime classification",
            ),
            ModuleDefinition(
                key="rl_engine", name="RL Engine",
                file_path="core/rl_engine.py",
                tier=TIER_B, role=ROLE_LEARNING, state=STATE_ACTIVE,
                consumes=["trade_outcomes", "market_context"],
                produces=["rl_weights", "rl_decisions"],
                influence_weight=15.0, critical=False,
                description="RL contextual bandit for strategy weighting",
            ),
            ModuleDefinition(
                key="genome_engine", name="Genome Engine",
                file_path="core/genome_engine.py",
                tier=TIER_B, role=ROLE_LEARNING, state=STATE_ACTIVE,
                consumes=["trade_outcomes", "performance_history"],
                produces=["genome_dna", "evolved_parameters"],
                influence_weight=15.0, critical=False,
                description="Strategy DNA evolution (genome)",
            ),
            ModuleDefinition(
                key="adaptive_filter", name="Adaptive Filter",
                file_path="core/adaptive_filter.py",
                tier=TIER_B, role=ROLE_SIGNAL, state=STATE_ACTIVE,
                consumes=["signal_history", "performance_feedback"],
                produces=["dynamic_thresholds"],
                influence_weight=15.0, critical=False,
                description="Dynamic signal threshold adjustment (Phase 5.1)",
            ),
            ModuleDefinition(
                key="adaptive_scorer", name="Adaptive Scorer",
                file_path="core/adaptive_scorer.py",
                tier=TIER_B, role=ROLE_SIGNAL, state=STATE_ACTIVE,
                consumes=["signal_features", "performance_history"],
                produces=["adaptive_weights"],
                influence_weight=12.0, critical=False,
                description="Dynamic signal weights based on recent performance",
            ),
            ModuleDefinition(
                key="edge_engine", name="Edge Engine",
                file_path="core/edge_engine.py",
                tier=TIER_B, role=ROLE_SIGNAL, state=STATE_ACTIVE,
                consumes=["trade_history", "strategy_performance"],
                produces=["edge_score", "edge_validity"],
                influence_weight=18.0, critical=False,
                fdt_ref="FTD-REF-024",
            ),
            ModuleDefinition(
                key="adaptive_edge_engine", name="Adaptive Edge Engine",
                file_path="core/adaptive_edge_engine.py",
                tier=TIER_B, role=ROLE_SIGNAL, state=STATE_ACTIVE,
                consumes=["edge_score", "regime_state"],
                produces=["adaptive_edge_decision"],
                influence_weight=16.0, critical=False,
                fdt_ref="FTD-037",
            ),
            ModuleDefinition(
                key="learning_engine", name="Learning Engine",
                file_path="core/learning_engine.py",
                tier=TIER_B, role=ROLE_LEARNING, state=STATE_ACTIVE,
                consumes=["trade_outcomes", "market_context"],
                produces=["learning_weights"],
                influence_weight=12.0, critical=False,
                fdt_ref="FTD-REF-023",
            ),
            ModuleDefinition(
                key="signal_truth_engine", name="Signal Truth Engine",
                file_path="core/signal_truth/signal_truth_engine.py",
                tier=TIER_B, role=ROLE_SIGNAL, state=STATE_ACTIVE,
                consumes=["trade_signals", "trade_outcomes"],
                produces=["signal_truth_score", "false_positive_flags"],
                influence_weight=18.0, critical=False,
                fdt_ref="PRP-001",
            ),
            ModuleDefinition(
                key="entry_truth_engine", name="Entry Truth Engine (ETE)",
                file_path="core/truth/entry_truth_engine.py",
                tier=TIER_B, role=ROLE_GOVERNANCE, state=STATE_ACTIVE,
                consumes=["trade_signals", "truth_archive"],
                produces=["entry_truth_score"],
                influence_weight=15.0, critical=False,
                description="Phase-1 observation mode — gate disabled until 500+ trades",
                fdt_ref="FTD-PHOENIX-ETE-001",
            ),
            ModuleDefinition(
                key="exit_truth_engine", name="Exit Truth Engine (XTE)",
                file_path="core/truth/exit_truth_engine.py",
                tier=TIER_B, role=ROLE_GOVERNANCE, state=STATE_ACTIVE,
                consumes=["exit_signals", "trade_outcomes"],
                produces=["exit_truth_score"],
                influence_weight=12.0, critical=False,
                fdt_ref="FTD-PHOENIX-XTE-001",
            ),
            ModuleDefinition(
                key="exploration_engine", name="Exploration Engine",
                file_path="core/exploration_engine.py",
                tier=TIER_B, role=ROLE_LEARNING, state=STATE_ACTIVE,
                consumes=["signal_history", "performance_history"],
                produces=["exploration_decisions"],
                influence_weight=10.0, critical=False,
                description="Exploration mode — Phase 5.1 freeze prevention",
            ),
            ModuleDefinition(
                key="safe_mode_engine", name="Safe Mode Engine",
                file_path="core/gating/safe_mode_engine.py",
                tier=TIER_B, role=ROLE_GOVERNANCE, state=STATE_ACTIVE,
                consumes=["gate_failure_events"],
                produces=["safe_mode_state"],
                influence_weight=25.0, critical=True,
                description="Auto-protection on failure cascade",
            ),
            ModuleDefinition(
                key="auto_intelligence_engine", name="Auto Intelligence Engine",
                file_path="core/intelligence/auto_intelligence_engine.py",
                tier=TIER_B, role=ROLE_INTELLIGENCE, state=STATE_ACTIVE,
                consumes=["performance_reports", "anomaly_events"],
                produces=["correction_plans"],
                influence_weight=12.0, critical=False,
                fdt_ref="FTD-030",
            ),
            ModuleDefinition(
                key="observability_orchestrator", name="Observability Orchestrator",
                file_path="core/observability/orchestrator.py",
                tier=TIER_C, role=ROLE_REPORTING, state=STATE_ACTIVE,
                consumes=["all_engine_state"],
                produces=["observability_snapshots"],
                influence_weight=5.0, critical=False,
                fdt_ref="FTD-053-GAIA",
            ),
            ModuleDefinition(
                key="imraf", name="IMRAF — Institutional Memory",
                file_path="core/institutional_memory/imraf_engine.py",
                tier=TIER_C, role=ROLE_INTELLIGENCE, state=STATE_ACTIVE,
                consumes=["decisions", "incidents", "knowledge_events"],
                produces=["institutional_memory_records"],
                influence_weight=8.0, critical=False,
                fdt_ref="FTD-IMR-001",
            ),
        ]
        for defn in _CATALOG:
            self._catalog[defn.key] = defn

    # ── Auto-discovery (Tier C/D) ─────────────────────────────────────────────

    def _autodiscover_tier_cd(self) -> None:
        """
        Walk core/ and register any .py file not already in the catalog.
        Auto-discovered modules get Tier D, role=infrastructure, weight=1.0.
        This ensures CORTEX has complete coverage even for unlisted modules.
        """
        if not _CORE_ROOT.exists():
            return
        with self._lock:
            known_paths = {m.file_path for m in self._catalog.values()}

        count = 0
        for py_file in _CORE_ROOT.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            rel = str(py_file.relative_to(_CORE_ROOT.parent))
            if rel in known_paths:
                continue
            key = rel.replace("/", ".").replace("\\", ".").removesuffix(".py")
            key = key.replace("core.", "", 1)
            with self._lock:
                if key in self._catalog:
                    continue
                self._catalog[key] = ModuleDefinition(
                    key=key,
                    name=py_file.stem.replace("_", " ").title(),
                    file_path=rel,
                    tier=TIER_D,
                    role=ROLE_INFRA,
                    state=STATE_ACTIVE,
                    consumes=[],
                    produces=[],
                    influence_weight=1.0,
                    critical=False,
                    auto_discovered=True,
                )
            count += 1


# Singleton
cortex_module_registry = CortexModuleRegistry()
