"""
EOW Quant Engine — core/orchestrator/execution_orchestrator.py
Phase 7A.1: Execution Orchestrator — Single Execution Authority

Central runtime controller. EVERY new-trade attempt flows through here.
No signal is generated, no capital is allocated, no order is placed without
explicit clearance from this orchestrator.

Exclusivity guarantee:
    Only ONE ExecutionOrchestrator may ever call run_cycle() per process.
    Any second orchestrator calling run_cycle() triggers RuntimeError.
    → enforce_exclusivity() is called at the start of every run_cycle() call.

Two-phase interaction:

    Phase A — Pre-signal gate check (BEFORE signal generation):
        orchestrator.gate_check() → GateCheckResult
        • Evaluates GlobalGateController + ScanController
        • Returns BLOCKED when can_trade=False or safe_mode=True
        • Caller MUST return immediately on blocked — do NOT generate signals

    Phase B — Full profit pipeline (AFTER quality filters have passed):
        orchestrator.run_cycle(ctx: TickContext) → CycleResult
        • enforce_exclusivity()  — abort if parallel executor detected
        • Re-evaluates gate     (1s cache — essentially free)
        • Rank → Compete → Concentrate → Pre-trade gate → Amplify
        • Exploration path: gate+scan+pre-trade only (no rank/compete/concentrate)
        • Returns CycleResult(execute=True, concentration_mult, tp_mult, trail_mult)

Full per-symbol per-tick flow:
    ┌─ gate_check() ─────────────────────── GATE BLOCKED → stop (no signal gen)
    │     ↓ ALLOWED
    │  [signal generation + quality filters in caller]
    │     ↓ signal exists + quality passed
    └─ run_cycle(ctx) ──────────────────── blocked at any step → stop
          enforce_exclusivity()            RuntimeError if dual executor
          gate re-check                   GATE_BLOCKED → stop
          scan re-check                   SCAN_BLOCKED → stop
          if exploration → PTG → EXECUTE  (skip rank/compete/concentrate)
          TradeRanker                     RANK_REJECT → stop
          CompetitionEngine               COMPETITION_REJECT → stop
          CapitalConcentrator             CONCENTRATE_REJECT → stop
          PreTradeGate                    PTG_BLOCKED → stop
          EdgeAmplifier                   (always returns; adds TP/trail params)
          → CycleResult(execute=True)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from loguru import logger

from core.gating.global_gate_controller import GlobalGateController, global_gate_controller as _default_ggc
from core.gating.safe_mode_engine import SafeModeEngine, safe_mode_engine as _default_sme
from core.gating.pre_trade_gate import PreTradeGate, pre_trade_gate as _default_ptg
from core.profit.scan_controller import ScanController, scan_controller as _default_sc
from core.profit.trade_ranker import GateAwareTradeRanker, trade_ranker as _default_ranker
from core.profit.trade_competition import (
    GateAwareCompetitionEngine,
    trade_competition_engine as _default_comp,
)
from core.profit.capital_concentrator import (
    GateAwareCapitalConcentrator,
    capital_concentrator as _default_cc,
)
from core.profit.edge_amplifier import GateAwareEdgeAmplifier, edge_amplifier as _default_amp
from core.trade_competition import TradeCandidate


# ── Exclusivity registry ──────────────────────────────────────────────────────
# Tracks the ONE orchestrator instance allowed to call run_cycle() in this process.
_EXECUTION_AUTHORITY: Optional["ExecutionOrchestrator"] = None


# ── Data contracts ────────────────────────────────────────────────────────────

@dataclass
class GateCheckResult:
    """Result of the pre-signal gate + scan check (Phase A)."""
    allowed:     bool
    action:      str   # ALLOWED | GATE_BLOCKED | SCAN_BLOCKED
    reason:      str
    gate_status: dict = field(default_factory=dict)


@dataclass
class TickContext:
    """
    All inputs the orchestrator needs for the full profit pipeline (Phase B).
    Populated by the caller after signal generation and quality filtering.

    is_exploration:
        True  → trade was injected by ExplorationEngine (bypasses rank/compete/concentrate)
                 gate + scan + pre-trade gate still apply — hard gate is never bypassed.
        False → normal quality-filtered trade (full pipeline).
    """
    symbol:         str
    price:          float
    regime:         str    # market regime ("TRENDING" etc.)
    strategy:       str    # strategy name ("TrendFollowing" etc.)
    ev:             float  # from EVEngine (USDT / unit risk); 0.0 for exploration
    trade_score:    float  # from AdaptiveScorer (0–1); raw conf for exploration
    volume_ratio:   float  # current_vol / avg_vol
    equity:         float  # current account equity (USDT)
    base_risk_usdt: float  # raw risk before any multipliers (from scaler)
    upstream_mult:  float  # combined mult from Phase 5/6 allocators
    indicator_ok:   bool   # indicator readiness
    data_fresh:     bool   # data freshness flag
    history_score:  Optional[float] = None   # from EdgeMemory; None = neutral 0.5
    is_exploration: bool   = False           # exploration trade flag


@dataclass
class CycleResult:
    """
    Result of the full orchestrator pipeline (Phase B).

    When execute=True:
        Apply sizing.qty  *= concentration_mult
        The concentrator already folds in upstream_mult + band boost.
        tp_multiplier / trail_multiplier come from EdgeAmplifier.

    When execute=False:
        concentration_mult = 1.0 (safe default)
        tp_multiplier      = 1.0
        trail_multiplier   = 1.0
    """
    action:             str    # EXECUTE | GATE_BLOCKED | SCAN_BLOCKED | RANK_REJECT |
                               # COMPETITION_REJECT | CONCENTRATE_REJECT | PTG_BLOCKED
    execute:            bool
    reason:             str
    concentration_mult: float = 1.0
    tp_multiplier:      float = 1.0
    trail_multiplier:   float = 1.0
    rank_score:         float = 0.0
    band:               str   = ""
    amplified:          bool  = False
    gate_status:        dict  = field(default_factory=dict)


# ── Orchestrator ──────────────────────────────────────────────────────────────

class ExecutionOrchestrator:
    """
    Single execution authority for the EOW Quant Engine.

    All new-trade activity flows through this class.  Instantiate ONCE and
    assign to the module-level singleton ``execution_orchestrator``.

    Constructor accepts optional overrides for every dependency so the class
    can be unit-tested without the full Phase 6.6 / 7A singleton stack.

    Args:
        exclusive: When True (default), registers this instance as the global
                   execution authority.  Pass False in tests that create
                   throwaway instances.
    """

    def __init__(
        self,
        global_gate:  Optional[GlobalGateController]         = None,
        safe_mode:    Optional[SafeModeEngine]               = None,
        scan_ctrl:    Optional[ScanController]               = None,
        ranker:       Optional[GateAwareTradeRanker]         = None,
        competition:  Optional[GateAwareCompetitionEngine]   = None,
        concentrator: Optional[GateAwareCapitalConcentrator] = None,
        pre_trade:    Optional[PreTradeGate]                 = None,
        amplifier:    Optional[GateAwareEdgeAmplifier]       = None,
        exclusive:    bool                                   = True,
    ):
        self._gate       = global_gate  or _default_ggc
        self._sme        = safe_mode    or _default_sme
        self._scan       = scan_ctrl    or _default_sc
        self._ranker     = ranker       or _default_ranker
        self._comp       = competition  or _default_comp
        self._conc       = concentrator or _default_cc
        self._ptg        = pre_trade    or _default_ptg
        self._amp        = amplifier    or _default_amp
        self._exclusive  = exclusive

        self._total_cycles:      int = 0
        self._total_blocked:     int = 0
        self._total_exec:        int = 0
        self._total_exploration: int = 0

        logger.info(
            f"[ORCHESTRATOR] Phase 7A.1 Execution Orchestrator online | "
            f"exclusive={exclusive}"
        )

    # ── Exclusivity enforcement ───────────────────────────────────────────────

    def detect_external_execution(self) -> bool:
        """
        Return True if another ExecutionOrchestrator instance has already
        claimed execution authority.  False when this IS the authority or
        when exclusivity checking is disabled.
        """
        global _EXECUTION_AUTHORITY
        if not self._exclusive:
            return False
        return _EXECUTION_AUTHORITY is not None and _EXECUTION_AUTHORITY is not self

    def enforce_exclusivity(self) -> None:
        """
        Assert that this is the ONLY active execution authority.

        Called at the start of every run_cycle() invocation.
        Raises RuntimeError if a different orchestrator instance has already
        registered as the execution authority — indicating an illegal parallel
        execution path exists.

        Side-effect: registers this instance as the authority on first call.
        """
        global _EXECUTION_AUTHORITY
        if self.detect_external_execution():
            raise RuntimeError(
                "[ORCHESTRATOR] CRITICAL: Legacy execution path detected — "
                "multiple ExecutionOrchestrator instances calling run_cycle(). "
                "Only one orchestrator may be the execution authority."
            )
        if self._exclusive:
            _EXECUTION_AUTHORITY = self

    @classmethod
    def _reset_authority(cls) -> None:
        """Reset the global authority registry.  TEST USE ONLY."""
        global _EXECUTION_AUTHORITY
        _EXECUTION_AUTHORITY = None

    # ── Phase A: Pre-signal gate check ───────────────────────────────────────

    def gate_check(
        self,
        symbol:       str            = "",
        strategy:     str            = "",
        indicator_ok: Optional[bool] = None,
        data_fresh:   Optional[bool] = None,
    ) -> GateCheckResult:
        """
        Fast gate + scan check.  MUST be called before signal generation.

        Returns BLOCKED immediately if gate is down or safe mode is active.
        Caller MUST return without generating any signals on BLOCKED.

        Args:
            indicator_ok: Pre-computed indicator readiness from caller (qFTD-004 SSOT fix).
                          None → gate uses its internal indicator_ready_fn().
            data_fresh:   Pre-computed data freshness from data_health_monitor.check().
                          None → gate uses its internal data_fresh_fn().

        Returns:
            GateCheckResult(allowed=True)  → proceed with signal generation
            GateCheckResult(allowed=False) → return from caller immediately
        """
        gate_status = self._gate.evaluate(
            indicator_ok=indicator_ok,
            data_fresh=data_fresh,
        )

        if not gate_status["can_trade"]:
            reason = gate_status.get("reason", "GATE_BLOCKED")
            self._sme.activate(reason)
            logger.warning(
                f"[ORCHESTRATOR] GATE BLOCKED — no scan | sym={symbol} reason={reason}"
            )
            return GateCheckResult(
                allowed=False, action="GATE_BLOCKED",
                reason=reason, gate_status=gate_status,
            )

        scan = self._scan.can_scan(gate_status)
        if not scan.allowed:
            logger.info(
                f"[ORCHESTRATOR] SCAN BLOCKED — no signal gen | "
                f"sym={symbol} reason={scan.reason}"
            )
            return GateCheckResult(
                allowed=False, action="SCAN_BLOCKED",
                reason=scan.reason, gate_status=gate_status,
            )

        return GateCheckResult(
            allowed=True, action="ALLOWED",
            reason="ALL_CLEAR", gate_status=gate_status,
        )

    # ── Phase B: Full profit pipeline ────────────────────────────────────────

    def run_cycle(self, ctx: TickContext) -> CycleResult:
        """
        Full gate-aware profit pipeline.  MUST be called after signal generation
        and all quality filters have passed.

        Enforces exclusivity on every call — raises if a parallel executor exists.

        Exploration trades (ctx.is_exploration=True) bypass rank/compete/concentrate
        but still respect the master gate, scan gate, and pre-trade gate.

        Returns:
            CycleResult(execute=True, concentration_mult, tp_multiplier, ...)
                → apply multipliers and submit order
            CycleResult(execute=False, reason=...)
                → skip trade; log reason
        """
        from core.orchestrator.execution_lock import ExecutionLock
        ExecutionLock.acquire()
        try:
            return self._run_cycle_inner(ctx)
        finally:
            ExecutionLock.release()

    def _run_cycle_inner(self, ctx: TickContext) -> CycleResult:
        self.enforce_exclusivity()
        self._total_cycles += 1

        # ── 1. Gate re-evaluation — pass ctx readiness values (qFTD-004 SSOT fix) ──
        gate_status = self._gate.evaluate(
            indicator_ok=ctx.indicator_ok,
            data_fresh=ctx.data_fresh,
        )

        if not gate_status["can_trade"]:
            reason = gate_status.get("reason", "GATE_BLOCKED")
            self._sme.activate(reason)
            logger.warning(
                f"[ORCHESTRATOR] BLOCKED in run_cycle | sym={ctx.symbol} reason={reason}"
            )
            self._total_blocked += 1
            return CycleResult(
                action="GATE_BLOCKED", execute=False,
                reason=reason, gate_status=gate_status,
            )

        # ── 2. Scan check ─────────────────────────────────────────────────
        scan = self._scan.can_scan(gate_status)
        if not scan.allowed:
            self._total_blocked += 1
            return CycleResult(
                action="SCAN_BLOCKED", execute=False,
                reason=scan.reason, gate_status=gate_status,
            )

        # ── Exploration fast-path (bypasses rank/compete/concentrate) ─────
        if ctx.is_exploration:
            ptg = self._ptg.check(
                gate_status,
                indicator_ok=ctx.indicator_ok,
                data_fresh=ctx.data_fresh,
                symbol=ctx.symbol,
                strategy=ctx.strategy,
            )
            if not ptg["allowed"]:
                self._total_blocked += 1
                return CycleResult(
                    action="PTG_BLOCKED", execute=False,
                    reason=ptg["reason"], gate_status=gate_status,
                )
            self._total_exploration += 1
            self._total_exec += 1
            logger.info(
                f"[ORCHESTRATOR] EXPLORATION_EXECUTE | sym={ctx.symbol} "
                f"upstream_mult={ctx.upstream_mult:.2f}×"
            )
            return CycleResult(
                action="EXECUTE", execute=True,
                reason="EXPLORATION_PATH",
                concentration_mult=ctx.upstream_mult,  # pass through; no band boost
                tp_multiplier=1.0,
                trail_multiplier=1.0,
                rank_score=0.0,
                band="EXPLORATION",
                amplified=False,
                gate_status=gate_status,
            )

        # ── 3. Trade Ranking ──────────────────────────────────────────────
        ranked = self._ranker.rank(
            gate_status,
            ev=ctx.ev,
            trade_score=ctx.trade_score,
            regime=ctx.regime,
            strategy=ctx.strategy,
            history_score=ctx.history_score,
        )
        if ranked is None or not ranked.ok:
            reason = ranked.reason if ranked is not None else "RANK_GATE_BLOCKED"
            self._total_blocked += 1
            return CycleResult(
                action="RANK_REJECT", execute=False,
                reason=reason, gate_status=gate_status,
            )

        # ── 4. Trade Competition ──────────────────────────────────────────
        candidate = TradeCandidate(
            signal_id=ctx.symbol,
            rank_score=ranked.rank_score,
            ev=ctx.ev,
            symbol=ctx.symbol,
            strategy=ctx.strategy,
        )
        comp = self._comp.select(gate_status, [candidate])
        if not comp.winners:
            self._total_blocked += 1
            return CycleResult(
                action="COMPETITION_REJECT", execute=False,
                reason=f"COMPETITION_REJECT(sym={ctx.symbol} rank={ranked.rank_score:.3f})",
                gate_status=gate_status,
            )

        # ── 5. Capital Concentration ──────────────────────────────────────
        conc = self._conc.concentrate(
            gate_status,
            rank_score=ranked.rank_score,
            equity=ctx.equity,
            base_risk_usdt=ctx.base_risk_usdt,
            upstream_mult=ctx.upstream_mult,
            ev=ctx.ev,   # Phase 7B: direct EV for secondary sizing boost/penalty
        )
        if not conc.ok:
            self._total_blocked += 1
            return CycleResult(
                action="CONCENTRATE_REJECT", execute=False,
                reason=conc.reason, gate_status=gate_status,
            )

        # ── 6. Pre-trade gate (final per-trade validation) ────────────────
        ptg = self._ptg.check(
            gate_status,
            indicator_ok=ctx.indicator_ok,
            data_fresh=ctx.data_fresh,
            symbol=ctx.symbol,
            strategy=ctx.strategy,
        )
        if not ptg["allowed"]:
            self._total_blocked += 1
            return CycleResult(
                action="PTG_BLOCKED", execute=False,
                reason=ptg["reason"], gate_status=gate_status,
            )

        # ── 7. Edge Amplification ─────────────────────────────────────────
        amp = self._amp.evaluate(
            gate_status,
            ev=ctx.ev,
            rank_score=ranked.rank_score,
            regime=ctx.regime,
            volume_ratio=ctx.volume_ratio,
        )

        self._total_exec += 1
        logger.info(
            f"[ORCHESTRATOR] EXECUTE | sym={ctx.symbol} "
            f"rank={ranked.rank_score:.3f} band={conc.band} "
            f"conc_mult={conc.size_multiplier:.2f}× "
            f"amplified={amp.amplified} "
            f"tp×={amp.tp_multiplier:.2f} trail×={amp.trail_multiplier:.2f}"
        )

        return CycleResult(
            action="EXECUTE",
            execute=True,
            reason="ALL_CLEAR",
            concentration_mult=conc.size_multiplier,
            tp_multiplier=amp.tp_multiplier,
            trail_multiplier=amp.trail_multiplier,
            rank_score=ranked.rank_score,
            band=conc.band,
            amplified=amp.amplified,
            gate_status=gate_status,
        )

    # ── Stats ─────────────────────────────────────────────────────────────────

    def summary(self) -> dict:
        total = self._total_cycles
        exec_rate = self._total_exec / total if total else 0.0
        return {
            "total_cycles":      self._total_cycles,
            "total_blocked":     self._total_blocked,
            "total_execute":     self._total_exec,
            "total_exploration": self._total_exploration,
            "execute_rate":      round(exec_rate, 4),
            "is_authority":      (
                _EXECUTION_AUTHORITY is self if self._exclusive else None
            ),
            "module": "EXECUTION_ORCHESTRATOR",
            "phase":  "7A.1",
        }


# ── Module-level singleton ────────────────────────────────────────────────────
execution_orchestrator = ExecutionOrchestrator(exclusive=True)
