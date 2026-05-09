"""
EOW Quant Engine — Hyper-Adaptive RL Evolution Engine  (FTD-RL-EVOLUTION)

Algorithm: Contextual Multi-Armed Bandit with UCB1 + adaptive intelligence layer.

Core improvements over v1.0:
  ① ADAPTIVE LEARNING RATE     — α scales with context maturity (0.25→0.07)
                                  Fresh contexts learn fast; mature ones stay stable.
  ② MULTI-FACTOR REWARD SHAPING — reward = f(net_pnl, fee_efficiency, R-quality)
                                  Teaches high-quality profitability, not raw profit.
  ③ TIME-DECAY OF STALE Q-VALUES — Q drifts toward 0 at 2% per day of inactivity.
                                  Prevents stale profitable-context memory from
                                  blocking necessary re-exploration.
  ④ 4-TIER CONFIDENCE BOOST     — ELITE/HIGH/NEUTRAL/PENALIZED (was 3-tier).
                                  Smoother, more responsive frequency scaling.
  ⑤ REGIME-AWARE UCB COEFFICIENT — TRENDING gets 1.2× exploration, VOLATILITY 0.8×.
                                  Regime-sensitive participation logic.
  ⑥ CROSS-CONTEXT BOOTSTRAP     — New context Q initialized from similar-regime
                                  contexts at 50% dampen. Eliminates cold-start lag.
  ⑦ TOXIC CONTEXT DETECTION     — Fee-toxic / deep-negative contexts flagged early
                                  to stop wasting exploration cycles.
  ⑧ SAFETY CLAMPS               — Q-values bounded [-2, +5]; multipliers bounded
                                  [0.75, 1.40]; decay floored at -0.50.

Public API (100% backward-compatible with v1.0):
  rl_engine.should_trade(regime, utc_hour, strategy, override_floor)
  rl_engine.update(regime, utc_hour, strategy, net_pnl, fee_cost, r_multiple)
  rl_engine.confidence_boost(regime, utc_hour, strategy)
  rl_engine.get_dynamic_min_rr(regime, utc_hour, strategy, base_min_rr)
  rl_engine.get_score_floor_delta(regime, utc_hour, strategy)
  rl_engine.summary()
  rl_engine.top_contexts(n), rl_engine.bottom_contexts(n)

New observability methods:
  rl_engine.get_evolution_state()
  rl_engine.get_toxic_contexts()
  rl_engine.is_toxic(regime, utc_hour, strategy)

Anti-cheating / realism guarantees:
  • Reward is derived from CLOSED TRADE data only (no look-ahead)
  • Fee efficiency shaping uses post-close fee_cost (already recorded)
  • Cross-context bootstrap is damped read-only average — cannot inflate rewards
  • Q-value clamps prevent runaway exploitation of lucky early trades
"""
from __future__ import annotations

import json
import math
import pathlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from loguru import logger


# Default path for cross-session Q-table persistence
_QTABLE_STATE_PATH = pathlib.Path("data/rl_qtable_state.json")

# ── Adaptive learning rates by context maturity ───────────────────────────────

LR_FAST     = 0.25   # < 5 visits  — fast learning from scratch
LR_ACCEL    = 0.15   # 5–19 visits — accelerated convergence
LR_STANDARD = 0.10   # 20–49 visits — standard update
LR_STABLE   = 0.07   # 50+ visits  — conservative / stable

def _alpha(n_visits: int) -> float:
    """Return adaptive learning rate based on context maturity."""
    if n_visits < 5:
        return LR_FAST
    if n_visits < 20:
        return LR_ACCEL
    if n_visits < 50:
        return LR_STANDARD
    return LR_STABLE


# ── Core constants ────────────────────────────────────────────────────────────

ENTRY_EV_FLOOR    = -0.30   # minimum expected PnL to allow trade (USDT)
UCB_EXPLORE_COEFF = 1.5     # base UCB1 coefficient C in C×√(ln(N)/n)
MIN_VISITS_EXPLORE = 3      # must visit ≥ this many times before blocking
MAX_CONTEXTS      = 200     # cap on distinct (regime|session|strategy) contexts

# Regime-aware UCB multipliers — controls exploration intensity per regime type.
# TRENDING markets have more exploitable structure → slightly more exploration.
# VOLATILITY_EXPANSION is noisy → conservative exploration to avoid noise traps.
REGIME_UCB_MULT: Dict[str, float] = {
    "TRENDING":              1.20,
    "MEAN_REVERTING":        1.00,
    "VOLATILITY_EXPANSION":  0.80,
    "UNKNOWN":               1.10,
}


# ── 4-Tier Confidence Boost ───────────────────────────────────────────────────
# Replaces 3-tier with smoother, more responsive tiers.

CB_ELITE_Q   = 0.80   # q > 0.80 → ELITE context
CB_HIGH_Q    = 0.40   # q > 0.40 → HIGH quality context
CB_LOW_Q     = -0.20  # q < -0.20 → PENALIZED context

CB_ELITE     = 1.35   # hard cap: never boosted beyond 1.40 (safety clamp)
CB_HIGH      = 1.20
CB_NEUTRAL   = 1.00
CB_PENALIZED = 0.85   # hard floor: never reduced below 0.75

# Absolute safety bounds on the returned multiplier
CB_MULT_MAX  = 1.40
CB_MULT_MIN  = 0.75


# ── 4-Tier Score Floor Delta ──────────────────────────────────────────────────
# Smoother than the original binary ±0.05 scheme.

FD_ELITE   = -0.08   # dominant context → significantly lower acceptance floor
FD_HIGH    = -0.04   # good context → moderately lower floor
FD_NEUTRAL =  0.00
FD_LOW     = +0.04   # poor context → tighter filter


# ── Q-value safety bounds ─────────────────────────────────────────────────────

Q_MAX         = 5.0    # max realistic per-trade avg net PnL in USDT
Q_MIN         = -2.0   # prevents death spiral; deeper learning still captured in n_visits


# ── Memory decay parameters ───────────────────────────────────────────────────
# Stale Q-values decay toward 0 so the system re-explores changed markets.
# Applied in update() BEFORE the new reward — not in should_trade() (read-only gate).

DECAY_PER_DAY     = 0.98    # Q × 0.98 per day of inactivity (≈1% per day)
DECAY_MIN_HOURS   = 2.4     # < 2.4 h elapsed → no decay (within same session)
DECAY_Q_FLOOR     = -0.50   # Q never decays below this from time alone


# ── Multi-factor reward shaping ───────────────────────────────────────────────
# Shapes the raw net_pnl reward using post-close trade quality signals.
# Teaches the bandit to prefer fee-efficient, high-R outcomes.

FEE_QUALITY_THRESH    = 0.30   # fee > 30% of gross profit → penalise reward
FEE_QUALITY_MIN_MULT  = 0.60   # reward multiplier floor from fee penalty
LOW_R_QUALITY_THRESH  = 0.80   # R < 0.80 on a win → low-quality win
LOW_R_QUALITY_MULT    = 0.90   # mild penalty for scraped low-R wins


def _shape_reward(net_pnl: float, fee_cost: float, r_multiple: float) -> float:
    """
    Shape raw net_pnl into a quality-adjusted reward signal.

    Rules (causal, post-close data only):
      1. Fee-heavy profitable trades: fee > 30% of gross → reduce reward.
         Teaches the bandit to value fee-efficient profits over noise wins.
      2. Low R-multiple wins (R < 0.80): mild 10% penalty.
         Discourages chasing weak signals that barely break even.
      3. Losses: passed through unchanged (no reward inflation on losses).
         The system must experience real loss pain to learn what not to do.

    Returns shaped reward (float). Never makes a loss look profitable.
    """
    reward = net_pnl

    if net_pnl > 0:
        # Fee efficiency penalty (only on profitable trades)
        if fee_cost > 0:
            gross = net_pnl + fee_cost
            if gross > 1e-9:
                fee_ratio = fee_cost / gross
                if fee_ratio > FEE_QUALITY_THRESH:
                    # Linear penalty from 0.30 to max: 1.0 → FEE_QUALITY_MIN_MULT
                    excess = fee_ratio - FEE_QUALITY_THRESH
                    fee_mult = max(FEE_QUALITY_MIN_MULT, 1.0 - excess * 2.0)
                    reward *= fee_mult

        # Low R-multiple penalty (catch marginal winners)
        if 0.0 < r_multiple < LOW_R_QUALITY_THRESH:
            reward *= LOW_R_QUALITY_MULT

    # Safety: shaped reward must never turn a loss into a profit or vice versa
    if net_pnl < 0 and reward >= 0:
        reward = net_pnl   # revert if shaping crossed zero (shouldn't happen)
    if net_pnl > 0 and reward <= 0:
        reward = net_pnl * 0.10   # minimum credit for real profit

    return round(reward, 6)


# ── Time decay ────────────────────────────────────────────────────────────────

def _apply_time_decay(q_value: float, last_ts_ms: int, now_ms: int) -> float:
    """
    Decay Q-value toward zero based on elapsed time since last update.
    Applied once in update() before the new TD step.
    Never decays below DECAY_Q_FLOOR.
    """
    if last_ts_ms <= 0:
        return q_value   # no prior update — nothing to decay
    elapsed_hours = (now_ms - last_ts_ms) / 3_600_000.0
    if elapsed_hours < DECAY_MIN_HOURS:
        return q_value   # within same session — no decay
    elapsed_days = elapsed_hours / 24.0
    decay = DECAY_PER_DAY ** elapsed_days
    decayed = q_value * decay
    # Decay floor: don't over-punish good contexts through time alone
    if q_value > 0:
        return max(decayed, 0.0)        # positive Q only decays toward 0
    return max(decayed, DECAY_Q_FLOOR)  # negative Q: floor at DECAY_Q_FLOOR


# ── Cross-context bootstrap ───────────────────────────────────────────────────

BOOTSTRAP_DAMPEN       = 0.50   # 50% of similar-context average (conservative)
BOOTSTRAP_MIN_VISITS   = 3      # similar context must have ≥ 3 visits

def _bootstrap_q(table: Dict[str, "ContextState"], new_key: str) -> float:
    """
    Initialize a new context's Q-value from similar-regime contexts.
    'Similar' means same regime prefix (e.g. 'TRENDING|*|*').
    Bootstrap is read-only and dampened — cannot inflate above realistic values.
    Returns 0.0 when no qualifying similar contexts exist.
    """
    regime_prefix = new_key.split("|")[0]
    similar = [
        s for k, s in table.items()
        if k.split("|")[0] == regime_prefix and s.n_visits >= BOOTSTRAP_MIN_VISITS
    ]
    if not similar:
        return 0.0
    total_visits = sum(s.n_visits for s in similar)
    if total_visits == 0:
        return 0.0
    weighted_q = sum(s.q_value * s.n_visits for s in similar) / total_visits
    bootstrapped = round(weighted_q * BOOTSTRAP_DAMPEN, 4)
    # Clamp bootstrap to prevent it from skipping exploration requirement
    return max(min(bootstrapped, 0.20), -0.20)


# ── Toxic context detection ───────────────────────────────────────────────────

TOXIC_Q_THRESH    = -0.30   # Q below this → candidate for toxic flag
TOXIC_MIN_VISITS  = 8       # minimum trades before toxic classification


# ── Context key ───────────────────────────────────────────────────────────────

def make_context(regime: str, utc_hour: int, strategy: str) -> str:
    """
    Create a hashable context key from the three dimensions.

    hour_bucket groups hours into coarse trading sessions:
      ASIA   0-5,  LONDON  6-12,  NY  13-18,  LATE  19-23
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
    q_value:    float = 0.0    # running average quality-adjusted net PnL per trade
    n_visits:   int   = 0      # trade count in this context
    n_wins:     int   = 0
    total_pnl:  float = 0.0    # cumulative raw net PnL (unshaped, for reporting)
    last_ts:    int   = 0      # epoch ms of last update
    last_q:     float = 0.0    # Q-value before last update (for velocity tracking)
    bootstrap:  float = 0.0    # initial bootstrap Q (for audit/observability)

    @property
    def win_rate(self) -> float:
        return self.n_wins / self.n_visits if self.n_visits > 0 else 0.0

    @property
    def q_velocity(self) -> float:
        """Magnitude of last Q-update — proxy for learning activity."""
        return round(abs(self.q_value - self.last_q), 4)

    @property
    def maturity_score(self) -> float:
        """0–1 context maturity: 1.0 = fully mature (50+ visits)."""
        return min(self.n_visits / 50.0, 1.0)

    def ucb_bonus(self, total_visits: int, coeff: float) -> float:
        if self.n_visits == 0:
            return float("inf")
        return coeff * math.sqrt(math.log(max(total_visits, 2)) / self.n_visits)

    def ucb_score(self, total_visits: int, coeff: float) -> float:
        return self.q_value + self.ucb_bonus(total_visits, coeff)


# ── RL Engine ─────────────────────────────────────────────────────────────────

class RLContextualBandit:
    """
    Hyper-Adaptive Contextual Bandit for regime-aware trade filtering.

    v2.0 improvements over v1.0:
      • Adaptive α: new contexts learn at α=0.25, mature ones stabilise at 0.07.
      • Reward shaping: fee-heavy and low-R profits count less (teaches quality).
      • Time decay: stale Q-values erode so re-exploration triggers correctly.
      • 4-tier confidence/floor adjustments: smoother participation modulation.
      • Regime-aware UCB: exploration budget allocated by regime structure quality.
      • Bootstrap initialization: cold-start accelerated via similar-regime priors.
      • Toxic detection: deeply negative, well-explored contexts are flagged.
      • Safety clamps: Q, multipliers, deltas all bounded to prevent overfit.
    """

    MODULE  = "RL_CONTEXTUAL_BANDIT"
    VERSION = "2.0"

    def __init__(self):
        self._table:          Dict[str, ContextState] = {}
        self._toxic_contexts: Set[str]                = set()
        self._total_pulls:    int   = 0
        self._total_updates:  int   = 0
        self._total_blocked:  int   = 0
        self._total_allowed:  int   = 0
        self._explore_trades: int   = 0
        self._exploit_trades: int   = 0
        self._boost_fires:    int   = 0   # times ELITE boost (1.35×) fired
        self._floor_lowers:   int   = 0   # times score floor lowered
        self._floor_raises:   int   = 0   # times score floor raised
        self._toxic_blocks:   int   = 0   # trades blocked via toxic flag
        self._init_ts:        float = time.time()
        # Active save path — bound by load_state() when a custom path is given,
        # defaults to the global constant so all auto-saves are consistent.
        self._state_path: pathlib.Path = _QTABLE_STATE_PATH

        # Restore cross-session knowledge so learning is not wiped on restart
        _loaded = self.load_state()
        logger.info(
            f"[RL-ENGINE] Contextual Bandit v{self.VERSION} online | "
            f"adaptive_lr=[{LR_STABLE}-{LR_FAST}] ev_floor={ENTRY_EV_FLOOR} "
            f"ucb_coeff={UCB_EXPLORE_COEFF} decay={DECAY_PER_DAY}/day "
            f"bootstrap_dampen={BOOTSTRAP_DAMPEN} toxic_q<{TOXIC_Q_THRESH} "
            f"restored={'yes' if _loaded else 'cold-start'}"
        )

    # ── Persistence ───────────────────────────────────────────────────────────

    def save_state(self, path: Optional[pathlib.Path] = None) -> None:
        """
        Persist Q-table and toxic context set to disk.

        Counters (_total_pulls etc.) are intentionally NOT persisted — they
        are session-level statistics for report metrics only.  The Q-table
        and toxic set are the learned knowledge that must survive restarts.
        """
        target = path or self._state_path
        try:
            payload = {
                "version":  self.VERSION,
                "saved_at": int(time.time() * 1000),
                "toxic_contexts": list(self._toxic_contexts),
                "table": {
                    k: {
                        "context":   s.context,
                        "q_value":   s.q_value,
                        "n_visits":  s.n_visits,
                        "n_wins":    s.n_wins,
                        "total_pnl": s.total_pnl,
                        "last_ts":   s.last_ts,
                        "last_q":    s.last_q,
                        "bootstrap": s.bootstrap,
                    }
                    for k, s in self._table.items()
                },
            }
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(payload, indent=2))
        except Exception as _e:
            logger.warning(f"[RL-ENGINE] save_state failed: {_e}")

    def load_state(self, path: Optional[pathlib.Path] = None) -> bool:
        """
        Load persisted Q-table from disk.  Returns True if successfully loaded.
        Silently no-ops when no state file exists (normal cold-start).
        """
        target = path or self._state_path
        if path is not None:
            self._state_path = path   # bind so auto-saves go to the same file
        if not target.exists():
            return False
        try:
            payload = json.loads(target.read_text())
            for k, v in payload.get("table", {}).items():
                self._table[k] = ContextState(
                    context   = v["context"],
                    q_value   = float(v["q_value"]),
                    n_visits  = int(v["n_visits"]),
                    n_wins    = int(v["n_wins"]),
                    total_pnl = float(v["total_pnl"]),
                    last_ts   = int(v["last_ts"]),
                    last_q    = float(v["last_q"]),
                    bootstrap = float(v.get("bootstrap", 0.0)),
                )
            self._toxic_contexts = set(payload.get("toxic_contexts", []))
            logger.info(
                f"[RL-ENGINE] State restored from {target} — "
                f"{len(self._table)} contexts, "
                f"{len(self._toxic_contexts)} toxic"
            )
            return True
        except Exception as _e:
            logger.warning(f"[RL-ENGINE] load_state failed: {_e}")
            return False

    # ── Public API ────────────────────────────────────────────────────────────

    def should_trade(
        self,
        regime:         str,
        utc_hour:       int,
        strategy:       str,
        override_floor: Optional[float] = None,
    ) -> Tuple[bool, str]:
        """
        Decide whether to enter a trade given current context.

        Returns (allowed: bool, reason: str).

        Rules:
          1. Under-explored contexts always pass (guaranteed exploration).
          2. Toxic contexts (deep negative Q, well-visited) are blocked.
          3. UCB score > floor → TRADE. UCB includes regime-aware coefficient.
        """
        ctx_key  = make_context(regime, utc_hour, strategy)
        state    = self._get_or_create(ctx_key)
        floor    = override_floor if override_floor is not None else ENTRY_EV_FLOOR
        self._total_pulls += 1

        # Rule 1: always explore under-visited contexts
        if state.n_visits < MIN_VISITS_EXPLORE:
            self._total_allowed  += 1
            self._explore_trades += 1
            return True, f"RL_EXPLORE(visits={state.n_visits}<{MIN_VISITS_EXPLORE})"

        # Rule 2: toxic context block (after sufficient visits)
        if ctx_key in self._toxic_contexts:
            self._total_blocked += 1
            self._toxic_blocks  += 1
            return False, (
                f"RL_TOXIC(q={state.q_value:+.3f} "
                f"wr={state.win_rate:.0%} n={state.n_visits})"
            )

        # Rule 3: regime-aware UCB gate
        regime_coeff = UCB_EXPLORE_COEFF * REGIME_UCB_MULT.get(regime, 1.0)
        ucb = state.ucb_score(self._total_pulls, regime_coeff)

        if ucb > floor:
            self._total_allowed  += 1
            self._exploit_trades += 1
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
        regime:     str,
        utc_hour:   int,
        strategy:   str,
        net_pnl:    float,
        fee_cost:   float = 0.0,
        r_multiple: float = 0.0,
    ) -> None:
        """
        Update Q-value after a trade closes.

        Steps:
          1. Apply time decay to stale Q-value.
          2. Shape reward for fee efficiency and R quality.
          3. TD(0) update with adaptive α.
          4. Clamp Q to safety bounds.
          5. Check toxic status.
        """
        ctx_key = make_context(regime, utc_hour, strategy)
        state   = self._get_or_create(ctx_key)
        now_ms  = int(time.time() * 1000)

        # Step 1: Time decay of stale Q-value
        old_q = _apply_time_decay(state.q_value, state.last_ts, now_ms)

        # Step 2: Multi-factor reward shaping
        reward = _shape_reward(net_pnl, fee_cost, r_multiple)

        # Step 3: Adaptive TD(0) update
        alpha = _alpha(state.n_visits)
        new_q = old_q + alpha * (reward - old_q)

        # Step 4: Safety clamp
        new_q = max(Q_MIN, min(Q_MAX, new_q))

        # Bookkeeping
        state.last_q     = state.q_value
        state.q_value    = round(new_q, 5)
        state.n_visits  += 1
        state.total_pnl += net_pnl   # raw PnL for reporting (unshaped)
        if net_pnl > 0:
            state.n_wins += 1
        state.last_ts = now_ms
        self._total_updates += 1

        # Step 5: Toxic context check
        self._check_toxic(ctx_key, state)

        # Persist updated knowledge so restarts don't wipe learning
        self.save_state()

        logger.debug(
            f"[RL-ENGINE] update ctx={ctx_key} "
            f"raw={net_pnl:+.4f} shaped={reward:+.4f} "
            f"α={alpha} q: {state.last_q:+.4f}→{state.q_value:+.4f} "
            f"n={state.n_visits} wr={state.win_rate:.0%}"
        )

    def confidence_boost(
        self,
        regime:   str,
        utc_hour: int,
        strategy: str,
    ) -> float:
        """
        Returns a confidence multiplier [0.75–1.40] based on learned Q-value.

        4-tier system for smoother participation modulation:
          ELITE    q > 0.80 → 1.35×  (dominant context, high frequency)
          HIGH     q > 0.40 → 1.20×  (profitable context, elevated frequency)
          NEUTRAL  q ≥ -0.20 → 1.00× (no adjustment)
          PENALIZED q < -0.20 → 0.85× (losing context, reduced participation)

        Under-explored contexts (< MIN_VISITS_EXPLORE) get NEUTRAL — no data yet.
        """
        ctx_key = make_context(regime, utc_hour, strategy)
        state   = self._get_or_create(ctx_key)

        if state.n_visits < MIN_VISITS_EXPLORE:
            return CB_NEUTRAL

        q = state.q_value
        if q > CB_ELITE_Q:
            self._boost_fires += 1
            mult = CB_ELITE
        elif q > CB_HIGH_Q:
            mult = CB_HIGH
        elif q >= CB_LOW_Q:
            mult = CB_NEUTRAL
        else:
            mult = CB_PENALIZED

        return round(max(CB_MULT_MIN, min(CB_MULT_MAX, mult)), 3)

    def get_dynamic_min_rr(
        self,
        regime:      str,
        utc_hour:    int,
        strategy:    str,
        base_min_rr: float = 2.5,
    ) -> float:
        """
        Returns a context-aware minimum RR requirement.

        Profitable contexts (q > +0.30): relax to 2.0 (more trades).
        Unprofitable contexts (q < -0.20): tighten to 3.0 (fewer, better trades).
        Neutral / unexplored: base_min_rr.
        """
        ctx_key = make_context(regime, utc_hour, strategy)
        state   = self._get_or_create(ctx_key)

        if state.n_visits < MIN_VISITS_EXPLORE:
            return max(base_min_rr - 0.5, 2.0)

        q = state.q_value
        if q > 0.30:
            return max(base_min_rr - 0.5, 2.0)
        if q < -0.20:
            return min(base_min_rr + 0.5, 3.5)
        return base_min_rr

    def get_score_floor_delta(
        self,
        regime:   str,
        utc_hour: int,
        strategy: str,
    ) -> float:
        """
        Returns a delta to subtract from the score gate floor.

        4-tier smooth scheme (was binary ±0.05):
          ELITE    q > 0.80 → -0.08  (significantly lower floor, more trades)
          HIGH     q > 0.40 → -0.04  (moderately lower floor)
          NEUTRAL  q ≥ -0.20 → 0.00 (no change)
          PENALIZED q < -0.20 → +0.04 (tighter filter)

        Combined with confidence_boost(): both signal side and threshold side
        move toward execution in high-alpha contexts (compounding lift).
        """
        ctx_key = make_context(regime, utc_hour, strategy)
        state   = self._get_or_create(ctx_key)

        if state.n_visits < MIN_VISITS_EXPLORE:
            return 0.0

        q = state.q_value
        if q > CB_ELITE_Q:
            self._floor_lowers += 1
            return FD_ELITE
        if q > CB_HIGH_Q:
            self._floor_lowers += 1
            return FD_HIGH
        if q >= CB_LOW_Q:
            return FD_NEUTRAL
        self._floor_raises += 1
        return FD_LOW

    # ── Toxic context ─────────────────────────────────────────────────────────

    def is_toxic(self, regime: str, utc_hour: int, strategy: str) -> bool:
        """Return True if this context has been flagged as toxic."""
        return make_context(regime, utc_hour, strategy) in self._toxic_contexts

    def get_toxic_contexts(self) -> List[dict]:
        """Return all flagged toxic contexts with current stats."""
        result = []
        for key in self._toxic_contexts:
            state = self._table.get(key)
            if state:
                result.append({
                    "context":   key,
                    "q_value":   round(state.q_value, 4),
                    "win_rate":  round(state.win_rate, 3),
                    "n_visits":  state.n_visits,
                    "total_pnl": round(state.total_pnl, 4),
                })
        return sorted(result, key=lambda x: x["q_value"])

    # ── Evolution observability ───────────────────────────────────────────────

    def get_evolution_state(self) -> dict:
        """
        Full learning-evolution snapshot for dashboards, diagnostics, and logs.
        Read-only — no trading logic depends on this.
        """
        contexts = list(self._table.values())
        n_total  = len(contexts)

        if n_total == 0:
            return {
                "module":  self.MODULE,
                "version": self.VERSION,
                "status":  "COLD_START",
                "total_contexts": 0,
            }

        # Learning speed — fraction of contexts in each maturity tier
        fresh    = sum(1 for s in contexts if s.n_visits < 5)
        accel    = sum(1 for s in contexts if 5  <= s.n_visits < 20)
        standard = sum(1 for s in contexts if 20 <= s.n_visits < 50)
        mature   = sum(1 for s in contexts if s.n_visits >= 50)

        # Intelligence quality
        profitable = sum(1 for s in contexts if s.q_value > 0)
        elite      = sum(1 for s in contexts if s.q_value > CB_ELITE_Q)
        high       = sum(1 for s in contexts if CB_HIGH_Q < s.q_value <= CB_ELITE_Q)
        penalized  = sum(1 for s in contexts if s.q_value < CB_LOW_Q)

        # Average Q across visited contexts
        visited = [s for s in contexts if s.n_visits >= MIN_VISITS_EXPLORE]
        avg_q   = sum(s.q_value for s in visited) / len(visited) if visited else 0.0

        # Q-velocity (average magnitude of last Q-update, proxy for learning activity)
        velocities = [s.q_velocity for s in contexts if s.n_visits > 0]
        avg_vel    = sum(velocities) / len(velocities) if velocities else 0.0

        # Exploration pressure: ratio of explore-to-exploit
        explored = self._explore_trades + self._exploit_trades
        explore_ratio = self._explore_trades / max(explored, 1)

        # Intelligence evolution score (0–100)
        # Based on: profitable ratio, maturity ratio, allow rate, avg Q
        profitable_ratio = profitable / max(n_total, 1)
        maturity_ratio   = mature / max(n_total, 1)
        allow_rate       = self._total_allowed / max(self._total_pulls, 1)
        q_score          = max(0.0, min(avg_q / 0.5, 1.0))   # normalized avg Q
        evo_score = round(
            (profitable_ratio * 30
             + maturity_ratio  * 20
             + allow_rate      * 20
             + q_score         * 30),
            1
        )

        # Per-session intelligence (by hour bucket)
        session_q: Dict[str, List[float]] = {"ASIA": [], "LONDON": [], "NY": [], "LATE": []}
        for k, s in self._table.items():
            parts = k.split("|")
            if len(parts) >= 2:
                bucket = parts[1]
                if bucket in session_q and s.n_visits >= MIN_VISITS_EXPLORE:
                    session_q[bucket].append(s.q_value)

        session_intel = {
            bucket: {
                "n_contexts": len(qs),
                "avg_q":      round(sum(qs) / len(qs), 4) if qs else 0.0,
                "profitable": sum(1 for q in qs if q > 0),
            }
            for bucket, qs in session_q.items()
        }

        return {
            "module":       self.MODULE,
            "version":      self.VERSION,
            "intelligence_score": evo_score,
            "total_contexts": n_total,
            "context_maturity": {
                "fresh":    fresh,
                "accel":    accel,
                "standard": standard,
                "mature":   mature,
            },
            "quality_distribution": {
                "elite":     elite,
                "high":      high,
                "neutral":   n_total - elite - high - penalized,
                "penalized": penalized,
                "profitable_pct": round(profitable_ratio * 100, 1),
            },
            "learning_dynamics": {
                "avg_q":         round(avg_q, 4),
                "avg_q_velocity": round(avg_vel, 4),
                "explore_ratio": round(explore_ratio, 3),
                "toxic_count":   len(self._toxic_contexts),
            },
            "session_intelligence": session_intel,
            "counters": {
                "total_pulls":    self._total_pulls,
                "total_updates":  self._total_updates,
                "total_allowed":  self._total_allowed,
                "total_blocked":  self._total_blocked,
                "toxic_blocks":   self._toxic_blocks,
                "boost_fires":    self._boost_fires,
                "floor_lowers":   self._floor_lowers,
                "floor_raises":   self._floor_raises,
            },
            "uptime_min": round((time.time() - self._init_ts) / 60, 1),
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _get_or_create(self, ctx_key: str) -> ContextState:
        if ctx_key not in self._table:
            if len(self._table) >= MAX_CONTEXTS:
                # Evict context with fewest visits (LRU by data, not by time)
                lru = min(self._table, key=lambda k: self._table[k].n_visits)
                del self._table[lru]
                self._toxic_contexts.discard(lru)

            # Bootstrap Q from similar-regime contexts (cold-start acceleration)
            bq = _bootstrap_q(self._table, ctx_key)
            self._table[ctx_key] = ContextState(
                context=ctx_key, q_value=bq, bootstrap=bq
            )
            if bq != 0.0:
                logger.debug(
                    f"[RL-ENGINE] New context {ctx_key} bootstrapped q={bq:+.4f}"
                )
        return self._table[ctx_key]

    def _check_toxic(self, ctx_key: str, state: ContextState) -> None:
        """
        Flag a context as toxic when it has enough data and a deep negative Q.
        A toxic context is still shown in reports but blocked in should_trade().
        Can recover: if Q rises above TOXIC_Q_THRESH after more trades, deflag.
        """
        if state.n_visits >= TOXIC_MIN_VISITS:
            if state.q_value < TOXIC_Q_THRESH:
                if ctx_key not in self._toxic_contexts:
                    self._toxic_contexts.add(ctx_key)
                    logger.warning(
                        f"[RL-ENGINE] TOXIC_CONTEXT flagged: {ctx_key} "
                        f"q={state.q_value:+.4f} n={state.n_visits} "
                        f"wr={state.win_rate:.0%}"
                    )
            else:
                # Recovery: context improved — deflag
                if ctx_key in self._toxic_contexts:
                    self._toxic_contexts.discard(ctx_key)
                    logger.info(
                        f"[RL-ENGINE] TOXIC_CONTEXT recovered: {ctx_key} "
                        f"q={state.q_value:+.4f}"
                    )

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
                "context":   s.context,
                "q_value":   round(s.q_value, 4),
                "ucb_bonus": round(s.ucb_bonus(self._total_pulls, UCB_EXPLORE_COEFF), 4),
                "win_rate":  round(s.win_rate, 3),
                "n_visits":  s.n_visits,
                "total_pnl": round(s.total_pnl, 4),
                "maturity":  round(s.maturity_score, 3),
            }
            for s in ranked[:n]
        ]

    def bottom_contexts(self, n: int = 3) -> list:
        """Return bottom-n visited contexts by Q-value (near-block / toxic candidates)."""
        visited = [s for s in self._table.values() if s.n_visits >= MIN_VISITS_EXPLORE]
        ranked  = sorted(visited, key=lambda s: s.q_value)
        return [
            {
                "context":   s.context,
                "q_value":   round(s.q_value, 4),
                "ucb_score": round(s.ucb_score(self._total_pulls, UCB_EXPLORE_COEFF), 4),
                "win_rate":  round(s.win_rate, 3),
                "n_visits":  s.n_visits,
                "total_pnl": round(s.total_pnl, 4),
                "near_block": s.ucb_score(self._total_pulls, UCB_EXPLORE_COEFF) < ENTRY_EV_FLOOR + 0.20,
                "toxic":     s.context in self._toxic_contexts,
            }
            for s in ranked[:n]
        ]

    def summary(self) -> dict:
        total      = len(self._table)
        profitable = sum(1 for s in self._table.values() if s.q_value > 0)
        explored   = self._explore_trades + self._exploit_trades
        return {
            "module":          self.MODULE,
            "version":         self.VERSION,
            "total_contexts":  total,
            "profitable_pct":  round(profitable / total, 3) if total else 0.0,
            "toxic_contexts":  len(self._toxic_contexts),
            "total_pulls":     self._total_pulls,
            "total_updates":   self._total_updates,
            "total_allowed":   self._total_allowed,
            "total_blocked":   self._total_blocked,
            "allow_rate":      round(
                self._total_allowed / max(self._total_pulls, 1), 3
            ),
            "explore_trades":  self._explore_trades,
            "exploit_trades":  self._exploit_trades,
            "explore_ratio":   round(
                self._explore_trades / max(explored, 1), 3
            ),
            "boost_fires":     self._boost_fires,
            "floor_lowers":    self._floor_lowers,
            "floor_raises":    self._floor_raises,
            "toxic_blocks":    self._toxic_blocks,
            "uptime_min":      round((time.time() - self._init_ts) / 60, 1),
            "top_contexts":    self.top_contexts(5),
            "bottom_contexts": self.bottom_contexts(3),
            "hyper": {
                "learning_rate_adaptive": f"{LR_STABLE}→{LR_FAST} (by maturity)",
                "ev_floor":              ENTRY_EV_FLOOR,
                "ucb_coeff":             UCB_EXPLORE_COEFF,
                "min_visits":            MIN_VISITS_EXPLORE,
                "q_bounds":              [Q_MIN, Q_MAX],
                "decay_per_day":         DECAY_PER_DAY,
                "bootstrap_dampen":      BOOTSTRAP_DAMPEN,
                "regime_ucb_mult":       REGIME_UCB_MULT,
            },
        }


# ── Module-level singleton ────────────────────────────────────────────────────
rl_engine = RLContextualBandit()
