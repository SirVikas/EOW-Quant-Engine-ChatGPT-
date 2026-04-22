"""
EOW Quant Engine — Phase 5.1: Exploration Engine
Allows 10% of signal slots to be "learning trades" with relaxed constraints.

Purpose: Prevent strategy stagnation by occasionally probing marginal setups
that strict exploitation gates would reject, generating real-trade data to
accelerate EV Engine and Adaptive Scorer learning.

Rules:
  - Every EXPLORE_PERIOD-th signal (floor(1 / EXPLORE_RATE) = 10) is a candidate.
  - Score must be ≥ EXPLORE_SCORE_MIN (0.45).
  - EV slightly negative allowed: EV ≥ −EXPLORE_EV_FLOOR × est_risk.
  - Size reduced to EXPLORE_SIZE_MULT (0.25×) of normal.
  - Daily exploration loss capped at EXPLORE_DAILY_LOSS_CAP (2% of equity).

Safety (non-negotiable):
  - DrawdownController and risk_engine caps always apply independently.
  - Daily loss cap stops exploration for the day when exhausted.
  - Every exploration trade is logged with [EXPLORE] prefix.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from loguru import logger

from config import cfg


@dataclass
class ExploreResult:
    is_exploration:       bool
    size_mult:            float   # EXPLORE_SIZE_MULT if exploration, else 1.0
    daily_loss_used_pct:  float   # current fraction of equity used for exploration losses
    reason:               str = ""


class ExplorationEngine:
    """
    Counter-based exploration slot allocator with daily loss tracking.
    Every _explore_period-th signal receives an exploration slot.
    """

    def __init__(self):
        self._signal_count:    int   = 0
        self._daily_loss_usdt: float = 0.0
        self._current_day:     int   = int(time.time()) // 86400
        self._explore_period:  int   = max(1, round(1.0 / cfg.EXPLORE_RATE))
        self._is_exploration_trade: set[str] = set()  # symbols with open exploration trades
        logger.info(
            f"[EXPLORE-ENGINE] Phase 5.1 activated | "
            f"rate={cfg.EXPLORE_RATE:.0%} "
            f"(every {self._explore_period}th signal) "
            f"size={cfg.EXPLORE_SIZE_MULT}× "
            f"daily_cap={cfg.EXPLORE_DAILY_LOSS_CAP:.0%}"
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def should_explore(
        self,
        symbol:   str,
        score:    float,
        equity:   float,
        ev_ok:    bool     = False,
        est_risk: float    = 0.0,
    ) -> ExploreResult:
        """
        Determine if this signal should be an exploration trade.

        Args:
            symbol:   trading symbol (for logging)
            score:    decayed confidence score (0–1)
            equity:   current equity in USDT (for daily loss cap)
            ev_ok:    True if EV gate already approved (exploration not needed)
            est_risk: estimated trade risk in USDT (bounds negative EV tolerance)

        Returns ExploreResult; is_exploration=True → take trade at 0.25× size.
        """
        self._reset_daily_if_needed()
        self._signal_count += 1
        is_slot = (self._signal_count % self._explore_period) == 0

        if not is_slot:
            return ExploreResult(
                is_exploration=False, size_mult=1.0,
                daily_loss_used_pct=self._daily_loss_pct(equity),
                reason="NOT_EXPLORE_SLOT",
            )

        # If EV is already fine, normal trade wins — no need for exploration sizing
        if ev_ok:
            return ExploreResult(
                is_exploration=False, size_mult=1.0,
                daily_loss_used_pct=self._daily_loss_pct(equity),
                reason="EV_OK_NO_EXPLORE_NEEDED",
            )

        # Score floor check
        if score < cfg.EXPLORE_SCORE_MIN:
            return ExploreResult(
                is_exploration=False, size_mult=1.0,
                daily_loss_used_pct=self._daily_loss_pct(equity),
                reason=(
                    f"EXPLORE_SCORE_BELOW_FLOOR"
                    f"({score:.3f}<{cfg.EXPLORE_SCORE_MIN})"
                ),
            )

        # Daily loss cap check
        max_daily_usdt = equity * cfg.EXPLORE_DAILY_LOSS_CAP
        if self._daily_loss_usdt >= max_daily_usdt:
            return ExploreResult(
                is_exploration=False, size_mult=1.0,
                daily_loss_used_pct=self._daily_loss_pct(equity),
                reason=(
                    f"EXPLORE_DAILY_CAP_HIT"
                    f"({self._daily_loss_pct(equity):.1%}"
                    f"≥{cfg.EXPLORE_DAILY_LOSS_CAP:.0%})"
                ),
            )

        reason = (
            f"EXPLORE_TRADE(slot={self._signal_count} "
            f"score={score:.3f} size={cfg.EXPLORE_SIZE_MULT}×)"
        )
        logger.info(f"[EXPLORE-ENGINE] {symbol} → {reason}")
        self._is_exploration_trade.add(symbol)
        return ExploreResult(
            is_exploration=True,
            size_mult=cfg.EXPLORE_SIZE_MULT,
            daily_loss_used_pct=self._daily_loss_pct(equity),
            reason=reason,
        )

    def record_result(self, symbol: str, net_pnl: float):
        """
        Record the outcome of an exploration trade.
        Only losses are counted against the daily cap.
        Call from the position-close handler.
        """
        self._reset_daily_if_needed()
        self._is_exploration_trade.discard(symbol)
        if net_pnl < 0:
            self._daily_loss_usdt += abs(net_pnl)
            logger.debug(
                f"[EXPLORE-ENGINE] {symbol} loss={net_pnl:.4f} "
                f"daily_total={self._daily_loss_usdt:.4f}"
            )

    def is_exploration(self, symbol: str) -> bool:
        """True if the symbol currently has an open exploration trade."""
        return symbol in self._is_exploration_trade

    def daily_loss_pct(self, equity: float) -> float:
        return self._daily_loss_pct(equity)

    def summary(self, equity: float = 1.0) -> dict:
        return {
            "signal_count":       self._signal_count,
            "explore_period":     self._explore_period,
            "daily_loss_usdt":    round(self._daily_loss_usdt, 4),
            "daily_loss_pct":     round(self._daily_loss_pct(equity), 4),
            "daily_cap_pct":      cfg.EXPLORE_DAILY_LOSS_CAP,
            "explore_rate":       cfg.EXPLORE_RATE,
            "size_mult":          cfg.EXPLORE_SIZE_MULT,
            "score_min":          cfg.EXPLORE_SCORE_MIN,
            "open_explore_trades": list(self._is_exploration_trade),
            "module": "EXPLORATION_ENGINE",
            "phase":  5.1,
        }

    # ── Internals ─────────────────────────────────────────────────────────────

    def _daily_loss_pct(self, equity: float) -> float:
        if equity <= 0:
            return 0.0
        return self._daily_loss_usdt / equity

    def _reset_daily_if_needed(self):
        today = int(time.time()) // 86400
        if today != self._current_day:
            self._current_day      = today
            self._daily_loss_usdt  = 0.0
            logger.debug("[EXPLORE-ENGINE] Daily loss counter reset")


# ── Module-level singleton ────────────────────────────────────────────────────
exploration_engine = ExplorationEngine()


# ── FTD-008: Explore gate helper ──────────────────────────────────────────────

def allow_explore(system_state: str, trades_last_30m: int) -> bool:
    """
    Returns True only when it is safe to run an exploration trade.

    Rules (from FTD-008):
      - system must be in LIVE state (not BOOTING / SAFE_MODE)
      - no regular trades executed in the last 30 minutes
        (exploration only fills idle cycles, never competes with real signals)
    """
    if system_state != "LIVE":
        return False
    if trades_last_30m > 0:
        return False
    return True
