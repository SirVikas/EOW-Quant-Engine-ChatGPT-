"""
EOW Quant Engine — Phase 5: Regime Memory Engine
Learns what strategy works best in each market regime from real trade history.

For every (regime, strategy_type) pair the engine tracks:
  win_rate, avg_r_multiple, n_trades  (rolling REGIME_MEMORY_WINDOW trades)

Outputs:
  get_fit_score(regime, strategy_type) → float [0, 1]
    A regime-fit score used to bias strategy selection or scoring.
    0.5 = neutral (no data), > 0.5 = above-average fit, < 0.5 = poor fit.

  preferred_strategy(regime) → str
    Returns the strategy_type with the best historical fit for the regime.

Integration: called from main.py to boost/penalise scoring based on
historical regime-strategy compatibility, and optionally to override
the default strategy selection when the engine has sufficient data.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, Deque, NamedTuple, Optional, Tuple

from loguru import logger

from config import cfg


WINDOW = cfg.REGIME_MEMORY_WINDOW
MIN_TRADES_FOR_PREFERENCE = 10   # minimum trades before overriding default selection


class _TradeRec(NamedTuple):
    won:    bool
    r_mult: float


@dataclass
class RegimeStats:
    regime:      str
    strategy:    str
    n_trades:    int
    win_rate:    float
    avg_r:       float
    fit_score:   float   # composite fit: 0–1 (0.5 = neutral)


class RegimeMemoryEngine:
    """
    Maintains a rolling performance record per (regime, strategy_type).
    Provides fit scores and strategy preference for each regime.
    """

    def __init__(self):
        self._history: Dict[Tuple[str, str], Deque[_TradeRec]] = {}
        logger.info(
            f"[REGIME-MEMORY] Phase 5 activated | window={WINDOW}"
        )

    # ── Recording ────────────────────────────────────────────────────────────

    def record(
        self,
        regime:        str,
        strategy_type: str,
        won:           bool,
        r_mult:        float = 0.0,
    ):
        """Record a closed trade outcome for the given regime + strategy pair."""
        key = (regime, strategy_type)
        if key not in self._history:
            self._history[key] = deque(maxlen=WINDOW)
        self._history[key].append(_TradeRec(won=won, r_mult=r_mult))
        stats = self._compute(key)
        logger.debug(
            f"[REGIME-MEMORY] {strategy_type}@{regime} "
            f"wr={stats.win_rate:.1%} avg_r={stats.avg_r:.2f} "
            f"fit={stats.fit_score:.3f} n={stats.n_trades}"
        )

    # ── Querying ──────────────────────────────────────────────────────────────

    def get_fit_score(self, regime: str, strategy_type: str) -> float:
        """
        Returns a fit score in [0, 1].
          0.5  = neutral (no data or exactly average performance)
          >0.5 = historically profitable for this regime
          <0.5 = historically poor for this regime

        The score is: 0.5 × win_rate_norm + 0.5 × avg_r_norm
        where norms map [0,1] and [0,3] ranges to [0,1].
        """
        key = (regime, strategy_type)
        if key not in self._history or len(self._history[key]) == 0:
            return 0.5  # neutral
        return self._compute(key).fit_score

    def preferred_strategy(self, regime: str) -> Optional[str]:
        """
        Return the strategy_type with the highest fit score for this regime.
        Returns None when no pair has MIN_TRADES_FOR_PREFERENCE history.
        """
        regime_pairs = [
            (strat, self._compute((regime, strat)))
            for (reg, strat) in self._history
            if reg == regime and len(self._history[(reg, strat)]) >= MIN_TRADES_FOR_PREFERENCE
        ]
        if not regime_pairs:
            return None
        best = max(regime_pairs, key=lambda x: x[1].fit_score)
        return best[0]

    def get_stats(self, regime: str, strategy_type: str) -> RegimeStats:
        key = (regime, strategy_type)
        return self._compute(key)

    def all_stats(self) -> list:
        return [self._compute(k) for k in self._history]

    def summary(self) -> dict:
        return {
            "window":    WINDOW,
            "pairs":     len(self._history),
            "regimes": {
                f"{strat}@{reg}": {
                    "n":        len(h),
                    "fit":      round(self._compute((reg, strat)).fit_score, 3),
                    "win_rate": round(self._compute((reg, strat)).win_rate, 3),
                    "avg_r":    round(self._compute((reg, strat)).avg_r, 3),
                }
                for (reg, strat), h in self._history.items()
            },
            "module": "REGIME_MEMORY",
            "phase":  5,
        }

    # ── Internals ────────────────────────────────────────────────────────────

    def _compute(self, key: Tuple[str, str]) -> RegimeStats:
        regime, strategy = key
        history = self._history.get(key, deque())
        n = len(history)

        if n == 0:
            return RegimeStats(
                regime=regime, strategy=strategy, n_trades=0,
                win_rate=0.5, avg_r=0.0, fit_score=0.5,
            )

        wins    = [t for t in history if t.won]
        r_mults = [t.r_mult for t in history]

        win_rate = len(wins) / n
        avg_r    = sum(r_mults) / n

        # Fit score: 50% from win_rate (normalised 0→1), 50% from avg_r (normalised 0→3×)
        win_norm  = win_rate                            # already in [0,1]
        r_norm    = min(max(avg_r / 3.0, 0.0), 1.0)   # 0→1 mapped from [0, 3R]
        fit_score = round(0.5 * win_norm + 0.5 * r_norm, 4)

        return RegimeStats(
            regime=regime, strategy=strategy, n_trades=n,
            win_rate=round(win_rate, 4),
            avg_r=round(avg_r, 4),
            fit_score=fit_score,
        )


# ── Module-level singleton ────────────────────────────────────────────────────
regime_memory = RegimeMemoryEngine()
