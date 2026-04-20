"""
EOW Quant Engine — Phase 7: Edge Memory Engine
Remembers what works and penalizes what doesn't.

Tracks performance per (strategy, symbol, regime) triple using a rolling
window of EM_WINDOW trades. Once EM_MIN_TRADES are recorded:
  • Win rate ≥ EM_WIN_RATE_BOOST_THRESHOLD   → history_score boosted toward 1.0
  • Win rate ≤ EM_WIN_RATE_PENALTY_THRESHOLD → history_score penalized toward 0.0
  • Otherwise                                → neutral history_score (0.5)

The history_score feeds into TradeRanker as the "historical performance"
component, biasing capital toward proven (strategy, symbol, regime) combos
and away from consistently losing ones.

Non-negotiable: memory effects are bounded by EM_BOOST_MAX / EM_PENALTY_MAX.
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Optional, Tuple

from loguru import logger

from config import cfg


TradeKey = Tuple[str, str, str]  # (strategy, symbol, regime)


@dataclass
class _TradeRecord:
    timestamp: float
    won: bool


@dataclass
class MemoryQueryResult:
    key:           TradeKey
    history_score: float       # 0.0 – 1.0; passed to TradeRanker
    win_rate:      Optional[float]
    sample_size:   int
    state:         str         # "BOOSTED" | "PENALIZED" | "NEUTRAL" | "INSUFFICIENT"


class EdgeMemoryEngine:
    """
    Per-(strategy, symbol, regime) performance tracker.

    Call record_outcome() after each trade closes.
    Call query() before ranking to get the history_score for that combo.
    """

    def __init__(self):
        self._memory: Dict[TradeKey, Deque[_TradeRecord]] = {}
        logger.info(
            f"[EDGE-MEMORY] Phase 7 activated | "
            f"window={cfg.EM_WINDOW} min_trades={cfg.EM_MIN_TRADES} "
            f"boost≥{cfg.EM_WIN_RATE_BOOST_THRESHOLD:.0%}(+{cfg.EM_BOOST_MAX:.0%}) "
            f"penalty≤{cfg.EM_WIN_RATE_PENALTY_THRESHOLD:.0%}(-{cfg.EM_PENALTY_MAX:.0%})"
        )

    def _get_deque(self, key: TradeKey) -> Deque[_TradeRecord]:
        if key not in self._memory:
            self._memory[key] = deque(maxlen=cfg.EM_WINDOW)
        return self._memory[key]

    def record_outcome(
        self,
        strategy: str,
        symbol:   str,
        regime:   str,
        won:      bool,
    ) -> None:
        """
        Record the outcome of a completed trade.

        Args:
            strategy: strategy name (e.g. "TrendFollowing")
            symbol:   trading symbol (e.g. "BTCUSDT")
            regime:   market regime at trade entry
            won:      True if trade was profitable (net PnL > 0)
        """
        key: TradeKey = (strategy, symbol, regime)
        dq = self._get_deque(key)
        dq.append(_TradeRecord(timestamp=time.time(), won=won))
        logger.debug(
            f"[EDGE-MEMORY] recorded outcome won={won} "
            f"key={key} n={len(dq)}"
        )

    def query(
        self,
        strategy: str,
        symbol:   str,
        regime:   str,
    ) -> MemoryQueryResult:
        """
        Return a history_score for (strategy, symbol, regime).

        The score is fed as history_component to TradeRanker.
        When fewer than EM_MIN_TRADES recorded, returns neutral 0.5.
        """
        key: TradeKey = (strategy, symbol, regime)
        dq = self._get_deque(key)
        n = len(dq)

        if n < cfg.EM_MIN_TRADES:
            return MemoryQueryResult(
                key=key, history_score=0.5,
                win_rate=None, sample_size=n,
                state="INSUFFICIENT",
            )

        win_rate = sum(1 for r in dq if r.won) / n

        if win_rate >= cfg.EM_WIN_RATE_BOOST_THRESHOLD:
            # Linearly scale boost: at threshold → 0; at 1.0 → EM_BOOST_MAX
            boost_range = 1.0 - cfg.EM_WIN_RATE_BOOST_THRESHOLD
            boost_t = (win_rate - cfg.EM_WIN_RATE_BOOST_THRESHOLD) / boost_range if boost_range > 0 else 1.0
            boost = cfg.EM_BOOST_MAX * boost_t
            history_score = min(0.5 + boost, 0.5 + cfg.EM_BOOST_MAX)
            state = "BOOSTED"
        elif win_rate <= cfg.EM_WIN_RATE_PENALTY_THRESHOLD:
            # Linearly scale penalty: at threshold → 0; at 0.0 → EM_PENALTY_MAX
            penalty_t = 1.0 - (win_rate / cfg.EM_WIN_RATE_PENALTY_THRESHOLD) if cfg.EM_WIN_RATE_PENALTY_THRESHOLD > 0 else 1.0
            penalty = cfg.EM_PENALTY_MAX * penalty_t
            history_score = max(0.5 - penalty, 0.5 - cfg.EM_PENALTY_MAX)
            state = "PENALIZED"
        else:
            history_score = 0.5
            state = "NEUTRAL"

        history_score = round(max(0.0, min(history_score, 1.0)), 4)
        logger.debug(
            f"[EDGE-MEMORY] query key={key} n={n} wr={win_rate:.2%} "
            f"state={state} history_score={history_score}"
        )

        return MemoryQueryResult(
            key=key,
            history_score=history_score,
            win_rate=round(win_rate, 4),
            sample_size=n,
            state=state,
        )

    def all_keys(self) -> list[TradeKey]:
        return list(self._memory.keys())

    def summary(self) -> dict:
        total_trades = sum(len(dq) for dq in self._memory.values())
        key_stats = {}
        for key, dq in self._memory.items():
            n = len(dq)
            wr = round(sum(1 for r in dq if r.won) / n, 3) if n else 0.0
            key_stats[str(key)] = {"n": n, "win_rate": wr}

        return {
            "tracked_keys":  len(self._memory),
            "total_trades":  total_trades,
            "window":        cfg.EM_WINDOW,
            "min_trades":    cfg.EM_MIN_TRADES,
            "boost_max":     cfg.EM_BOOST_MAX,
            "penalty_max":   cfg.EM_PENALTY_MAX,
            "boost_threshold":   cfg.EM_WIN_RATE_BOOST_THRESHOLD,
            "penalty_threshold": cfg.EM_WIN_RATE_PENALTY_THRESHOLD,
            "key_stats":     key_stats,
            "module": "EDGE_MEMORY_ENGINE",
            "phase":  7,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
edge_memory_engine = EdgeMemoryEngine()
