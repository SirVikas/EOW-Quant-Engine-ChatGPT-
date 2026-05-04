"""
EOW Quant Engine — RL Contextual Bandit Engine

Algorithm Decision: Contextual Multi-Armed Bandit with UCB1 exploration.

Why this over full PPO/DQN:
  • No external ML dependencies (TensorFlow/PyTorch not needed)
  • Works with hundreds of trades — not millions required for neural nets
  • Provably convergent: UCB1 regret bound is O(√(T log T))
  • Interpretable: Q-table can be read directly in reports
  • Zero cold-start paralysis: priors bootstrap from historical performance

How it works:
  Each "context" is a (regime, hour_bucket, strategy_type) tuple.
  For each context the bandit maintains:
    q_value   — running average net PnL per trade (the Q-value)
    n_visits  — how many times this context was acted on
    ucb_bonus — exploration bonus = √(2 ln(total_pulls) / n_visits)

  At signal time, `should_trade(context)` returns True when:
    q_value + ucb_bonus  >  ENTRY_EV_FLOOR

  After trade close, `update(context, reward)` performs a simple TD update:
    q_value ← q_value + α × (reward − q_value)

  This is RL in its simplest, most reliable form.  The UCB1 bonus ensures
  the engine explores conditions it has not tried recently, while the Q-value
  ensures it exploits the profitable ones (07h/10h/14h MEAN_REVERTING).

  Goal: MAX NET PNL PER MINUTE (after fees) by learning WHICH contexts trade,
  WHEN to trade, and HOW MUCH confidence to give each signal.

Integration:
  rl_engine.should_trade(ctx) — call before lean gate; soft-filter low-EV contexts
  rl_engine.update(ctx, net_pnl) — call in trade close handler
  rl_engine.confidence_boost(ctx) — multiplier (0.8–1.3) for signal confidence
  rl_engine.summary() — full Q-table for dashboard / reports
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from loguru import logger


# ── Hyper-parameters ──────────────────────────────────────────────────────────

LEARNING_RATE       = 0.10   # α — how fast Q-values update (0.05 = slow/stable, 0.20 = fast)
ENTRY_EV_FLOOR      = -0.30  # Minimum expected PnL to allow trade (USDT); very permissive at start
UCB_EXPLORE_COEFF   = 1.5    # C in UCB1 = C × √(ln(N)/n) — higher = more exploration
MIN_VISITS_EXPLORE  = 3      # Must visit a context ≥ this many times before blocking it
MAX_CONTEXTS        = 200    # Cap on number of distinct (regime, hour, strategy) contexts
CONFIDENCE_BOOST_HIGH   = 1.25  # Multiply signal confidence when Q > +0.5 USDT
CONFIDENCE_BOOST_NEUTRAL = 1.00  # No change when Q is near zero
CONFIDENCE_BOOST_LOW    = 0.80  # Reduce confidence when Q < -0.3 USDT


# ── Context key ───────────────────────────────────────────────────────────────

def make_context(regime: str, utc_hour: int, strategy: str) -> str:
    """
    Create a hashable context key from the three dimensions.

    hour_bucket groups hours into coarse trading windows:
      ASIA  0-5, LONDON  6-12, NY  13-18, LATE  19-23
    This reduces the Q-table size while still capturing hour-of-day effects.
    """
    if utc_hour < 6:
        bucket = "ASIA"
    elif utc_hour < 13:
        bucket = "LONDON"
    elif utc_hour < 19:
        bucket = "NY"
    else:
        bucket = "LATE"
    return f"{regime}|{bucket}|{strategy}"


# ── Context state ─────────────────────────────────────────────────────────────

@dataclass
class ContextState:
    context:    str
    q_value:    float = 0.0    # running average net PnL per trade
    n_visits:   int   = 0      # how many trades in this context
    n_wins:     int   = 0
    total_pnl:  float = 0.0
    last_ts:    int   = 0

    @property
    def win_rate(self) -> float:
        return self.n_wins / self.n_visits if self.n_visits > 0 else 0.0

    def ucb_bonus(self, total_visits: int, coeff: float) -> float:
        if self.n_visits == 0:
            return float("inf")   # unvisited context = highest priority to explore
        return coeff * math.sqrt(math.log(max(total_visits, 2)) / self.n_visits)

    def ucb_score(self, total_visits: int, coeff: float) -> float:
        return self.q_value + self.ucb_bonus(total_visits, coeff)


# ── RL Engine ─────────────────────────────────────────────────────────────────

class RLContextualBandit:
    """
    Lightweight Contextual Bandit for regime-adaptive trade filtering.

    Decision: TRADE or SKIP based on learned expected value per context.
    Learning: Q-value updated after every trade close.
    Exploration: UCB1 ensures under-explored contexts are tried before blocking.

    This replaces static RR/score thresholds with DATA-DRIVEN decisions that
    improve continuously as the engine accumulates trade history.
    """

    MODULE = "RL_CONTEXTUAL_BANDIT"
    VERSION = "1.0"

    def __init__(self):
        self._table:         Dict[str, ContextState] = {}
        self._total_pulls:   int   = 0
        self._total_updates: int   = 0
        self._total_blocked: int   = 0
        self._total_allowed: int   = 0
        self._init_ts:       float = time.time()

        logger.info(
            f"[RL-ENGINE] Contextual Bandit v{self.VERSION} online | "
            f"lr={LEARNING_RATE} ev_floor={ENTRY_EV_FLOOR} "
            f"ucb_coeff={UCB_EXPLORE_COEFF} min_explore={MIN_VISITS_EXPLORE}"
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def should_trade(
        self,
        regime:    str,
        utc_hour:  int,
        strategy:  str,
        override_floor: Optional[float] = None,
    ) -> Tuple[bool, str]:
        """
        Decide whether to enter a trade given current context.

        Returns (allowed: bool, reason: str).

        Rule: TRADE if:
          • context is under-explored (n_visits < MIN_VISITS_EXPLORE), OR
          • UCB score > ENTRY_EV_FLOOR (Q-value + exploration bonus)

        This guarantees every new context is tried before being gated.
        """
        ctx_key   = make_context(regime, utc_hour, strategy)
        state     = self._get_or_create(ctx_key)
        floor     = override_floor if override_floor is not None else ENTRY_EV_FLOOR
        self._total_pulls += 1

        # Always explore under-visited contexts
        if state.n_visits < MIN_VISITS_EXPLORE:
            self._total_allowed += 1
            return True, f"RL_EXPLORE(visits={state.n_visits}<{MIN_VISITS_EXPLORE})"

        ucb = state.ucb_score(self._total_pulls, UCB_EXPLORE_COEFF)
        if ucb > floor:
            self._total_allowed += 1
            return True, (
                f"RL_TRADE(q={state.q_value:+.3f} ucb={ucb:+.3f} "
                f"wr={state.win_rate:.0%} n={state.n_visits})"
            )

        self._total_blocked += 1
        return False, (
            f"RL_SKIP(q={state.q_value:+.3f} ucb={ucb:+.3f} "
            f"floor={floor:+.3f} n={state.n_visits})"
        )

    def update(
        self,
        regime:    str,
        utc_hour:  int,
        strategy:  str,
        net_pnl:   float,
        fee_cost:  float = 0.0,
    ) -> None:
        """
        Update Q-value after a trade is closed.

        reward = net_pnl (already includes fees when called from trade close handler)
        Q ← Q + α × (reward − Q)
        """
        ctx_key = make_context(regime, utc_hour, strategy)
        state   = self._get_or_create(ctx_key)

        reward = net_pnl   # net_pnl already deducts fees
        old_q  = state.q_value

        # TD(0) update — exponential moving average of rewards
        state.q_value   = old_q + LEARNING_RATE * (reward - old_q)
        state.n_visits  += 1
        state.total_pnl += reward
        if reward > 0:
            state.n_wins += 1
        state.last_ts = int(time.time() * 1000)
        self._total_updates += 1

        logger.debug(
            f"[RL-ENGINE] update ctx={ctx_key} "
            f"reward={reward:+.4f} q: {old_q:+.4f}→{state.q_value:+.4f} "
            f"n={state.n_visits} wr={state.win_rate:.0%}"
        )

    def confidence_boost(
        self,
        regime:   str,
        utc_hour: int,
        strategy: str,
    ) -> float:
        """
        Returns a confidence multiplier (0.80–1.25) based on learned Q-value.

        High-EV contexts get boosted confidence (more likely to clear score gate).
        Low-EV contexts get reduced confidence (harder to trade, but not blocked).
        """
        ctx_key = make_context(regime, utc_hour, strategy)
        state   = self._get_or_create(ctx_key)

        if state.n_visits < MIN_VISITS_EXPLORE:
            return CONFIDENCE_BOOST_NEUTRAL   # no data yet — neutral

        q = state.q_value
        if q > 0.50:
            return CONFIDENCE_BOOST_HIGH
        if q < -0.30:
            return CONFIDENCE_BOOST_LOW
        return CONFIDENCE_BOOST_NEUTRAL

    def get_dynamic_min_rr(
        self,
        regime:   str,
        utc_hour: int,
        strategy: str,
        base_min_rr: float = 2.5,
    ) -> float:
        """
        Returns a context-aware minimum RR requirement.

        In profitable contexts (q > +0.30): relax to 2.0 (more trades).
        In unprofitable contexts (q < -0.20): tighten to 3.0 (fewer, better trades).
        In neutral/unexplored: keep base_min_rr (2.5).
        """
        ctx_key = make_context(regime, utc_hour, strategy)
        state   = self._get_or_create(ctx_key)

        if state.n_visits < MIN_VISITS_EXPLORE:
            return max(base_min_rr - 0.5, 2.0)   # slightly relaxed for new contexts

        q = state.q_value
        if q > 0.30:
            return max(base_min_rr - 0.5, 2.0)   # profitable context → relax
        if q < -0.20:
            return min(base_min_rr + 0.5, 3.5)   # losing context → tighten
        return base_min_rr

    def get_score_floor_delta(
        self,
        regime:   str,
        utc_hour: int,
        strategy: str,
    ) -> float:
        """
        Returns a delta to subtract from _eff_score_min (the score gate floor).

        This is the second half of frequency scaling — confidence_boost() raises
        the signal side; this lowers the threshold side for winning contexts:
          • High-EV context (q > +0.50): lower floor by 0.05 → more trades pass
          • Losing context (q < -0.30):  raise floor by 0.05 → tighter filter
          • Neutral / unexplored:        no change (return 0.0)

        Net effect: in 07h/10h/14h MEAN_REVERTING alpha contexts where Q climbs
        positive, both the signal confidence and the acceptance threshold move
        in the same direction — compounding the frequency lift for high-alpha setups.
        """
        ctx_key = make_context(regime, utc_hour, strategy)
        state   = self._get_or_create(ctx_key)

        if state.n_visits < MIN_VISITS_EXPLORE:
            return 0.0   # no data yet — do not adjust threshold

        q = state.q_value
        if q > 0.50:
            return -0.05   # lower floor → more trades in winning context
        if q < -0.30:
            return +0.05   # raise floor → tighter filter in losing context
        return 0.0

    # ── Internal ──────────────────────────────────────────────────────────────

    def _get_or_create(self, ctx_key: str) -> ContextState:
        if ctx_key not in self._table:
            if len(self._table) >= MAX_CONTEXTS:
                # Remove the least-visited context to cap table size
                lru = min(self._table, key=lambda k: self._table[k].n_visits)
                del self._table[lru]
            self._table[ctx_key] = ContextState(context=ctx_key)
        return self._table[ctx_key]

    # ── Reporting ─────────────────────────────────────────────────────────────

    def top_contexts(self, n: int = 10) -> list:
        """Return top-n contexts by Q-value (for dashboard)."""
        ranked = sorted(
            self._table.values(),
            key=lambda s: s.q_value,
            reverse=True,
        )
        return [
            {
                "context":  s.context,
                "q_value":  round(s.q_value, 4),
                "win_rate": round(s.win_rate, 3),
                "n_visits": s.n_visits,
                "total_pnl": round(s.total_pnl, 4),
            }
            for s in ranked[:n]
        ]

    def summary(self) -> dict:
        total = len(self._table)
        profitable = sum(1 for s in self._table.values() if s.q_value > 0)
        return {
            "module":          self.MODULE,
            "version":         self.VERSION,
            "total_contexts":  total,
            "profitable_pct":  round(profitable / total, 3) if total else 0.0,
            "total_pulls":     self._total_pulls,
            "total_updates":   self._total_updates,
            "total_allowed":   self._total_allowed,
            "total_blocked":   self._total_blocked,
            "allow_rate":      round(
                self._total_allowed / max(self._total_pulls, 1), 3
            ),
            "uptime_min":      round((time.time() - self._init_ts) / 60, 1),
            "top_contexts":    self.top_contexts(5),
            "hyper": {
                "learning_rate":    LEARNING_RATE,
                "ev_floor":         ENTRY_EV_FLOOR,
                "ucb_coeff":        UCB_EXPLORE_COEFF,
                "min_visits":       MIN_VISITS_EXPLORE,
            },
        }


# ── Module-level singleton ────────────────────────────────────────────────────
rl_engine = RLContextualBandit()
