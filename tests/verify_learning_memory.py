"""
LRN-001 — Learning Memory Pipeline Verification

Tests:
  - memory_applier bug fix (blended formula)
  - TradeMemoryBridge: record_trade wiring
  - LMO: records populate, patterns form, negative memory persists
  - Cross-session persistence (JSONL survives re-load)
  - Telemetry endpoints

Run: python tests/verify_learning_memory.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

PASS = 0
FAIL = 0
FAILURES: list = []


def check(label: str, condition: bool, detail: str = "") -> None:
    global PASS, FAIL
    if condition:
        print(f"  \033[92m✓\033[0m {label}")
        PASS += 1
    else:
        msg = f"{label}" + (f" [{detail}]" if detail else "")
        print(f"  \033[91m✗\033[0m {msg}")
        FAILURES.append(msg)
        FAIL += 1


def section(title: str) -> None:
    print(f"\n\033[1m\033[93m── {title} ──────────────────────────────────────────────────\033[0m")


# ── Imports ────────────────────────────────────────────────────────────────────
section("IMPORT — learning memory modules")

from core.learning_memory.memory_applier      import MemoryApplier
from core.learning_memory.memory_store        import MemoryStore
from core.learning_memory.pattern_engine      import PatternEngine, FORMATION_MIN_SAMPLES
from core.learning_memory.negative_memory     import NegativeMemory
from core.learning_memory.forgetting_engine   import ForgettingEngine
from core.learning_memory.confidence_updater  import ConfidenceUpdater
from core.learning_memory.pattern_indexer     import PatternIndexer
from core.learning_memory.learning_memory_orchestrator import (
    LearningMemoryOrchestrator, learning_memory_orchestrator,
)
from core.learning_memory.trade_memory_bridge import TradeMemoryBridge, trade_memory_bridge

check("A01 MemoryApplier importable", True)
check("A02 MemoryStore importable", True)
check("A03 PatternEngine importable", True)
check("A04 NegativeMemory importable", True)
check("A05 TradeMemoryBridge importable", True)
check("A06 trade_memory_bridge singleton is TradeMemoryBridge",
      isinstance(trade_memory_bridge, TradeMemoryBridge))
check("A07 learning_memory_orchestrator singleton is LearningMemoryOrchestrator",
      isinstance(learning_memory_orchestrator, LearningMemoryOrchestrator))


# ── memory_applier bug fix ────────────────────────────────────────────────────
section("TEST B — memory_applier blended formula fix")

from core.learning_memory.pattern_engine import PatternRecord, PatternKey
from core.learning_memory.negative_memory import NegativeMemory as NM

# Build a fresh applier with isolated dependencies
applier = MemoryApplier()

# Construct a mock pattern with confidence=80 (above cutoff)
# Use a real TUNABLE_PARAMS key so MemoryGuard does not block it.
# KELLY_FRACTION bounds: (0.10, 0.35); current=0.20, proposed=0.24 → 20% shift ≤ 30% cap.
mock_key: PatternKey = ("MEAN_REVERTING", "MEDIUM", "BTCUSDT", "KELLY_FRACTION", "UP")
mock_pat = PatternRecord(mock_key)
mock_pat.samples    = 25
mock_pat.success    = 20
mock_pat.confidence = 80.0
mock_pat.contexts   = {"r1", "r2", "r3"}

# Build a mock engine and negative memory
from core.learning_memory.pattern_engine import PatternEngine as PE
mock_engine = PE()
mock_engine._patterns[mock_key] = mock_pat

# Inject into applier's guard (reset state)
applier.reset_cycle()

# Build a plan using KELLY_FRACTION values within tunable bounds
plan = {
    "parameter":      "KELLY_FRACTION",
    "current_value":  0.20,
    "proposed_value": 0.24,   # +20% shift from 0.20, within 30% cap and [0.10, 0.35]
    "rationale":      "test",
}
context = {
    "regime":      "MEAN_REVERTING",
    "volatility":  "MEDIUM",
    "instrument":  "BTCUSDT",
}

from core.learning_memory.negative_memory import NegativeMemory as NegMem
mock_neg = NegMem.__new__(NegMem)
mock_neg._path    = "/tmp/test_neg_mem.jsonl"
mock_neg._entries = {}
mock_neg._cycle   = 0

enhanced_plan, explanation = applier._try_enhance(
    plan, context, mock_engine, mock_neg,
    ftd028_meta_score=75.0, ftd027_passed=True,
)

check("B01 enhanced plan has memory_hint=True", enhanced_plan.get("memory_hint") is True,
      f"hint={enhanced_plan.get('memory_hint')}")

blended_val = enhanced_plan.get("proposed_value", 0.24)
# With fix: weight=0.5 (conf≥60), blended = 0.5*0.20 + 0.5*0.24 = 0.22
# conf=80 ≥ 70 → override: scale=0.8, delta=0.04*0.8=0.032, blended=0.20+0.032=0.232
check("B02 blended value is NOT equal to proposed_value (fix verified)",
      abs(blended_val - 0.24) > 0.001, f"blended={blended_val}")
check("B03 blended value is between current and proposed (0.20–0.24 range)",
      0.19 <= blended_val <= 0.25, f"blended={blended_val}")

# conf=80 ≥ 70: the conf<70 override block is skipped.
# Standard 50/50 blend: 0.5*0.20 + 0.5*0.24 = 0.22
check("B04 high confidence path: blended = 0.22 (standard 50/50 weighted blend)",
      abs(blended_val - 0.22) < 0.005, f"blended={blended_val}")


# ── MemoryStore ────────────────────────────────────────────────────────────────
section("TEST C — MemoryStore record persistence")

with tempfile.TemporaryDirectory() as tmpdir:
    store_path = os.path.join(tmpdir, "test_memory.jsonl")
    store = MemoryStore(path=store_path)

    check("C01 new store is empty", store.count() == 0)

    rec = MemoryStore.build_record(
        cycle_id="TRADE-001", regime="MEAN_REVERTING", volatility="MEDIUM",
        timeframe="10", instrument="BTCUSDT", parameter="MR_PAPER_SPEED",
        direction="UP", score_delta=10.0, rollback=False,
        meta_score=75.0, contradiction=False, ai_mode="TRADE", rationale="test",
    )
    result = store.append(rec)
    check("C02 valid record appended (returns True)", result is True)
    check("C03 store count = 1 after append", store.count() == 1)

    # Invalid record (missing field)
    bad_rec = {"cycle_id": "x", "timestamp": 1}
    result_bad = store.append(bad_rec)
    check("C04 invalid record rejected (returns False)", result_bad is False)
    check("C05 count still = 1 after rejected record", store.count() == 1)

    # Persistence: re-load from disk
    store2 = MemoryStore(path=store_path)
    check("C06 reloaded store count = 1 (persistence verified)", store2.count() == 1)

    loaded = store2.recent(1)
    check("C07 loaded record has cycle_id=TRADE-001",
          loaded[0]["cycle_id"] == "TRADE-001")
    check("C08 loaded record has correct context",
          loaded[0]["context"]["regime"] == "MEAN_REVERTING")

    # Direction validation
    bad_dir = MemoryStore.build_record(
        cycle_id="X", regime="TR", volatility="MED", timeframe="0",
        instrument="X", parameter="P", direction="LEFT",  # invalid
        score_delta=0, rollback=False, meta_score=0, contradiction=False,
        ai_mode="TRADE", rationale="",
    )
    check("C09 invalid direction rejected", store.append(bad_dir) is False)


# ── PatternEngine ──────────────────────────────────────────────────────────────
section("TEST D — PatternEngine: pattern formation")

engine = PatternEngine()

def _make_rec(cycle_id, regime, hour, strategy, side, rollback):
    return {
        "cycle_id": cycle_id,
        "timestamp": time.time(),
        "context": {"regime": regime, "volatility": "MEDIUM",
                    "timeframe": str(hour), "instrument": "TESTUSDT"},
        "change":   {"parameter": strategy, "direction": "UP" if side == "LONG" else "DOWN"},
        "outcome":  {"score_delta": 10.0 if not rollback else -10.0, "rollback": rollback},
        "validation": {"meta_score": 75.0, "contradiction": False},
        "decision": {"ai_mode": "TRADE", "rationale": "test"},
    }

# Feed 20 winning records across 3 different hours (required for pattern formation)
for i in range(20):
    hour = [10, 14, 20][i % 3]   # 3 distinct hours → 3 context buckets
    rec  = _make_rec(f"T{i}", "MEAN_REVERTING", hour, "MR_STRAT", "LONG", False)
    engine.ingest(rec)

all_pats = engine.all_patterns()
check("D01 patterns dict has 1 entry", len(all_pats) == 1)

pat = all_pats[0]
check("D02 pattern has 20 samples", pat.samples == 20)
check("D03 pattern has 20 successes (no rollbacks)", pat.success == 20)
check("D04 pattern has 3 distinct context buckets", len(pat.contexts) == 3)

# Update confidence
updater = ConfidenceUpdater()
updater.update(pat, current_cycle=20)
check("D05 confidence > 0 after update", pat.confidence > 0,
      f"confidence={pat.confidence}")

# is_formed requires: samples≥20, confidence≥70, contexts≥3
# After winning 20/20 with 3 contexts, confidence should be high
check("D06 pattern is_formed = True after 20/20 wins + 3 contexts + update",
      pat.is_formed, f"formed={pat.is_formed} conf={pat.confidence:.1f}")

# Feed 5 loss records → pattern success drops
for i in range(5):
    hour = [10, 14, 20][i % 3]
    rec  = _make_rec(f"L{i}", "MEAN_REVERTING", hour, "MR_STRAT", "LONG", True)
    engine.ingest(rec)

pat_after = engine.all_patterns()[0]
check("D07 samples = 25 after 5 more records", pat_after.samples == 25)
check("D08 success still = 20 (losses don't increment success)", pat_after.success == 20)

# Formed patterns vs all patterns
formed = engine.formed_patterns()
check("D09 formed_patterns() contains the formed pattern", len(formed) >= 1)


# ── NegativeMemory ────────────────────────────────────────────────────────────
section("TEST E — NegativeMemory: rollback tracking and persistence")

with tempfile.TemporaryDirectory() as tmpdir:
    neg_path = os.path.join(tmpdir, "test_neg.jsonl")
    neg = NegativeMemory(path=neg_path)

    test_key = ("MEAN_REVERTING", "MEDIUM", "TESTUSDT", "BAD_STRAT", "UP")

    check("E01 not banned before any rollback", not neg.is_banned(test_key))

    neg.record_rollback(test_key)
    check("E02 banned after 1 rollback (temp ban, score=1.0 ≥ 0.10)", neg.is_banned(test_key))

    neg.record_rollback(test_key)
    neg.record_rollback(test_key)
    check("E03 3 rollbacks → permanent ban", neg.is_banned(test_key))

    entry = neg._entries[neg._key_str(test_key)]
    check("E04 entry.permanent = True", entry["permanent"] is True)
    check("E05 entry.rollbacks = 3", entry["rollbacks"] == 3)

    # Persistence: reload
    neg2 = NegativeMemory(path=neg_path)
    check("E06 permanent ban survives reload", neg2.is_banned(test_key),
          f"entries={list(neg2._entries.keys())}")

    # Decay: temp entry
    temp_key = ("TRENDING", "HIGH", "ETHUSDT", "TR_STRAT", "DOWN")
    neg2.record_rollback(temp_key)
    check("E07 temp ban active after 1 rollback", neg2.is_banned(temp_key))

    # Advance many cycles to decay below threshold
    for _ in range(100):
        neg2.advance_cycle()
    check("E08 temp ban decayed after 100 cycles (0.90^100 < 0.10)", not neg2.is_banned(temp_key))

    # Permanent ban unaffected by decay
    check("E09 permanent ban unaffected by 100 cycles decay", neg2.is_banned(test_key))

    counts = neg2.count()
    check("E10 count() has permanent/temporary/total keys",
          all(k in counts for k in ("permanent", "temporary", "total")))
    check("E11 permanent count = 1", counts["permanent"] == 1)

    to_list = neg2.to_list()
    check("E12 to_list() returns list", isinstance(to_list, list))
    check("E13 to_list() has at least 1 entry", len(to_list) >= 1)


# ── TradeMemoryBridge ─────────────────────────────────────────────────────────
section("TEST F — TradeMemoryBridge: trade→memory pipeline")

# Use isolated LMO to avoid polluting the global singleton
with tempfile.TemporaryDirectory() as tmpdir:
    # Patch LMO store path for isolation
    orig_store_path = "reports/learning_memory/memory_store.jsonl"
    test_store_path = os.path.join(tmpdir, "bridge_test_store.jsonl")

    lmo_iso = LearningMemoryOrchestrator.__new__(LearningMemoryOrchestrator)
    lmo_iso._store      = MemoryStore(path=test_store_path)
    lmo_iso._engine     = PatternEngine()
    lmo_iso._updater    = ConfidenceUpdater()
    lmo_iso._applier    = MemoryApplier()
    lmo_iso._forgetter  = ForgettingEngine()

    nm_path = os.path.join(tmpdir, "neg_mem.jsonl")
    lmo_iso._neg_memory = NegativeMemory(path=nm_path)
    lmo_iso._indexer    = PatternIndexer(lmo_iso._store, lmo_iso._engine)
    from core.learning_memory.explainability_engine import ExplainabilityEngine
    lmo_iso._explain    = ExplainabilityEngine()
    lmo_iso._enabled    = True
    lmo_iso._last_prune_ts   = 0.0
    lmo_iso._cycle_count     = 0
    lmo_iso._exploration_boost = False

    # Build a bridge pointing at isolated LMO
    import core.learning_memory.trade_memory_bridge as _tmb_mod
    orig_lmo = _tmb_mod.learning_memory_orchestrator
    _tmb_mod.learning_memory_orchestrator = lmo_iso

    bridge = TradeMemoryBridge()

    # Feed 3 winning trades
    for i in range(3):
        bridge.record_trade(
            trade_id    = f"TR-WIN-{i}",
            symbol      = "BTCUSDT",
            regime      = "MEAN_REVERTING",
            strategy_id = "MR_PAPER_SPEED",
            side        = "LONG",
            net_pnl     = 5.0,
            confidence  = 0.70,
            atr_pct     = 1.5,
            utc_hour    = 10 + i,   # different hours
        )

    check("F01 bridge total_recorded = 3", bridge._total_recorded == 3)
    check("F02 bridge total_wins = 3", bridge._total_wins == 3)
    check("F03 bridge total_losses = 0", bridge._total_losses == 0)
    check("F04 LMO store has 3 records", lmo_iso._store.count() == 3)
    check("F05 LMO cycle_count = 3", lmo_iso._cycle_count == 3)

    # Verify record format in store
    records = lmo_iso._store.recent(3)
    check("F06 record has cycle_id matching trade_id", records[0]["cycle_id"] == "TR-WIN-0")
    check("F07 record context.regime = MEAN_REVERTING",
          records[0]["context"]["regime"] == "MEAN_REVERTING")
    check("F08 record change.parameter = MR_PAPER_SPEED",
          records[0]["change"]["parameter"] == "MR_PAPER_SPEED")
    check("F09 record change.direction = UP (LONG → UP)",
          records[0]["change"]["direction"] == "UP")
    check("F10 record outcome.rollback = False (win)",
          records[0]["outcome"]["rollback"] is False)
    check("F11 record decision.ai_mode = TRADE",
          records[0]["decision"]["ai_mode"] == "TRADE")

    # Feed 1 losing trade
    bridge.record_trade(
        trade_id="TR-LOSS-0", symbol="BTCUSDT", regime="MEAN_REVERTING",
        strategy_id="MR_PAPER_SPEED", side="LONG", net_pnl=-1.0,
        confidence=0.55, atr_pct=1.5, utc_hour=14,
    )
    check("F12 loss recorded in bridge", bridge._total_losses == 1)
    check("F13 LMO store has 4 records after loss", lmo_iso._store.count() == 4)

    loss_rec = lmo_iso._store.recent(1)[0]
    check("F14 loss record outcome.rollback = True", loss_rec["outcome"]["rollback"] is True)

    # Catastrophic loss triggers extra negative memory
    bridge.record_trade(
        trade_id="TR-CAT-0", symbol="BTCUSDT", regime="MEAN_REVERTING",
        strategy_id="BAD_STRAT", side="LONG", net_pnl=-5.0,  # below -$2 threshold
        confidence=0.51, atr_pct=1.5, utc_hour=10,
    )
    check("F15 catastrophic loss: LMO store has 5 records", lmo_iso._store.count() == 5)
    # Catastrophic loss should trigger negative memory (1 normal rollback + 1 extra)
    cat_key = ("MEAN_REVERTING", "MEDIUM", "BTCUSDT", "BAD_STRAT", "UP")
    cat_key_str = "|".join(str(k) for k in cat_key)
    neg_entry = lmo_iso._neg_memory._entries.get(cat_key_str)
    check("F16 catastrophic loss → negative memory entry exists", neg_entry is not None,
          f"keys={list(lmo_iso._neg_memory._entries.keys())}")
    if neg_entry:
        check("F17 catastrophic loss → rollbacks ≥ 2 (normal + extra)",
              neg_entry["rollbacks"] >= 2, f"rollbacks={neg_entry['rollbacks']}")

    # SHORT → DOWN mapping
    bridge.record_trade(
        trade_id="TR-SHORT-0", symbol="ETHUSDT", regime="TRENDING",
        strategy_id="TR_STRAT", side="SHORT", net_pnl=3.0,
        confidence=0.65, atr_pct=2.0, utc_hour=10,
    )
    short_rec = lmo_iso._store.recent(1)[0]
    check("F18 SHORT → direction=DOWN in record",
          short_rec["change"]["direction"] == "DOWN")

    # Disabled LMO → no records added
    lmo_iso.disable()
    before_count = lmo_iso._store.count()
    bridge.record_trade(
        trade_id="TR-DISABLED", symbol="X", regime="UNKNOWN",
        strategy_id="S", side="LONG", net_pnl=1.0, utc_hour=0,
    )
    lmo_iso.enable()
    check("F19 disabled LMO → no record added",
          lmo_iso._store.count() == before_count)

    # Telemetry
    telem = bridge.get_telemetry()
    check("F20 telemetry has module=TradeMemoryBridge",
          telem["module"] == "TradeMemoryBridge")
    check("F21 telemetry has total_recorded ≥ 5", telem["total_recorded"] >= 5)
    check("F22 telemetry has win_rate", 0.0 <= telem["win_rate"] <= 1.0)
    check("F23 telemetry has lmo_records", telem["lmo_records"] >= 5)
    check("F24 telemetry has lmo_enabled", "lmo_enabled" in telem)

    # Restore global LMO
    _tmb_mod.learning_memory_orchestrator = orig_lmo


# ── Pattern formation from 20 trades ──────────────────────────────────────────
section("TEST G — Full pipeline: 20 trades → pattern crystallisation")

with tempfile.TemporaryDirectory() as tmpdir:
    # Fresh isolated LMO
    s_path = os.path.join(tmpdir, "store.jsonl")
    n_path = os.path.join(tmpdir, "neg.jsonl")

    lmo2 = LearningMemoryOrchestrator.__new__(LearningMemoryOrchestrator)
    lmo2._store      = MemoryStore(path=s_path)
    lmo2._engine     = PatternEngine()
    lmo2._updater    = ConfidenceUpdater()
    lmo2._applier    = MemoryApplier()
    lmo2._forgetter  = ForgettingEngine()
    lmo2._neg_memory = NegativeMemory(path=n_path)
    lmo2._indexer    = PatternIndexer(lmo2._store, lmo2._engine)
    from core.learning_memory.explainability_engine import ExplainabilityEngine as EE
    lmo2._explain    = EE()
    lmo2._enabled    = True
    lmo2._last_prune_ts   = 0.0
    lmo2._cycle_count     = 0
    lmo2._exploration_boost = False

    import core.learning_memory.trade_memory_bridge as _tmb2
    _tmb2.learning_memory_orchestrator = lmo2

    bridge2 = TradeMemoryBridge()

    # Feed 20 winning trades across 3 distinct hours → pattern forms
    for i in range(20):
        hour = [10, 14, 20][i % 3]
        bridge2.record_trade(
            trade_id=f"PAT-{i}", symbol="BTCUSDT", regime="MEAN_REVERTING",
            strategy_id="MR_PAPER_SPEED", side="LONG", net_pnl=5.0,
            confidence=0.70, atr_pct=1.5, utc_hour=hour,
        )

    check("G01 20 records in store", lmo2._store.count() == 20)
    all_p = lmo2._engine.all_patterns()
    check("G02 pattern engine has 1 pattern", len(all_p) == 1)

    pat = all_p[0]
    check("G03 pattern samples = 20", pat.samples == 20)
    check("G04 pattern success = 20", pat.success == 20)
    check("G05 pattern has 3 context buckets (10h, 14h, 20h)", len(pat.contexts) == 3)

    # Update confidence and check formation
    lmo2._updater.update(pat, current_cycle=20)
    check("G06 pattern confidence > 70 (→ is_formed possible)",
          pat.confidence > 70.0, f"conf={pat.confidence:.1f}")
    check("G07 pattern is_formed = True", pat.is_formed,
          f"formed={pat.is_formed} conf={pat.confidence:.1f} contexts={len(pat.contexts)}")

    formed = lmo2._engine.formed_patterns()
    check("G08 formed_patterns() returns 1", len(formed) == 1)

    # Heatmap generates from formed patterns
    heatmap = lmo2.pattern_heatmap()
    check("G09 heatmap is non-empty list", isinstance(heatmap, list) and len(heatmap) > 0)
    check("G10 heatmap entry has regime/parameter/avg_conf/count",
          all(k in heatmap[0] for k in ("regime", "parameter", "avg_conf", "count")))

    # Cross-session persistence: reload LMO from disk
    lmo3 = LearningMemoryOrchestrator.__new__(LearningMemoryOrchestrator)
    lmo3._store      = MemoryStore(path=s_path)
    lmo3._engine     = PatternEngine()
    lmo3._updater    = ConfidenceUpdater()
    lmo3._applier    = MemoryApplier()
    lmo3._forgetter  = ForgettingEngine()
    lmo3._neg_memory = NegativeMemory(path=n_path)
    lmo3._indexer    = PatternIndexer(lmo3._store, lmo3._engine)
    lmo3._explain    = EE()
    lmo3._enabled    = True
    lmo3._last_prune_ts   = 0.0
    lmo3._cycle_count     = 0
    lmo3._exploration_boost = False

    loaded_count = lmo3._indexer.build_from_store()
    check("G11 reload: 20 records loaded from disk", loaded_count == 20)
    check("G12 reload: pattern engine has 1 pattern after bootstrap",
          len(lmo3._engine.all_patterns()) == 1)

    pat3 = lmo3._engine.all_patterns()[0]
    check("G13 reloaded pattern: samples = 20", pat3.samples == 20)
    check("G14 reloaded pattern: success = 20", pat3.success == 20)
    check("G15 reloaded pattern: 3 context buckets", len(pat3.contexts) == 3)

    # Restore
    _tmb2.learning_memory_orchestrator = orig_lmo


# ── ATR volatility mapping ────────────────────────────────────────────────────
section("TEST H — ATR → volatility tier mapping")

from core.learning_memory.trade_memory_bridge import _volatility_tier

check("H01 atr=0.5 → LOW",    _volatility_tier(0.5)  == "LOW")
check("H02 atr=1.0 → MEDIUM", _volatility_tier(1.0)  == "MEDIUM")
check("H03 atr=2.0 → MEDIUM", _volatility_tier(2.0)  == "MEDIUM")
check("H04 atr=3.0 → HIGH",   _volatility_tier(3.0)  == "HIGH")
check("H05 atr=5.0 → HIGH",   _volatility_tier(5.0)  == "HIGH")
check("H06 atr=0.0 → LOW",    _volatility_tier(0.0)  == "LOW")


# ── Singleton identity ─────────────────────────────────────────────────────────
section("TEST I — Singleton identity")

from core.learning_memory.trade_memory_bridge import trade_memory_bridge as tb1
from core.learning_memory.trade_memory_bridge import trade_memory_bridge as tb2
check("I01 trade_memory_bridge singleton is same object", tb1 is tb2)

from core.learning_memory import learning_memory_orchestrator as lmo1
from core.learning_memory import learning_memory_orchestrator as lmo2
check("I02 learning_memory_orchestrator singleton is same object", lmo1 is lmo2)


# ── Results ────────────────────────────────────────────────────────────────────
print("\n" + "─" * 60)
print("  RESULTS")
print("─" * 60)
print(f"\n  Total checks: {PASS + FAIL}")
print(f"  Passed:       {PASS}")
print(f"  Failed:       {FAIL}")
if FAILURES:
    print("\n  FAILURES:")
    for f in FAILURES:
        print(f"    • {f}")
    print()
    sys.exit(1)
else:
    print(
        f"\n  \033[92m✓ ALL {PASS} CHECKS PASSED — LRN-001 Learning Memory Pipeline VALIDATED\033[0m\n"
    )
