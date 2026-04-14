"""
EOW Quant Engine — Edge Engine  (FTD-REF-024)
Data-driven edge learning, auto strategy kill switch, and edge booster.

For every (regime, strategy_id) pair the engine tracks over a rolling window:
  win_rate, avg_win, avg_loss, avg_rr, expectancy
  edge = (win_rate × avg_win) − ((1 − win_rate) × avg_loss)

Auto Kill Switch (FTD-REF-024):
  if trades ≥ MIN_TRADES and edge < 0 → strategy disabled for that regime.
  Disable clears automatically when edge turns positive (re-evaluated on
  every record() call — no manual intervention needed).

Edge Booster (FTD-REF-024):
  if edge > EDGE_BOOST_THRESH → get_size_multiplier() > 1.0 (up to 1.40×)
  — winning edge amplified by increasing position size.

Trade Rejection via check_trade():
  (allowed=False) when kill switch is active for that (regime, strategy).
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, Deque, NamedTuple, Tuple

from loguru import logger


# ── Constants ─────────────────────────────────────────────────────────────────
WINDOW_SIZE       = 50      # rolling trades per (regime, strategy) pair
MIN_TRADES        = 20      # minimum before kill switch / booster activates
EDGE_BOOST_THRESH = 0.15    # edge > this → boost position size
EDGE_BOOST_MULT   = 1.25    # +25% size when edge is clearly positive
MAX_EDGE_MULT     = 1.40    # hard cap on edge-driven boost
EDGE_KILL_THRESH  = 0.0     # edge < 0 → disable strategy for that regime


class _TradeRecord(NamedTuple):
    net_pnl: float   # positive = win, negative = loss
    r_mult:  float   # R-multiple = net_pnl / initial_risk


@dataclass
class EdgeStats:
    regime:      str
    strategy_id: str
    n_trades:    int
    win_rate:    float
    avg_win:     float     # average profit on winning trades (USDT)
    avg_loss:    float     # average loss on losing trades (USDT, positive value)
    avg_rr:      float     # average R-multiple
    expectancy:  float     # (win_rate × avg_win) − ((1−win_rate) × avg_loss)
    edge:        float     # same as expectancy — the key metric
    disabled:    bool      # True = kill switch active
    size_mult:   float     # edge booster multiplier (1.0 = normal)


class EdgeEngine:
    """
    Stateful per-(regime, strategy_id) edge tracker and kill switch.
    Thread-safe for a single asyncio event loop.
    """

    def __init__(self):
        # (regime, strategy_id) → rolling window of trade records
        self._history:  Dict[Tuple[str, str], Deque[_TradeRecord]] = {}
        # (regime, strategy_id) → kill-switch flag
        self._disabled: Dict[Tuple[str, str], bool] = {}

    # ── Public ────────────────────────────────────────────────────────────────

    def record(
        self,
        regime:      str,
        strategy_id: str,
        net_pnl:     float,
        r_mult:      float = 0.0,
    ):
        """
        Record a closed trade result.
        Call after every position close with the strategy's regime and PnL.
        r_mult — R-multiple = net_pnl / initial_risk (0.0 if unknown).
        """
        key = (regime, strategy_id)
        if key not in self._history:
            self._history[key] = deque(maxlen=WINDOW_SIZE)
        self._history[key].append(_TradeRecord(net_pnl=net_pnl, r_mult=r_mult))

        stats = self._compute(key)
        was_disabled = self._disabled.get(key, False)

        if stats.n_trades >= MIN_TRADES:
            now_disabled = stats.edge < EDGE_KILL_THRESH
            self._disabled[key] = now_disabled

            if now_disabled and not was_disabled:
                logger.warning(
                    f"[EDGE-ENG] KILL SWITCH ON  {strategy_id}@{regime}: "
                    f"edge={stats.edge:.4f} wr={stats.win_rate:.1%} "
                    f"n={stats.n_trades}"
                )
            elif was_disabled and not now_disabled:
                logger.info(
                    f"[EDGE-ENG] KILL SWITCH OFF {strategy_id}@{regime}: "
                    f"edge={stats.edge:.4f} (positive again)"
                )
        else:
            self._disabled[key] = False   # not enough data to decide

        logger.debug(
            f"[EDGE-ENG] {strategy_id}@{regime} "
            f"edge={stats.edge:.4f} wr={stats.win_rate:.1%} "
            f"n={stats.n_trades} boost={stats.size_mult:.2f}× "
            f"disabled={self._disabled.get(key, False)}"
        )

    def check_trade(self, regime: str, strategy_id: str) -> Tuple[bool, str]:
        """
        Returns (allowed, reason).
        Call BEFORE opening a new position.
        Returns (False, reason) when the kill switch is active.
        """
        key = (regime, strategy_id)
        if self._disabled.get(key, False):
            stats = self._compute(key)
            return (
                False,
                f"EDGE_KILL({strategy_id}@{regime} "
                f"edge={stats.edge:.4f} n={stats.n_trades})",
            )
        return True, ""

    def get_edge(self, regime: str, strategy_id: str) -> float:
        """
        Returns current edge value (expectancy in USDT).
        Negative = losing edge; 0.0 if no data yet.
        """
        key = (regime, strategy_id)
        if key not in self._history or len(self._history[key]) == 0:
            return 0.0
        return self._compute(key).edge

    def get_size_multiplier(self, regime: str, strategy_id: str) -> float:
        """
        Returns a position-size multiplier based on measured edge strength.
        1.0 = normal size (default when edge is unknown / insufficient data).
        > 1.0 = booster active (strong positive edge).
        Never returns < 1.0 — separate risk controls handle downside.
        """
        key = (regime, strategy_id)
        if key not in self._history:
            return 1.0
        stats = self._compute(key)
        return stats.size_mult if stats.n_trades >= MIN_TRADES else 1.0

    def stats(self, regime: str, strategy_id: str) -> EdgeStats:
        return self._compute((regime, strategy_id))

    def all_stats(self) -> list:
        return [self._compute(k) for k in self._history]

    def summary(self) -> dict:
        return {
            "window_size":     WINDOW_SIZE,
            "min_trades":      MIN_TRADES,
            "edge_boost_at":   EDGE_BOOST_THRESH,
            "edge_kill_at":    EDGE_KILL_THRESH,
            "boost_mult":      EDGE_BOOST_MULT,
            "strategies": {
                f"{r}@{s}": {
                    "n_trades":  len(h),
                    "edge":      round(self._compute((r, s)).edge,      4),
                    "win_rate":  round(self._compute((r, s)).win_rate,  3),
                    "size_mult": round(self._compute((r, s)).size_mult, 3),
                    "disabled":  self._disabled.get((r, s), False),
                }
                for (r, s), h in self._history.items()
            },
        }

    # ── Internals ─────────────────────────────────────────────────────────────

    def _compute(self, key: Tuple[str, str]) -> EdgeStats:
        regime, strategy_id = key
        history = self._history.get(key, deque())
        n = len(history)

        if n == 0:
            return EdgeStats(
                regime=regime, strategy_id=strategy_id, n_trades=0,
                win_rate=0.0, avg_win=0.0, avg_loss=0.0,
                avg_rr=0.0, expectancy=0.0, edge=0.0,
                disabled=False, size_mult=1.0,
            )

        wins   = [t.net_pnl for t in history if t.net_pnl >  0]
        losses = [abs(t.net_pnl) for t in history if t.net_pnl <= 0]
        r_mults = [t.r_mult for t in history]

        win_rate   = len(wins)   / n
        avg_win    = sum(wins)   / len(wins)   if wins   else 0.0
        avg_loss   = sum(losses) / len(losses) if losses else 0.0
        avg_rr     = sum(r_mults) / n
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        edge       = expectancy

        # Edge booster: only kicks in after MIN_TRADES
        if n >= MIN_TRADES and edge > EDGE_BOOST_THRESH:
            size_mult = min(MAX_EDGE_MULT, EDGE_BOOST_MULT)
        else:
            size_mult = 1.0

        return EdgeStats(
            regime=regime, strategy_id=strategy_id, n_trades=n,
            win_rate=round(win_rate, 3),
            avg_win=round(avg_win, 4),
            avg_loss=round(avg_loss, 4),
            avg_rr=round(avg_rr, 4),
            expectancy=round(expectancy, 4),
            edge=round(edge, 4),
            disabled=self._disabled.get(key, False),
            size_mult=round(size_mult, 3),
        )


# ── Module-level singleton ────────────────────────────────────────────────────
edge_engine = EdgeEngine()
