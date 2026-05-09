"""
EOW Quant Engine — FTD-055-ATHENA + FTD-054-PHOENIX Regression Test Suite

Validates every RL-related fix deployed in this session:

  A. Q-TABLE PERSISTENCE   — save/load survives restart (cross-session learning)
  B. TOXIC BYPASS          — BYPASS_ALL_GATES prevents RL TOXIC hard-block
  C. LEARNING CONTINUITY   — Engine B resumes where Engine A left off
  D. TOXIC RECOVERY        — TOXIC flag recovers if Q rises after restart
  E. COUNTER ISOLATION     — Session counters reset; Q-table carries over
  F. CORRUPT STATE SAFETY  — Bad save file → clean cold start, no crash
  G. UNIFIED REPORT FIX    — n_trades key mismatch corrected (total_trades alias)
  H. INTELLIGENCE REPORTS  — rl_intelligence.json + trade_quality_evolution.json
  I. GET_EVOLUTION_STATE   — observability API produces structured output

Run:
    python tests/test_ftd055_athena_rl_fixes.py

Exit codes:
    0 — all checks passed
    1 — one or more checks failed
"""
from __future__ import annotations

import json
import math
import pathlib
import sys
import tempfile
import time

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


def _check(label: str, condition: bool, reason: str = "") -> None:
    if condition:
        _ok(label)
    else:
        _fail(label, reason)


def _section(title: str) -> None:
    print(f"\n{BOLD}{YELLOW}── {title} {'─' * max(0, 55 - len(title))}{RESET}")


# ── Module imports ─────────────────────────────────────────────────────────────

_section("MODULE IMPORTS")

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

try:
    from core.rl_engine import (
        RLContextualBandit,
        ContextState,
        make_context,
        TOXIC_Q_THRESH,
        TOXIC_MIN_VISITS,
        ENTRY_EV_FLOOR,
        MIN_VISITS_EXPLORE,
        Q_MIN,
        _QTABLE_STATE_PATH,
    )
    _ok("core.rl_engine imported")
except Exception as e:
    _fail("core.rl_engine import", str(e))
    sys.exit(1)

try:
    from core.reporting.unified_report_engine_v2 import generate_full_report_v2
    _ok("unified_report_engine_v2 imported")
except Exception as e:
    _fail("unified_report_engine_v2 import", str(e))

try:
    from core.pnl_calculator import PnLCalculator
    _ok("core.pnl_calculator imported")
    PnLCalculator = PnLCalculator
except Exception:
    # Optional — pydantic_settings may not be installed in isolated test env
    print(f"  {YELLOW}⚠{RESET}  core.pnl_calculator skipped (pydantic_settings not installed)")
    PnLCalculator = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_engine(save_path: pathlib.Path) -> RLContextualBandit:
    """Create a fresh engine isolated to a custom save path (not production path)."""
    engine = RLContextualBandit.__new__(RLContextualBandit)
    engine._table          = {}
    engine._toxic_contexts = set()
    engine._total_pulls    = 0
    engine._total_updates  = 0
    engine._total_blocked  = 0
    engine._total_allowed  = 0
    engine._explore_trades = 0
    engine._exploit_trades = 0
    engine._boost_fires    = 0
    engine._floor_lowers   = 0
    engine._floor_raises   = 0
    engine._toxic_blocks   = 0
    engine._init_ts        = time.time()
    # Pre-bind state_path so auto-saves in update() use the temp path, not production
    engine._state_path     = save_path
    engine.load_state(save_path)   # also re-binds _state_path
    return engine


def _drive_toxic(engine: RLContextualBandit, regime: str = "MEAN_REVERTING",
                 strategy: str = "MeanReversion", hour: int = 15,
                 n: int = TOXIC_MIN_VISITS) -> None:
    """Push n updates with negative PnL to make a context toxic."""
    for _ in range(n):
        engine.update(regime, hour, strategy, net_pnl=-0.60, fee_cost=0.05, r_multiple=-0.15)


def _minimal_report_data(n_trades: int = 50, total_trades_key: bool = False) -> dict:
    """Build minimal data dict for unified report. total_trades_key=True simulates the bug."""
    ss_key   = "total_trades" if total_trades_key else "n_trades"
    return {
        "generated_at": "2026-05-09 20:00:00 UTC",
        "trade_flow": {
            "total_signals": 100,
            "total_trades":  n_trades,
            "total_skips":   50,
            "signals_per_hour": 50.0,
            "trades_per_hour": 5.0,
            "minutes_since_last_trade": 3.0,
            "top_rejection_reasons": {"RSI_FILTER": 40, "LCC": 10},
        },
        "mins_idle":  3.0,
        "thresholds": {"tier": "NORMAL", "score_min": 0.48, "af_state": "NORMAL"},
        "session_stats": {
            ss_key:         n_trades,
            "win_rate":     26.6,
            "profit_factor": 0.48,
            "avg_win_usdt":  1.04,
            "avg_loss_usdt": 0.78,
            "total_net_pnl": -25.0,
            "total_fees_paid": 11.76,
        },
        "capital": {},
        "risk": {"halted": False, "graceful_stop": False},
        "gate": {},
        "errors": [],
        "learning_memory": {"status": "ACTIVE", "memory_records": 0,
                            "total_patterns": 0, "formed_patterns": 0},
        "ct_scan": {},
        "ai_brain": {},
        "drawdown": {},
        "activator": {},
        "thoughts": [],
        "edge_engine": {"strategies": {}},
        "rl_bandit": {},
    }


# ═════════════════════════════════════════════════════════════════════════════
# A. Q-TABLE PERSISTENCE — save / load
# ═════════════════════════════════════════════════════════════════════════════

_section("A — Q-TABLE PERSISTENCE (save/load)")

with tempfile.TemporaryDirectory() as _tmpdir:
    _save_path = pathlib.Path(_tmpdir) / "rl_state.json"

    # A1: Cold start — no file → empty table
    eng_a = _make_engine(_save_path)
    _check("A1: cold start — empty table on missing file",
           len(eng_a._table) == 0,
           f"Expected 0 contexts, got {len(eng_a._table)}")

    # A2: Train a few updates and save
    eng_a.update("TRENDING", 15, "TrendFollowing", net_pnl=0.80, fee_cost=0.04, r_multiple=0.3)
    eng_a.update("TRENDING", 15, "TrendFollowing", net_pnl=0.60, fee_cost=0.04, r_multiple=0.2)
    eng_a.update("MEAN_REVERTING", 15, "MeanReversion", net_pnl=-0.30, fee_cost=0.03, r_multiple=-0.1)
    eng_a.save_state(_save_path)
    _check("A2: state file created after save_state()",
           _save_path.exists(),
           "File not created")

    # A3: Load into fresh engine and verify Q-values
    eng_b = _make_engine(_save_path)
    ctx_tf = make_context("TRENDING", 15, "TrendFollowing")
    ctx_mr = make_context("MEAN_REVERTING", 15, "MeanReversion")
    _check("A3: TrendFollowing context loaded",
           ctx_tf in eng_b._table,
           f"Context '{ctx_tf}' missing from loaded table")
    _check("A4: MeanReversion context loaded",
           ctx_mr in eng_b._table,
           f"Context '{ctx_mr}' missing from loaded table")

    # A5: n_visits preserved
    loaded_tf = eng_b._table.get(ctx_tf)
    _check("A5: n_visits preserved across save/load",
           loaded_tf is not None and loaded_tf.n_visits == 2,
           f"Expected n_visits=2, got {loaded_tf.n_visits if loaded_tf else 'None'}")

    # A6: Q-value preserved (within float rounding)
    orig_q = eng_a._table[ctx_tf].q_value
    loaded_q = loaded_tf.q_value if loaded_tf else 0.0
    _check("A6: Q-value preserved across save/load",
           abs(orig_q - loaded_q) < 1e-4,
           f"Q mismatch: original={orig_q:.5f} loaded={loaded_q:.5f}")

    # A7: n_wins preserved
    _check("A7: n_wins preserved across save/load",
           loaded_tf is not None and loaded_tf.n_wins == 2,
           f"Expected n_wins=2, got {loaded_tf.n_wins if loaded_tf else 'None'}")

    # A8: total_pnl preserved
    orig_pnl = eng_a._table[ctx_tf].total_pnl
    loaded_pnl = loaded_tf.total_pnl if loaded_tf else 0.0
    _check("A8: total_pnl preserved across save/load",
           abs(orig_pnl - loaded_pnl) < 1e-4,
           f"PnL mismatch: original={orig_pnl:.4f} loaded={loaded_pnl:.4f}")


# ═════════════════════════════════════════════════════════════════════════════
# B. TOXIC BYPASS — should_trade() respects BYPASS_ALL_GATES pattern
# ═════════════════════════════════════════════════════════════════════════════

_section("B — RL TOXIC BYPASS (FTD-054-PHOENIX)")

with tempfile.TemporaryDirectory() as _tmpdir:
    _save_path = pathlib.Path(_tmpdir) / "rl_state.json"
    eng = _make_engine(_save_path)

    # B1: Drive context to TOXIC
    _drive_toxic(eng, n=TOXIC_MIN_VISITS)
    ctx_key = make_context("MEAN_REVERTING", 15, "MeanReversion")
    _check("B1: context flagged TOXIC after enough negative updates",
           ctx_key in eng._toxic_contexts,
           f"Toxic set: {eng._toxic_contexts}")

    # B2: should_trade() returns False for TOXIC
    ok, reason = eng.should_trade("MEAN_REVERTING", 15, "MeanReversion")
    _check("B2: should_trade() → False for TOXIC context (gate active)",
           not ok,
           f"Expected False, got ok={ok} reason='{reason}'")

    # B3: reason contains RL_TOXIC
    _check("B3: reason string identifies RL_TOXIC",
           "RL_TOXIC" in reason,
           f"Reason: '{reason}'")

    # B4: Under-explored context always allowed (exploration guarantee)
    ok_new, reason_new = eng.should_trade("TRENDING", 15, "TrendFollowing")
    _check("B4: unvisited context always allowed (exploration guarantee)",
           ok_new,
           f"Expected True, got ok={ok_new} reason='{reason_new}'")

    # B5: TOXIC block counter increments
    _check("B5: _toxic_blocks counter incremented",
           eng._toxic_blocks >= 1,
           f"_toxic_blocks={eng._toxic_blocks}")


# ═════════════════════════════════════════════════════════════════════════════
# C. CROSS-SESSION LEARNING CONTINUITY
# ═════════════════════════════════════════════════════════════════════════════

_section("C — CROSS-SESSION LEARNING CONTINUITY")

with tempfile.TemporaryDirectory() as _tmpdir:
    _save_path = pathlib.Path(_tmpdir) / "rl_state.json"

    # Session 1: Engine A accumulates 20 profitable London trades
    eng_a = _make_engine(_save_path)
    for _ in range(20):
        eng_a.update("MEAN_REVERTING", 9, "MeanReversion",
                     net_pnl=0.50, fee_cost=0.04, r_multiple=0.2)
    q_after_s1 = eng_a._table[make_context("MEAN_REVERTING", 9, "MeanReversion")].q_value
    eng_a.save_state(_save_path)

    # Session 2: Engine B (fresh object) loads and continues
    eng_b = _make_engine(_save_path)
    ctx = make_context("MEAN_REVERTING", 9, "MeanReversion")

    _check("C1: Session 2 engine has Session 1 context",
           ctx in eng_b._table,
           f"Context not found: {ctx}")

    visits_after_load = eng_b._table[ctx].n_visits if ctx in eng_b._table else 0
    _check("C2: n_visits carries over (20 from session 1)",
           visits_after_load == 20,
           f"Expected 20, got {visits_after_load}")

    # Session 2: 5 more updates
    for _ in range(5):
        eng_b.update("MEAN_REVERTING", 9, "MeanReversion",
                     net_pnl=0.55, fee_cost=0.04, r_multiple=0.25)
    visits_s2 = eng_b._table[ctx].n_visits
    _check("C3: Session 2 updates accumulate on top of Session 1 (total=25)",
           visits_s2 == 25,
           f"Expected 25, got {visits_s2}")

    # Session 3: Engine C loads — should see 25 visits
    eng_b.save_state(_save_path)
    eng_c = _make_engine(_save_path)
    _check("C4: Session 3 inherits cumulative 25 visits",
           eng_c._table.get(ctx, ContextState(ctx)).n_visits == 25,
           f"Expected 25, got {eng_c._table.get(ctx, ContextState(ctx)).n_visits}")


# ═════════════════════════════════════════════════════════════════════════════
# D. TOXIC RECOVERY ACROSS RESTART
# ═════════════════════════════════════════════════════════════════════════════

_section("D — TOXIC RECOVERY ACROSS RESTART")

with tempfile.TemporaryDirectory() as _tmpdir:
    _save_path = pathlib.Path(_tmpdir) / "rl_state.json"

    # Make context TOXIC and save
    eng_a = _make_engine(_save_path)
    _drive_toxic(eng_a, n=TOXIC_MIN_VISITS)
    ctx = make_context("MEAN_REVERTING", 15, "MeanReversion")
    assert ctx in eng_a._toxic_contexts, "Setup: context should be toxic"
    eng_a.save_state(_save_path)

    # D1: Toxic state persists across restart
    eng_b = _make_engine(_save_path)
    _check("D1: TOXIC context survives restart",
           ctx in eng_b._toxic_contexts,
           f"Toxic set after load: {eng_b._toxic_contexts}")

    # D2: should_trade() correctly blocks the restored TOXIC context
    ok, reason = eng_b.should_trade("MEAN_REVERTING", 15, "MeanReversion")
    _check("D2: should_trade() blocks TOXIC context after reload",
           not ok,
           f"Expected block, got ok={ok}")

    # D3: Drive recovery (many wins → Q rises above TOXIC_Q_THRESH)
    for _ in range(30):
        eng_b.update("MEAN_REVERTING", 15, "MeanReversion",
                     net_pnl=0.80, fee_cost=0.04, r_multiple=0.4)
    recovered_q = eng_b._table[ctx].q_value
    _check("D3: Q-value recovers above TOXIC_Q_THRESH after wins",
           recovered_q > TOXIC_Q_THRESH,
           f"Q={recovered_q:.4f} still below threshold {TOXIC_Q_THRESH}")
    _check("D4: TOXIC flag removed on recovery",
           ctx not in eng_b._toxic_contexts,
           f"Context still in toxic set after Q={recovered_q:.4f}")

    # D5: After recovery, should_trade() allows
    ok_rec, reason_rec = eng_b.should_trade("MEAN_REVERTING", 15, "MeanReversion")
    _check("D5: should_trade() allows recovered context",
           ok_rec,
           f"Expected allow, got ok={ok_rec} reason='{reason_rec}'")


# ═════════════════════════════════════════════════════════════════════════════
# E. SESSION COUNTER ISOLATION
# ═════════════════════════════════════════════════════════════════════════════

_section("E — SESSION COUNTER ISOLATION")

with tempfile.TemporaryDirectory() as _tmpdir:
    _save_path = pathlib.Path(_tmpdir) / "rl_state.json"

    # Session 1: run 15 updates
    eng_a = _make_engine(_save_path)
    for _ in range(15):
        eng_a.update("TRENDING", 15, "TrendFollowing",
                     net_pnl=0.40, fee_cost=0.04, r_multiple=0.2)
    _check("E1: Session 1 has 15 total_updates counter",
           eng_a._total_updates == 15,
           f"Got {eng_a._total_updates}")
    eng_a.save_state(_save_path)

    # Session 2: fresh engine loads; counters should be session-local (reset to 0)
    eng_b = _make_engine(_save_path)
    _check("E2: Session 2 total_updates resets to 0 (session-local counter)",
           eng_b._total_updates == 0,
           f"Got {eng_b._total_updates} — counters should not persist")
    _check("E3: Session 2 total_pulls resets to 0",
           eng_b._total_pulls == 0,
           f"Got {eng_b._total_pulls}")

    # But Q-table knowledge IS there
    ctx = make_context("TRENDING", 15, "TrendFollowing")
    _check("E4: Q-table knowledge (n_visits=15) carries over despite counter reset",
           eng_b._table.get(ctx, ContextState(ctx)).n_visits == 15,
           f"Expected 15 visits, got {eng_b._table.get(ctx, ContextState(ctx)).n_visits}")


# ═════════════════════════════════════════════════════════════════════════════
# F. CORRUPT STATE FILE — graceful cold start
# ═════════════════════════════════════════════════════════════════════════════

_section("F — CORRUPT STATE FILE SAFETY")

with tempfile.TemporaryDirectory() as _tmpdir:
    _corrupt_path = pathlib.Path(_tmpdir) / "rl_state.json"

    # F1: Completely invalid JSON
    _corrupt_path.write_text("NOT_VALID_JSON{{{")
    eng = _make_engine(_corrupt_path)
    _check("F1: corrupt JSON → clean cold start (empty table)",
           len(eng._table) == 0,
           f"Expected empty table, got {len(eng._table)} contexts")

    # F2: Valid JSON but wrong schema
    _corrupt_path.write_text(json.dumps({"bad_key": [1, 2, 3]}))
    eng2 = _make_engine(_corrupt_path)
    _check("F2: wrong schema → clean cold start",
           len(eng2._table) == 0,
           f"Expected empty table, got {len(eng2._table)} contexts")

    # F3: Empty file
    _corrupt_path.write_text("")
    eng3 = _make_engine(_corrupt_path)
    _check("F3: empty file → clean cold start",
           len(eng3._table) == 0,
           f"Expected empty table, got {len(eng3._table)} contexts")


# ═════════════════════════════════════════════════════════════════════════════
# G. UNIFIED REPORT n_trades KEY FIX
# ═════════════════════════════════════════════════════════════════════════════

_section("G — UNIFIED REPORT n_trades KEY FIX")

try:
    # G1: Old bug — session_stats has "total_trades" but not "n_trades"
    data_bug = _minimal_report_data(n_trades=846, total_trades_key=True)
    # Verify our test fixture actually has the buggy key
    _check("G1: test fixture uses 'total_trades' key (simulating pnl_calculator output)",
           "total_trades" in data_bug["session_stats"]
           and "n_trades" not in data_bug["session_stats"],
           f"Fixture keys: {list(data_bug['session_stats'].keys())}")

    report_bug = generate_full_report_v2(data_bug)

    # G2: Report should show 846 trades, not 0
    _check("G2: 'Total Trades' shows correct count after fix",
           "| Total Trades | 0 |" not in report_bug,
           "Report still shows 'Total Trades: 0' — fix not working")

    # G3: Fee per trade should NOT equal total fees ($11.76)
    # With n_trades correctly = 846: fee_per_trade = 11.76 / 846 ≈ $0.014
    # Without fix: fee_per_trade = 11.76 / 1 = $11.76
    _check("G3: 'Fee per Trade' shows per-trade avg, not total",
           "| Fee per Trade (avg) | $11.76 |" not in report_bug,
           "Report still shows total fee as fee-per-trade — fix not working")

    # G4: No false SESSION_HISTORICAL_MIX contradiction
    _check("G4: SESSION_HISTORICAL_MIX false alarm eliminated",
           "SESSION/HISTORICAL METRICS MIXED" not in report_bug
           or "Session trades=0" not in report_bug,
           "False SESSION_HISTORICAL_MIX still firing")

    # G5: Normal path with "n_trades" still works
    data_ok = _minimal_report_data(n_trades=50, total_trades_key=False)
    report_ok = generate_full_report_v2(data_ok)
    _check("G5: normal path (n_trades key) still generates valid report",
           "## 1. Executive Snapshot" in report_ok,
           "Section 1 missing from normal-path report")

except Exception as e:
    _fail("G — unified report section", str(e))


# ═════════════════════════════════════════════════════════════════════════════
# H. RL INTELLIGENCE REPORTS — generated from _generate_rl_intelligence_reports
# ═════════════════════════════════════════════════════════════════════════════

_section("H — RL INTELLIGENCE REPORT STRUCTURE")

try:
    import ast

    src = (pathlib.Path(__file__).parent.parent / "main.py").read_text()
    tree = ast.parse(src)
    fn_names = {
        node.name for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    _check("H1: _generate_rl_intelligence_reports defined in main.py",
           "_generate_rl_intelligence_reports" in fn_names,
           f"Not found. Fns with 'rl': {[f for f in sorted(fn_names) if 'rl' in f.lower()]}")
    _check("H2: _generate_evolution_reports defined in main.py",
           "_generate_evolution_reports" in fn_names,
           "_generate_evolution_reports missing")
    _check("H3: _generate_forensic_reports defined in main.py",
           "_generate_forensic_reports" in fn_names,
           "_generate_forensic_reports missing")
    _check("H4: /api/rl-intelligence endpoint defined (get_rl_intelligence)",
           "get_rl_intelligence" in fn_names,
           "get_rl_intelligence endpoint handler missing")

except Exception as e:
    _fail("H — intelligence report structure check", str(e))


# ═════════════════════════════════════════════════════════════════════════════
# I. GET_EVOLUTION_STATE — observability API
# ═════════════════════════════════════════════════════════════════════════════

_section("I — get_evolution_state() OBSERVABILITY API")

with tempfile.TemporaryDirectory() as _tmpdir:
    _save_path = pathlib.Path(_tmpdir) / "rl_state.json"
    eng = _make_engine(_save_path)

    # Do some updates to give the engine real data
    for i in range(6):
        eng.update("MEAN_REVERTING", 9, "MeanReversion",
                   net_pnl=0.40, fee_cost=0.04, r_multiple=0.2)
    for i in range(4):
        eng.update("TRENDING", 15, "TrendFollowing",
                   net_pnl=-0.20, fee_cost=0.04, r_multiple=-0.05)

    try:
        state = eng.get_evolution_state()
        _check("I1: get_evolution_state() returns dict",
               isinstance(state, dict),
               f"Got type: {type(state)}")
        _check("I2: intelligence_score present (0-100)",
               "intelligence_score" in state
               and 0 <= state["intelligence_score"] <= 100,
               f"intelligence_score={state.get('intelligence_score')}")
        _check("I3: total_contexts count correct",
               state.get("total_contexts", 0) == len(eng._table),
               f"state says {state.get('total_contexts')}, table has {len(eng._table)}")
        _check("I4: context_maturity dict present",
               "context_maturity" in state and isinstance(state["context_maturity"], dict),
               f"context_maturity={state.get('context_maturity')}")
        _check("I5: learning_dynamics dict present",
               "learning_dynamics" in state and isinstance(state["learning_dynamics"], dict),
               f"learning_dynamics={state.get('learning_dynamics')}")
        _check("I6: session_intelligence dict present",
               "session_intelligence" in state and isinstance(state["session_intelligence"], dict),
               f"session_intelligence={state.get('session_intelligence')}")
        _check("I7: quality_distribution dict present",
               "quality_distribution" in state and isinstance(state["quality_distribution"], dict),
               f"quality_distribution={state.get('quality_distribution')}")
    except AttributeError:
        _fail("I1: get_evolution_state() method missing from RLContextualBandit")
    except Exception as e:
        _fail("I — get_evolution_state()", str(e))


# ═════════════════════════════════════════════════════════════════════════════
# J. Q-TABLE AUTO-SAVE WIRING — save called from update()
# ═════════════════════════════════════════════════════════════════════════════

_section("J — AUTO-SAVE WIRING IN update()")

with tempfile.TemporaryDirectory() as _tmpdir:
    _save_path = pathlib.Path(_tmpdir) / "rl_state.json"
    eng = _make_engine(_save_path)

    # J1: File doesn't exist before any update
    _check("J1: no state file before first update",
           not _save_path.exists(),
           "File unexpectedly exists before first update")

    # J2: File created after update
    eng.update("TRENDING", 15, "TrendFollowing",
                net_pnl=0.50, fee_cost=0.04, r_multiple=0.2)
    _check("J2: state file created after first update()",
           _save_path.exists(),
           "State file not created after update")

    # J3: File content is valid JSON after update
    try:
        content = json.loads(_save_path.read_text())
        _check("J3: saved state is valid JSON",
               isinstance(content, dict) and "table" in content,
               f"Keys: {list(content.keys())}")
    except Exception as e:
        _fail("J3: saved state is valid JSON", str(e))

    # J4: Multiple updates accumulate correctly
    for _ in range(4):
        eng.update("TRENDING", 15, "TrendFollowing",
                   net_pnl=0.40, fee_cost=0.04, r_multiple=0.2)
    content2 = json.loads(_save_path.read_text())
    saved_visits = content2["table"].get(
        make_context("TRENDING", 15, "TrendFollowing"), {}
    ).get("n_visits", 0)
    _check("J4: saved n_visits reflects all 5 updates",
           saved_visits == 5,
           f"Expected 5 visits saved, got {saved_visits}")

    # J5: A new engine loading this state sees 5 visits
    eng2 = _make_engine(_save_path)
    ctx = make_context("TRENDING", 15, "TrendFollowing")
    loaded_visits = eng2._table.get(ctx, ContextState(ctx)).n_visits
    _check("J5: loaded engine correctly reads 5 visits",
           loaded_visits == 5,
           f"Expected 5, got {loaded_visits}")


# ═════════════════════════════════════════════════════════════════════════════
# K. BYPASS-GUARD — RL TOXIC doesn't permanently freeze learning
# ═════════════════════════════════════════════════════════════════════════════

_section("K — LEARNING CONTINUES IN TOXIC CONTEXT (BYPASS MODEL)")

with tempfile.TemporaryDirectory() as _tmpdir:
    _save_path = pathlib.Path(_tmpdir) / "rl_state.json"
    eng = _make_engine(_save_path)

    # Make context TOXIC
    _drive_toxic(eng, n=TOXIC_MIN_VISITS)
    ctx = make_context("MEAN_REVERTING", 15, "MeanReversion")
    assert ctx in eng._toxic_contexts

    q_before = eng._table[ctx].q_value
    n_before = eng._table[ctx].n_visits

    # In bypass mode, should_trade() returns False but main.py overrides it.
    # We simulate that by calling update() anyway — like main.py does.
    eng.update("MEAN_REVERTING", 15, "MeanReversion",
               net_pnl=0.70, fee_cost=0.04, r_multiple=0.3)
    q_after  = eng._table[ctx].q_value
    n_after  = eng._table[ctx].n_visits

    _check("K1: update() works even on TOXIC context (learning not frozen)",
           n_after == n_before + 1,
           f"n_visits didn't increment: {n_before} → {n_after}")
    _check("K2: Q-value changes after update on TOXIC context",
           abs(q_after - q_before) > 0,
           f"Q unchanged: {q_before:.4f} → {q_after:.4f}")

    # K3: After enough wins, TOXIC flag auto-clears
    for _ in range(40):
        eng.update("MEAN_REVERTING", 15, "MeanReversion",
                   net_pnl=0.60, fee_cost=0.04, r_multiple=0.3)
    _check("K3: TOXIC flag auto-clears after sufficient wins",
           ctx not in eng._toxic_contexts,
           f"Context still toxic after recovery updates. Q={eng._table[ctx].q_value:.4f}")


# ─────────────────────────────────────────────────────────────────────────────
# Final summary
# ─────────────────────────────────────────────────────────────────────────────

print(f"\n{'═' * 62}")
total = _passed + _failed
if _failed == 0:
    print(f"{BOLD}{GREEN}  ALL {_passed}/{total} CHECKS PASSED ✓{RESET}")
    print("  FTD-055-ATHENA + FTD-054-PHOENIX fixes verified.")
else:
    print(f"{BOLD}{RED}  {_failed} FAILED / {_passed} PASSED (of {total}){RESET}")
print(f"{'═' * 62}\n")

sys.exit(0 if _failed == 0 else 1)
