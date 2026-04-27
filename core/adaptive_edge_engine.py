"""
core/adaptive_edge_engine.py
FTD-037 — Adaptive Edge Engine (REAL)

Complements existing EdgeEngine with:
  ✔ Time-aware weighting   — recent trades count more (exponential decay)
  ✔ AEE Score              — f(PF, RR, Cost, Consistency), 0–1, explainable
  ✔ PF-based auto-disable  — PF < 0.80 → DISABLED (in addition to edge < 0)
  ✔ Loss-streak gate       — ≥ 4 losses → REDUCED, ≥ 7 → DISABLED
  ✔ Auto-scale             — PF > 1.20 AND stable wins → SCALING (1.25–1.50×)
  ✔ Allocation rank        — priority ordering of all strategies by AEE Score
  ✔ Cost-aware filter      — block trade if historical E[profit] ≤ fees
  ✔ Disable log            — who/when/why (last 10 events per strategy)
  ✔ Clear state machine    — ACTIVE / REDUCED / DISABLED / SCALING

Philosophy: simple logic, fast execution, visible output.
"""
from __future__ import annotations

import math
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from typing import Deque, Dict, List, Optional, Tuple

from loguru import logger


# ── Config ────────────────────────────────────────────────────────────────────

WINDOW        = 50      # max trades tracked per strategy (rolling)
MIN_TRADES    = 10      # min before scoring / disable logic fires
DECAY_HALF    = 20      # trades: age at which weight halves (recency bias)

PF_DISABLE    = 0.80    # PF < 0.80  → DISABLED
PF_SCALE      = 1.20    # PF > 1.20  + stable wins → SCALING
EDGE_KILL     = 0.0     # edge < 0   → DISABLED (immediate)

LOSS_STK_WARN = 4       # ≥ 4 consecutive losses → REDUCED
LOSS_STK_OFF  = 7       # ≥ 7 consecutive losses → DISABLED
WIN_RECOVER   = 3       # consecutive wins needed to exit REDUCED
PF_RECOVER    = 0.85    # PF must reach this to exit DISABLED

SCALE_MULT    = 1.25    # base size multiplier in SCALING state
MAX_SCALE     = 1.50    # hard cap on scale multiplier
REDUCE_MULT   = 0.50    # size multiplier in REDUCED state

# AEE Score weights (sum = 1.0, explainable)
W_PF   = 0.35
W_RR   = 0.25
W_COST = 0.25
W_CONS = 0.15


# ── Internal trade record ─────────────────────────────────────────────────────

@dataclass
class _T:
    net_pnl:    float
    r_multiple: float
    cost_pct:   float   # fee_total / max(abs(gross_pnl), ε)  → 0..∞
    ts_ms:      int
    won:        bool


# ── Strategy states ───────────────────────────────────────────────────────────

class State:
    ACTIVE   = "ACTIVE"
    REDUCED  = "REDUCED"
    DISABLED = "DISABLED"
    SCALING  = "SCALING"


# ── Public stats dataclass ────────────────────────────────────────────────────

@dataclass
class AEEStats:
    strategy_id:  str
    n_trades:     int
    state:        str     # State.*
    aee_score:    float   # 0–1 (higher = better)
    rank:         int     # 1 = best
    weighted_pf:  float
    weighted_rr:  float
    cost_pct:     float   # avg fee as % of gross  (e.g. 25.0 = 25%)
    win_rate:     float   # 0–100
    win_streak:   int
    loss_streak:  int
    size_mult:    float   # 0.0=blocked, 0.5=reduced, 1.0=normal, 1.25-1.5=scaling
    can_trade:    bool
    block_reason: str     # empty when can_trade=True
    disable_log:  List[dict]   # last 5 events: {ts, reason, pf, edge}


# ── Main class ────────────────────────────────────────────────────────────────

class AdaptiveEdgeEngine:
    """
    FTD-037 — Adaptive Edge Engine.
    One singleton instance; tracks all strategy_ids in one place.

    Regime awareness delegates to existing EdgeEngine; this module
    adds time-weighted PF/score/streak logic and the disable log.
    """

    def __init__(self) -> None:
        self._hist:     Dict[str, Deque[_T]]     = defaultdict(lambda: deque(maxlen=WINDOW))
        self._state:    Dict[str, str]            = {}
        self._dis_log:  Dict[str, list]           = defaultdict(list)   # list[dict]
        self._lambda    = 0.5 ** (1.0 / DECAY_HALF)    # decay factor per trade age

    # ── Public write ──────────────────────────────────────────────────────────

    def on_trade_closed(
        self,
        strategy_id: str,
        net_pnl:     float,
        r_multiple:  float,
        gross_pnl:   float,
        fee_total:   float,
    ) -> None:
        """Record closed trade outcome. Call after every closed trade."""
        cost_pct = fee_total / max(abs(gross_pnl), 1e-9)
        self._hist[strategy_id].append(_T(
            net_pnl    = net_pnl,
            r_multiple = r_multiple,
            cost_pct   = cost_pct,
            ts_ms      = int(time.time() * 1000),
            won        = net_pnl > 0,
        ))
        self._update_state(strategy_id)

    # ── Public read ───────────────────────────────────────────────────────────

    def check_trade(
        self,
        strategy_id:    str,
        expected_gross: float = 0.0,
        fee_estimate:   float = 0.0,
    ) -> Tuple[bool, str]:
        """
        Pre-trade kill switch.  Returns (can_trade, reason).

        Blocks when:
          1. State is DISABLED
          2. Historical E[profit] ≤ fee_estimate (cost-aware filter, FTD-037 §8)
        """
        s = self._state.get(strategy_id, State.ACTIVE)
        if s == State.DISABLED:
            log = self._dis_log.get(strategy_id, [])
            reason = log[-1]["reason"] if log else "negative edge / low PF"
            return False, f"AEE_DISABLED: {reason}"

        # §8 cost-aware filter: block if expected gross ≤ fee
        if expected_gross > 0 and fee_estimate > 0 and expected_gross <= fee_estimate:
            return False, (
                f"AEE_COST_BLOCK: E[gross]={expected_gross:.4f} ≤ fees={fee_estimate:.4f}"
            )

        # §8 historical cost filter: if avg E[profit] is ≤ 0 (strategy always fee-drag)
        hist = self._hist.get(strategy_id)
        if hist and len(hist) >= MIN_TRADES:
            m = self._metrics(hist)
            if m["edge"] <= 0 and fee_estimate > 0:
                return False, (
                    f"AEE_HIST_COST: E[profit]={m['edge']:.4f} ≤ 0 (fee drag confirmed)"
                )

        return True, ""

    def get_size_mult(self, strategy_id: str) -> float:
        """Position size multiplier: 0=blocked, 0.5=reduced, 1.0=normal, 1.25–1.5=scaling."""
        s = self._state.get(strategy_id, State.ACTIVE)
        if s == State.DISABLED:
            return 0.0
        if s == State.REDUCED:
            return REDUCE_MULT
        if s == State.SCALING:
            return self._scale_mult(strategy_id)
        return 1.0

    def all_stats(self) -> List[AEEStats]:
        """Return all tracked strategies ranked by AEE Score (best first)."""
        results = [self._build(sid) for sid in self._hist]
        results.sort(key=lambda x: (-x.aee_score, x.strategy_id))
        for i, s in enumerate(results):
            s.rank = i + 1
        return results

    def get_stats(self, strategy_id: str) -> Optional[AEEStats]:
        if strategy_id not in self._hist:
            return None
        s = self._build(strategy_id)
        s.rank = 1  # single lookup — rank is relative; full rank needs all_stats()
        return s

    def summary(self) -> dict:
        stats = self.all_stats()
        active   = [s.strategy_id for s in stats if s.state == State.ACTIVE]
        reduced  = [s.strategy_id for s in stats if s.state == State.REDUCED]
        scaling  = [s.strategy_id for s in stats if s.state == State.SCALING]
        disabled = [s.strategy_id for s in stats if s.state == State.DISABLED]
        top      = stats[0] if stats else None
        return {
            "module":         "ADAPTIVE_EDGE_ENGINE",
            "phase":          "FTD-037",
            "total_tracked":  len(stats),
            "active":         active,
            "reduced":        reduced,
            "scaling":        scaling,
            "disabled":       disabled,
            "top_strategy":   top.strategy_id if top else None,
            "top_score":      top.aee_score   if top else 0.0,
            "strategies":     [asdict(s) for s in stats],
            "score_formula":  (
                "AEE_Score = 0.35×PF_score + 0.25×RR_score "
                "+ 0.25×Cost_score + 0.15×Consistency"
            ),
        }

    # ── State machine ─────────────────────────────────────────────────────────

    def _update_state(self, sid: str) -> None:
        hist = self._hist[sid]
        if len(hist) < MIN_TRADES:
            self._state[sid] = State.ACTIVE
            return

        m         = self._metrics(hist)
        pf        = m["pf"]
        edge      = m["edge"]
        ws, ls    = self._streaks(hist)
        current   = self._state.get(sid, State.ACTIVE)

        # ── 1. Hard disable ───────────────────────────────────────────────────
        if edge < EDGE_KILL:
            if current != State.DISABLED:
                self._disable(sid, f"edge={edge:.4f} < 0 (immediate kill)", pf, edge)
            return

        if pf < PF_DISABLE:
            if current != State.DISABLED:
                self._disable(sid, f"PF={pf:.3f} < {PF_DISABLE}", pf, edge)
            return

        if ls >= LOSS_STK_OFF:
            if current != State.DISABLED:
                self._disable(sid, f"loss_streak={ls} ≥ {LOSS_STK_OFF}", pf, edge)
            return

        # ── 2. Recovery from DISABLED ─────────────────────────────────────────
        if current == State.DISABLED:
            if pf >= PF_RECOVER and edge >= 0 and ws >= WIN_RECOVER:
                logger.info(f"[AEE] {sid}: DISABLED → ACTIVE  PF={pf:.3f} wins={ws}")
                self._state[sid] = State.ACTIVE
            return   # still disabled — wait for recovery criteria

        # ── 3. Scale condition ────────────────────────────────────────────────
        if pf >= PF_SCALE and ws >= WIN_RECOVER:
            if current != State.SCALING:
                logger.info(f"[AEE] {sid}: → SCALING  PF={pf:.3f} wins={ws}")
            self._state[sid] = State.SCALING
            return

        # ── 4. Loss-streak warn ───────────────────────────────────────────────
        if ls >= LOSS_STK_WARN:
            if current not in (State.REDUCED, State.SCALING):
                logger.warning(f"[AEE] {sid}: → REDUCED  loss_streak={ls}")
            self._state[sid] = State.REDUCED
            return

        # ── 5. Recovery from REDUCED ──────────────────────────────────────────
        if current == State.REDUCED and ws >= WIN_RECOVER:
            logger.info(f"[AEE] {sid}: REDUCED → ACTIVE  wins={ws}")
            self._state[sid] = State.ACTIVE
            return

        # ── 6. Default: stay ACTIVE ───────────────────────────────────────────
        if current not in (State.REDUCED, State.SCALING):
            self._state[sid] = State.ACTIVE

    def _disable(self, sid: str, reason: str, pf: float, edge: float) -> None:
        evt = {"ts": int(time.time() * 1000), "reason": reason,
               "pf": round(pf, 4), "edge": round(edge, 4)}
        log = self._dis_log[sid]
        log.append(evt)
        if len(log) > 10:
            log.pop(0)
        self._state[sid] = State.DISABLED
        logger.warning(f"[AEE] {sid} DISABLED — {reason}")

    # ── Metric computation ────────────────────────────────────────────────────

    def _metrics(self, hist: Deque[_T]) -> dict:
        """
        Time-aware weighted metrics.
        Weight of trade at age k (0=most recent): λ^k
        This gives recent trades more influence.
        """
        trades = list(hist)          # oldest → newest
        n      = len(trades)
        lam    = self._lambda

        # weights[i] = λ^(n-1-i)  →  trades[-1] (newest) gets weight=1.0
        weights     = [lam ** (n - 1 - i) for i in range(n)]
        total_w     = sum(weights)

        win_w = loss_w = 0.0
        sum_win_pnl = sum_loss_pnl = sum_rr = sum_cost = 0.0

        for t, w in zip(trades, weights):
            if t.won:
                win_w       += w
                sum_win_pnl += t.net_pnl * w
            else:
                loss_w       += w
                sum_loss_pnl += abs(t.net_pnl) * w
            sum_rr   += t.r_multiple * w
            sum_cost += t.cost_pct   * w

        wr    = win_w / total_w
        avg_w = sum_win_pnl  / max(win_w,  1e-9)
        avg_l = sum_loss_pnl / max(loss_w, 1e-9)
        pf    = sum_win_pnl  / max(sum_loss_pnl, 1e-9)
        rr    = sum_rr   / total_w
        cost  = sum_cost / total_w
        edge  = wr * avg_w - (1.0 - wr) * avg_l   # expected profit per trade

        return {"pf": pf, "rr": rr, "wr": wr, "cost": cost, "edge": edge}

    def _aee_score(self, pf: float, rr: float, cost: float, wr: float) -> float:
        """
        AEE Score = 0.35×PF_score + 0.25×RR_score + 0.25×Cost_score + 0.15×Consistency
        All inputs bounded 0–1. Formula is simple and explainable.

        PF_score    = min(PF/2.0, 1.0)          saturates at PF = 2.0
        RR_score    = min(max(RR,0)/3.0, 1.0)   saturates at RR = 3.0
        Cost_score  = max(0, 1 - cost_pct)      lower cost → higher score
        Consistency = max(0, (WR-0.5)×2)        0 at WR=50%, 1 at WR=100%
        """
        pf_s   = min(pf / 2.0, 1.0)
        rr_s   = min(max(rr, 0.0) / 3.0, 1.0)
        cost_s = max(0.0, 1.0 - cost)
        cons_s = max(0.0, min((wr - 0.5) * 2.0, 1.0))
        return round(W_PF * pf_s + W_RR * rr_s + W_COST * cost_s + W_CONS * cons_s, 4)

    def _streaks(self, hist: Deque[_T]) -> Tuple[int, int]:
        """Return (win_streak, loss_streak) from most recent trade backwards."""
        wins = losses = 0
        for t in reversed(list(hist)):
            if t.won:
                if losses:
                    break
                wins += 1
            else:
                if wins:
                    break
                losses += 1
        return wins, losses

    def _scale_mult(self, sid: str) -> float:
        """Linear scale: PF 1.2→1.25×, PF 2.0+→1.50×."""
        hist = self._hist[sid]
        pf   = self._metrics(hist)["pf"]
        mult = SCALE_MULT + (MAX_SCALE - SCALE_MULT) * min((pf - PF_SCALE) / 0.8, 1.0)
        return round(min(mult, MAX_SCALE), 3)

    def _build(self, sid: str) -> AEEStats:
        hist  = self._hist[sid]
        m     = self._metrics(hist)
        ws, ls = self._streaks(hist)
        s     = self._state.get(sid, State.ACTIVE)
        score = self._aee_score(m["pf"], m["rr"], m["cost"], m["wr"])
        mult  = self.get_size_mult(sid)

        can   = s != State.DISABLED
        block = ""
        if not can:
            log   = self._dis_log.get(sid, [])
            block = log[-1]["reason"] if log else "negative edge"

        return AEEStats(
            strategy_id  = sid,
            n_trades     = len(hist),
            state        = s,
            aee_score    = score,
            rank         = 0,        # filled by all_stats()
            weighted_pf  = round(m["pf"],   4),
            weighted_rr  = round(m["rr"],   4),
            cost_pct     = round(m["cost"] * 100, 2),
            win_rate     = round(m["wr"]   * 100, 2),
            win_streak   = ws,
            loss_streak  = ls,
            size_mult    = mult,
            can_trade    = can,
            block_reason = block,
            disable_log  = list(self._dis_log.get(sid, []))[-5:],
        )


# ── Module-level singleton ────────────────────────────────────────────────────
adaptive_edge_engine = AdaptiveEdgeEngine()
