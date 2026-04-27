"""
EOW Quant Engine — FTD-040: Consistency Engine
"Profit banana nahi — Profit ko repeatable banana."

This engine is the FINAL sizing layer applied before trade execution.
It coordinates the outputs of Phase 5/6 controllers and adds three new
dimensions that those controllers individually cannot provide:

  1. Equity Volatility Control   — rolling std-dev of equity returns.
                                   High volatility → brake size.

  2. Profit Smoothing            — consecutive-win brake.
                                   Prevents over-excitement / scaling euphoria.

  3. Unified System Mode         — single user-visible state that aggregates
                                   DD tier, recovery state, loss cluster, and
                                   equity volatility into one word: NORMAL /
                                   DEFENSIVE / RECOVERY / PAUSED.

What this engine does NOT do:
  - Replace DrawdownController, LossClusterController, CapitalRecoveryEngine,
    or StreakIntelligenceEngine. Those run independently. This engine reads
    their results to produce a unified view + adds new dimensions.
  - Boost size above existing multipliers. ConsistencyState.size_mult only
    reduces (≤ 1.0). Stability > speed.

Integration pattern:
    # Equity tick (alongside other equity updates)
    consistency_engine.update_equity(scaler.equity)

    # Pre-trade — after _combined_mult is computed
    _ce = consistency_engine.evaluate(
        consecutive_wins, consecutive_losses,
        dd_result, recovery_result, lcc_result
    )
    if not _ce.allowed:
        return   # mode=PAUSED
    _combined_mult = round(_combined_mult * _ce.size_mult, 6)

    # Post-trade — in the closed-trade handler
    consistency_engine.record_trade(last_trade.net_pnl)

    # Visibility — API endpoint or report
    consistency_engine.status()
"""
from __future__ import annotations

import statistics
from collections import deque
from dataclasses import dataclass, field
from typing import List

from loguru import logger

from config import cfg
from core.drawdown_controller import DrawdownResult
from core.capital_recovery import RecoveryResult
from core.loss_cluster import LossClusterResult


# ── Data contract ─────────────────────────────────────────────────────────────

@dataclass
class ConsistencyState:
    """
    Result of ConsistencyEngine.evaluate().

    size_mult is an ADDITIONAL multiplier applied AFTER Phase 5/6 combined_mult.
    It is always ≤ 1.0 — this engine only throttles, never amplifies.

    When allowed=False the trade must be skipped immediately (mode=PAUSED).
    """
    allowed:           bool   # False → block trade (PAUSED mode)
    mode:              str    # NORMAL | DEFENSIVE | RECOVERY | PAUSED
    size_mult:         float  # final additional multiplier (0.0–1.0)
    dd_pct:            float  # current drawdown as percentage
    equity_volatility: float  # rolling std-dev of equity returns
    win_brake_mult:    float  # profit-smoothing multiplier (0.70–1.0)
    reason:            str    # human-readable explanation for UI
    detail:            dict = field(default_factory=dict)  # full breakdown


# ── Engine ────────────────────────────────────────────────────────────────────

class ConsistencyEngine:
    """
    FTD-040 Consistency Engine — makes profit repeatable, not just possible.

    Instantiate once at module level.  All public methods are thread-safe for
    reading; equity/trade updates are called from the single event-loop thread
    so no locking is required.
    """

    def __init__(self) -> None:
        # Rolling equity returns for volatility measurement
        self._equity_history: deque = deque(maxlen=cfg.CE_EQUITY_VOL_WINDOW + 1)
        # Per-trade net PnL for rolling analysis
        self._trade_history:  deque = deque(maxlen=cfg.CE_ROLLING_DD_WINDOW)
        self._last_equity:    float = 0.0

        logger.info(
            f"[CONSISTENCY-ENGINE] FTD-040 online | "
            f"vol_window={cfg.CE_EQUITY_VOL_WINDOW} "
            f"vol_high={cfg.CE_EQUITY_VOL_HIGH:.2%} "
            f"vol_normal={cfg.CE_EQUITY_VOL_NORMAL:.2%} "
            f"win_brake_start={cfg.CE_WIN_BRAKE_START} "
            f"win_brake_per_win={cfg.CE_WIN_BRAKE_PER_WIN:.0%} "
            f"win_brake_min={cfg.CE_WIN_BRAKE_MIN:.0%} "
            f"noise_filter={cfg.CE_NOISE_FILTER_MIN_TRADES} trades"
        )

    # ── State updates (called every tick / every trade) ───────────────────────

    def update_equity(self, equity: float) -> None:
        """
        Record current equity for volatility tracking.
        Call on every tick, alongside drawdown_controller.update_equity().
        """
        if self._last_equity > 0 and equity > 0:
            ret = (equity - self._last_equity) / self._last_equity
            self._equity_history.append(ret)
        self._last_equity = equity

    def record_trade(self, net_pnl: float) -> None:
        """
        Record a completed trade result for rolling DD / pattern analysis.
        Call from the closed-trade handler in main.py.
        """
        self._trade_history.append(net_pnl)

    # ── Core evaluation ───────────────────────────────────────────────────────

    def evaluate(
        self,
        consecutive_wins:   int,
        consecutive_losses: int,
        dd_result:          DrawdownResult,
        recovery_result:    RecoveryResult,
        lcc_result:         LossClusterResult,
    ) -> ConsistencyState:
        """
        Evaluate unified consistency and return a ConsistencyState.

        Aggregates existing Phase 5/6 controller results together with the
        new equity-volatility and profit-smoothing dimensions into a single
        mode and composite size_mult.

        The returned size_mult must be applied AFTER the Phase 5/6 combined_mult.
        It is always ≤ 1.0 — this engine enforces stability, never amplification.
        """
        reasons:    List[str] = []
        final_mult: float     = 1.0
        allowed:    bool      = True
        trade_count: int      = len(self._trade_history)

        # ── 1. Equity Volatility Control (NEW) ────────────────────────────────
        eq_vol   = self._equity_volatility()
        vol_mult = 1.0

        if eq_vol >= cfg.CE_EQUITY_VOL_HIGH:
            # Noise filter: only apply hard brake when we have real trade history
            if trade_count >= cfg.CE_NOISE_FILTER_MIN_TRADES:
                vol_mult   = cfg.CE_EQUITY_VOL_HIGH_MULT
                final_mult = min(final_mult, vol_mult)
                reasons.append(f"EQ_VOL_HIGH({eq_vol:.2%}→{vol_mult:.0%}×)")
            else:
                # Not enough history — soft cap only, don't over-react
                vol_mult   = 0.90
                final_mult = min(final_mult, vol_mult)
                reasons.append(
                    f"EQ_VOL_NOISE_FILTER(vol={eq_vol:.2%} trades={trade_count}"
                    f"<{cfg.CE_NOISE_FILTER_MIN_TRADES}→soft)"
                )
        elif eq_vol >= cfg.CE_EQUITY_VOL_NORMAL:
            # Elevated but not critical — 10% soft brake
            vol_mult   = 0.90
            final_mult = min(final_mult, vol_mult)
            reasons.append(f"EQ_VOL_ELEVATED({eq_vol:.2%}→90%×)")

        # ── 2. Profit Smoothing — win-streak brake (NEW) ──────────────────────
        win_brake = self._win_brake(consecutive_wins)
        if win_brake < 1.0:
            final_mult = min(final_mult, win_brake)
            reasons.append(f"WIN_BRAKE({consecutive_wins} wins→{win_brake:.0%}×)")

        # ── 3. Mode consolidation (NEW) ───────────────────────────────────────
        mode = self._determine_mode(
            dd_result=dd_result,
            recovery_result=recovery_result,
            lcc_result=lcc_result,
            consecutive_losses=consecutive_losses,
        )

        if mode == "PAUSED":
            allowed    = False
            final_mult = 0.0
            reasons.append("MODE_PAUSED")
        # DEFENSIVE / RECOVERY modes don't add additional blocks here
        # (DrawdownController + LossCluster already reduced size upstream)

        reason_str = " | ".join(reasons) if reasons else f"MODE_{mode}_OK"

        detail = {
            "mode":               mode,
            "equity_volatility":  round(eq_vol, 6),
            "vol_mult":           round(vol_mult, 4),
            "win_brake_mult":     round(win_brake, 4),
            "consecutive_wins":   consecutive_wins,
            "consecutive_losses": consecutive_losses,
            "dd_pct":             round(dd_result.drawdown * 100, 2),
            "dd_tier":            dd_result.tier,
            "recovery_state":     recovery_result.state,
            "lcc_state":          lcc_result.state,
            "trade_history_len":  trade_count,
            "size_mult":          round(final_mult, 4),
            "allowed":            allowed,
            "reason":             reason_str,
        }

        if reasons or mode != "NORMAL":
            logger.debug(
                f"[CONSISTENCY-ENGINE] mode={mode} "
                f"size_mult={final_mult:.2f}× "
                f"reason={reason_str}"
            )

        return ConsistencyState(
            allowed=allowed,
            mode=mode,
            size_mult=round(final_mult, 4),
            dd_pct=round(dd_result.drawdown * 100, 2),
            equity_volatility=round(eq_vol, 6),
            win_brake_mult=round(win_brake, 4),
            reason=reason_str,
            detail=detail,
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _equity_volatility(self) -> float:
        """Rolling std-dev of equity returns. Returns 0.0 if < 5 data points."""
        returns = list(self._equity_history)
        if len(returns) < 5:
            return 0.0
        try:
            return statistics.stdev(returns)
        except statistics.StatisticsError:
            return 0.0

    def _win_brake(self, consecutive_wins: int) -> float:
        """
        Profit-smoothing multiplier for consecutive wins.
        Returns 1.0 when below brake threshold (no restriction).
        Decreases by CE_WIN_BRAKE_PER_WIN per additional win beyond the start,
        floored at CE_WIN_BRAKE_MIN.

        Example (defaults: start=3, per_win=0.05, min=0.70):
          3 wins → 0.95×  (1 extra win beyond start-1)
          5 wins → 0.85×
          7 wins → 0.75×
          9+ wins → 0.70× (floor)
        """
        if consecutive_wins < cfg.CE_WIN_BRAKE_START:
            return 1.0
        extra = consecutive_wins - cfg.CE_WIN_BRAKE_START + 1
        brake = 1.0 - extra * cfg.CE_WIN_BRAKE_PER_WIN
        return max(cfg.CE_WIN_BRAKE_MIN, round(brake, 4))

    def _determine_mode(
        self,
        dd_result:          DrawdownResult,
        recovery_result:    RecoveryResult,
        lcc_result:         LossClusterResult,
        consecutive_losses: int,
    ) -> str:
        """
        Consolidate all Phase 5/6 states into one user-visible mode.
        Priority: PAUSED > DEFENSIVE > RECOVERY > NORMAL
        """
        # PAUSED — hard stop
        if not dd_result.allowed or not lcc_result.ok:
            return "PAUSED"

        # DEFENSIVE — in meaningful drawdown or active loss streak
        if dd_result.tier in ("SOFT_CUT", "HARD_CUT"):
            return "DEFENSIVE"
        if consecutive_losses >= cfg.LCC_REDUCE_AFTER:
            return "DEFENSIVE"

        # RECOVERY — equity rising from a confirmed trough
        if recovery_result.state in ("DEFENSIVE", "RECOVERING"):
            return "RECOVERY"

        return "NORMAL"

    # ── Visibility ────────────────────────────────────────────────────────────

    def status(self) -> dict:
        """
        Dashboard-ready status dict. Exposed by /api/consistency.
        Shows current DD level, system mode context, and configuration.
        """
        eq_vol = self._equity_volatility()
        return {
            "equity_volatility_pct":  round(eq_vol * 100, 4),
            "equity_vol_window":      cfg.CE_EQUITY_VOL_WINDOW,
            "vol_high_threshold_pct": round(cfg.CE_EQUITY_VOL_HIGH * 100, 2),
            "vol_normal_threshold_pct": round(cfg.CE_EQUITY_VOL_NORMAL * 100, 2),
            "vol_high_size_mult":     cfg.CE_EQUITY_VOL_HIGH_MULT,
            "win_brake_start":        cfg.CE_WIN_BRAKE_START,
            "win_brake_per_win_pct":  round(cfg.CE_WIN_BRAKE_PER_WIN * 100, 0),
            "win_brake_min":          cfg.CE_WIN_BRAKE_MIN,
            "noise_filter_min_trades": cfg.CE_NOISE_FILTER_MIN_TRADES,
            "rolling_dd_window":      cfg.CE_ROLLING_DD_WINDOW,
            "trade_history_len":      len(self._trade_history),
            "equity_history_len":     len(self._equity_history),
            "module": "CONSISTENCY_ENGINE",
            "phase":  "FTD-040",
        }


# ── Module-level singleton ─────────────────────────────────────────────────────
consistency_engine = ConsistencyEngine()
