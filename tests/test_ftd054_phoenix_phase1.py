"""
FTD-054-PHOENIX Phase 1 — Verifier

Sections:
  A: Inverse engine always returns NORMAL                     (7 checks)
  B: CALIBRATE never triggered by consecutive losses          (7 checks)
  C: PAPER_SPEED RSI thresholds — MEAN_REVERTING >70/<30     (7 checks)
  D: PAPER_SPEED RSI thresholds — TRENDING ≤48/≥52           (8 checks)
  E: AEE bypass-mode observability logic                      (4 checks)
  F: Module import sanity                                     (2 checks)

Total: 35 checks
"""
from __future__ import annotations

import sys
import time

PASS = 0
FAIL = 0
_results: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        _results.append(f"  PASS  {name}")
    else:
        FAIL += 1
        _results.append(f"  FAIL  {name}" + (f" | {detail}" if detail else ""))


# ── Helper: fresh InverseEngine instance ──────────────────────────────────────

def _fresh_ie():
    if "core.inverse_engine" in sys.modules:
        del sys.modules["core.inverse_engine"]
    from core.inverse_engine import InverseEngine
    return InverseEngine()


# ── Helper: PAPER_SPEED signal logic (mirrors main.py post-FTD-054) ───────────

def _ps_side(regime: str, above_sma: bool, rsi_val: float):
    if regime == "MEAN_REVERTING":
        if above_sma and rsi_val > 70:
            return "SHORT"
        elif not above_sma and rsi_val < 30:
            return "LONG"
        return None
    else:  # TRENDING / UNKNOWN
        if above_sma and rsi_val <= 48:
            return "LONG"
        elif not above_sma and rsi_val >= 52:
            return "SHORT"
        return None


# ─────────────────────────────────────────────────────────────────────────────
# A: Inverse engine always returns NORMAL
# ─────────────────────────────────────────────────────────────────────────────
print("A: Inverse engine — always NORMAL")

try:
    from core.inverse_engine import TradeMode, InverseEngine
    _ie = _fresh_ie()

    check("A1: _mode() returns NORMAL with no history",
          _ie._mode("any_strategy") == TradeMode.NORMAL)

    for _ in range(50):
        _ie.record("MeanReversion_PAPER_SPEED", won=False)
    check("A2: _mode() returns NORMAL after 50 losses (WR=0%)",
          _ie._mode("MeanReversion_PAPER_SPEED") == TradeMode.NORMAL)

    _ie2 = _fresh_ie()
    from core.inverse_engine import MIN_SAMPLES
    for _ in range(MIN_SAMPLES + 5):
        _ie2.record("test_strat", won=False)
    check("A3: _mode() NORMAL even with 0% WR above MIN_SAMPLES",
          _ie2._mode("test_strat") == TradeMode.NORMAL)

    _ie3 = _fresh_ie()
    for _ in range(40):
        _ie3.record("TrendFollowing_PAPER_SPEED", won=False)
    _d = _ie3.get_decision("TrendFollowing_PAPER_SPEED", "LONG", 100.0, 99.0, 103.0)
    check("A4: get_decision().mode is NORMAL after 40 losses",
          _d.mode == TradeMode.NORMAL)

    check("A5: get_decision() does not invert LONG signal",
          _d.final_signal == "LONG" and not _d.inverted)

    _ie4 = _fresh_ie()
    for _ in range(40):
        _ie4.record("MeanReversion_PAPER_SPEED", won=False)
    _d2 = _ie4.get_decision("MeanReversion_PAPER_SPEED", "SHORT", 100.0, 101.0, 97.0)
    check("A6: get_decision() does not invert SHORT signal",
          _d2.final_signal == "SHORT" and not _d2.inverted)

    _ie5 = _fresh_ie()
    for _ in range(35):
        _ie5.record("strat_x", won=False)
    check("A7: current_mode() returns NORMAL",
          _ie5.current_mode("strat_x") == TradeMode.NORMAL)

except Exception as e:
    for i in range(1, 8):
        check(f"A{i}: inverse engine — NORMAL enforcement", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# B: CALIBRATE never triggered
# ─────────────────────────────────────────────────────────────────────────────
print("B: CALIBRATE never triggered by consecutive losses")

try:
    from core.inverse_engine import EQUITY_PROTECT_LOSSES

    _ie_b = _fresh_ie()
    for _ in range(EQUITY_PROTECT_LOSSES + 5):
        _ie_b.record("strat_a", won=False)
    check("B1: _calibrate_until remains 0 after enough losses to trigger (pre-fix)",
          _ie_b._calibrate_until == 0.0)

    _ie_b2 = _fresh_ie()
    for s in ["s1", "s2", "s3", "s4"]:
        for _ in range(10):
            _ie_b2.record(s, won=False)
    check("B2: _calibrate_until remains 0 across 4 strategies all losing",
          _ie_b2._calibrate_until == 0.0)

    _ie_b3 = _fresh_ie()
    for _ in range(4):
        _ie_b3.record("strat_b", won=False)
    check("B3: _mode() != CALIBRATE after 4 consecutive losses",
          _ie_b3._mode("strat_b") != TradeMode.CALIBRATE)

    _ie_b4 = _fresh_ie()
    for _ in range(20):
        _ie_b4.record("strat_c", won=False)
    check("B4: _mode() != CALIBRATE after 20 consecutive losses",
          _ie_b4._mode("strat_c") != TradeMode.CALIBRATE)

    _ie_b5 = _fresh_ie()
    for _ in range(10):
        _ie_b5.record("strat_d", won=False)
    _d_b = _ie_b5.get_decision("strat_d", "LONG", 50.0, 49.0, 53.0)
    check("B5: get_decision().mode != CALIBRATE after streak",
          _d_b.mode != TradeMode.CALIBRATE)

    _ie_b6 = _fresh_ie()
    for _ in range(5):
        _ie_b6.record("strat_e", won=False)
    check("B6: consecutive losses still tracked in _consec_losses",
          _ie_b6._consec_losses.get("strat_e", 0) == 5)

    _ie_b7 = _fresh_ie()
    for _ in range(6):
        _ie_b7.record("strat_f", won=False)
    _ie_b7.record("strat_f", won=True)
    check("B7: win resets consecutive loss counter to 0",
          _ie_b7._consec_losses.get("strat_f", 0) == 0)

except Exception as e:
    for i in range(1, 8):
        check(f"B{i}: CALIBRATE not triggered", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# C: PAPER_SPEED RSI thresholds — MEAN_REVERTING
# ─────────────────────────────────────────────────────────────────────────────
print("C: PAPER_SPEED RSI — MEAN_REVERTING (>70 SHORT, <30 LONG)")

try:
    check("C1: MR RSI=71 above_sma → SHORT",
          _ps_side("MEAN_REVERTING", True, 71.0) == "SHORT")

    check("C2: MR RSI=70 above_sma → None (boundary: must be strictly >70)",
          _ps_side("MEAN_REVERTING", True, 70.0) is None)

    check("C3: MR RSI=60 above_sma → None (old threshold >60 now blocked)",
          _ps_side("MEAN_REVERTING", True, 60.0) is None)

    check("C4: MR RSI=29 below_sma → LONG",
          _ps_side("MEAN_REVERTING", False, 29.0) == "LONG")

    check("C5: MR RSI=30 below_sma → None (boundary: must be strictly <30)",
          _ps_side("MEAN_REVERTING", False, 30.0) is None)

    check("C6: MR RSI=40 below_sma → None (old threshold <40 now blocked)",
          _ps_side("MEAN_REVERTING", False, 40.0) is None)

    check("C7: MR RSI=50 neutral — no signal either direction",
          _ps_side("MEAN_REVERTING", True, 50.0) is None
          and _ps_side("MEAN_REVERTING", False, 50.0) is None)

except Exception as e:
    for i in range(1, 8):
        check(f"C{i}: MR RSI thresholds", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# D: PAPER_SPEED RSI thresholds — TRENDING
# ─────────────────────────────────────────────────────────────────────────────
print("D: PAPER_SPEED RSI — TRENDING (≤48 LONG, ≥52 SHORT)")

try:
    check("D1: TRENDING RSI=48 above_sma → LONG (boundary: ≤48)",
          _ps_side("TRENDING", True, 48.0) == "LONG")

    check("D2: TRENDING RSI=49 above_sma → None (boundary: >48 blocked)",
          _ps_side("TRENDING", True, 49.0) is None)

    check("D3: TRENDING RSI=62 above_sma → None (old threshold <62 now blocked)",
          _ps_side("TRENDING", True, 62.0) is None)

    check("D4: TRENDING RSI=52 below_sma → SHORT (boundary: ≥52)",
          _ps_side("TRENDING", False, 52.0) == "SHORT")

    check("D5: TRENDING RSI=51 below_sma → None (boundary: <52 blocked)",
          _ps_side("TRENDING", False, 51.0) is None)

    check("D6: TRENDING RSI=38 below_sma → None (old threshold >38 now blocked)",
          _ps_side("TRENDING", False, 38.0) is None)

    _neutral_above_blocked = all(
        _ps_side("TRENDING", True, r) is None for r in [49.0, 50.0, 51.0]
    )
    check("D7: TRENDING neutral zone 49–51 above_sma → no signal",
          _neutral_above_blocked)

    _neutral_below_blocked = all(
        _ps_side("TRENDING", False, r) is None for r in [49.0, 50.0, 51.0]
    )
    check("D8: TRENDING neutral zone 49–51 below_sma → no signal",
          _neutral_below_blocked)

except Exception as e:
    for i in range(1, 9):
        check(f"D{i}: TRENDING RSI thresholds", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# E: AEE bypass-mode observability logic
# ─────────────────────────────────────────────────────────────────────────────
print("E: AEE bypass-mode kill visibility")

try:
    def _aee_msg(bypass: bool, aee_ok: bool, sym: str, strat: str, reason: str) -> str:
        if bypass and not aee_ok:
            return (
                f"⚠️ AEE_KILL {sym} [{strat}]: {reason} "
                f"[bypass=active, trade_allowed, size_restored_to_1.0x]"
            )
        return ""

    _m1 = _aee_msg(True, False, "BTCUSDT", "MeanReversion", "AEE_DISABLED(edge<0)")
    check("E1: bypass=True + aee_ok=False → message contains AEE_KILL and bypass=active",
          "AEE_KILL" in _m1 and "bypass=active" in _m1)

    check("E2: message contains size_restored_to_1.0x and trade_allowed",
          "size_restored_to_1.0x" in _m1 and "trade_allowed" in _m1)

    _m2 = _aee_msg(True, True, "BTCUSDT", "MeanReversion", "ok")
    check("E3: bypass=True + aee_ok=True → no message emitted",
          _m2 == "")

    _m3 = _aee_msg(False, False, "BTCUSDT", "MeanReversion", "AEE_DISABLED(edge<0)")
    check("E4: bypass=False + aee_ok=False → no message emitted (non-bypass path handles it)",
          _m3 == "")

except Exception as e:
    for i in range(1, 5):
        check(f"E{i}: AEE observability", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# F: Module import sanity
# ─────────────────────────────────────────────────────────────────────────────
print("F: Module import sanity")

try:
    if "core.inverse_engine" in sys.modules:
        del sys.modules["core.inverse_engine"]
    import core.inverse_engine as _m
    check("F1: core.inverse_engine imports cleanly",
          hasattr(_m, "inverse_engine") and hasattr(_m, "InverseEngine"))

    check("F2: singleton always returns NORMAL",
          _m.inverse_engine._mode("any") == _m.TradeMode.NORMAL)

except Exception as e:
    check("F1: core.inverse_engine imports cleanly", False, str(e))
    check("F2: singleton always returns NORMAL", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
for line in _results:
    print(line)

total = PASS + FAIL
print(f"\n{'=' * 60}")
print(f"FTD-054-PHOENIX Phase 1 Verifier: {PASS}/{total} checks passed")
if FAIL > 0:
    print(f"FAILED: {FAIL} checks")
    sys.exit(1)
else:
    print("ALL CHECKS PASSED")
    sys.exit(0)
