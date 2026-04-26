"""
EOW Quant Engine — FTD-033 Part 6: Exploration Mode Controller

Controls "bulk learning" trades that are allowed through with reduced size
even when net edge is marginal or slightly negative.

Rules:
  ✔ Allow more trades (relaxed score floor)
  ✔ Allow low net edge (tagged as EXPLORE)
  ✔ Reduce size to EXPLORE_SIZE_MULT (0.25×)
  ✔ Track separately from main P&L
  ✔ Daily loss cap enforced independently

Complements core/exploration_engine.py (which manages counter-based slots).
This controller focuses on cost-aware exploration decisions.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

try:
    from config import cfg
    _EXPLORATION_MODE        = getattr(cfg, "EXPLORATION_MODE",           True)
    _EXPLORE_SIZE_MULT       = cfg.EXPLORE_SIZE_MULT
    _EXPLORE_DAILY_LOSS      = cfg.EXPLORE_DAILY_LOSS_CAP
    _EXPLORE_SCORE_MIN       = cfg.EXPLORE_SCORE_MIN
    _MIN_NET_EDGE            = getattr(cfg, "COST_MIN_NET_EDGE_PCT",       0.001)
    _EXPLORE_LOSS_MAX_PCT    = getattr(cfg, "COST_EXPLORE_LOSS_MAX_PCT",   0.0005)
    _EXPLORE_MAX_TRADES_DAY  = getattr(cfg, "EXPLORE_MAX_TRADES_PER_DAY",  20)
except Exception:
    _EXPLORATION_MODE        = True
    _EXPLORE_SIZE_MULT       = 0.25
    _EXPLORE_DAILY_LOSS      = 0.02
    _EXPLORE_SCORE_MIN       = 0.60
    _MIN_NET_EDGE            = 0.001
    _EXPLORE_LOSS_MAX_PCT    = 0.0005
    _EXPLORE_MAX_TRADES_DAY  = 20


@dataclass
class ExploreDecision:
    """Outcome of exploration evaluation for a single signal."""
    allow:           bool
    size_mult:       float
    tagged:          bool     # True = EXPLORE tag applied to order
    reason:          str = ""
    daily_loss_used: float = 0.0


@dataclass
class ExploreTradeRecord:
    """Record of an exploration trade for cost-aware tracking."""
    symbol:       str
    signal_type:  str
    net_edge_pct: float
    size_mult:    float
    actual_pnl:   Optional[float] = None    # filled after close
    timestamp:    float = field(default_factory=time.time)


class ExplorationController:
    """
    Decides whether a marginally-rejected signal should be allowed
    through as an exploration trade.

    Separate from core/exploration_engine.py (counter-based slot allocation).
    This controller evaluates cost-specific criteria:
      - Is EXPLORATION_MODE enabled?
      - Is the net_edge within the exploration floor?
      - Is the score above the exploration minimum?
      - Is the daily exploration loss cap not exhausted?
    """

    def __init__(self):
        self._daily_loss_usdt:  float = 0.0
        self._daily_trade_count: int  = 0         # qFTD-033R Q13: max-trades guardrail
        self._current_day:      int   = int(time.time()) // 86400
        self._records:          list[ExploreTradeRecord] = []
        self._equity_ref:       float = 1000.0   # updated by caller

    # ── Public API ────────────────────────────────────────────────────────────

    def set_equity(self, equity: float) -> None:
        self._equity_ref = max(equity, 1.0)

    def should_explore(
        self,
        net_edge_pct:  float,
        score:         float,
    ) -> ExploreDecision:
        """
        Decide whether a marginal signal qualifies for exploration.

        Args:
            net_edge_pct: net edge as percentage of notional (can be negative)
            score:        signal quality score (0–1)
        """
        self._reset_day_if_needed()

        if not _EXPLORATION_MODE:
            return ExploreDecision(allow=False, size_mult=0.0, tagged=False,
                                   reason="EXPLORATION_MODE disabled")

        if score < _EXPLORE_SCORE_MIN:
            return ExploreDecision(allow=False, size_mult=0.0, tagged=False,
                                   reason=f"score {score:.3f} < floor {_EXPLORE_SCORE_MIN}")

        # Check edge is within exploration floor (not too negative)
        floor_pct = -(_EXPLORE_LOSS_MAX_PCT * 100)
        if net_edge_pct < floor_pct:
            return ExploreDecision(allow=False, size_mult=0.0, tagged=False,
                                   reason=f"net_edge {net_edge_pct:.3f}% below floor {floor_pct:.3f}%")

        # Check daily loss cap
        daily_cap_usdt = self._equity_ref * _EXPLORE_DAILY_LOSS
        if self._daily_loss_usdt >= daily_cap_usdt:
            return ExploreDecision(
                allow=False, size_mult=0.0, tagged=False,
                reason=f"daily exploration loss cap exhausted ({self._daily_loss_usdt:.2f}/{daily_cap_usdt:.2f} USDT)",
                daily_loss_used=self._daily_loss_usdt,
            )

        # qFTD-033R Q13: max-trades-per-day guardrail
        if self._daily_trade_count >= _EXPLORE_MAX_TRADES_DAY:
            return ExploreDecision(
                allow=False, size_mult=0.0, tagged=False,
                reason=f"daily exploration trade limit reached ({self._daily_trade_count}/{_EXPLORE_MAX_TRADES_DAY})",
                daily_loss_used=self._daily_loss_usdt,
            )

        return ExploreDecision(
            allow=True,
            size_mult=_EXPLORE_SIZE_MULT,
            tagged=True,
            reason="EXPLORATION approved (marginal net edge, reduced size)",
            daily_loss_used=self._daily_loss_usdt,
        )

    def record_outcome(self, symbol: str, signal_type: str, net_edge_pct: float,
                       size_mult: float, pnl_usdt: float) -> None:
        """Record trade outcome; update daily loss and trade-count trackers."""
        self._reset_day_if_needed()
        self._daily_trade_count += 1    # qFTD-033R Q13: count every settled exploration trade
        if pnl_usdt < 0:
            self._daily_loss_usdt += abs(pnl_usdt)
        self._records.append(ExploreTradeRecord(
            symbol=symbol, signal_type=signal_type,
            net_edge_pct=net_edge_pct, size_mult=size_mult,
            actual_pnl=pnl_usdt,
        ))

    def summary(self) -> dict:
        """Stats for reporting (qFTD-033R Q13: guardrail fields added)."""
        self._reset_day_if_needed()
        total      = len(self._records)
        wins       = sum(1 for r in self._records if (r.actual_pnl or 0) > 0)
        total_pnl  = sum((r.actual_pnl or 0) for r in self._records)
        daily_cap_usdt = self._equity_ref * _EXPLORE_DAILY_LOSS

        return {
            "enabled":              _EXPLORATION_MODE,
            "total_trades":         total,
            "win_count":            wins,
            "win_rate_pct":         round(wins / total * 100, 1) if total else 0.0,
            "total_pnl":            round(total_pnl, 4),
            "daily_loss_used":      round(self._daily_loss_usdt, 4),
            "daily_loss_cap":       round(daily_cap_usdt, 4),
            "cap_remaining":        round(max(daily_cap_usdt - self._daily_loss_usdt, 0), 4),
            "size_mult":            _EXPLORE_SIZE_MULT,
            "daily_trade_count":    self._daily_trade_count,
            "daily_trade_limit":    _EXPLORE_MAX_TRADES_DAY,
            "daily_trades_remaining": max(_EXPLORE_MAX_TRADES_DAY - self._daily_trade_count, 0),
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _reset_day_if_needed(self) -> None:
        today = int(time.time()) // 86400
        if today != self._current_day:
            self._daily_loss_usdt   = 0.0
            self._daily_trade_count = 0    # qFTD-033R Q13: reset daily trade counter
            self._current_day       = today


# ── Singleton ─────────────────────────────────────────────────────────────────
exploration_controller = ExplorationController()
