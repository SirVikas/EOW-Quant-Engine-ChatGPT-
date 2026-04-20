"""
EOW Quant Engine — core/orchestrator/execution_orchestrator.py
Phase 7A Integration: Execution Orchestrator — Nervous System

Central runtime controller. Every new-trade attempt flows through here.
No signal is generated, no capital is allocated, no order is placed without
explicit clearance from this orchestrator.

Two-phase interaction:

    Phase A — Pre-signal gate check (BEFORE signal generation):
        orchestrator.gate_check() → GateCheckResult
        • Evaluates GlobalGateController + ScanController
        • Returns fast BLOCKED when can_trade=False or safe_mode=True
        • Caller MUST return immediately on blocked; do NOT generate signals

    Phase B — Full profit pipeline (AFTER quality filters have passed):
        orchestrator.run_cycle(ctx: TickContext) → CycleResult
        • Re-evaluates gate (1s cache, essentially free)
        • Rank → Compete → Concentrate → Pre-trade gate → Amplify
        • Returns EXECUTE=True with sizing/amplification params on success

Full execution flow (per symbol per tick):
    ┌─ gate_check() ─────────────────────────────── GATE BLOCKED → stop
    │     ↓ ALLOWED
    │  [signal generation + quality filters in caller]
    │     ↓ signal exists + quality passed
    └─ run_cycle(ctx) ──────────────────────────── BLOCKED at any step → stop
          → TradeRanker              RANK_REJECT → stop
          → CompetitionEngine        COMPETITION_REJECT → stop
          → CapitalConcentrator      CONCENTRATE_REJECT → stop (rank below all bands)
          → PreTradeGate             PTG_BLOCKED → stop
          → EdgeAmplifier            (always returns; just adds TP/trail params)
          → CycleResult(execute=True, concentration_mult, tp_mult, trail_mult)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

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


# ── Data contracts ────────────────────────────────────────────────────────────

@dataclass
class GateCheckResult:
    """Result of the pre-signal gate + scan check."""
    allowed: bool
    action:  str    # ALLOWED | GATE_BLOCKED | SCAN_BLOCKED
    reason:  str
    gate_status: dict = field(default_factory=dict)


@dataclass
class TickContext:
    """
    All inputs the orchestrator needs to run the full profit pipeline.
    Populated by the caller after signal generation and quality filtering.
    """
    symbol:          str
    price:           float
    regime:          str    # market regime string ("TRENDING" etc.)
    strategy:        str    # strategy name ("TrendFollowing" etc.)
    ev:              float  # from EVEngine (USDT / unit risk)
    trade_score:     float  # from AdaptiveScorer composite (0–1)
    volume_ratio:    float  # current_vol / avg_vol
    equity:          float  # current account equity (USDT)
    base_risk_usdt:  float  # raw risk before any multipliers (from scaler)
    upstream_mult:   float  # combined mult from Phase 5/6 allocators (DD+LossCluster+CapAllocator)
    indicator_ok:    bool   # indicator readiness (from indicator_guard.ok)
    data_fresh:      bool   # data freshness flag
    history_score:   Optional[float] = None  # from EdgeMemory (None = neutral 0.5)


@dataclass
class CycleResult:
    """
    Result of the full orchestrator pipeline.

    If execute=True:
        • Apply sizing.qty  *= concentration_mult (INSTEAD of the Phase 5/6 upstream_mult
          since the concentrator already folds upstream_mult in)
        • Apply take_profit  = entry + (entry - stop_loss) * rr * tp_multiplier
        • Trail SL aggressiveness *= trail_multiplier

    If execute=False:
        All multipliers are 1.0 / 0.0 as appropriate.
    """
    action:             str    # EXECUTE | GATE_BLOCKED | SCAN_BLOCKED | RANK_REJECT |
                               # COMPETITION_REJECT | CONCENTRATE_REJECT | PTG_BLOCKED
    execute:            bool
    reason:             str
    concentration_mult: float = 1.0  # size multiplier from CapitalConcentrator
    tp_multiplier:      float = 1.0  # TP boost from EdgeAmplifier
    trail_multiplier:   float = 1.0  # trail aggr boost from EdgeAmplifier
    rank_score:         float = 0.0
    band:               str   = ""
    amplified:          bool  = False
    gate_status:        dict  = field(default_factory=dict)


# ── Orchestrator ──────────────────────────────────────────────────────────────

class ExecutionOrchestrator:
    """
    Nervous system of the EOW Quant Engine.

    All profit-engine activity flows through this class.
    No signal is generated, no trade is placed without its approval.

    Constructor accepts optional overrides for all dependencies to allow
    clean unit testing without the full Phase 6.6 / 7A singleton stack.
    """

    def __init__(
        self,
        global_gate:   Optional[GlobalGateController]        = None,
        safe_mode:     Optional[SafeModeEngine]              = None,
        scan_ctrl:     Optional[ScanController]              = None,
        ranker:        Optional[GateAwareTradeRanker]        = None,
        competition:   Optional[GateAwareCompetitionEngine]  = None,
        concentrator:  Optional[GateAwareCapitalConcentrator]= None,
        pre_trade:     Optional[PreTradeGate]                = None,
        amplifier:     Optional[GateAwareEdgeAmplifier]      = None,
    ):
        self._gate       = global_gate  or _default_ggc
        self._sme        = safe_mode    or _default_sme
        self._scan       = scan_ctrl    or _default_sc
        self._ranker     = ranker       or _default_ranker
        self._comp       = competition  or _default_comp
        self._conc       = concentrator or _default_cc
        self._ptg        = pre_trade    or _default_ptg
        self._amp        = amplifier    or _default_amp

        self._total_cycles:  int = 0
        self._total_blocked: int = 0
        self._total_exec:    int = 0

        logger.info("[ORCHESTRATOR] Phase 7A Execution Orchestrator online")

    # ── Phase A: Pre-signal gate check ───────────────────────────────────────

    def gate_check(
        self,
        symbol:       str  = "",
        strategy:     str  = "",
        indicator_ok: bool = True,
        data_fresh:   bool = True,
    ) -> GateCheckResult:
        """
        Fast gate + scan check.  MUST be called before signal generation.
        Return immediately on blocked — do NOT generate signals.

        Args:
            symbol:       trading pair (for log context)
            strategy:     strategy name (for log context)
            indicator_ok: current indicator readiness
            data_fresh:   current data freshness

        Returns:
            GateCheckResult(allowed=False) → return from caller immediately
            GateCheckResult(allowed=True)  → proceed with signal generation
        """
        gate_status = self._gate.evaluate()

        if not gate_status["can_trade"]:
            reason = gate_status.get("reason", "GATE_BLOCKED")
            self._sme.activate(reason)
            logger.warning(f"[ORCHESTRATOR] BLOCKED | sym={symbol} reason={reason}")
            return GateCheckResult(
                allowed=False, action="GATE_BLOCKED",
                reason=reason, gate_status=gate_status,
            )

        scan = self._scan.can_scan(gate_status)
        if not scan.allowed:
            logger.info(f"[ORCHESTRATOR] Scan skipped | sym={symbol} reason={scan.reason}")
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
        Full gate-aware profit pipeline.  Call AFTER signal generation and
        all quality filters (RR, EV, score, signal_filter) have passed.

        The gate is re-evaluated here (1s cache makes this ~free).
        If any step blocks, returns a CycleResult with execute=False.

        Args:
            ctx: TickContext populated from the caller's quality-filter outputs.

        Returns:
            CycleResult(execute=True, concentration_mult, tp_multiplier, ...)
                → apply multipliers and place order
            CycleResult(execute=False, reason=...)
                → skip trade; log reason
        """
        self._total_cycles += 1

        # ── 1. Gate re-evaluation (uses cache — essentially free) ─────────
        gate_status = self._gate.evaluate()

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
        )
        if not conc.ok:
            self._total_blocked += 1
            return CycleResult(
                action="CONCENTRATE_REJECT", execute=False,
                reason=conc.reason, gate_status=gate_status,
            )

        # ── 6. Pre-trade gate (final per-trade check) ─────────────────────
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
            "total_cycles":  self._total_cycles,
            "total_blocked": self._total_blocked,
            "total_execute": self._total_exec,
            "execute_rate":  round(exec_rate, 4),
            "module": "EXECUTION_ORCHESTRATOR",
            "phase":  "7A",
        }


# ── Module-level singleton ────────────────────────────────────────────────────
execution_orchestrator = ExecutionOrchestrator()
