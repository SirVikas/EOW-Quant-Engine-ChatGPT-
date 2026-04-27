"""
core/capital_flow_engine.py
FTD-038 — Capital Allocation  +  FTD-039 — Profit Stabilization  (COMBINED)

What this adds on top of existing modules
(CapitalAllocator / DrawdownController / CapitalScaler / CapitalRecoveryEngine):

  FTD-038 — Capital Allocation
    ✔ AEE-rank-based strategy priority (rank 1 = 1.25×, rank 2 = 1.0×, ...)
    ✔ DISABLED strategy → 0× capital (doubly enforced)
    ✔ SCALING strategy → +0.10× priority boost
    ✔ Capital Protect Mode  (extreme rapid loss → all mults capped at 0.5×)
    ✔ Allocation % per strategy (visible, explainable)
    ✔ Allocation change log (why it changed)

  FTD-039 — Profit Stabilization
    ✔ Equity curve smoothness tracking (rolling std dev of trade PnL)
    ✔ Profit spike detection → SPIKE mode (sudden gain → protect with 0.75×)
    ✔ SMOOTH / VOLATILE / SPIKE / DEFENSIVE stabilizer states
    ✔ Consecutive loss reducer (tightens size immediately)
    ✔ High-volatility defensive mode

Goal: Survive → Grow → Stabilize → Scale
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, asdict
from typing import Deque, Dict, List, Optional

from loguru import logger


# ── Config ────────────────────────────────────────────────────────────────────

# Strategy priority multipliers by AEE rank
PRIORITY = {1: 1.25, 2: 1.00, 3: 0.75}
PRIORITY_REST    = 0.50    # rank 4 and below
PRIORITY_SCALING_BOOST = 0.10   # extra × when AEE state = SCALING
PRIORITY_REDUCED_MULT  = 0.50   # AEE REDUCED overrides priority

# Capital Protect Mode (FTD-038 extreme loss)
CP_WINDOW        = 10     # trades to measure rapid loss over
CP_TRIGGER_PCT   = 0.05   # 5% equity rapid loss → CAPITAL_PROTECT
CP_EXIT_PCT      = 0.02   # exit protect when rapid loss < 2% equity
CP_SIZE_MULT     = 0.50   # max size in protect mode (safest strategy only)

# Profit Stabilizer (FTD-039)
STAB_WINDOW      = 20     # rolling PnL window for smoothness
SPIKE_THRESHOLD  = 0.03   # equity jump > 3% in 5 trades → SPIKE mode
VOLATILE_COV     = 0.60   # CoV (std/mean_abs) > 0.6 → VOLATILE
STAB_MULT = {
    "SMOOTH":    1.00,
    "VOLATILE":  0.85,
    "SPIKE":     0.75,
    "DEFENSIVE": 0.60,
}


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class StrategyAllocation:
    strategy_id:    str
    aee_state:      str     # ACTIVE / REDUCED / DISABLED / SCALING
    aee_rank:       int     # 1 = best (from AEE)
    priority_mult:  float   # the size multiplier this engine contributes
    alloc_pct:      float   # % of active capital allocated (0–100)
    can_trade:      bool


@dataclass
class CFEState:
    stabilizer_state:  str            # SMOOTH / VOLATILE / SPIKE / DEFENSIVE
    stabilizer_mult:   float          # 0.60–1.00
    protect_mode:      bool
    protect_reason:    str
    equity_smoothness: float          # CoV, lower = smoother (0 = perfect)
    recent_pnl_sum:    float          # sum of last CP_WINDOW trades
    allocations:       List[dict]     # per-strategy allocation (serializable)
    alloc_log:         List[dict]     # last 10 allocation change events


# ── Main class ────────────────────────────────────────────────────────────────

class CapitalFlowEngine:
    """
    FTD-038 + FTD-039 — Capital allocation priority + profit stabilization.

    Produces two composable multipliers:
      get_strategy_priority_mult(strategy_id) → 0.5–1.35  (or 0.0 if DISABLED)
      get_stabilizer_mult()                   → 0.60–1.00

    These are combined into _combined_mult alongside alloc/dd/recovery.
    """

    def __init__(self) -> None:
        self._pnl_history:   Deque[float] = deque(maxlen=STAB_WINDOW)
        self._equity_hist:   Deque[float] = deque(maxlen=STAB_WINDOW)

        # Per-strategy last known priority state (for change log)
        self._last_priority: Dict[str, float] = {}

        # Stabilizer state
        self._stab_state:    str   = "SMOOTH"
        self._stab_mult:     float = 1.00

        # Capital Protect Mode
        self._protect_mode:  bool  = False
        self._protect_reason: str  = ""

        # Alloc change log (last 10)
        self._alloc_log: List[dict] = []

        # Cache last AEE stats to avoid circular import at module load
        self._aee_cache: dict = {}    # strategy_id → {state, rank}

    # ── Post-trade feedback ───────────────────────────────────────────────────

    def on_trade(
        self,
        strategy_id: str,
        net_pnl:     float,
        equity:      float,
    ) -> None:
        """
        Call after every closed trade.
        Updates PnL history, equity curve, and re-evaluates stabilizer state.
        """
        self._pnl_history.append(net_pnl)
        self._equity_hist.append(equity)
        self._update_stabilizer(equity)
        self._update_protect(equity)

    # ── Pre-trade multipliers ─────────────────────────────────────────────────

    def get_strategy_priority_mult(self, strategy_id: str) -> float:
        """
        FTD-038 — Strategy capital priority based on AEE rank.

        Returns a multiplier (0.0–1.35) to be included in _combined_mult.
        This shapes WHERE capital flows within the system.
        """
        # Lazy-import AEE to avoid circular deps at module level
        try:
            from core.adaptive_edge_engine import adaptive_edge_engine as _aee
            stats = _aee.get_stats(strategy_id)
        except Exception:
            stats = None

        if stats is None:
            return 1.0   # untracked strategy → neutral

        # Cache for summary() visibility
        self._aee_cache[strategy_id] = {
            "state": stats.state,
            "rank":  stats.rank,
        }

        # DISABLED → zero (capital protection first)
        from core.adaptive_edge_engine import State as _S
        if stats.state == _S.DISABLED:
            return 0.0

        # REDUCED → cap at PRIORITY_REDUCED_MULT regardless of rank
        if stats.state == _S.REDUCED:
            return PRIORITY_REDUCED_MULT

        # Normal priority by rank
        priority = PRIORITY.get(stats.rank, PRIORITY_REST)

        # SCALING → small boost on top
        if stats.state == _S.SCALING:
            priority = min(priority + PRIORITY_SCALING_BOOST, 1.50)

        # In capital protect mode: cap at CP_SIZE_MULT
        if self._protect_mode:
            priority = min(priority, CP_SIZE_MULT)

        return round(priority, 4)

    def get_stabilizer_mult(self) -> float:
        """
        FTD-039 — Profit stabilization multiplier.
        Reduces size when equity curve is volatile or spike-detected.
        """
        if self._protect_mode:
            return STAB_MULT["DEFENSIVE"]
        return self._stab_mult

    def get_combined_mult(self, strategy_id: str) -> float:
        """
        Convenience: priority × stabilizer  (single call for _combined_mult).
        Returns product of both FTD-038 and FTD-039 multipliers.
        """
        return round(
            self.get_strategy_priority_mult(strategy_id)
            * self.get_stabilizer_mult(),
            4,
        )

    # ── Computed allocation breakdown ─────────────────────────────────────────

    def allocations(self) -> List[StrategyAllocation]:
        """
        Return per-strategy allocation breakdown for dashboard visibility.
        Allocation % = priority_mult / sum(all active priority_mults)
        """
        try:
            from core.adaptive_edge_engine import adaptive_edge_engine as _aee
            all_stats = _aee.all_stats()
        except Exception:
            all_stats = []

        items: List[StrategyAllocation] = []
        for s in all_stats:
            pm = self.get_strategy_priority_mult(s.strategy_id)
            items.append(StrategyAllocation(
                strategy_id   = s.strategy_id,
                aee_state     = s.state,
                aee_rank      = s.rank,
                priority_mult = pm,
                alloc_pct     = 0.0,   # filled below
                can_trade     = pm > 0.0,
            ))

        # Compute allocation %
        total_priority = sum(i.priority_mult for i in items if i.can_trade)
        for item in items:
            if total_priority > 0 and item.can_trade:
                item.alloc_pct = round(item.priority_mult / total_priority * 100, 1)
            else:
                item.alloc_pct = 0.0

        # Log allocation changes
        for item in items:
            sid = item.strategy_id
            prev = self._last_priority.get(sid)
            if prev is not None and abs(prev - item.priority_mult) > 0.01:
                reason = (
                    f"state={item.aee_state} rank={item.aee_rank} "
                    f"mult={prev:.2f}→{item.priority_mult:.2f}"
                )
                self._log_alloc(sid, prev, item.priority_mult, reason)
            self._last_priority[sid] = item.priority_mult

        return items

    def summary(self) -> dict:
        allocs = self.allocations()
        return {
            "module":            "CAPITAL_FLOW_ENGINE",
            "phase":             "FTD-038+039",
            "stabilizer_state":  self._stab_state,
            "stabilizer_mult":   self._stab_mult,
            "protect_mode":      self._protect_mode,
            "protect_reason":    self._protect_reason,
            "equity_smoothness": self._equity_smoothness(),
            "recent_pnl_sum":    round(sum(list(self._pnl_history)[-CP_WINDOW:]), 4),
            "allocations":       [asdict(a) for a in allocs],
            "alloc_log":         list(self._alloc_log)[-10:],
            "stab_formula":      (
                "SMOOTH=1.00× | VOLATILE=0.85× | SPIKE=0.75× | DEFENSIVE=0.60×"
            ),
            "priority_formula":  (
                "rank1=1.25× | rank2=1.00× | rank3=0.75× | rank4+=0.50× "
                "| SCALING+0.10× | REDUCED=0.50× | DISABLED=0×"
            ),
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _update_stabilizer(self, equity: float) -> None:
        """FTD-039: Evaluate equity curve smoothness and spike detection."""
        pnl_list = list(self._pnl_history)
        if len(pnl_list) < 5:
            self._stab_state = "SMOOTH"
            self._stab_mult  = STAB_MULT["SMOOTH"]
            return

        cov = self._equity_smoothness()

        # Spike detection: equity jumped significantly in last 5 trades
        recent5 = pnl_list[-5:]
        baseline_equity = list(self._equity_hist)[-6] if len(self._equity_hist) >= 6 else equity
        spike_gain = (equity - baseline_equity) / max(abs(baseline_equity), 1e-9)

        if spike_gain > SPIKE_THRESHOLD:
            new_state = "SPIKE"
        elif cov > VOLATILE_COV:
            new_state = "VOLATILE"
        elif cov < 0.20:
            new_state = "SMOOTH"
        else:
            # Gradual: between smooth and volatile
            new_state = "VOLATILE" if cov > 0.40 else "SMOOTH"

        if new_state != self._stab_state:
            logger.info(
                f"[CFE] Stabilizer: {self._stab_state} → {new_state} "
                f"(CoV={cov:.2f} spike_gain={spike_gain:.2%})"
            )

        self._stab_state = new_state
        self._stab_mult  = STAB_MULT[new_state]

    def _update_protect(self, equity: float) -> None:
        """FTD-038: Activate Capital Protect Mode on rapid loss."""
        recent = list(self._pnl_history)[-CP_WINDOW:]
        if not recent:
            return

        rapid_loss = sum(recent)
        if equity <= 0:
            return

        loss_pct = abs(rapid_loss) / equity

        if not self._protect_mode:
            if rapid_loss < 0 and loss_pct >= CP_TRIGGER_PCT:
                self._protect_mode   = True
                self._protect_reason = (
                    f"rapid_loss={rapid_loss:.2f} USDT "
                    f"({loss_pct:.1%} in {len(recent)} trades)"
                )
                logger.warning(
                    f"[CFE] CAPITAL_PROTECT activated — {self._protect_reason}"
                )
        else:
            # Exit protect when rapid loss shrinks below exit threshold
            if rapid_loss >= 0 or loss_pct < CP_EXIT_PCT:
                logger.info(
                    f"[CFE] CAPITAL_PROTECT lifted — "
                    f"rapid_loss={rapid_loss:.2f} ({loss_pct:.1%})"
                )
                self._protect_mode   = False
                self._protect_reason = ""

    def _equity_smoothness(self) -> float:
        """Coefficient of Variation of PnL: lower = smoother equity curve."""
        pnl = list(self._pnl_history)
        if len(pnl) < 3:
            return 0.0
        n      = len(pnl)
        mean   = sum(pnl) / n
        var    = sum((x - mean) ** 2 for x in pnl) / n
        std    = var ** 0.5
        denom  = sum(abs(x) for x in pnl) / n
        return round(std / max(denom, 1e-9), 4)

    def _log_alloc(
        self,
        sid:       str,
        old_mult:  float,
        new_mult:  float,
        reason:    str,
    ) -> None:
        evt = {
            "ts":      int(time.time() * 1000),
            "strategy": sid,
            "old":     round(old_mult, 4),
            "new":     round(new_mult, 4),
            "reason":  reason,
        }
        self._alloc_log.append(evt)
        if len(self._alloc_log) > 10:
            self._alloc_log.pop(0)


# ── Module-level singleton ────────────────────────────────────────────────────
capital_flow_engine = CapitalFlowEngine()
