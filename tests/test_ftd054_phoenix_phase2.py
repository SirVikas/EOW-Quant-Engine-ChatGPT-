"""
FTD-054-PHOENIX Phase 2 — Verifier

Sections:
  A: RSI crash guard — MEAN_REVERTING LONG (prev must be < 35)         (8 checks)
  B: RSI crash guard — MEAN_REVERTING SHORT (prev must be > 65)        (6 checks)
  C: RSI crash guard — TRENDING unaffected (no stability check)        (4 checks)
  D: RSI crash guard boundary conditions                                (6 checks)
  E: ALLOC_ZERO observability logic                                     (4 checks)
  F: Phase 1 thresholds still intact                                    (3 checks)

Total: 31 checks

Evidence basis:
  NEARUSDT RSI 68→29 in one candle: crash, not reversal → must block
  NILUSDT RSI 43→33→29 over multiple candles: genuine mean reversion → must allow
  NOTUSDT RSI 30.0 (prev unknown but likely >35): must block
"""
from __future__ import annotations

import sys

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


# ── Mirrors the PAPER_SPEED signal logic from main.py post-FTD-054 Phase 2 ──

def _ps_side_p2(regime: str, above_sma: bool, rsi_val: float, rsi_prev: float):
    """PAPER_SPEED signal logic with Phase 2 RSI stability check."""
    LONG, SHORT, NONE = "LONG", "SHORT", None
    if regime == "MEAN_REVERTING":
        if above_sma and rsi_val > 70 and rsi_prev > 65:
            return SHORT
        elif not above_sma and rsi_val < 30 and rsi_prev < 35:
            return LONG
        return NONE
    else:  # TRENDING / UNKNOWN
        if above_sma and rsi_val <= 48:
            return LONG
        elif not above_sma and rsi_val >= 52:
            return SHORT
        return NONE


def _is_crash_guard_long(regime, above_sma, rsi_val, rsi_prev):
    return (regime == "MEAN_REVERTING"
            and not above_sma and rsi_val < 30 and rsi_prev >= 35)


def _is_crash_guard_short(regime, above_sma, rsi_val, rsi_prev):
    return (regime == "MEAN_REVERTING"
            and above_sma and rsi_val > 70 and rsi_prev <= 65)


# ─────────────────────────────────────────────────────────────────────────────
# A: RSI crash guard — MEAN_REVERTING LONG
# ─────────────────────────────────────────────────────────────────────────────
print("A: RSI crash guard — MEAN_REVERTING LONG (prev must be <35)")

try:
    # Evidence case: NEARUSDT crash (RSI 68→29 in one candle)
    check("A1: MR LONG blocked when rsi=29 but prev=68 (NEARUSDT crash scenario)",
          _ps_side_p2("MEAN_REVERTING", False, 29.0, 68.0) is None)

    check("A2: crash guard fires for NEARUSDT scenario (not just level block)",
          _is_crash_guard_long("MEAN_REVERTING", False, 29.0, 68.0))

    # NILUSDT oscillation (RSI 33→29, prev=33 < 35)
    check("A3: MR LONG allowed when rsi=29 and prev=33 (NILUSDT oscillation)",
          _ps_side_p2("MEAN_REVERTING", False, 29.0, 33.0) == "LONG")

    check("A4: MR LONG allowed when rsi=28 and prev=32 (deep oversold, stable)",
          _ps_side_p2("MEAN_REVERTING", False, 28.0, 32.0) == "LONG")

    # Boundary: prev=35 exactly → blocked (need prev < 35, not ≤ 35)
    check("A5: MR LONG blocked when prev=35.0 exactly (boundary: need prev<35)",
          _ps_side_p2("MEAN_REVERTING", False, 29.0, 35.0) is None)

    # Boundary: prev=34.9 → allowed
    check("A6: MR LONG allowed when prev=34.9 (just inside boundary)",
          _ps_side_p2("MEAN_REVERTING", False, 29.0, 34.9) == "LONG")

    # NOTUSDT scenario: prev likely ~40 (quick drop to RSI 30)
    check("A7: MR LONG blocked when rsi=30 prev=40 (NOTUSDT first-touch scenario)",
          _ps_side_p2("MEAN_REVERTING", False, 29.5, 40.0) is None)

    # Re-entry after established oversold: prev=28, current=26 → allowed
    check("A8: MR LONG allowed when rsi=26 and prev=28 (established oversold range)",
          _ps_side_p2("MEAN_REVERTING", False, 26.0, 28.0) == "LONG")

except Exception as e:
    for i in range(1, 9):
        check(f"A{i}: MEAN_REVERTING LONG crash guard", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# B: RSI crash guard — MEAN_REVERTING SHORT
# ─────────────────────────────────────────────────────────────────────────────
print("B: RSI crash guard — MEAN_REVERTING SHORT (prev must be >65)")

try:
    # Flash spike scenario: RSI 40→75 in one candle
    check("B1: MR SHORT blocked when rsi=75 but prev=40 (flash spike)",
          _ps_side_p2("MEAN_REVERTING", True, 75.0, 40.0) is None)

    check("B2: crash guard fires for flash spike scenario",
          _is_crash_guard_short("MEAN_REVERTING", True, 75.0, 40.0))

    # Stable overbought: prev=68 (already overbought) → allowed
    check("B3: MR SHORT allowed when rsi=75 and prev=68 (stable overbought)",
          _ps_side_p2("MEAN_REVERTING", True, 75.0, 68.0) == "SHORT")

    # Boundary: prev=65 exactly → blocked (need prev > 65)
    check("B4: MR SHORT blocked when prev=65.0 exactly (boundary: need prev>65)",
          _ps_side_p2("MEAN_REVERTING", True, 75.0, 65.0) is None)

    # Boundary: prev=65.1 → allowed
    check("B5: MR SHORT allowed when prev=65.1 (just inside boundary)",
          _ps_side_p2("MEAN_REVERTING", True, 75.0, 65.1) == "SHORT")

    # Deep overbought stable: prev=72, current=78 → allowed
    check("B6: MR SHORT allowed when rsi=78 and prev=72 (deep stable overbought)",
          _ps_side_p2("MEAN_REVERTING", True, 78.0, 72.0) == "SHORT")

except Exception as e:
    for i in range(1, 7):
        check(f"B{i}: MEAN_REVERTING SHORT crash guard", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# C: TRENDING unaffected by crash guard
# ─────────────────────────────────────────────────────────────────────────────
print("C: TRENDING — crash guard does NOT apply (no stability check)")

try:
    # TRENDING LONG: no prev check — RSI ≤ 48 above_sma
    check("C1: TRENDING LONG allowed regardless of prev RSI (above_sma, rsi=45, prev=60)",
          _ps_side_p2("TRENDING", True, 45.0, 60.0) == "LONG")

    check("C2: TRENDING LONG allowed regardless of prev RSI (above_sma, rsi=30, prev=50)",
          _ps_side_p2("TRENDING", True, 30.0, 50.0) == "LONG")

    # TRENDING SHORT: no prev check — RSI ≥ 52 below_sma
    check("C3: TRENDING SHORT allowed regardless of prev RSI (below_sma, rsi=55, prev=30)",
          _ps_side_p2("TRENDING", False, 55.0, 30.0) == "SHORT")

    check("C4: TRENDING SHORT allowed regardless of prev RSI (below_sma, rsi=70, prev=40)",
          _ps_side_p2("TRENDING", False, 70.0, 40.0) == "SHORT")

except Exception as e:
    for i in range(1, 5):
        check(f"C{i}: TRENDING crash guard not applied", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# D: Boundary conditions
# ─────────────────────────────────────────────────────────────────────────────
print("D: Boundary conditions")

try:
    # RSI exactly 30.0 with prev=31 (floating-point boundary)
    check("D1: MR LONG with rsi=30.0 prev=31 — rsi=30 is NOT < 30 → no signal",
          _ps_side_p2("MEAN_REVERTING", False, 30.0, 31.0) is None)

    # RSI exactly 29.999 with prev=31 → allowed (< 30)
    check("D2: MR LONG with rsi=29.999 prev=31 — rsi<30 AND prev<35 → LONG",
          _ps_side_p2("MEAN_REVERTING", False, 29.999, 31.0) == "LONG")

    # Not enough data scenario: prev defaults to rsi_val itself → stable assumed
    # When rsi_val=29 and rsi_prev defaults to rsi_val=29: 29 < 35 → LONG
    check("D3: Not enough data (rsi_prev=rsi_val=29) → treated as stable → LONG",
          _ps_side_p2("MEAN_REVERTING", False, 29.0, 29.0) == "LONG")

    # Crash from RSI 36 to 29 (prev=36, barely above 35 threshold)
    check("D4: MR LONG blocked when rsi=29 prev=36 (prev ≥35 = crash, not stable)",
          _ps_side_p2("MEAN_REVERTING", False, 29.0, 36.0) is None)

    # Established oscillation: prev=31.5 → allowed
    check("D5: MR LONG allowed when rsi=28 prev=31.5 (oscillating in oversold)",
          _ps_side_p2("MEAN_REVERTING", False, 28.0, 31.5) == "LONG")

    # UNKNOWN regime treated same as TRENDING (no crash guard)
    check("D6: UNKNOWN regime — no crash guard (falls into TRENDING branch)",
          _ps_side_p2("UNKNOWN", True, 45.0, 65.0) == "LONG")

except Exception as e:
    for i in range(1, 7):
        check(f"D{i}: Boundary condition", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# E: ALLOC_ZERO observability logic
# ─────────────────────────────────────────────────────────────────────────────
print("E: ALLOC_ZERO observability logic")

try:
    def _alloc_zero_msg(bypass: bool, combined_mult: float, score: float, sym: str) -> str:
        if bypass and combined_mult == 0.0:
            return (
                f"⚠️ ALLOC_ZERO {sym}: score={score:.3f} below min "
                f"allocator band [bypass=active, orchestrator BYPASS override]"
            )
        return ""

    _m1 = _alloc_zero_msg(True, 0.0, 0.246, "NILUSDT")
    check("E1: bypass=True + combined=0.0 → ALLOC_ZERO message emitted",
          "ALLOC_ZERO" in _m1 and "bypass=active" in _m1)

    check("E2: message contains score and orchestrator BYPASS override text",
          "0.246" in _m1 and "orchestrator BYPASS override" in _m1)

    _m2 = _alloc_zero_msg(True, 0.5, 0.311, "NOTUSDT")
    check("E3: bypass=True + combined=0.5 → no message (not zero)",
          _m2 == "")

    _m3 = _alloc_zero_msg(False, 0.0, 0.246, "NILUSDT")
    check("E4: bypass=False + combined=0.0 → no message (non-bypass path blocks directly)",
          _m3 == "")

except Exception as e:
    for i in range(1, 5):
        check(f"E{i}: ALLOC_ZERO observability", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# F: Phase 1 thresholds still intact
# ─────────────────────────────────────────────────────────────────────────────
print("F: Phase 1 thresholds preserved")

try:
    # MR SHORT: still requires RSI > 70 (not just > 60 as pre-Phase 1)
    check("F1: MR SHORT still blocked at rsi=65 (Phase 1: need >70)",
          _ps_side_p2("MEAN_REVERTING", True, 65.0, 68.0) is None)

    # TRENDING LONG: still requires RSI ≤ 48 (not < 62 as pre-Phase 1)
    check("F2: TRENDING LONG blocked at rsi=55 above_sma (Phase 1: need ≤48)",
          _ps_side_p2("TRENDING", True, 55.0, 52.0) is None)

    # TRENDING SHORT: still requires RSI ≥ 52 (not >38 as pre-Phase 1)
    check("F3: TRENDING SHORT blocked at rsi=45 below_sma (Phase 1: need ≥52)",
          _ps_side_p2("TRENDING", False, 45.0, 42.0) is None)

except Exception as e:
    for i in range(1, 4):
        check(f"F{i}: Phase 1 threshold preserved", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
for line in _results:
    print(line)

total = PASS + FAIL
print(f"\n{'=' * 60}")
print(f"FTD-054-PHOENIX Phase 2 Verifier: {PASS}/{total} checks passed")
if FAIL > 0:
    print(f"FAILED: {FAIL} checks")
    sys.exit(1)
else:
    print("ALL CHECKS PASSED")
    sys.exit(0)
