"""
FTD-EXPLORE-FLOOR — Minimum Exploration Floor Unit Tests

Asserts:
  1.  Rule 4 constants exist with correct types and semantics.
  2.  EXPLORE_FLOOR_ENABLED defaults to True.
  3.  Rule 4 fires for immature, mildly-negative contexts (Q in the floor zone).
  4.  Rule 4 does NOT fire when EXPLORE_FLOOR_ENABLED is False.
  5.  Rule 4 does NOT fire when q <= EXPLORE_FLOOR_Q_THRESH (too negative).
  6.  Rule 4 does NOT fire when q >= 0 (positive Q — handled by Rule 3).
  7.  Rule 4 does NOT fire when n_visits >= EXPLORE_FLOOR_MAX_VISITS (mature).
  8.  Rule 1 still fires for ultra-fresh contexts (n < MIN_VISITS_EXPLORE).
  9.  Rule 2 still blocks toxic contexts before Rule 4 is evaluated.
  10. Rule 4 reason string contains RL_FLOOR_EXPLORE with q and n fields.
  11. floor_explores counter increments only on Rule 4 grants.
  12. explore_trades increments on both Rule 1 and Rule 4.
  13. get_evolution_state() exposes floor_explores in counters.
  14. get_evolution_state() exposes floor_explore_pct in learning_dynamics.
  15. get_evolution_state() exposes explore_floor_cfg with correct values.
  16. Rule 4 increments _total_allowed; blocked trade does not increment it.

Run: python -m pytest tests/test_exploration_floor.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import core.rl_engine as rl_mod
from core.rl_engine import (
    RLContextualBandit,
    EXPLORE_FLOOR_ENABLED,
    EXPLORE_FLOOR_MAX_VISITS,
    EXPLORE_FLOOR_Q_THRESH,
    MIN_VISITS_EXPLORE,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _fresh_engine() -> RLContextualBandit:
    """Construct engine without invoking load_state() or __init__ I/O."""
    eng = RLContextualBandit.__new__(RLContextualBandit)
    import time, pathlib
    eng._table           = {}
    eng._toxic_contexts  = set()
    eng._total_pulls     = 0
    eng._total_updates   = 0
    eng._total_blocked   = 0
    eng._total_allowed   = 0
    eng._explore_trades  = 0
    eng._exploit_trades  = 0
    eng._boost_fires     = 0
    eng._floor_lowers    = 0
    eng._floor_raises    = 0
    eng._toxic_blocks    = 0
    eng._floor_explores  = 0
    eng._init_ts         = time.time()
    eng._state_path      = pathlib.Path("/tmp/_test_rl_qtable.json")
    return eng


def _seed_context(
    eng: RLContextualBandit,
    *,
    regime: str    = "UNKNOWN",
    utc_hour: int  = 13,
    strategy: str  = "TEST_STRAT",
    n_visits: int  = 10,
    q_value: float = -0.10,
) -> str:
    from core.time.session_definitions import make_context
    from core.rl_engine import ContextState
    key   = make_context(regime, utc_hour, strategy)
    state = ContextState(context=key, q_value=q_value, n_visits=n_visits)
    state.n_wins = max(0, int(n_visits * 0.5))
    eng._table[key] = state
    return key


# ── 1–2. Constants ────────────────────────────────────────────────────────────

def test_explore_floor_enabled_constant_exists():
    assert hasattr(rl_mod, "EXPLORE_FLOOR_ENABLED")


def test_explore_floor_max_visits_constant_exists():
    assert hasattr(rl_mod, "EXPLORE_FLOOR_MAX_VISITS")


def test_explore_floor_q_thresh_constant_exists():
    assert hasattr(rl_mod, "EXPLORE_FLOOR_Q_THRESH")


def test_explore_floor_enabled_default_true():
    assert EXPLORE_FLOOR_ENABLED is True


def test_explore_floor_max_visits_is_int():
    assert isinstance(EXPLORE_FLOOR_MAX_VISITS, int)


def test_explore_floor_q_thresh_is_float():
    assert isinstance(EXPLORE_FLOOR_Q_THRESH, float)


def test_explore_floor_q_thresh_is_negative():
    # Lower bound of the mildly-negative zone must itself be negative
    assert EXPLORE_FLOOR_Q_THRESH < 0


def test_explore_floor_max_visits_above_min_visits():
    # Must cover contexts that have passed the Rule 1 guarantee
    assert EXPLORE_FLOOR_MAX_VISITS > MIN_VISITS_EXPLORE


# ── 3. Rule 4 fires under correct conditions ─────────────────────────────────
# Mildly-negative zone: EXPLORE_FLOOR_Q_THRESH < q < 0  (e.g. -0.15 < q < 0)

def test_rule4_fires_for_immature_mildly_negative_context():
    eng = _fresh_engine()
    _seed_context(eng, n_visits=10, q_value=-0.10)  # q in (-0.15, 0) ✓
    ok, reason = eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert ok is True
    assert "RL_FLOOR_EXPLORE" in reason


def test_rule4_reason_contains_q_and_n():
    eng = _fresh_engine()
    _seed_context(eng, n_visits=8, q_value=-0.10)
    _, reason = eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert "q=" in reason
    assert "n=" in reason


def test_rule4_fires_at_q_just_above_thresh():
    eng = _fresh_engine()
    q = EXPLORE_FLOOR_Q_THRESH + 0.001   # barely inside the mildly-negative zone
    _seed_context(eng, n_visits=5, q_value=q)
    ok, reason = eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert ok is True
    assert "RL_FLOOR_EXPLORE" in reason


def test_rule4_fires_at_n_just_below_max_visits():
    eng = _fresh_engine()
    _seed_context(eng, n_visits=EXPLORE_FLOOR_MAX_VISITS - 1, q_value=-0.10)
    ok, reason = eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert ok is True
    assert "RL_FLOOR_EXPLORE" in reason


def test_rule4_fires_for_very_small_negative_q():
    eng = _fresh_engine()
    _seed_context(eng, n_visits=10, q_value=-0.01)  # barely negative, inside zone
    ok, reason = eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert ok is True
    assert "RL_FLOOR_EXPLORE" in reason


# ── 4. Rule 4 disabled when flag is False ────────────────────────────────────

def test_rule4_does_not_fire_when_disabled(monkeypatch):
    monkeypatch.setattr(rl_mod, "EXPLORE_FLOOR_ENABLED", False)
    eng = _fresh_engine()
    _seed_context(eng, n_visits=10, q_value=-0.10)
    ok, reason = eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert "RL_FLOOR_EXPLORE" not in reason
    # Context still passes (UCB allows q > floor), just not tagged as floor_explore
    assert ok is True
    assert "RL_TRADE" in reason


# ── 5. Rule 4 does NOT fire when q at or below EXPLORE_FLOOR_Q_THRESH ────────

def test_rule4_does_not_fire_when_q_exactly_at_thresh():
    # Boundary: q == Q_THRESH is NOT in the open zone (Q_THRESH, 0)
    eng = _fresh_engine()
    _seed_context(eng, n_visits=10, q_value=EXPLORE_FLOOR_Q_THRESH)
    _, reason = eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert "RL_FLOOR_EXPLORE" not in reason


def test_rule4_does_not_fire_when_q_below_thresh():
    eng = _fresh_engine()
    _seed_context(eng, n_visits=10, q_value=-0.25)  # below Q_THRESH (-0.15)
    _, reason = eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert "RL_FLOOR_EXPLORE" not in reason


# ── 6. Rule 4 does NOT fire when q >= 0 (positive or zero Q) ─────────────────

def test_rule4_does_not_fire_for_positive_q():
    eng = _fresh_engine()
    _seed_context(eng, n_visits=10, q_value=0.50)
    _, reason = eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert "RL_FLOOR_EXPLORE" not in reason
    assert "RL_TRADE" in reason


def test_rule4_does_not_fire_for_zero_q():
    eng = _fresh_engine()
    _seed_context(eng, n_visits=10, q_value=0.0)
    _, reason = eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert "RL_FLOOR_EXPLORE" not in reason


# ── 7. Rule 4 does NOT fire for mature contexts ───────────────────────────────

def test_rule4_does_not_fire_when_n_equals_max_visits():
    eng = _fresh_engine()
    # n == MAX_VISITS: boundary, not < MAX → Rule 4 fails, falls through to Rule 3
    _seed_context(eng, n_visits=EXPLORE_FLOOR_MAX_VISITS, q_value=-0.10)
    _, reason = eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert "RL_FLOOR_EXPLORE" not in reason


def test_rule4_does_not_fire_for_well_visited_context():
    eng = _fresh_engine()
    _seed_context(eng, n_visits=50, q_value=-0.10)
    _, reason = eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert "RL_FLOOR_EXPLORE" not in reason


# ── 8. Rule 1 still fires for ultra-fresh contexts ───────────────────────────

def test_rule1_still_fires_before_rule4():
    eng = _fresh_engine()
    # n < MIN_VISITS_EXPLORE → Rule 1 fires regardless of Q
    _seed_context(eng, n_visits=1, q_value=-0.10)
    ok, reason = eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert ok is True
    assert "RL_EXPLORE" in reason


def test_rule1_fires_for_brand_new_context():
    eng = _fresh_engine()  # no context seeded → n=0 → Rule 1
    ok, reason = eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert ok is True
    assert "RL_EXPLORE" in reason


# ── 9. Rule 2 still blocks toxic contexts ────────────────────────────────────

def test_rule2_blocks_toxic_before_rule4():
    eng = _fresh_engine()
    key = _seed_context(eng, n_visits=12, q_value=-0.10)  # in floor zone
    eng._toxic_contexts.add(key)
    ok, reason = eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert ok is False
    assert "RL_TOXIC" in reason


# ── 10. Reason string format ──────────────────────────────────────────────────

def test_rule4_reason_starts_with_correct_prefix():
    eng = _fresh_engine()
    _seed_context(eng, n_visits=10, q_value=-0.10)
    _, reason = eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert reason.startswith("RL_FLOOR_EXPLORE")


def test_rule4_reason_contains_max_visits():
    eng = _fresh_engine()
    _seed_context(eng, n_visits=10, q_value=-0.10)
    _, reason = eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert str(EXPLORE_FLOOR_MAX_VISITS) in reason


# ── 11. floor_explores counter ───────────────────────────────────────────────

def test_floor_explores_counter_zero_at_init():
    eng = _fresh_engine()
    assert eng._floor_explores == 0


def test_floor_explores_increments_on_rule4():
    eng = _fresh_engine()
    _seed_context(eng, n_visits=10, q_value=-0.10)
    eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert eng._floor_explores == 1


def test_floor_explores_does_not_increment_on_rule1():
    eng = _fresh_engine()
    _seed_context(eng, n_visits=1, q_value=-0.10)
    eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert eng._floor_explores == 0


def test_floor_explores_does_not_increment_on_rule3():
    eng = _fresh_engine()
    # Positive Q → UCB gate allows via Rule 3 (not Rule 4)
    _seed_context(eng, n_visits=10, q_value=1.50)
    eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert eng._floor_explores == 0


def test_floor_explores_does_not_increment_on_block():
    eng = _fresh_engine()
    # q below zone → doesn't trigger Rule 4; with large n, Rule 3 blocks
    _seed_context(eng, n_visits=50, q_value=-0.50)
    eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert eng._floor_explores == 0


def test_floor_explores_cumulative():
    eng = _fresh_engine()
    _seed_context(eng, n_visits=10, q_value=-0.10)
    for _ in range(5):
        eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert eng._floor_explores == 5


# ── 12. explore_trades increments on both Rule 1 and Rule 4 ──────────────────

def test_explore_trades_increments_on_rule4():
    eng = _fresh_engine()
    _seed_context(eng, n_visits=10, q_value=-0.10)
    before = eng._explore_trades
    eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert eng._explore_trades == before + 1


def test_explore_trades_increments_on_rule1():
    eng = _fresh_engine()
    _seed_context(eng, n_visits=1, q_value=-0.10)
    before = eng._explore_trades
    eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert eng._explore_trades == before + 1


def test_explore_trades_does_not_increment_on_rule3():
    eng = _fresh_engine()
    _seed_context(eng, n_visits=10, q_value=0.50)  # positive Q → Rule 3
    before = eng._explore_trades
    eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert eng._explore_trades == before


# ── 13–15. get_evolution_state() observability ───────────────────────────────

def test_evolution_state_has_floor_explores_in_counters():
    eng = _fresh_engine()
    _seed_context(eng, n_visits=10, q_value=-0.10)
    eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    state = eng.get_evolution_state()
    assert "floor_explores" in state["counters"]
    assert state["counters"]["floor_explores"] == 1


def test_evolution_state_floor_explores_zero_after_rule3():
    eng = _fresh_engine()
    _seed_context(eng, n_visits=10, q_value=0.50)
    eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    state = eng.get_evolution_state()
    assert state["counters"]["floor_explores"] == 0


def test_evolution_state_has_floor_explore_pct_in_learning_dynamics():
    eng = _fresh_engine()
    _seed_context(eng, n_visits=10, q_value=-0.10)
    eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    state = eng.get_evolution_state()
    assert "floor_explore_pct" in state["learning_dynamics"]
    assert isinstance(state["learning_dynamics"]["floor_explore_pct"], float)


def test_evolution_state_floor_explore_pct_nonzero_after_rule4():
    eng = _fresh_engine()
    _seed_context(eng, n_visits=10, q_value=-0.10)
    eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    state = eng.get_evolution_state()
    assert state["learning_dynamics"]["floor_explore_pct"] > 0


def test_evolution_state_has_explore_floor_cfg():
    eng = _fresh_engine()
    _seed_context(eng, n_visits=10, q_value=-0.10)
    state = eng.get_evolution_state()
    cfg = state["learning_dynamics"]["explore_floor_cfg"]
    assert "enabled"    in cfg
    assert "max_visits" in cfg
    assert "q_thresh"   in cfg


def test_evolution_state_explore_floor_cfg_values_match_constants():
    eng = _fresh_engine()
    _seed_context(eng, n_visits=10, q_value=-0.10)
    state = eng.get_evolution_state()
    cfg = state["learning_dynamics"]["explore_floor_cfg"]
    assert cfg["enabled"]    == EXPLORE_FLOOR_ENABLED
    assert cfg["max_visits"] == EXPLORE_FLOOR_MAX_VISITS
    assert cfg["q_thresh"]   == EXPLORE_FLOOR_Q_THRESH


# ── 16. _total_allowed and _total_blocked correctness ────────────────────────

def test_total_allowed_increments_on_rule4():
    eng = _fresh_engine()
    _seed_context(eng, n_visits=10, q_value=-0.10)
    before = eng._total_allowed
    ok, _ = eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert ok is True
    assert eng._total_allowed == before + 1


def test_total_blocked_does_not_increment_on_rule4():
    eng = _fresh_engine()
    _seed_context(eng, n_visits=10, q_value=-0.10)
    before = eng._total_blocked
    eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert eng._total_blocked == before


def test_total_blocked_increments_on_skip():
    eng = _fresh_engine()
    # Large n, deeply negative q → Rule 3 blocks
    _seed_context(eng, n_visits=50, q_value=-0.50)
    before_blocked = eng._total_blocked
    ok, reason = eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert ok is False
    assert "RL_SKIP" in reason
    assert eng._total_blocked == before_blocked + 1


def test_explore_trades_and_exploit_trades_are_disjoint():
    eng = _fresh_engine()
    _seed_context(eng, n_visits=10, q_value=-0.10)  # → floor explore
    eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert eng._explore_trades == 1
    assert eng._exploit_trades == 0
