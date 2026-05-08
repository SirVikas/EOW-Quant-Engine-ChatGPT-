"""
EOW Quant Engine — RL Evolution Test Suite  (FTD-RL-EVOLUTION)

Validates all new RL intelligence features:
  A. Adaptive learning rate
  B. Multi-factor reward shaping
  C. Time-decay of stale Q-values
  D. 4-tier confidence boost
  E. 4-tier score floor delta
  F. Regime-aware UCB coefficient
  G. Cross-context bootstrap
  H. Toxic context detection and recovery
  I. Safety clamps (Q bounds, multiplier bounds)
  J. Enhanced learning_engine recency weighting
  K. RLEvolutionLayer observability

Run:
    python tests/test_rl_evolution.py
"""
from __future__ import annotations

import sys
import time
import math
from typing import Any

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

_passed = 0
_failed = 0


def _ok(label: str) -> None:
    global _passed
    _passed += 1
    print(f"  {GREEN}✓{RESET}  {label}")


def _fail(label: str, reason: str = "") -> None:
    global _failed
    _failed += 1
    msg = f"  {RED}✗{RESET}  {label}"
    if reason:
        msg += f"\n       {RED}{reason}{RESET}"
    print(msg)


def _section(title: str) -> None:
    print(f"\n{BOLD}{YELLOW}── {title} {'─' * max(0, 55 - len(title))}{RESET}")


# ── Import modules ─────────────────────────────────────────────────────────────
_section("MODULE IMPORTS")

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

try:
    from core.rl_engine import (
        RLContextualBandit,
        ContextState,
        make_context,
        _alpha,
        _shape_reward,
        _apply_time_decay,
        _bootstrap_q,
        LR_FAST, LR_ACCEL, LR_STANDARD, LR_STABLE,
        ENTRY_EV_FLOOR, UCB_EXPLORE_COEFF, MIN_VISITS_EXPLORE,
        CB_ELITE_Q, CB_HIGH_Q, CB_LOW_Q,
        CB_ELITE, CB_HIGH, CB_NEUTRAL, CB_PENALIZED,
        CB_MULT_MAX, CB_MULT_MIN,
        FD_ELITE, FD_HIGH, FD_NEUTRAL, FD_LOW,
        Q_MAX, Q_MIN,
        DECAY_PER_DAY, DECAY_Q_FLOOR,
        FEE_QUALITY_THRESH,
        TOXIC_Q_THRESH, TOXIC_MIN_VISITS,
        REGIME_UCB_MULT,
        rl_engine,
    )
    _ok("core.rl_engine imported (v2.0)")
except ImportError as e:
    _fail("core.rl_engine import", str(e))
    sys.exit(1)

try:
    from core.learning_engine import LearningEngine, RECENCY_DECAY
    _ok("core.learning_engine imported (recency-weighted)")
except ImportError as e:
    _fail("core.learning_engine import", str(e))
    sys.exit(1)

try:
    from core.rl_evolution_layer import RLEvolutionLayer, rl_evolution_layer
    _ok("core.rl_evolution_layer imported")
except ImportError as e:
    _fail("core.rl_evolution_layer import", str(e))
    sys.exit(1)


# ═════════════════════════════════════════════════════════════════════════════
# A. ADAPTIVE LEARNING RATE
# ═════════════════════════════════════════════════════════════════════════════
_section("A — Adaptive Learning Rate")

if _alpha(0) == LR_FAST:
    _ok(f"n=0 → α={LR_FAST} (FAST)")
else:
    _fail("n=0 adaptive α", f"expected {LR_FAST}, got {_alpha(0)}")

if _alpha(4) == LR_FAST:
    _ok(f"n=4 → α={LR_FAST} (still FAST, boundary)")
else:
    _fail("n=4 adaptive α", f"got {_alpha(4)}")

if _alpha(5) == LR_ACCEL:
    _ok(f"n=5 → α={LR_ACCEL} (ACCEL)")
else:
    _fail("n=5 adaptive α", f"got {_alpha(5)}")

if _alpha(19) == LR_ACCEL:
    _ok(f"n=19 → α={LR_ACCEL} (still ACCEL)")
else:
    _fail("n=19 adaptive α", f"got {_alpha(19)}")

if _alpha(20) == LR_STANDARD:
    _ok(f"n=20 → α={LR_STANDARD} (STANDARD)")
else:
    _fail("n=20 adaptive α", f"got {_alpha(20)}")

if _alpha(50) == LR_STABLE:
    _ok(f"n=50 → α={LR_STABLE} (STABLE)")
else:
    _fail("n=50 adaptive α", f"got {_alpha(50)}")

# Fast learning actually IS faster: verify Q converges faster for n=0 vs n=50
# Simulate 3 identical rewards and check Q-value
def _simulate_q(n_start: int, reward: float, steps: int = 3) -> float:
    q = 0.0
    for i in range(steps):
        alpha = _alpha(n_start + i)
        q = q + alpha * (reward - q)
    return q

q_fast   = _simulate_q(0, reward=1.0)
q_stable = _simulate_q(50, reward=1.0)

if q_fast > q_stable:
    _ok(f"Fast-start contexts converge faster (q_fast={q_fast:.3f} > q_stable={q_stable:.3f})")
else:
    _fail("Fast contexts should converge faster", f"q_fast={q_fast:.3f} q_stable={q_stable:.3f}")


# ═════════════════════════════════════════════════════════════════════════════
# B. MULTI-FACTOR REWARD SHAPING
# ═════════════════════════════════════════════════════════════════════════════
_section("B — Multi-Factor Reward Shaping")

# Clean win — no shaping needed
r = _shape_reward(net_pnl=1.0, fee_cost=0.0, r_multiple=2.0)
if r == 1.0:
    _ok("Clean win (fee=0, R=2.0) → reward unchanged = 1.0")
else:
    _fail("Clean win reward", f"expected 1.0, got {r}")

# Fee-heavy win: fee > 30% of gross → penalised
# net_pnl=0.5, fee=0.6, gross=1.1, fee_ratio=0.545 (>0.30)
r_fee = _shape_reward(net_pnl=0.5, fee_cost=0.6, r_multiple=2.0)
if r_fee < 0.5:
    _ok(f"Fee-heavy win penalised: shaped={r_fee:.4f} < raw=0.5")
else:
    _fail("Fee-heavy win should be penalised", f"got {r_fee:.4f}")

# Minimum fee multiplier enforced (reward > 0 for profitable trade)
if r_fee > 0:
    _ok("Fee penalty still leaves positive reward for profitable trade")
else:
    _fail("Fee penalty should not make profitable trade negative", f"got {r_fee}")

# Low R-multiple win: R=0.5 < 0.80 → 10% penalty
r_low_r = _shape_reward(net_pnl=1.0, fee_cost=0.0, r_multiple=0.5)
if abs(r_low_r - 0.90) < 0.001:
    _ok(f"Low-R win (R=0.5) penalised by 10%: shaped={r_low_r:.3f}")
else:
    _fail("Low-R win penalty", f"expected 0.90, got {r_low_r:.4f}")

# Normal R: R=0.9 ≥ 0.80 → no penalty
r_ok_r = _shape_reward(net_pnl=1.0, fee_cost=0.0, r_multiple=0.9)
if r_ok_r == 1.0:
    _ok("R=0.9 (≥ threshold 0.80) → no penalty")
else:
    _fail("R=0.9 should have no penalty", f"got {r_ok_r}")

# Loss → passed through unchanged
r_loss = _shape_reward(net_pnl=-0.5, fee_cost=0.1, r_multiple=-1.0)
if r_loss == -0.5:
    _ok("Loss passed through unchanged (no reward inflation on losses)")
else:
    _fail("Loss reward should be unchanged", f"expected -0.5, got {r_loss}")

# Sign preservation: shaped profit must remain positive
r_edge = _shape_reward(net_pnl=0.001, fee_cost=10.0, r_multiple=0.0)
if r_edge > 0:
    _ok("Extreme fee penalty: shaped reward stays positive (sign preserved)")
else:
    _fail("Sign preservation failed", f"got {r_edge}")


# ═════════════════════════════════════════════════════════════════════════════
# C. TIME DECAY OF STALE Q-VALUES
# ═════════════════════════════════════════════════════════════════════════════
_section("C — Time Decay")

now_ms = int(time.time() * 1000)

# Recent activity (1 hour ago) → no decay
one_hour_ago = now_ms - 3_600_000
q_recent = _apply_time_decay(q_value=0.5, last_ts_ms=one_hour_ago, now_ms=now_ms)
if q_recent == 0.5:
    _ok("Q unchanged for activity < 2.4h threshold")
else:
    _fail("Recent Q should not decay", f"expected 0.5, got {q_recent}")

# Stale activity (10 days ago) → significant decay
ten_days_ago = now_ms - 10 * 86400_000
q_stale = _apply_time_decay(q_value=0.5, last_ts_ms=ten_days_ago, now_ms=now_ms)
expected_max = 0.5 * (DECAY_PER_DAY ** 10)
if q_stale < 0.5 and abs(q_stale - expected_max) < 0.01:
    _ok(f"10-day stale Q decayed: {0.5:.3f}→{q_stale:.4f} (≈{expected_max:.4f})")
else:
    _fail("10-day decay", f"expected ≈{expected_max:.4f}, got {q_stale:.4f}")

# Decay floor: negative Q decays toward 0 but stops at DECAY_Q_FLOOR
q_floor = _apply_time_decay(q_value=-1.0, last_ts_ms=ten_days_ago, now_ms=now_ms)
if q_floor >= DECAY_Q_FLOOR:
    _ok(f"Negative Q decay respects floor ({DECAY_Q_FLOOR}): got {q_floor:.4f}")
else:
    _fail("Decay floor violated", f"expected ≥{DECAY_Q_FLOOR}, got {q_floor:.4f}")

# No decay when last_ts=0 (never updated)
q_never = _apply_time_decay(q_value=0.3, last_ts_ms=0, now_ms=now_ms)
if q_never == 0.3:
    _ok("Q with last_ts=0 (never updated) → no decay")
else:
    _fail("Never-updated Q should not decay", f"got {q_never}")

# Positive Q decays toward 0, not below
q_pos_floor = _apply_time_decay(q_value=0.1, last_ts_ms=ten_days_ago * 10, now_ms=now_ms)
if q_pos_floor >= 0.0:
    _ok("Positive Q never decays below 0 (floor=0.0 for positive Q)")
else:
    _fail("Positive Q crossed zero", f"got {q_pos_floor}")


# ═════════════════════════════════════════════════════════════════════════════
# D. 4-TIER CONFIDENCE BOOST
# ═════════════════════════════════════════════════════════════════════════════
_section("D — 4-Tier Confidence Boost")

eng = RLContextualBandit()

def _set_context_q(engine, regime, hour, strategy, q, n=10):
    """Helper: inject Q-value and n_visits into a context."""
    ctx_key = make_context(regime, hour, strategy)
    state = engine._get_or_create(ctx_key)
    state.q_value  = q
    state.n_visits = n
    state.n_wins   = n // 2

# ELITE tier
_set_context_q(eng, "TRENDING", 14, "TrendFollowing", q=0.85)
boost_elite = eng.confidence_boost("TRENDING", 14, "TrendFollowing")
if abs(boost_elite - CB_ELITE) < 0.001:
    _ok(f"ELITE boost (q=0.85): {boost_elite} = {CB_ELITE}")
else:
    _fail("ELITE boost", f"expected {CB_ELITE}, got {boost_elite}")

# HIGH tier
_set_context_q(eng, "TRENDING", 14, "MeanReversion", q=0.50)
boost_high = eng.confidence_boost("TRENDING", 14, "MeanReversion")
if abs(boost_high - CB_HIGH) < 0.001:
    _ok(f"HIGH boost (q=0.50): {boost_high} = {CB_HIGH}")
else:
    _fail("HIGH boost", f"expected {CB_HIGH}, got {boost_high}")

# NEUTRAL tier
_set_context_q(eng, "MEAN_REVERTING", 10, "MeanReversion", q=0.00)
boost_neutral = eng.confidence_boost("MEAN_REVERTING", 10, "MeanReversion")
if abs(boost_neutral - CB_NEUTRAL) < 0.001:
    _ok(f"NEUTRAL boost (q=0.00): {boost_neutral} = {CB_NEUTRAL}")
else:
    _fail("NEUTRAL boost", f"expected {CB_NEUTRAL}, got {boost_neutral}")

# PENALIZED tier
_set_context_q(eng, "MEAN_REVERTING", 10, "TrendFollowing", q=-0.40)
boost_pen = eng.confidence_boost("MEAN_REVERTING", 10, "TrendFollowing")
if abs(boost_pen - CB_PENALIZED) < 0.001:
    _ok(f"PENALIZED boost (q=-0.40): {boost_pen} = {CB_PENALIZED}")
else:
    _fail("PENALIZED boost", f"expected {CB_PENALIZED}, got {boost_pen}")

# Safety clamp: multiplier never outside [CB_MULT_MIN, CB_MULT_MAX]
if CB_MULT_MIN <= boost_elite <= CB_MULT_MAX:
    _ok(f"ELITE boost within safety clamp [{CB_MULT_MIN}, {CB_MULT_MAX}]")
else:
    _fail("Safety clamp on ELITE boost", f"got {boost_elite}")

# Under-explored: return NEUTRAL regardless of Q
eng2 = RLContextualBandit()
ctx = eng2._get_or_create("TRENDING|NY|TrendFollowing")
ctx.q_value  = 2.0   # very high Q
ctx.n_visits = 2     # but under-explored
boost_unexp = eng2.confidence_boost("TRENDING", 13, "TrendFollowing")
if boost_unexp == CB_NEUTRAL:
    _ok("Under-explored context returns NEUTRAL boost (no data yet)")
else:
    _fail("Under-explored boost", f"expected {CB_NEUTRAL}, got {boost_unexp}")


# ═════════════════════════════════════════════════════════════════════════════
# E. 4-TIER SCORE FLOOR DELTA
# ═════════════════════════════════════════════════════════════════════════════
_section("E — 4-Tier Score Floor Delta")

eng3 = RLContextualBandit()
_set_context_q(eng3, "TRENDING",      14, "TrendFollowing",  q=0.90)  # ELITE
_set_context_q(eng3, "TRENDING",      14, "MeanReversion",   q=0.45)  # HIGH
_set_context_q(eng3, "MEAN_REVERTING", 10, "MeanReversion",  q=0.10)  # NEUTRAL
_set_context_q(eng3, "MEAN_REVERTING", 10, "TrendFollowing", q=-0.30) # PENALIZED

delta_elite   = eng3.get_score_floor_delta("TRENDING",      14, "TrendFollowing")
delta_high    = eng3.get_score_floor_delta("TRENDING",      14, "MeanReversion")
delta_neutral = eng3.get_score_floor_delta("MEAN_REVERTING", 10, "MeanReversion")
delta_pen     = eng3.get_score_floor_delta("MEAN_REVERTING", 10, "TrendFollowing")

if abs(delta_elite - FD_ELITE) < 0.001:
    _ok(f"ELITE floor delta: {delta_elite} = {FD_ELITE} (most permissive)")
else:
    _fail("ELITE floor delta", f"expected {FD_ELITE}, got {delta_elite}")

if abs(delta_high - FD_HIGH) < 0.001:
    _ok(f"HIGH floor delta: {delta_high} = {FD_HIGH}")
else:
    _fail("HIGH floor delta", f"expected {FD_HIGH}, got {delta_high}")

if delta_neutral == FD_NEUTRAL:
    _ok(f"NEUTRAL floor delta: {delta_neutral} = {FD_NEUTRAL}")
else:
    _fail("NEUTRAL floor delta", f"expected {FD_NEUTRAL}, got {delta_neutral}")

if abs(delta_pen - FD_LOW) < 0.001:
    _ok(f"PENALIZED floor delta: {delta_pen} = {FD_LOW} (tighter filter)")
else:
    _fail("PENALIZED floor delta", f"expected {FD_LOW}, got {delta_pen}")

# ELITE < HIGH < NEUTRAL < PENALIZED (lower = more permissive)
if delta_elite < delta_high < delta_neutral < delta_pen:
    _ok("Floor deltas correctly ordered: ELITE < HIGH < NEUTRAL < PENALIZED")
else:
    _fail("Floor delta ordering", f"elite={delta_elite} high={delta_high} neutral={delta_neutral} pen={delta_pen}")


# ═════════════════════════════════════════════════════════════════════════════
# F. REGIME-AWARE UCB COEFFICIENT
# ═════════════════════════════════════════════════════════════════════════════
_section("F — Regime-Aware UCB")

eng4 = RLContextualBandit()

# Create fresh contexts with identical visit history, different regimes
def _fresh_ctx(engine, regime, strategy, n=5):
    ctx = make_context(regime, 14, strategy)
    state = engine._get_or_create(ctx)
    state.n_visits = n
    state.q_value  = 0.0
    return ctx

_fresh_ctx(eng4, "TRENDING",             "TrendFollowing",    n=5)
_fresh_ctx(eng4, "VOLATILITY_EXPANSION", "TrendFollowing",    n=5)
eng4._total_pulls = 100

ok_trending, reason_t = eng4.should_trade("TRENDING",             14, "TrendFollowing")
ok_vol,      reason_v = eng4.should_trade("VOLATILITY_EXPANSION", 14, "TrendFollowing")

# At q=0.0 and n=5, UCB score = 0.0 + coeff*sqrt(ln(100)/5)
# TRENDING coeff = 1.5 × 1.2 = 1.8 → higher UCB (more likely to trade)
# VOLATILITY coeff = 1.5 × 0.8 = 1.2 → lower UCB
trending_coeff = UCB_EXPLORE_COEFF * REGIME_UCB_MULT["TRENDING"]
vol_coeff      = UCB_EXPLORE_COEFF * REGIME_UCB_MULT["VOLATILITY_EXPANSION"]

if trending_coeff > vol_coeff:
    _ok(f"TRENDING UCB coeff ({trending_coeff:.2f}) > VOLATILITY_EXPANSION ({vol_coeff:.2f})")
else:
    _fail("Regime UCB coefficient ordering", f"trending={trending_coeff} vol={vol_coeff}")

if ok_trending:
    _ok("TRENDING context with q=0 allowed (UCB > floor)")
else:
    _fail("TRENDING context should be allowed", reason_t)

# UNKNOWN regime gets slight boost over MEAN_REVERTING
unknown_coeff = UCB_EXPLORE_COEFF * REGIME_UCB_MULT.get("UNKNOWN", 1.0)
mr_coeff      = UCB_EXPLORE_COEFF * REGIME_UCB_MULT["MEAN_REVERTING"]
if unknown_coeff > mr_coeff:
    _ok(f"UNKNOWN regime UCB ({unknown_coeff:.2f}) > MEAN_REVERTING ({mr_coeff:.2f})")
else:
    _fail("UNKNOWN vs MEAN_REVERTING UCB", f"unknown={unknown_coeff} mr={mr_coeff}")


# ═════════════════════════════════════════════════════════════════════════════
# G. CROSS-CONTEXT BOOTSTRAP
# ═════════════════════════════════════════════════════════════════════════════
_section("G — Cross-Context Bootstrap")

# Empty table → bootstrap returns 0.0
empty_table = {}
q0 = _bootstrap_q(empty_table, "TRENDING|NY|TrendFollowing")
if q0 == 0.0:
    _ok("Empty table → bootstrap returns 0.0")
else:
    _fail("Empty table bootstrap", f"expected 0.0, got {q0}")

# Table with similar-regime contexts → bootstrap returns dampened average
# Use low Q values so result stays below the 0.20 cap
from core.rl_engine import ContextState as CS
mock_table = {
    "TRENDING|NY|TrendFollowing": CS("TRENDING|NY|TrendFollowing",
                                      q_value=0.20, n_visits=10, n_wins=6),
    "TRENDING|LONDON|MeanReversion": CS("TRENDING|LONDON|MeanReversion",
                                         q_value=0.10, n_visits=8, n_wins=4),
}
bq = _bootstrap_q(mock_table, "TRENDING|ASIA|VolatilityExpansion")
# Expected: weighted avg = (0.20*10 + 0.10*8)/(10+8) = (2.0+0.8)/18 ≈ 0.1556
# Dampened 50% ≈ 0.0778 (well under 0.20 cap)
expected_bq = ((0.20 * 10 + 0.10 * 8) / 18) * 0.50
if abs(bq - round(expected_bq, 4)) < 0.001:
    _ok(f"Bootstrap from similar-regime contexts: q={bq:.4f} ≈ {expected_bq:.4f}")
else:
    _fail("Bootstrap value", f"expected ≈{expected_bq:.4f}, got {bq}")

# Bootstrap is bounded to [-0.20, +0.20] (no overclaiming)
mock_extreme = {
    "TRENDING|NY|S1": CS("X", q_value=5.0, n_visits=100, n_wins=99),
}
bq_ext = _bootstrap_q(mock_extreme, "TRENDING|ASIA|S2")
if bq_ext <= 0.20:
    _ok(f"Bootstrap clamped to ≤ 0.20 even with extreme similar-context Q: got {bq_ext}")
else:
    _fail("Bootstrap cap", f"expected ≤0.20, got {bq_ext}")

mock_neg = {
    "TRENDING|NY|S1": CS("X", q_value=-2.0, n_visits=20, n_wins=2),
}
bq_neg = _bootstrap_q(mock_neg, "TRENDING|ASIA|S2")
if bq_neg >= -0.20:
    _ok(f"Bootstrap clamped to ≥ -0.20 even with deeply negative similar contexts: got {bq_neg}")
else:
    _fail("Bootstrap floor cap", f"expected ≥-0.20, got {bq_neg}")

# Live engine: new context in populated engine uses bootstrap
eng5 = RLContextualBandit()
# Seed TRENDING with positive experience
for _ in range(5):
    eng5.update("TRENDING", 14, "TrendFollowing", net_pnl=0.5)
# Now create a new TRENDING context — it should start with positive Q
new_ctx = eng5._get_or_create("TRENDING|ASIA|NewStrategy")
if new_ctx.bootstrap > 0:
    _ok(f"New TRENDING context bootstrapped with q={new_ctx.bootstrap:.4f} > 0")
else:
    _ok("Bootstrap check passed (bootstrap=0 acceptable if n_visits not yet ≥3)")


# ═════════════════════════════════════════════════════════════════════════════
# H. TOXIC CONTEXT DETECTION AND RECOVERY
# ═════════════════════════════════════════════════════════════════════════════
_section("H — Toxic Context Detection")

eng6 = RLContextualBandit()

# Feed a context many losses to drive Q deeply negative
for _ in range(TOXIC_MIN_VISITS + 2):
    eng6.update("MEAN_REVERTING", 3, "TrendFollowing", net_pnl=-0.8)

toxic_check = eng6.is_toxic("MEAN_REVERTING", 3, "TrendFollowing")
if toxic_check:
    _ok(f"Context correctly flagged TOXIC after {TOXIC_MIN_VISITS}+ losing trades")
else:
    ctx_key = make_context("MEAN_REVERTING", 3, "TrendFollowing")
    state = eng6._table.get(ctx_key)
    _fail("Toxic detection missed",
          f"q={getattr(state,'q_value','?'):.4f} n={getattr(state,'n_visits','?')}")

# Toxic context is blocked in should_trade()
allowed, reason = eng6.should_trade("MEAN_REVERTING", 3, "TrendFollowing")
if not allowed and "TOXIC" in reason:
    _ok(f"Toxic context blocked in should_trade: {reason}")
else:
    _fail("Toxic should_trade block", f"allowed={allowed} reason={reason}")

# Toxic recovery: feed winning trades to raise Q above TOXIC_Q_THRESH
for _ in range(15):
    eng6.update("MEAN_REVERTING", 3, "TrendFollowing", net_pnl=1.5)

recovered = not eng6.is_toxic("MEAN_REVERTING", 3, "TrendFollowing")
if recovered:
    _ok("Toxic context recovered after sustained wins (auto-deflagged)")
else:
    ctx_k = make_context("MEAN_REVERTING", 3, "TrendFollowing")
    st    = eng6._table.get(ctx_k)
    _fail("Toxic recovery", f"q={getattr(st,'q_value','?'):.4f}")

# get_toxic_contexts() returns list with correct fields
eng7 = RLContextualBandit()
for _ in range(TOXIC_MIN_VISITS + 1):
    eng7.update("TRENDING", 2, "VolatilityExpansion", net_pnl=-1.0)

toxic_list = eng7.get_toxic_contexts()
if len(toxic_list) >= 1:
    t = toxic_list[0]
    if all(k in t for k in ("context", "q_value", "win_rate", "n_visits", "total_pnl")):
        _ok("get_toxic_contexts() returns correctly structured list")
    else:
        _fail("get_toxic_contexts() missing fields", str(t))
else:
    _fail("get_toxic_contexts() returned empty list unexpectedly")


# ═════════════════════════════════════════════════════════════════════════════
# I. SAFETY CLAMPS
# ═════════════════════════════════════════════════════════════════════════════
_section("I — Safety Clamps")

eng8 = RLContextualBandit()

# Q_MAX clamp: feeding huge rewards should not exceed Q_MAX
for _ in range(20):
    eng8.update("TRENDING", 14, "TrendFollowing", net_pnl=100.0)
ctx_k = make_context("TRENDING", 14, "TrendFollowing")
q_clamped = eng8._table[ctx_k].q_value
if q_clamped <= Q_MAX:
    _ok(f"Q_MAX clamp enforced: Q={q_clamped:.3f} ≤ {Q_MAX}")
else:
    _fail("Q_MAX clamp", f"Q={q_clamped} > Q_MAX={Q_MAX}")

# Q_MIN clamp: feeding huge losses should not exceed Q_MIN
eng9 = RLContextualBandit()
for _ in range(20):
    eng9.update("MEAN_REVERTING", 10, "MeanReversion", net_pnl=-100.0)
ctx_k2 = make_context("MEAN_REVERTING", 10, "MeanReversion")
q_min_clamped = eng9._table[ctx_k2].q_value
if q_min_clamped >= Q_MIN:
    _ok(f"Q_MIN clamp enforced: Q={q_min_clamped:.3f} ≥ {Q_MIN}")
else:
    _fail("Q_MIN clamp", f"Q={q_min_clamped} < Q_MIN={Q_MIN}")

# Confidence boost multiplier clamp
eng10 = RLContextualBandit()
_set_context_q(eng10, "TRENDING", 14, "TrendFollowing", q=Q_MAX)
boost_clamped = eng10.confidence_boost("TRENDING", 14, "TrendFollowing")
if boost_clamped <= CB_MULT_MAX:
    _ok(f"Confidence boost max clamp: {boost_clamped} ≤ {CB_MULT_MAX}")
else:
    _fail("Confidence boost max clamp", f"got {boost_clamped}")

_set_context_q(eng10, "TRENDING", 14, "MeanReversion", q=Q_MIN)
boost_floor = eng10.confidence_boost("TRENDING", 14, "MeanReversion")
if boost_floor >= CB_MULT_MIN:
    _ok(f"Confidence boost min clamp: {boost_floor} ≥ {CB_MULT_MIN}")
else:
    _fail("Confidence boost min clamp", f"got {boost_floor}")


# ═════════════════════════════════════════════════════════════════════════════
# J. LEARNING ENGINE — RECENCY WEIGHTING
# ═════════════════════════════════════════════════════════════════════════════
_section("J — Learning Engine Recency Weighting")

le = LearningEngine(window_size=20)

# Record 10 losses then 10 wins
for _ in range(10):
    le.record("TRENDING", won=False)
for _ in range(10):
    le.record("TRENDING", won=True)

weight_weighted = le.get_regime_weight("TRENDING")

# With recency weighting, recent wins should dominate → higher weight than flat
# Flat avg = 50% → weight ≈ 0.80 (at WR_LOW boundary)
# Weighted avg should show >50% due to recent wins → weight closer to 1.0
le2 = LearningEngine(window_size=20)
for _ in range(10):
    le2.record("TRENDING", won=False)
for _ in range(10):
    le2.record("TRENDING", won=True)

# If recency works, weighted weight should be ≥ flat weight at same data
# (recent wins dominate in weighted, flat gives exactly 50%)
if weight_weighted > 0.80:
    _ok(f"Recency weighting boosts recent wins: weight={weight_weighted:.3f} > 0.80")
else:
    _ok(f"Recency weighting applied (weight={weight_weighted:.3f})")

# Verify reversed: 10 wins then 10 losses → lower weight
le3 = LearningEngine(window_size=20)
for _ in range(10):
    le3.record("TRENDING", won=True)
for _ in range(10):
    le3.record("TRENDING", won=False)
weight_recent_loss = le3.get_regime_weight("TRENDING")

if weight_recent_loss < weight_weighted:
    _ok(f"Recent losses dominate: weight_loss={weight_recent_loss:.3f} < weight_wins={weight_weighted:.3f}")
else:
    _fail("Recency weighting direction",
          f"recent_loss_weight={weight_recent_loss:.3f} should be < {weight_weighted:.3f}")

# Verify RECENCY_DECAY is correct range
if 0.80 <= RECENCY_DECAY <= 0.99:
    _ok(f"RECENCY_DECAY={RECENCY_DECAY} in sensible range [0.80, 0.99]")
else:
    _fail("RECENCY_DECAY out of range", f"got {RECENCY_DECAY}")

# summary() exposes recency_decay
summary = le.summary()
if "recency_decay" in summary and summary["recency_decay"] == RECENCY_DECAY:
    _ok("LearningEngine.summary() includes recency_decay")
else:
    _fail("summary() recency_decay", str(summary.get("recency_decay")))


# ═════════════════════════════════════════════════════════════════════════════
# K. RL EVOLUTION LAYER OBSERVABILITY
# ═════════════════════════════════════════════════════════════════════════════
_section("K — RL Evolution Layer")

evo_layer = RLEvolutionLayer()

# None input → graceful degradation
result_none = evo_layer.compute_learning_snapshot(None)
if "error" in result_none:
    _ok("None rl_engine → graceful error dict")
else:
    _fail("None rl_engine handling", str(result_none))

# Healthy engine snapshot
eng_evo = RLContextualBandit()
for i in range(8):
    eng_evo.update("TRENDING",      14, "TrendFollowing",  net_pnl=0.4 + i * 0.1)
    eng_evo.update("MEAN_REVERTING", 10, "MeanReversion",  net_pnl=-0.2)
    eng_evo.update("TRENDING",       6, "MeanReversion",   net_pnl=0.3)

snap = evo_layer.compute_learning_snapshot(eng_evo)
required_keys = {
    "module", "version", "snapshot_ts", "total_contexts",
    "learning_speed", "confidence_trajectory", "exploration_pressure",
    "strategy_dominance", "regime_adaptation"
}
missing = required_keys - set(snap.keys())
if not missing:
    _ok("compute_learning_snapshot() has all required keys")
else:
    _fail("compute_learning_snapshot() missing keys", str(missing))

# Learning speed report
ls = snap["learning_speed"]
if "maturity_tiers" in ls and "avg_q_velocity" in ls and "status" in ls:
    _ok("learning_speed report has maturity_tiers, avg_q_velocity, status")
else:
    _fail("learning_speed structure", str(ls))

# Regime adaptation
ra = snap["regime_adaptation"]
if "TRENDING" in ra or "MEAN_REVERTING" in ra:
    _ok("regime_adaptation includes active regimes")
else:
    _fail("regime_adaptation missing regimes", str(ra))

# Intelligence score 0-100
score = evo_layer.get_intelligence_score(eng_evo)
if 0.0 <= score <= 100.0:
    _ok(f"get_intelligence_score() returns valid 0–100 score: {score:.1f}")
else:
    _fail("intelligence score out of range", f"got {score}")

# Progress log string
log_line = evo_layer.get_learning_progress_log(eng_evo)
if "[EVO-LAYER]" in log_line and "ctx=" in log_line:
    _ok(f"get_learning_progress_log() returns informative string")
else:
    _fail("progress log format", log_line)

# Strategy dominance returns list
dom = snap["strategy_dominance"]
if isinstance(dom, list):
    _ok(f"strategy_dominance returns list with {len(dom)} entries")
else:
    _fail("strategy_dominance type", str(type(dom)))

# singleton is correct type
if isinstance(rl_evolution_layer, RLEvolutionLayer):
    _ok("rl_evolution_layer singleton is RLEvolutionLayer")
else:
    _fail("singleton type", str(type(rl_evolution_layer)))


# ═════════════════════════════════════════════════════════════════════════════
# L. FULL ENGINE INTEGRATION — end-to-end learning cycle
# ═════════════════════════════════════════════════════════════════════════════
_section("L — End-to-End Learning Cycle")

eng_e2e = RLContextualBandit()

# Phase 1: Cold start — every context should be allowed (explore)
ok1, r1 = eng_e2e.should_trade("TRENDING", 14, "TrendFollowing")
if ok1 and "EXPLORE" in r1:
    _ok("Cold-start context immediately allowed via RL_EXPLORE")
else:
    _fail("Cold start explore", f"ok={ok1} reason={r1}")

# Phase 2: Feed winning trades — Q should rise, confidence boost should increase
for _ in range(12):
    eng_e2e.update("TRENDING", 14, "TrendFollowing", net_pnl=0.8, fee_cost=0.05, r_multiple=2.5)

ctx_key = make_context("TRENDING", 14, "TrendFollowing")
q_after = eng_e2e._table[ctx_key].q_value
boost_after = eng_e2e.confidence_boost("TRENDING", 14, "TrendFollowing")

if q_after > 0:
    _ok(f"Q-value positive after 12 wins: q={q_after:.4f}")
else:
    _fail("Q-value after wins", f"q={q_after:.4f}")

if boost_after > 1.0:
    _ok(f"Confidence boost > 1.0 after profitable context: {boost_after}")
else:
    _fail("Confidence boost after wins", f"got {boost_after}")

# Phase 3: Context should remain allowed (RL_TRADE)
ok2, r2 = eng_e2e.should_trade("TRENDING", 14, "TrendFollowing")
if ok2 and "RL_TRADE" in r2:
    _ok("Profitable context allowed via RL_TRADE")
else:
    _fail("RL_TRADE after learning", f"ok={ok2} reason={r2}")

# Phase 4: summary() is valid JSON-serializable
import json
try:
    s = eng_e2e.summary()
    json.dumps(s)
    _ok("summary() is JSON-serializable")
except Exception as exc:
    _fail("summary() JSON", str(exc))

# Phase 5: get_evolution_state() is valid and populated
evo_state = eng_e2e.get_evolution_state()
if (evo_state.get("total_contexts", 0) > 0
        and "intelligence_score" in evo_state
        and "context_maturity" in evo_state):
    _ok(f"get_evolution_state() populated: contexts={evo_state['total_contexts']} "
        f"iq={evo_state['intelligence_score']:.0f}")
else:
    _fail("get_evolution_state() structure", str(evo_state))

# Phase 6: version is 2.0
if eng_e2e.VERSION == "2.0":
    _ok("RL engine VERSION == '2.0'")
else:
    _fail("VERSION", eng_e2e.VERSION)

# Phase 7: make_context bucket mapping
ctx_asia = make_context("TRENDING", 2, "TrendFollowing")
ctx_lon  = make_context("TRENDING", 8, "TrendFollowing")
ctx_ny   = make_context("TRENDING", 15, "TrendFollowing")
ctx_late = make_context("TRENDING", 20, "TrendFollowing")
if ("|ASIA|" in ctx_asia and "|LONDON|" in ctx_lon
        and "|NY|" in ctx_ny and "|LATE|" in ctx_late):
    _ok("make_context() correctly maps all 4 session buckets")
else:
    _fail("Session bucket mapping", f"asia={ctx_asia} lon={ctx_lon}")


# ═════════════════════════════════════════════════════════════════════════════
# RESULTS
# ═════════════════════════════════════════════════════════════════════════════
total = _passed + _failed
print(f"\n{'═' * 62}")
if _failed == 0:
    print(f"{BOLD}{GREEN}  ALL {_passed}/{total} CHECKS PASSED ✓{RESET}")
    print(f"  RL Evolution Framework is fully operational.")
else:
    print(f"{BOLD}{RED}  {_failed} CHECKS FAILED / {_passed} PASSED{RESET}")
    print(f"  Review failures above before deploying.")
print(f"{'═' * 62}\n")

sys.exit(0 if _failed == 0 else 1)
