"""
PRP-002 — Opportunity Ecology Orchestrator

Single integration point for main.py. Coordinates all four signal ecology
modules into one unified decision per signal evaluation:

  1. AdaptiveRSIGovernor   → does this RSI reading pass dynamic bands?
  2. AlphaContextMemory     → is this regime/hour/strategy context profitable or toxic?
  3. SignalDensityEngine    → record flow health; detect drought/starvation
  4. ExplorationRecovery    → in starvation, issue curiosity trades at reduced size

Caller contract (main.py):
  At signal generation time:
    dec = opportunity_ecology.evaluate_opportunity(...)
    if not dec.approved: skip trade
    position_size *= dec.size_multiplier

  At trade close:
    opportunity_ecology.record_trade_outcome(regime, utc_hour, strategy_id, net_pnl)

Forensic outputs (via get_telemetry):
  prp002_ecology_snapshot.json
"""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from loguru import logger

from core.signal_ecology.adaptive_rsi_governor import (
    adaptive_rsi_governor, RSIDecision,
)
from core.signal_ecology.signal_density_engine import signal_density_engine
from core.signal_ecology.exploration_recovery import (
    exploration_recovery_governor, RecoveryDecision, RecoveryMode,
)
from core.signal_ecology.alpha_context_memory import alpha_context_memory


@dataclass
class EcologyDecision:
    """Full signal ecology verdict for one signal evaluation."""
    approved:             bool
    block_reason:         str            # "" if approved
    size_multiplier:      float          # 1.0 normal; <1 recovery; >1 context boost; 0 = hard block

    # Sub-module outputs (always populated for forensic use)
    rsi_blocked:          bool
    rsi_side:             Optional[str]  # "LONG" | "SHORT" | None
    rsi_block_reason:     str
    context_type:         str            # "PROFITABLE" | "TOXIC" | "NEUTRAL" | "UNKNOWN"
    context_boost_mult:   float          # raw boost from alpha context memory
    recovery_mode:        str            # RecoveryMode.value
    recovery_size_mult:   float          # raw mult from recovery governor

    symbol:               str
    regime:               str
    utc_hour:             int
    strategy_id:          str
    rsi_val:              float
    survival_rate:        float
    drought_seconds:      float
    ts:                   int = field(default_factory=lambda: int(time.time() * 1000))


class OpportunityEcology:
    """
    PRP-002 orchestrator. Thread-safe.

    Size multiplier resolution (priority order):
      1. RSI blocked → size_mult = 0, approved = False
      2. Context TOXIC → size_mult = 0, approved = False
      3. Recovery mode active (CURIOSITY/FORCED) → use recovery mult (do NOT amplify
         during recovery — keeps exploration conservative)
      4. Context PROFITABLE → apply context boost mult
      5. Otherwise → 1.0
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._total_evaluated:  int = 0
        self._total_approved:   int = 0
        self._total_rsi_blocked: int = 0
        self._total_ctx_blocked: int = 0
        self._total_recovery_trades: int = 0

    # ── Primary evaluation API ─────────────────────────────────────────────────

    def evaluate_opportunity(
        self,
        regime:      str,
        rsi_val:     float,
        rsi_prev:    float,
        above_sma:   bool,
        utc_hour:    int,
        strategy_id: str,
        symbol:      str = "",
    ) -> EcologyDecision:
        """
        Full ecology evaluation for one signal candidate.
        Returns EcologyDecision; caller checks .approved and multiplies by .size_multiplier.
        """
        with self._lock:
            self._total_evaluated += 1

            # 1. RSI governor
            rsi_dec: RSIDecision = adaptive_rsi_governor.get_signal(
                regime=regime,
                rsi_val=rsi_val,
                rsi_prev=rsi_prev,
                above_sma=above_sma,
                symbol=symbol,
            )

            if rsi_dec.blocked:
                # Record block everywhere
                signal_density_engine.record_block(
                    reason=rsi_dec.block_reason, regime=regime, symbol=symbol
                )
                exploration_recovery_governor.on_signal_blocked()
                self._total_rsi_blocked += 1

                snap = signal_density_engine.snapshot()
                rec_dec = exploration_recovery_governor.evaluate(
                    drought_seconds=snap.signals_per_hr,  # not relevant here, use drought
                    survival_rate=snap.survival_rate,
                    is_starvation=snap.is_starvation,
                )
                # Even in recovery we don't bypass RSI — ecology observes only
                return EcologyDecision(
                    approved=False,
                    block_reason=f"RSI: {rsi_dec.block_reason}",
                    size_multiplier=0.0,
                    rsi_blocked=True,
                    rsi_side=rsi_dec.side,
                    rsi_block_reason=rsi_dec.block_reason,
                    context_type="UNKNOWN",
                    context_boost_mult=1.0,
                    recovery_mode=rec_dec.mode.value,
                    recovery_size_mult=rec_dec.size_multiplier,
                    symbol=symbol,
                    regime=regime,
                    utc_hour=utc_hour,
                    strategy_id=strategy_id,
                    rsi_val=rsi_val,
                    survival_rate=snap.survival_rate,
                    drought_seconds=snap.signals_per_hr,
                )

            # 2. Alpha context memory
            ctx = alpha_context_memory.get_amplification(
                regime=regime,
                utc_hour=utc_hour,
                strategy=strategy_id,
            )

            if ctx["context_type"] == "TOXIC":
                signal_density_engine.record_block(
                    reason=f"TOXIC_CONTEXT:{ctx['context_key']}",
                    regime=regime, symbol=symbol,
                )
                exploration_recovery_governor.on_signal_blocked()
                self._total_ctx_blocked += 1

                snap = signal_density_engine.snapshot()
                return EcologyDecision(
                    approved=False,
                    block_reason=f"CONTEXT_TOXIC: {ctx['reason']}",
                    size_multiplier=0.0,
                    rsi_blocked=False,
                    rsi_side=rsi_dec.side,
                    rsi_block_reason="",
                    context_type="TOXIC",
                    context_boost_mult=0.0,
                    recovery_mode="NONE",
                    recovery_size_mult=1.0,
                    symbol=symbol,
                    regime=regime,
                    utc_hour=utc_hour,
                    strategy_id=strategy_id,
                    rsi_val=rsi_val,
                    survival_rate=snap.survival_rate,
                    drought_seconds=time.time() - signal_density_engine._last_pass_ts,
                )

            # 3. Signal passed RSI + context — record pass
            signal_density_engine.record_pass(regime=regime, symbol=symbol)
            exploration_recovery_governor.on_signal_passed()
            self._total_approved += 1

            # 4. Recovery governor evaluation (for size multiplier only)
            snap = signal_density_engine.snapshot()
            drought_sec = time.time() - signal_density_engine._last_pass_ts
            rec_dec: RecoveryDecision = exploration_recovery_governor.evaluate(
                drought_seconds=drought_sec,
                survival_rate=snap.survival_rate,
                is_starvation=snap.is_starvation,
            )

            # 5. Resolve final size multiplier
            if rec_dec.mode != RecoveryMode.NONE:
                # Recovery active → conservative; skip context boost
                final_mult = rec_dec.size_multiplier
                self._total_recovery_trades += 1
                logger.info(
                    f"[PRP-002] {symbol} RECOVERY trade | "
                    f"mode={rec_dec.mode.value} mult={final_mult:.2f}"
                )
            elif ctx["context_type"] == "PROFITABLE":
                final_mult = ctx["boost_mult"]
            else:
                final_mult = 1.0

            return EcologyDecision(
                approved=True,
                block_reason="",
                size_multiplier=final_mult,
                rsi_blocked=False,
                rsi_side=rsi_dec.side,
                rsi_block_reason="",
                context_type=ctx["context_type"],
                context_boost_mult=ctx["boost_mult"],
                recovery_mode=rec_dec.mode.value,
                recovery_size_mult=rec_dec.size_multiplier,
                symbol=symbol,
                regime=regime,
                utc_hour=utc_hour,
                strategy_id=strategy_id,
                rsi_val=rsi_val,
                survival_rate=snap.survival_rate,
                drought_seconds=drought_sec,
            )

    # ── Trade outcome recording ────────────────────────────────────────────────

    def record_trade_outcome(
        self,
        regime:      str,
        utc_hour:    int,
        strategy_id: str,
        net_pnl:     float,
    ) -> None:
        """Call at every trade close. Updates alpha context memory."""
        alpha_context_memory.record_outcome(
            regime=regime,
            utc_hour=utc_hour,
            strategy=strategy_id,
            net_pnl=net_pnl,
        )

    # ── Telemetry ──────────────────────────────────────────────────────────────

    def get_telemetry(self) -> Dict[str, Any]:
        with self._lock:
            snap = signal_density_engine.snapshot()
            return {
                "module":                "OpportunityEcology",
                "prp":                   "002",
                "total_evaluated":       self._total_evaluated,
                "total_approved":        self._total_approved,
                "total_rsi_blocked":     self._total_rsi_blocked,
                "total_ctx_blocked":     self._total_ctx_blocked,
                "total_recovery_trades": self._total_recovery_trades,
                "approval_rate":         round(
                    self._total_approved / self._total_evaluated, 4
                ) if self._total_evaluated > 0 else 0.0,
                "density_snapshot": {
                    "signals_per_hr":  snap.signals_per_hr,
                    "survival_rate":   snap.survival_rate,
                    "is_drought":      snap.is_drought,
                    "is_starvation":   snap.is_starvation,
                },
                "rsi_governor":   adaptive_rsi_governor.get_telemetry(),
                "density_engine": signal_density_engine.get_telemetry(),
                "recovery":       exploration_recovery_governor.get_telemetry(),
                "context_memory": alpha_context_memory.get_telemetry(),
                "ts":             int(time.time() * 1000),
            }

    def ecology_snapshot(self) -> Dict[str, Any]:
        """Compact snapshot for dashboard / API polling."""
        with self._lock:
            snap = signal_density_engine.snapshot()
            return {
                "report":                "prp002_ecology_snapshot",
                "prp":                   "002",
                "total_evaluated":       self._total_evaluated,
                "total_approved":        self._total_approved,
                "approval_rate":         round(
                    self._total_approved / self._total_evaluated, 4
                ) if self._total_evaluated > 0 else 0.0,
                "rsi_blocked":           self._total_rsi_blocked,
                "context_blocked":       self._total_ctx_blocked,
                "recovery_trades":       self._total_recovery_trades,
                "signals_per_hr":        snap.signals_per_hr,
                "survival_rate":         snap.survival_rate,
                "is_drought":            snap.is_drought,
                "is_starvation":         snap.is_starvation,
                "global_rsi_survival":   round(
                    adaptive_rsi_governor.global_survival_rate(), 4
                ),
                "context_memory": {
                    "total_contexts":   alpha_context_memory.get_telemetry()["total_contexts"],
                    "profitable_count": alpha_context_memory.get_telemetry()["profitable_count"],
                    "toxic_count":      alpha_context_memory.get_telemetry()["toxic_count"],
                },
                "ts": int(time.time() * 1000),
            }


# ── Singleton ──────────────────────────────────────────────────────────────────
opportunity_ecology = OpportunityEcology()
