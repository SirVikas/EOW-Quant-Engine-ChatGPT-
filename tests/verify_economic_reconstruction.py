"""
FTD-PHOENIX-ESR-001 — Economic Survivability Reconstruction Verifier
=====================================================================
Validates that all 7 phases of the reconstruction program are correctly
implemented before deployment.

Run: python tests/verify_economic_reconstruction.py
All assertions must pass (exit code 0) before the build is deployable.
"""
import sys
import os
import time
import copy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import cfg

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"

_failures: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = PASS if condition else FAIL
    suffix = f"  ({detail})" if detail else ""
    print(f"  [{status}] {name}{suffix}")
    if not condition:
        _failures.append(f"{name}: {detail}")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1 — OOS Validation Hardening
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Phase 1: OOS Validation Hardening ──")

check(
    "GENOME_OOS_PASSTHROUGH_ENABLED is False (default)",
    cfg.GENOME_OOS_PASSTHROUGH_ENABLED is False,
    f"got {cfg.GENOME_OOS_PASSTHROUGH_ENABLED}",
)
check(
    "GENOME_OOS_MIN_TRADES >= 10",
    cfg.GENOME_OOS_MIN_TRADES >= 10,
    f"got {cfg.GENOME_OOS_MIN_TRADES}",
)

# Functional test: genome with insufficient candles must NOT promote
from core.genome_engine import GenomeEngine
from unittest.mock import patch, MagicMock

genome_test = GenomeEngine()

import asyncio

async def _test_oos_no_passthrough():
    from core.genome_engine import GenomeResult
    # Simulate a candidate that passes all gates EXCEPT has oos_valid=False
    candidate = GenomeResult(
        genome_id="test-oos",
        strategy_type="TrendFollowing",
        dna={},
        trades=10,
        win_rate=60.0,
        profit_factor=1.5,
        net_pnl=10.0,
        sharpe=1.0,
        avg_r_multiple=0.6,
        total_fees=1.0,
        cost_drag_pct=10.0,
        oos_pf=0.0,
        oos_win_rate=0.0,
        oos_trades=0,
        oos_valid=False,  # OOS failed — should be REJECTED
    )
    before_promotions = len([p for p in genome_test.promotion_log if p.decision == "PROMOTED"])
    await genome_test._maybe_promote("TrendFollowing", candidate)
    after_promotions = len([p for p in genome_test.promotion_log if p.decision == "PROMOTED"])
    return after_promotions == before_promotions  # no new promotion

oos_hardened = asyncio.run(_test_oos_no_passthrough())
check(
    "Insufficient OOS candidate is REJECTED (not promoted)",
    oos_hardened,
    "candidate with oos_valid=False must not be promoted",
)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 — Economic Truth Feedback Loop
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Phase 2: Economic Truth Feedback Loop ──")

genome_et = GenomeEngine()

check(
    "GenomeEngine has frozen_strategies dict",
    hasattr(genome_et, "frozen_strategies") and isinstance(genome_et.frozen_strategies, dict),
)
check(
    "GenomeEngine has et_feedback_log list",
    hasattr(genome_et, "et_feedback_log") and isinstance(genome_et.et_feedback_log, list),
)
check(
    "GenomeEngine has apply_economic_truth_feedback method",
    callable(getattr(genome_et, "apply_economic_truth_feedback", None)),
)
check(
    "GenomeEngine has unfreeze_strategy method",
    callable(getattr(genome_et, "unfreeze_strategy", None)),
)

# Functional test: high FDR triggers freeze
_toxic_decomp = {
    "TrendFollowing_PAPER_SPEED": {
        "count": 200,              # above GENOME_ET_FREEZE_MIN_TRADES=100
        "net_expectancy": -0.25,   # below GENOME_ET_NET_EXP_FREEZE_THRESHOLD=-0.15
        "fee_destruction_ratio": 75.0,  # above GENOME_ET_FDR_FREEZE_THRESHOLD=50.0
    }
}
feedback = genome_et.apply_economic_truth_feedback(_toxic_decomp)
check(
    "Toxic strategy triggers FREEZE event",
    len(feedback["events"]) == 1,
    f"events={feedback['events']}",
)
check(
    "TrendFollowing is in frozen_strategies after toxic feedback",
    "TrendFollowing" in genome_et.frozen_strategies,
    f"frozen={genome_et.frozen_strategies}",
)
check(
    "et_feedback_log has the freeze event",
    any(e.get("action") == "FREEZE" for e in genome_et.et_feedback_log),
)

# Test unfreeze
unfrozen = genome_et.unfreeze_strategy("TrendFollowing", operator="TEST")
check(
    "unfreeze_strategy returns True for a frozen strategy",
    unfrozen is True,
)
check(
    "TrendFollowing is no longer in frozen_strategies after unfreeze",
    "TrendFollowing" not in genome_et.frozen_strategies,
)

# Test insufficient trades does NOT trigger freeze
_small_decomp = {
    "TrendFollowing_PAPER_SPEED": {
        "count": 50,           # below GENOME_ET_FREEZE_MIN_TRADES=100
        "net_expectancy": -0.30,
        "fee_destruction_ratio": 200.0,
    }
}
genome_et2 = GenomeEngine()
feedback2 = genome_et2.apply_economic_truth_feedback(_small_decomp)
check(
    "Strategy with insufficient live trades is NOT frozen (evidence threshold not met)",
    "TrendFollowing" not in genome_et2.frozen_strategies,
    f"count=50 < GENOME_ET_FREEZE_MIN_TRADES={cfg.GENOME_ET_FREEZE_MIN_TRADES}",
)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3 / Phase 6 — Sub-1-Minute Eradication + Alpha Pocket Preservation
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Phase 3/6: Trade Duration Protection ──")

check(
    "TRADE_MIN_HOLD_FAST_FAIL_SEC is set in config",
    hasattr(cfg, "TRADE_MIN_HOLD_FAST_FAIL_SEC"),
    f"got {getattr(cfg, 'TRADE_MIN_HOLD_FAST_FAIL_SEC', 'MISSING')}",
)
check(
    "TRADE_MIN_HOLD_FAST_FAIL_SEC >= 60",
    cfg.TRADE_MIN_HOLD_FAST_FAIL_SEC >= 60,
    f"got {cfg.TRADE_MIN_HOLD_FAST_FAIL_SEC}",
)

# Functional test: FAST_FAIL must not fire at 30 seconds
from core.trade_manager import TradeManager, ManagedPosition

tm = TradeManager()
pos = ManagedPosition(
    symbol="BTCUSDT",
    side="LONG",
    qty=0.01,
    entry_price=50000.0,
    stop_loss=49750.0,   # initial_risk = 250
    take_profit=52500.0,
    initial_risk=250.0,
    exec_mode="TREND_FOLLOW",
)
pos.open_ts = time.time() - 30  # 30 seconds ago
tm.register(pos)

# Price dropped to trigger FAST_FAIL threshold (50000 - 0.35*250 = 49912.5 → below 49912)
action_30s = tm.update("BTCUSDT", 49870.0, 100.0)  # -0.52R
check(
    "FAST_FAIL does NOT fire at 30s elapsed (below _FAST_FAIL_MIN_ELAPSED=90s)",
    action_30s.action != "TIME_EXIT" or "Fast-fail" not in action_30s.reason,
    f"action={action_30s.action} reason={action_30s.reason}",
)

# Same setup at 120 seconds — FAST_FAIL SHOULD fire
tm2 = TradeManager()
pos2 = ManagedPosition(
    symbol="ETHUSDT",
    side="LONG",
    qty=0.1,
    entry_price=3000.0,
    stop_loss=2970.0,
    take_profit=3120.0,
    initial_risk=30.0,
    exec_mode="TREND_FOLLOW",
)
tm2.register(pos2)
pos2.open_ts = time.time() - 120  # override after register (register() resets open_ts to now)

# Price at -0.40R (2988 = 3000 - 0.40*30 = 2988)
action_120s = tm2.update("ETHUSDT", 2988.0, 15.0)
check(
    "FAST_FAIL DOES fire at 120s elapsed (above _FAST_FAIL_MIN_ELAPSED=90s) when r < -0.35",
    action_120s.action == "TIME_EXIT" and "Fast-fail" in action_120s.reason,
    f"action={action_120s.action} reason={action_120s.reason}",
)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 4 — Exploration Economics Review
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Phase 4: Exploration Economics Review ──")

check(
    "EXPLORE_MAX_COST_DRAG_PCT is set in config",
    hasattr(cfg, "EXPLORE_MAX_COST_DRAG_PCT"),
    f"got {getattr(cfg, 'EXPLORE_MAX_COST_DRAG_PCT', 'MISSING')}",
)
check(
    "EXPLORE_MAX_COST_DRAG_PCT <= 25 (meaningful ceiling)",
    cfg.EXPLORE_MAX_COST_DRAG_PCT <= 25.0,
    f"got {cfg.EXPLORE_MAX_COST_DRAG_PCT}",
)

from core.exploration_engine import ExplorationEngine

explore_eng = ExplorationEngine()
# Force the engine to an explore slot so the cost_drag gate is reached
explore_eng._signal_count = explore_eng._explore_period - 1
# Test: genome_cost_drag above threshold blocks exploration
result_blocked = explore_eng.should_explore(
    symbol="BTCUSDT",
    score=0.75,
    equity=1000.0,
    genome_cost_drag=cfg.EXPLORE_MAX_COST_DRAG_PCT + 10.0,
)
check(
    "Exploration blocked when genome_cost_drag exceeds EXPLORE_MAX_COST_DRAG_PCT",
    result_blocked.is_exploration is False and "FEE_TOXIC" in result_blocked.reason,
    f"is_exploration={result_blocked.is_exploration} reason={result_blocked.reason}",
)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 5 — Fee Destruction Governance (Promotion Gate 5)
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Phase 5: Fee Destruction Governance ──")

check(
    "GENOME_PROMOTE_MAX_COST_DRAG_PCT is set in config",
    hasattr(cfg, "GENOME_PROMOTE_MAX_COST_DRAG_PCT"),
    f"got {getattr(cfg, 'GENOME_PROMOTE_MAX_COST_DRAG_PCT', 'MISSING')}",
)
check(
    "GENOME_PROMOTE_MAX_COST_DRAG_PCT <= 50 (meaningful gate)",
    cfg.GENOME_PROMOTE_MAX_COST_DRAG_PCT <= 50.0,
    f"got {cfg.GENOME_PROMOTE_MAX_COST_DRAG_PCT}",
)

async def _test_fee_gate():
    from core.genome_engine import GenomeResult
    genome_fee = GenomeEngine()
    # Candidate that would pass all other gates but has extreme cost_drag
    candidate_fee_toxic = GenomeResult(
        genome_id="fee-toxic",
        strategy_type="TrendFollowing",
        dna={},
        trades=20,
        win_rate=60.0,
        profit_factor=1.5,
        net_pnl=10.0,
        sharpe=1.0,
        avg_r_multiple=0.6,
        total_fees=5.0,
        cost_drag_pct=80.0,  # 80% cost drag — far above Gate 5 limit of 30%
        oos_pf=1.2,
        oos_win_rate=55.0,
        oos_trades=8,
        oos_valid=True,
    )
    before = len([p for p in genome_fee.promotion_log if p.decision == "PROMOTED"])
    await genome_fee._maybe_promote("TrendFollowing", candidate_fee_toxic)
    after = len([p for p in genome_fee.promotion_log if p.decision == "PROMOTED"])
    rejected = [p for p in genome_fee.promotion_log if p.decision == "REJECTED"]
    has_fee_gate_reason = any(
        "fee_gate" in (p.reason or "") for p in rejected
    )
    return after == before, has_fee_gate_reason

promoted_ok, fee_gate_logged = asyncio.run(_test_fee_gate())
check(
    "Fee-toxic candidate is NOT promoted (Gate 5 blocks)",
    promoted_ok,
    "cost_drag=80% should fail Gate 5 (limit=30%)",
)
check(
    "Rejection reason includes 'fee_gate'",
    fee_gate_logged,
    "promotion_log.reason must reference fee_gate",
)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 7 — Observability (export_state includes ET governance)
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Phase 7: Observability / RCAF ──")

genome_obs = GenomeEngine()
state = genome_obs.export_state()

check(
    "export_state includes 'et_governance' block",
    "et_governance" in state,
    f"keys={list(state.keys())}",
)
et_gov = state.get("et_governance", {})
check(
    "et_governance.frozen_strategies present",
    "frozen_strategies" in et_gov,
)
check(
    "et_governance.oos_passthrough reflects config",
    et_gov.get("oos_passthrough") == cfg.GENOME_OOS_PASSTHROUGH_ENABLED,
    f"got {et_gov.get('oos_passthrough')} expected {cfg.GENOME_OOS_PASSTHROUGH_ENABLED}",
)
check(
    "et_governance.promote_max_cost_drag reflects config",
    et_gov.get("promote_max_cost_drag") == cfg.GENOME_PROMOTE_MAX_COST_DRAG_PCT,
)
check(
    "et_governance.et_feedback_log is a list",
    isinstance(et_gov.get("et_feedback_log"), list),
)


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "═" * 60)
if _failures:
    print(f"\n{FAIL}  {len(_failures)} assertion(s) failed:\n")
    for f in _failures:
        print(f"  • {f}")
    print()
    sys.exit(1)
else:
    total_checks = sum(
        1 for line in open(__file__).readlines() if line.strip().startswith("check(")
    )
    print(f"\n{PASS}  All checks passed — FTD-PHOENIX-ESR-001 verified.\n")
    sys.exit(0)
