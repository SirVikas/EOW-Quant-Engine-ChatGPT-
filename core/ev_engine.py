"""
EOW Quant Engine — Phase 5: EV Engine (Core Profit Brain)
Computes the mathematical Expected Value of every trade before execution.

Formula:
  EV = (P_win × AvgWin) − (P_loss × AvgLoss) − AvgCost

Where:
  P_win    = rolling win rate over last EV_WINDOW trades
  AvgWin   = average absolute profit on winning trades (USDT)
  P_loss   = 1 − P_win
  AvgLoss  = average absolute loss on losing trades (USDT)
  AvgCost  = rolling average round-trip cost per trade (USDT)

Rule: EV <= 0 → REJECT TRADE (negative expectancy = long-term guaranteed loss)

Prospective evaluation (at signal time):
  EV_prospect = (P_win × EstReward) − (P_loss × EstRisk) − CurrentCost
  Where EstReward and EstRisk come from the current signal's TP/SL distances.

Bootstrap: when history < EV_MIN_TRADES the gate passes (no data = no kill).
Tracking: per (strategy_id, symbol) for symbol-level granularity.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, Deque, NamedTuple, Tuple

from loguru import logger

from config import cfg


# ── Constants ─────────────────────────────────────────────────────────────────
WINDOW       = cfg.EV_WINDOW       # rolling window size
MIN_TRADES   = cfg.EV_MIN_TRADES   # bootstrap threshold


class _TradeRec(NamedTuple):
    net_pnl: float   # USDT; positive = win
    cost:    float   # round-trip cost (fees + slippage) USDT


@dataclass
class EVResult:
    ok:          bool
    ev:          float   # expected value in USDT (after Phase 7B scaling)
    p_win:       float
    avg_win:     float
    avg_loss:    float
    avg_cost:    float
    n_trades:    int
    bootstrapped: bool   # True = gate passed because < MIN_TRADES
    confidence:  float = 1.0  # Phase 7B: estimate reliability (0–1); 0.3 = bootstrap
    reason:      str = ""


class EVEngine:
    """
    Per-(strategy_id, symbol) Expected Value tracker and gate.
    Records closed trade outcomes; evaluates prospective EV before entry.
    """

    def __init__(self):
        self._history: Dict[Tuple[str, str], Deque[_TradeRec]] = {}
        logger.info(
            f"[EV-ENGINE] Phase 5 activated | "
            f"window={WINDOW} min_trades={MIN_TRADES} "
            f"bootstrap_pass={cfg.EV_BOOTSTRAP_PASS}"
        )

    # ── Recording ────────────────────────────────────────────────────────────

    def record(
        self,
        strategy_id: str,
        symbol:      str,
        net_pnl:     float,
        cost:        float = 0.0,
    ):
        """
        Record a closed trade outcome.
        Call from the on_tick position-close handler.
        """
        key = (strategy_id, symbol)
        if key not in self._history:
            self._history[key] = deque(maxlen=WINDOW)
        self._history[key].append(_TradeRec(net_pnl=net_pnl, cost=cost))
        stats = self._compute_stats(key)
        _hist_ev = ((stats["p_win"] * stats["avg_win"])
                    - ((1 - stats["p_win"]) * stats["avg_loss"])
                    - stats["avg_cost"])
        logger.debug(
            f"[EV-ENGINE] {strategy_id}@{symbol} "
            f"ev={_hist_ev:.4f} p_win={stats['p_win']:.1%} "
            f"n={stats['n']}"
        )

    # ── Evaluation ───────────────────────────────────────────────────────────

    def evaluate(
        self,
        strategy_id:       str,
        symbol:            str,
        est_reward:        float,        # |take_profit − entry| × qty (USDT)
        est_risk:          float,        # |entry − stop_loss| × qty (USDT)
        current_cost:      float,        # round-trip fee + slippage for this trade
        drawdown:          float = 0.0,  # Phase 7B: current drawdown fraction (0–1)
        regime_confidence: float = 0.5,  # Phase 7B: regime detection confidence (0–1)
    ) -> EVResult:
        """
        Evaluate prospective EV using historical win-rate + current trade parameters.
        Phase 7B: applies adaptive scaling via drawdown dampening, regime-confidence
        multiplier, and historical-performance multiplier.
        Returns EVResult(ok=True) when scaled EV > 0.
        """
        key = (strategy_id, symbol)
        history = self._history.get(key)
        n = len(history) if history else 0

        # Bootstrap: pass when not enough history.
        # qFTD-008: ev=0.05 instead of 0.0 — a small positive placeholder representing
        # neutral-to-slightly-positive expectation during warmup.  ev=0.0 caused the
        # ranker's 55%-weighted EV component to be zero, making rank ≈ 0.34 which is
        # below TR_MIN_RANK_SCORE, permanently blocking all trades until 10 trades
        # accumulated — a mathematical impossibility (catch-22).  0.05 USDT/unit-risk
        # is conservative and still dwarfed by real EV once history accumulates.
        if n < MIN_TRADES:
            if cfg.EV_BOOTSTRAP_PASS:
                return EVResult(
                    ok=True, ev=0.05, p_win=0.5, avg_win=0.0, avg_loss=0.0,
                    avg_cost=current_cost, n_trades=n, bootstrapped=True,
                    confidence=0.3,
                    reason=f"BOOTSTRAP({n}<{MIN_TRADES})",
                )
            else:
                return EVResult(
                    ok=False, ev=0.0, p_win=0.0, avg_win=0.0, avg_loss=0.0,
                    avg_cost=current_cost, n_trades=n, bootstrapped=True,
                    confidence=0.3,
                    reason=f"BOOTSTRAP_BLOCKED({n}<{MIN_TRADES})",
                )

        stats = self._compute_stats(key)
        p_win    = stats["p_win"]
        p_loss   = 1.0 - p_win
        avg_cost = stats["avg_cost"]

        # Base prospective EV
        ev = (p_win * est_reward) - (p_loss * est_risk) - avg_cost

        # ── Phase 7B: Adaptive Scaling ─────────────────────────────────────
        # 1. Performance-history multiplier (only if enough trades)
        if n >= cfg.P7B_PERF_MIN_TRADES:
            if p_win >= cfg.P7B_PERF_WIN_THRESHOLD:
                ev *= cfg.P7B_PERF_BOOST
            elif p_win < cfg.P7B_PERF_LOSS_THRESHOLD:
                ev *= cfg.P7B_PERF_PENALTY

        # 2. Drawdown dampening — extreme DD forces EV to ≤ 0
        if drawdown >= cfg.P7B_DD_MAX:
            ev = min(ev, 0.0)

        # 3. Regime-confidence multiplier
        if regime_confidence >= cfg.P7B_REGIME_CONF_HIGH:
            ev *= cfg.P7B_REGIME_BOOST
        elif regime_confidence < cfg.P7B_REGIME_CONF_LOW:
            ev *= cfg.P7B_REGIME_PENALTY

        # Confidence scales with history depth (0.3 → 1.0 as n → WINDOW)
        confidence = min(1.0, 0.3 + 0.7 * (n / WINDOW))

        if ev <= 0:
            return EVResult(
                ok=False, ev=round(ev, 4), p_win=round(p_win, 4),
                avg_win=stats["avg_win"], avg_loss=stats["avg_loss"],
                avg_cost=round(avg_cost, 4), n_trades=n, bootstrapped=False,
                confidence=round(confidence, 3),
                reason=f"NEGATIVE_EV({ev:.4f}≤0 p_win={p_win:.1%})",
            )

        return EVResult(
            ok=True, ev=round(ev, 4), p_win=round(p_win, 4),
            avg_win=stats["avg_win"], avg_loss=stats["avg_loss"],
            avg_cost=round(avg_cost, 4), n_trades=n, bootstrapped=False,
            confidence=round(confidence, 3),
        )

    # ── Inspection ───────────────────────────────────────────────────────────

    def get_ev(self, strategy_id: str, symbol: str) -> float:
        """Return raw historical EV (historical, not prospective). 0.0 if no data."""
        key = (strategy_id, symbol)
        if key not in self._history or len(self._history[key]) == 0:
            return 0.0
        s = self._compute_stats(key)
        avg_win  = s["avg_win"]
        avg_loss = s["avg_loss"]
        p_win    = s["p_win"]
        avg_cost = s["avg_cost"]
        return round((p_win * avg_win) - ((1 - p_win) * avg_loss) - avg_cost, 4)

    def summary(self) -> dict:
        return {
            "window":       WINDOW,
            "min_trades":   MIN_TRADES,
            "bootstrap_pass": cfg.EV_BOOTSTRAP_PASS,
            "tracked_pairs": len(self._history),
            "strategies": {
                f"{s}@{sym}": {
                    "n":     len(h),
                    "ev":    round(self.get_ev(s, sym), 4),
                    "p_win": round(self._compute_stats((s, sym))["p_win"], 3),
                }
                for (s, sym), h in self._history.items()
            },
            "module": "EV_ENGINE",
            "phase":  5,
        }

    # ── Internals ────────────────────────────────────────────────────────────

    def _compute_stats(self, key: Tuple[str, str]) -> dict:
        history = self._history.get(key, deque())
        if not history:
            return {"p_win": 0.5, "avg_win": 0.0, "avg_loss": 0.0,
                    "avg_cost": 0.0, "n": 0}
        wins   = [t.net_pnl for t in history if t.net_pnl > 0]
        losses = [abs(t.net_pnl) for t in history if t.net_pnl <= 0]
        costs  = [t.cost for t in history]
        n      = len(history)
        return {
            "p_win":    len(wins) / n,
            "avg_win":  round(sum(wins)   / len(wins)   if wins   else 0.0, 4),
            "avg_loss": round(sum(losses) / len(losses) if losses else 0.0, 4),
            "avg_cost": round(sum(costs)  / n, 4),
            "n":        n,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
ev_engine = EVEngine()
