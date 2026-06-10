"""
PRP-002 — Signal Ecology Test Suite

Tests: OpportunityEcology, AdaptiveRSIGovernor, SignalDensityEngine,
       ExplorationRecoveryGovernor, AlphaContextMemory

Run: python tests/verify_signal_ecology.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# ── Path setup ──────────────────────────────────────────────────────────────────
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


# ── Import all modules ─────────────────────────────────────────────────────────
section("IMPORT — all 5 signal ecology modules")

from core.signal_ecology.adaptive_rsi_governor import (
    AdaptiveRSIGovernor, RSIDecision, adaptive_rsi_governor,
)
from core.signal_ecology.signal_density_engine import (
    SignalDensityEngine, DensitySnapshot, signal_density_engine,
)
from core.signal_ecology.exploration_recovery import (
    ExplorationRecoveryGovernor, RecoveryDecision, RecoveryMode,
    exploration_recovery_governor,
)
from core.signal_ecology.alpha_context_memory import (
    AlphaContextMemory, ContextRecord, alpha_context_memory,
)
from core.signal_ecology.opportunity_ecology import (
    OpportunityEcology, EcologyDecision, opportunity_ecology,
)

check("A01 AdaptiveRSIGovernor importable", True)
check("A02 SignalDensityEngine importable", True)
check("A03 ExplorationRecoveryGovernor importable", True)
check("A04 AlphaContextMemory importable", True)
check("A05 OpportunityEcology importable", True)

check("A06 adaptive_rsi_governor singleton is AdaptiveRSIGovernor",
      isinstance(adaptive_rsi_governor, AdaptiveRSIGovernor))
check("A07 signal_density_engine singleton is SignalDensityEngine",
      isinstance(signal_density_engine, SignalDensityEngine))
check("A08 exploration_recovery_governor singleton is ExplorationRecoveryGovernor",
      isinstance(exploration_recovery_governor, ExplorationRecoveryGovernor))
check("A09 alpha_context_memory singleton is AlphaContextMemory",
      isinstance(alpha_context_memory, AlphaContextMemory))
check("A10 opportunity_ecology singleton is OpportunityEcology",
      isinstance(opportunity_ecology, OpportunityEcology))


# ── AdaptiveRSIGovernor ────────────────────────────────────────────────────────
section("TEST B — AdaptiveRSIGovernor")

gov = AdaptiveRSIGovernor()

# MEAN_REVERTING SHORT: rsi > 70, prev > 65, above_sma
d1 = gov.get_signal(regime="MEAN_REVERTING", rsi_val=72.0, rsi_prev=67.0,
                    above_sma=True, symbol="TEST")
check("B01 MR SHORT passes", not d1.blocked, f"reason={d1.block_reason}")
check("B02 MR SHORT side=SHORT", d1.side == "SHORT", f"side={d1.side}")

# MEAN_REVERTING LONG: rsi < 30, prev < 35, below_sma
d2 = gov.get_signal(regime="MEAN_REVERTING", rsi_val=28.0, rsi_prev=33.0,
                    above_sma=False, symbol="TEST")
check("B03 MR LONG passes", not d2.blocked, f"reason={d2.block_reason}")
check("B04 MR LONG side=LONG", d2.side == "LONG", f"side={d2.side}")

# MEAN_REVERTING LONG crash guard: rsi < 30 but prev >= 35 → blocked
d3 = gov.get_signal(regime="MEAN_REVERTING", rsi_val=28.0, rsi_prev=36.0,
                    above_sma=False, symbol="TEST")
check("B05 MR crash guard LONG blocked", d3.blocked, f"reason={d3.block_reason}")
check("B06 MR crash guard reason mentions RSI_CRASH_GUARD", "CRASH_GUARD" in d3.block_reason,
      f"reason={d3.block_reason}")

# MEAN_REVERTING SHORT crash guard: rsi > 70 but prev <= 65 → blocked
d4 = gov.get_signal(regime="MEAN_REVERTING", rsi_val=72.0, rsi_prev=64.0,
                    above_sma=True, symbol="TEST")
check("B07 MR crash guard SHORT blocked", d4.blocked)

# TRENDING LONG: above_sma, rsi <= 48
d5 = gov.get_signal(regime="TRENDING", rsi_val=45.0, rsi_prev=46.0,
                    above_sma=True, symbol="TEST")
check("B08 TR LONG passes", not d5.blocked)
check("B09 TR LONG side=LONG", d5.side == "LONG", f"side={d5.side}")

# TRENDING SHORT (schema v2 unified threshold): not above_sma, rsi <= long_band(48)
# — confirms downtrend momentum; old v1 logic (rsi >= 52) never fired in
# sustained downtrends and was replaced in the governor.
d6 = gov.get_signal(regime="TRENDING", rsi_val=45.0, rsi_prev=46.0,
                    above_sma=False, symbol="TEST")
check("B10 TR SHORT passes", not d6.blocked)
check("B11 TR SHORT side=SHORT", d6.side == "SHORT")

# TRENDING level blocked
d7 = gov.get_signal(regime="TRENDING", rsi_val=50.0, rsi_prev=50.0,
                    above_sma=True, symbol="TEST")
check("B12 TR level blocked (rsi=50 in pullback, rsi=50 not ≤48)", d7.blocked)

# Unknown regime falls back to TRENDING logic
d8 = gov.get_signal(regime="UNKNOWN", rsi_val=45.0, rsi_prev=46.0,
                    above_sma=True, symbol="TEST")
check("B13 UNKNOWN regime handled (TRENDING logic)", not d8.blocked)

# RSIDecision has required fields
check("B14 RSIDecision has ts field", d1.ts > 0)
check("B15 RSIDecision band_lo/hi present", d1.band_lo >= 0 and d1.band_hi > 0)

# Telemetry
telem = gov.get_telemetry()
check("B16 telemetry has total_evaluated", telem["total_evaluated"] > 0)
check("B17 telemetry has bands by regime", "MEAN_REVERTING" in telem["bands"])
check("B18 telemetry has survival_by_regime", "MEAN_REVERTING" in telem["survival_by_regime"])
check("B19 band_state() returns dict", isinstance(gov.band_state(), dict))
check("B20 recent_decisions returns list", isinstance(gov.recent_decisions(5), list))

# ── Multi-candle RSI persistence confirmation (v1.11.0) ───────────────────────
# B21: LONG passes when ≥2 of last 3 readings are below long_band+5 (=35)
d_p1 = gov.get_signal(regime="MEAN_REVERTING", rsi_val=27.0, rsi_prev=29.0,
                      above_sma=False, symbol="TEST",
                      rsi_history=[28.0, 29.0, 27.0])   # all 3 in zone → pass
check("B21 persistence LONG passes (3/3 in zone)", not d_p1.blocked,
      f"reason={d_p1.block_reason}")

# B22: LONG passes when exactly 2 of 3 readings are in zone (boundary)
d_p2 = gov.get_signal(regime="MEAN_REVERTING", rsi_val=27.0, rsi_prev=29.0,
                      above_sma=False, symbol="TEST",
                      rsi_history=[38.0, 29.0, 27.0])   # first above 35, last 2 in zone → pass
check("B22 persistence LONG passes (2/3 in zone)", not d_p2.blocked,
      f"reason={d_p2.block_reason}")

# B23: LONG blocked when only 1 of 3 readings is in zone (first-touch crash)
d_p3 = gov.get_signal(regime="MEAN_REVERTING", rsi_val=27.0, rsi_prev=29.0,
                      above_sma=False, symbol="TEST",
                      rsi_history=[42.0, 38.0, 27.0])   # only last 1 in zone → blocked
check("B23 persistence LONG blocked (1/3 in zone, first-touch crash)", d_p3.blocked,
      f"reason={d_p3.block_reason}")
check("B24 persistence block reason mentions RSI_PERSIST_LONG",
      "RSI_PERSIST_LONG" in d_p3.block_reason, f"reason={d_p3.block_reason}")

# B25: SHORT passes when ≥2 of last 3 readings are above short_band-5 (=65)
d_p4 = gov.get_signal(regime="MEAN_REVERTING", rsi_val=73.0, rsi_prev=71.0,
                      above_sma=True, symbol="TEST",
                      rsi_history=[72.0, 71.0, 73.0])   # all 3 above 65 → pass
check("B25 persistence SHORT passes (3/3 in zone)", not d_p4.blocked,
      f"reason={d_p4.block_reason}")

# B26: SHORT blocked when only 1 of 3 readings is in overbought zone (first-touch spike)
d_p5 = gov.get_signal(regime="MEAN_REVERTING", rsi_val=73.0, rsi_prev=71.0,
                      above_sma=True, symbol="TEST",
                      rsi_history=[58.0, 62.0, 73.0])   # only last 1 above 65 → blocked
check("B26 persistence SHORT blocked (1/3 in zone, first-touch spike)", d_p5.blocked,
      f"reason={d_p5.block_reason}")
check("B27 persistence block reason mentions RSI_PERSIST_SHORT",
      "RSI_PERSIST_SHORT" in d_p5.block_reason, f"reason={d_p5.block_reason}")

# B28: No history provided → crash guard still gates correctly (graceful degradation)
d_p6 = gov.get_signal(regime="MEAN_REVERTING", rsi_val=28.0, rsi_prev=33.0,
                      above_sma=False, symbol="TEST",
                      rsi_history=None)   # None → persistence check skipped
check("B28 no history → crash guard only, LONG passes if prev<35", not d_p6.blocked,
      f"reason={d_p6.block_reason}")

# B29: Short history (1 value) → graceful degradation, no persistence block
d_p7 = gov.get_signal(regime="MEAN_REVERTING", rsi_val=28.0, rsi_prev=33.0,
                      above_sma=False, symbol="TEST",
                      rsi_history=[28.0])   # len=1 → skip persistence
check("B29 single-item history → no persistence block", not d_p7.blocked,
      f"reason={d_p7.block_reason}")

# B30: TRENDING regime ignores persistence check entirely (persistence is MR-only)
d_p8 = gov.get_signal(regime="TRENDING", rsi_val=45.0, rsi_prev=46.0,
                      above_sma=True, symbol="TEST",
                      rsi_history=[60.0, 58.0, 45.0])   # history with non-extreme values
check("B30 TRENDING regime unaffected by rsi_history", not d_p8.blocked,
      f"reason={d_p8.block_reason}")


# ── SignalDensityEngine ────────────────────────────────────────────────────────
section("TEST C — SignalDensityEngine")

de = SignalDensityEngine()

check("C01 new engine has total_evaluated=0", de._total_evaluated == 0)

de.record_pass(regime="MEAN_REVERTING", symbol="A")
de.record_pass(regime="MEAN_REVERTING", symbol="B")
de.record_block(reason="RSI_LEVEL", regime="TRENDING", symbol="C")
de.record_block(reason="RSI_LEVEL", regime="TRENDING", symbol="D")
de.record_block(reason="RSI_CRASH_GUARD", regime="MEAN_REVERTING", symbol="E")

check("C02 total_evaluated = 5", de._total_evaluated == 5)
check("C03 total_passed = 2", de._total_passed == 2)
check("C04 survival_rate = 0.4 (2/5)", abs(de.survival_rate() - 0.4) < 0.01)

snap = de.snapshot()
check("C05 snapshot is DensitySnapshot", isinstance(snap, DensitySnapshot))
check("C06 snapshot.passed_count = 2", snap.passed_count == 2)
check("C07 snapshot.blocked_count = 3", snap.blocked_count == 3)
check("C08 snapshot.survival_rate = 0.4", abs(snap.survival_rate - 0.4) < 0.01)
check("C09 snapshot has regime_breakdown", "MEAN_REVERTING" in snap.regime_breakdown)
check("C10 top_block_reason is non-empty", snap.top_block_reason != "")

check("C11 no drought yet (fresh engine, last_pass_ts seeded)", not de.is_drought())
check("C12 signals_per_hr >= 2", de.signals_per_hour() >= 2)

telem_de = de.get_telemetry()
check("C13 telemetry has total_evaluated=5", telem_de["total_evaluated"] == 5)
check("C14 telemetry has survival_rate", "survival_rate" in telem_de)
check("C15 telemetry has top_block_reasons", isinstance(telem_de["top_block_reasons"], list))

brm = de.block_reason_matrix()
check("C16 block_reason_matrix is list", isinstance(brm, list))
check("C17 block_reason_matrix has entries", len(brm) >= 2)
check("C18 block_reason entry has reason/count/pct keys",
      all(k in brm[0] for k in ("reason", "count", "pct")))

# Starvation: need 20 evaluations below 5%
de2 = SignalDensityEngine()
for _ in range(20):
    de2.record_block(reason="X", regime="TEST")
check("C19 starvation detected after 20 pure blocks", de2.is_starvation())

# mark_auto_recover
de3 = SignalDensityEngine()
de3._last_pass_ts -= 700  # simulate 700s drought
check("C20 should_auto_recover after 700s drought", de3.should_auto_recover())
de3.mark_auto_recover_triggered()
check("C21 auto_recover_triggered clears should_auto_recover", not de3.should_auto_recover())


# ── ExplorationRecoveryGovernor ────────────────────────────────────────────────
section("TEST D — ExplorationRecoveryGovernor")

erg = ExplorationRecoveryGovernor()

# Healthy state — no drought, no starvation
rec0 = erg.evaluate(drought_seconds=10.0, survival_rate=0.15, is_starvation=False)
check("D01 healthy state → NONE mode", rec0.mode == RecoveryMode.NONE)
check("D02 healthy state → size_mult = 1.0", rec0.size_multiplier == 1.0)

# Rejection loop (50 consecutive blocks)
for _ in range(50):
    erg.on_signal_blocked()

rec1 = erg.evaluate(drought_seconds=10.0, survival_rate=0.15, is_starvation=False)
check("D03 rejection loop → CURIOSITY mode", rec1.mode == RecoveryMode.CURIOSITY,
      f"mode={rec1.mode}")
check("D04 CURIOSITY size_mult = 0.4", abs(rec1.size_multiplier - 0.4) < 0.01)

# Force cooldown to pass
erg._last_recovery_ts = 0.0

# Forced drought
rec2 = erg.evaluate(drought_seconds=950.0, survival_rate=0.10, is_starvation=False)
check("D05 forced drought → FORCED mode", rec2.mode == RecoveryMode.FORCED,
      f"mode={rec2.mode}")
check("D06 FORCED size_mult = 0.25", abs(rec2.size_multiplier - 0.25) < 0.01)

# Signal passed closes cycle
erg.on_signal_passed()
check("D07 consecutive_blocks reset to 0 after pass", erg._consecutive_blocks == 0)

# Starvation
erg2 = ExplorationRecoveryGovernor()
rec3 = erg2.evaluate(drought_seconds=10.0, survival_rate=0.03, is_starvation=True)
check("D08 starvation → CURIOSITY", rec3.mode == RecoveryMode.CURIOSITY,
      f"mode={rec3.mode}")

# Recovery cap (MAX_RECOVERY_TRADES = 3)
erg3 = ExplorationRecoveryGovernor()
for i in range(4):
    erg3._last_recovery_ts = 0.0  # bypass cooldown
    r = erg3.evaluate(drought_seconds=10.0, survival_rate=0.03, is_starvation=True)

check("D09 recovery cap: 4th call returns NONE (cap=3)", r.mode == RecoveryMode.NONE,
      f"mode={r.mode}")

# Telemetry
telem_erg = erg.get_telemetry()
check("D10 telemetry has total_recoveries", "total_recoveries" in telem_erg)
check("D11 telemetry has consecutive_blocks", "consecutive_blocks" in telem_erg)
check("D12 cycle_history returns list", isinstance(erg.cycle_history(5), list))


# ── AlphaContextMemory ─────────────────────────────────────────────────────────
section("TEST E — AlphaContextMemory")

acm = AlphaContextMemory.__new__(AlphaContextMemory)
import threading
acm._lock = threading.RLock()
acm._contexts = {}
acm._last_save_ts = time.time()
acm._lookup_count = 0
acm._boost_count = 0
acm._block_count = 0

# Unknown context (no trades)
r0 = acm.get_amplification("MEAN_REVERTING", 10, "MR_STRAT")
check("E01 unknown context → UNKNOWN type", r0["context_type"] == "UNKNOWN")
check("E02 unknown context → boost_mult = 1.0", r0["boost_mult"] == 1.0)

# Record 5 winning trades → profitable context
for _ in range(5):
    acm.record_outcome("MEAN_REVERTING", 10, "MR_STRAT", net_pnl=10.0)

r1 = acm.get_amplification("MEAN_REVERTING", 10, "MR_STRAT")
check("E03 5 wins → PROFITABLE type", r1["context_type"] == "PROFITABLE",
      f"type={r1['context_type']}")
check("E04 PROFITABLE → boost_mult > 1.0", r1["boost_mult"] > 1.0,
      f"mult={r1['boost_mult']}")
check("E05 PROFITABLE → boost_mult ≤ 1.5 (cap)", r1["boost_mult"] <= 1.5)
check("E06 PROFITABLE n_trades = 5", r1["n_trades"] == 5)

# Record 5 big-loss trades → toxic
acm2 = AlphaContextMemory.__new__(AlphaContextMemory)
acm2._lock = threading.RLock()
acm2._contexts = {}
acm2._last_save_ts = time.time()
acm2._lookup_count = 0
acm2._boost_count = 0
acm2._block_count = 0

for _ in range(5):
    acm2.record_outcome("TRENDING", 14, "TR_STRAT", net_pnl=-2.0)

r2 = acm2.get_amplification("TRENDING", 14, "TR_STRAT")
check("E07 5 big losses → TOXIC type", r2["context_type"] == "TOXIC",
      f"type={r2['context_type']} avg_pnl={r2['avg_pnl']}")
check("E08 TOXIC → boost_mult = 0.0", r2["boost_mult"] == 0.0)

# Neutral context (small avg_pnl, above TOXIC_THRESH)
acm3 = AlphaContextMemory.__new__(AlphaContextMemory)
acm3._lock = threading.RLock()
acm3._contexts = {}
acm3._last_save_ts = time.time()
acm3._lookup_count = 0
acm3._boost_count = 0
acm3._block_count = 0

for i in range(5):
    acm3.record_outcome("TRENDING", 14, "TR_MIX", net_pnl=-0.05)  # avg=-0.05 → above TOXIC_THRESH

r3 = acm3.get_amplification("TRENDING", 14, "TR_MIX")
check("E09 small-loss trades → NEUTRAL type (avg_pnl=-0.05 > TOXIC_THRESH -0.30)",
      r3["context_type"] == "NEUTRAL",
      f"type={r3['context_type']} avg={r3['avg_pnl']}")
check("E10 NEUTRAL → boost_mult = 1.0", r3["boost_mult"] == 1.0)

# Context key format
key = acm._contexts.get("MEAN_REVERTING|10|MR_STRAT")
check("E11 context_key format is regime|hour|strategy", key is not None)

# Telemetry
telem_acm = acm.get_telemetry()
check("E12 telemetry has total_contexts", telem_acm["total_contexts"] >= 1)
check("E13 telemetry has profitable_count", "profitable_count" in telem_acm)
check("E14 telemetry has boost_count", telem_acm["boost_count"] >= 1)
check("E15 context_clusters returns list", isinstance(acm.context_clusters(5), list))


# ── OpportunityEcology ────────────────────────────────────────────────────────
section("TEST F — OpportunityEcology")

oe = OpportunityEcology()

# RSI pass + unknown context → approved, mult=1.0
dec1 = oe.evaluate_opportunity(
    regime="MEAN_REVERTING",
    rsi_val=72.0, rsi_prev=67.0, above_sma=True,
    utc_hour=10, strategy_id="TEST_STRAT", symbol="TESTUSDT",
)
check("F01 MR SHORT approved", dec1.approved)
check("F02 approved has rsi_side=SHORT", dec1.rsi_side == "SHORT",
      f"side={dec1.rsi_side}")
check("F03 block_reason empty when approved", dec1.block_reason == "")
check("F04 context_type UNKNOWN on fresh engine", dec1.context_type == "UNKNOWN")
check("F05 size_multiplier = 1.0 for unknown context", abs(dec1.size_multiplier - 1.0) < 0.01)

# RSI block → not approved
dec2 = oe.evaluate_opportunity(
    regime="MEAN_REVERTING",
    rsi_val=50.0, rsi_prev=50.0, above_sma=True,
    utc_hour=10, strategy_id="TEST_STRAT", symbol="TESTUSDT",
)
check("F06 RSI block → not approved", not dec2.approved)
check("F07 RSI block → block_reason starts with RSI:", dec2.block_reason.startswith("RSI:"),
      f"reason={dec2.block_reason}")
check("F08 RSI block → rsi_blocked=True", dec2.rsi_blocked)
check("F09 RSI block → size_multiplier=0", dec2.size_multiplier == 0.0)

# Toxic context → not approved
oe2 = OpportunityEcology()
# Build the toxic context in alpha_context_memory
from core.signal_ecology.alpha_context_memory import AlphaContextMemory as ACM
_acm = ACM.__new__(ACM)
_acm._lock = threading.RLock()
_acm._contexts = {}
_acm._last_save_ts = time.time()
_acm._lookup_count = 0
_acm._boost_count = 0
_acm._block_count = 0
for _ in range(5):
    _acm.record_outcome("TRENDING", 10, "TOXIC_STRAT", net_pnl=-2.0)

# Inject into the singleton temporarily
import core.signal_ecology.alpha_context_memory as _acm_mod
orig_acm = _acm_mod.alpha_context_memory
_acm_mod.alpha_context_memory = _acm

# Also patch inside opportunity_ecology
import core.signal_ecology.opportunity_ecology as _oe_mod
_oe_mod.alpha_context_memory = _acm

dec3 = oe2.evaluate_opportunity(
    regime="TRENDING",
    rsi_val=45.0, rsi_prev=46.0, above_sma=True,
    utc_hour=10, strategy_id="TOXIC_STRAT", symbol="TEST",
)
check("F10 toxic context → not approved", not dec3.approved,
      f"approved={dec3.approved} ctx={dec3.context_type}")
check("F11 toxic context → CONTEXT_TOXIC in block_reason",
      "CONTEXT_TOXIC" in dec3.block_reason or dec3.context_type == "TOXIC",
      f"reason={dec3.block_reason}")
check("F12 toxic context → context_type=TOXIC", dec3.context_type == "TOXIC")

# Restore singletons
_acm_mod.alpha_context_memory = orig_acm
_oe_mod.alpha_context_memory = orig_acm

# Counters
oe3 = OpportunityEcology()
# 2 passes, 1 RSI block
oe3.evaluate_opportunity("MEAN_REVERTING", 72.0, 67.0, True, 10, "S1", "A")
oe3.evaluate_opportunity("MEAN_REVERTING", 28.0, 33.0, False, 10, "S1", "B")
oe3.evaluate_opportunity("MEAN_REVERTING", 50.0, 50.0, True, 10, "S1", "C")

check("F13 total_evaluated = 3", oe3._total_evaluated == 3)
check("F14 total_approved = 2", oe3._total_approved == 2)
check("F15 total_rsi_blocked = 1", oe3._total_rsi_blocked == 1)

# EcologyDecision has required fields
check("F16 EcologyDecision has ts", dec1.ts > 0)
check("F17 EcologyDecision has survival_rate", dec1.survival_rate >= 0)
check("F18 EcologyDecision has recovery_mode", isinstance(dec1.recovery_mode, str))

# record_trade_outcome (no error)
oe3.record_trade_outcome("MEAN_REVERTING", 10, "S1", net_pnl=5.0)
check("F19 record_trade_outcome does not raise", True)

# Telemetry
telem_oe = oe3.get_telemetry()
check("F20 telemetry has module=OpportunityEcology", telem_oe["module"] == "OpportunityEcology")
check("F21 telemetry has prp=002", telem_oe["prp"] == "002")
check("F22 telemetry has rsi_governor sub-dict", "rsi_governor" in telem_oe)
check("F23 telemetry has density_engine sub-dict", "density_engine" in telem_oe)
check("F24 telemetry has recovery sub-dict", "recovery" in telem_oe)
check("F25 telemetry has context_memory sub-dict", "context_memory" in telem_oe)

# ecology_snapshot
snap_oe = oe3.ecology_snapshot()
check("F26 ecology_snapshot has report=prp002_ecology_snapshot",
      snap_oe["report"] == "prp002_ecology_snapshot")
check("F27 ecology_snapshot has approval_rate", "approval_rate" in snap_oe)
check("F28 ecology_snapshot has is_drought", "is_drought" in snap_oe)
check("F29 ecology_snapshot has context_memory sub-dict", "context_memory" in snap_oe)

# Singleton identity preserved
from core.signal_ecology.opportunity_ecology import opportunity_ecology as oe_sg1
from core.signal_ecology.opportunity_ecology import opportunity_ecology as oe_sg2
check("F30 singleton identity preserved", oe_sg1 is oe_sg2)


# ── Integration: end-to-end flow ──────────────────────────────────────────────
section("TEST G — End-to-end ecology flow")

from core.signal_ecology.opportunity_ecology import OpportunityEcology
from core.signal_ecology.signal_density_engine import SignalDensityEngine
from core.signal_ecology.exploration_recovery import ExplorationRecoveryGovernor
from core.signal_ecology.alpha_context_memory import AlphaContextMemory
from core.signal_ecology.adaptive_rsi_governor import AdaptiveRSIGovernor

# Build isolated instances for integration test
_gov_i = AdaptiveRSIGovernor()
_de_i  = SignalDensityEngine()
_erg_i = ExplorationRecoveryGovernor()
_acm_i = AlphaContextMemory.__new__(AlphaContextMemory)
_acm_i._lock = threading.RLock()
_acm_i._contexts = {}
_acm_i._last_save_ts = time.time()
_acm_i._lookup_count = 0
_acm_i._boost_count = 0
_acm_i._block_count = 0

# Inject into a fresh OE
import core.signal_ecology.opportunity_ecology as _oe_mod2
import core.signal_ecology.signal_density_engine as _de_mod
import core.signal_ecology.exploration_recovery as _erg_mod
import core.signal_ecology.adaptive_rsi_governor as _gov_mod

_orig_gov = _gov_mod.adaptive_rsi_governor
_orig_de  = _de_mod.signal_density_engine
_orig_erg = _erg_mod.exploration_recovery_governor
_orig_acm2 = _oe_mod2.alpha_context_memory

_gov_mod.adaptive_rsi_governor = _gov_i
_de_mod.signal_density_engine  = _de_i
_erg_mod.exploration_recovery_governor = _erg_i
_oe_mod2.alpha_context_memory = _acm_i
_oe_mod2.adaptive_rsi_governor = _gov_i
_oe_mod2.signal_density_engine = _de_i
_oe_mod2.exploration_recovery_governor = _erg_i

oe_int = OpportunityEcology()

# Simulate 10 passing RSI signals
for i in range(10):
    d = oe_int.evaluate_opportunity(
        regime="MEAN_REVERTING",
        rsi_val=72.0, rsi_prev=67.0, above_sma=True,
        utc_hour=10, strategy_id="INT_STRAT", symbol=f"SYM{i}",
    )

check("G01 10 passed signals → density total_passed >= 10", _de_i._total_passed >= 10)
check("G02 10 passed signals → ecology total_approved >= 10", oe_int._total_approved >= 10)
check("G03 no recovery mode active (healthy)", oe_int._total_recovery_trades == 0)

# Simulate 20 blocked signals to build rejection loop
for i in range(20):
    oe_int.evaluate_opportunity(
        regime="MEAN_REVERTING",
        rsi_val=50.0, rsi_prev=50.0, above_sma=True,
        utc_hour=10, strategy_id="INT_STRAT", symbol="BLKSYM",
    )

check("G04 20 blocked signals → rsi_blocked >= 20", oe_int._total_rsi_blocked >= 20)
check("G05 density blocked_count updated", _de_i._total_evaluated - _de_i._total_passed >= 20)

# Record trade outcomes and verify context memory updates
for i in range(5):
    oe_int.record_trade_outcome("MEAN_REVERTING", 10, "INT_STRAT", net_pnl=5.0)

ctx_check = _acm_i.get_amplification("MEAN_REVERTING", 10, "INT_STRAT")
check("G06 after 5 winning outcomes → context is PROFITABLE",
      ctx_check["context_type"] == "PROFITABLE",
      f"type={ctx_check['context_type']}")

# Now a passing signal should get context boost
oe_int._total_evaluated = 0  # reset for clean test
d_boost = oe_int.evaluate_opportunity(
    regime="MEAN_REVERTING",
    rsi_val=72.0, rsi_prev=67.0, above_sma=True,
    utc_hour=10, strategy_id="INT_STRAT", symbol="BOOST_TEST",
)
check("G07 profitable context → approved with size_mult > 1.0",
      d_boost.approved and d_boost.size_multiplier > 1.0,
      f"approved={d_boost.approved} mult={d_boost.size_multiplier}")

# Restore singletons
_gov_mod.adaptive_rsi_governor = _orig_gov
_de_mod.signal_density_engine  = _orig_de
_erg_mod.exploration_recovery_governor = _orig_erg
_oe_mod2.alpha_context_memory = _orig_acm2
_oe_mod2.adaptive_rsi_governor = _orig_gov
_oe_mod2.signal_density_engine = _orig_de
_oe_mod2.exploration_recovery_governor = _orig_erg

check("G08 singletons restored (no error)", True)


# ── Band adaptation logic ────────────────────────────────────────────────────
section("TEST H — Band adaptation")

gov2 = AdaptiveRSIGovernor()

# Force starvation-level survival: fill window with all blocks
for _ in range(100):
    gov2._windows["MEAN_REVERTING"].append(0)

gov2._last_adapt_ts = 0.0  # force next adapt
gov2._maybe_adapt()  # trigger adaptation

bands_after = gov2.band_state()
mr_bands = bands_after["MEAN_REVERTING"]
check("H01 after starvation: MR long_rsi > 30 (relaxed)",
      mr_bands["long_rsi"] > 30.0, f"long_rsi={mr_bands['long_rsi']}")
check("H02 after starvation: MR short_rsi < 70 (relaxed)",
      mr_bands["short_rsi"] < 70.0, f"short_rsi={mr_bands['short_rsi']}")

# Adapt log populated
check("H03 adapt_log has entries", len(gov2._adapt_log) > 0)
adapt_entry = list(gov2._adapt_log)[-1]
check("H04 adapt entry has action=RELAX", adapt_entry["action"] == "RELAX")

# Reset bands works
gov2.reset_bands()
bands_reset = gov2.band_state()
check("H05 reset_bands: MR long_rsi = 30.0", bands_reset["MEAN_REVERTING"]["long_rsi"] == 30.0)
check("H06 reset_bands: MR short_rsi = 70.0", bands_reset["MEAN_REVERTING"]["short_rsi"] == 70.0)
check("H07 reset_bands: TR long_rsi = 48.0", bands_reset["TRENDING"]["long_rsi"] == 48.0)

# Tighten: fill with all passes
gov3 = AdaptiveRSIGovernor()
for _ in range(100):
    gov3._windows["TRENDING"].append(1)

gov3._last_adapt_ts = 0.0
gov3._maybe_adapt()

bands_tight = gov3.band_state()
tr_bands = bands_tight["TRENDING"]
check("H08 after glut: TR long_rsi < 48.0 (tightened)",
      tr_bands["long_rsi"] < 48.0, f"long_rsi={tr_bands['long_rsi']}")


# ── Singleton import consistency ─────────────────────────────────────────────
section("TEST I — Singleton import consistency")

from core.signal_ecology.adaptive_rsi_governor import adaptive_rsi_governor as arsg1
from core.signal_ecology.adaptive_rsi_governor import adaptive_rsi_governor as arsg2
check("I01 adaptive_rsi_governor singleton is same object", arsg1 is arsg2)

from core.signal_ecology.signal_density_engine import signal_density_engine as sde1
from core.signal_ecology.signal_density_engine import signal_density_engine as sde2
check("I02 signal_density_engine singleton is same object", sde1 is sde2)

from core.signal_ecology.exploration_recovery import exploration_recovery_governor as erg1
from core.signal_ecology.exploration_recovery import exploration_recovery_governor as erg2
check("I03 exploration_recovery_governor singleton is same object", erg1 is erg2)

from core.signal_ecology.alpha_context_memory import alpha_context_memory as acm1
from core.signal_ecology.alpha_context_memory import alpha_context_memory as acm2
check("I04 alpha_context_memory singleton is same object", acm1 is acm2)

from core.signal_ecology.opportunity_ecology import opportunity_ecology as oe1
from core.signal_ecology.opportunity_ecology import opportunity_ecology as oe2
check("I05 opportunity_ecology singleton is same object", oe1 is oe2)


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
    print(f"\n  \033[92m✓ ALL {PASS} CHECKS PASSED — PRP-002 Signal Ecology VALIDATED\033[0m\n")
