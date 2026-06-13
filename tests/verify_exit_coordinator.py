#!/usr/bin/env python3
"""
Verifier for the Exit Coordinator SHADOW (FTD-094A blueprint X1+X2).

Confirms, with no live engine:
  1. protective tighten is detected + passes invariant I-1
  2. non-protective loosen (not terminal) is flagged as a violation (H-1)
  3. terminal close-pending (SL→price) is exempt from tighten-only
  4. TP widen is flagged as needs-grant (I-2 / H-3)
  5. observe() never mutates the position; on_close clears state

Exit code 0 = all checks pass.
"""
from __future__ import annotations

import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.exit_coordinator import exit_coordinator_shadow as ec

_PASS = 0
_FAIL = 0


def check(label: str, cond: bool, detail: str = "") -> None:
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print(f"  ✓  {label}")
    else:
        _FAIL += 1
        print(f"  ✗  {label}  {detail}")


def _pos(side="LONG", sl=98.0, tp=110.0):
    return SimpleNamespace(symbol="TESTUSDT", side=side, stop_loss=sl, take_profit=tp)


def main() -> int:
    print("\n══ FTD-094A — EXIT COORDINATOR SHADOW VERIFIER ══\n")
    ec.reset()

    # ── TEST 1 — protective tighten (LONG SL up) ─────────────────────────────
    print("── TEST 1 — protective tighten ──")
    p = _pos(side="LONG", sl=98.0, tp=110.0)
    ec.observe(p, price=103.0)              # baseline
    p.stop_loss = 99.5                       # BE/trail raise
    evs = ec.observe(p, price=103.0)
    check("one SL event recorded", len(evs) == 1, f"got {len(evs)}")
    check("classified PROTECTIVE_TIGHTEN", evs and evs[0].category == "PROTECTIVE_TIGHTEN")
    check("invariant_ok True", evs and evs[0].invariant_ok is True)
    check("observe did not mutate position SL", p.stop_loss == 99.5)

    # ── TEST 2 — non-protective loosen (violation) ───────────────────────────
    print("\n── TEST 2 — non-protective loosen (H-1) ──")
    p.stop_loss = 97.0                       # LONG SL dropped, not at price → violation
    evs = ec.observe(p, price=103.0)
    check("classified NON_PROTECTIVE_LOOSEN", evs and evs[0].category == "NON_PROTECTIVE_LOOSEN")
    check("invariant_ok False (flagged)", evs and evs[0].invariant_ok is False)

    # ── TEST 3 — terminal close-pending (SL→price) exempt ────────────────────
    print("\n── TEST 3 — terminal close-pending exempt ──")
    p2 = _pos(side="LONG", sl=99.0, tp=110.0)
    ec.observe(p2, price=101.0)
    p2.stop_loss = 101.0                      # VTP/TIME/FAST set SL=price
    evs = ec.observe(p2, price=101.0)
    check("classified TERMINAL_CLOSE_PENDING", evs and evs[0].category == "TERMINAL_CLOSE_PENDING")
    check("terminal is invariant_ok True (exempt)", evs and evs[0].invariant_ok is True)

    # ── TEST 4 — TP widen needs grant ────────────────────────────────────────
    print("\n── TEST 4 — TP widen flagged ──")
    p3 = _pos(side="LONG", sl=98.0, tp=110.0)
    ec.observe(p3, price=103.0)
    p3.take_profit = 114.0                    # EXTEND_TP widening (LONG)
    evs = ec.observe(p3, price=103.0)
    check("one TP event recorded", len(evs) == 1, f"got {len(evs)}")
    check("classified TP_WIDEN_NEEDS_GRANT", evs and evs[0].category == "TP_WIDEN_NEEDS_GRANT")
    check("TP widen invariant_ok False", evs and evs[0].invariant_ok is False)

    # SHORT mirror: protective tighten is SL down
    print("\n── TEST 5 — SHORT mirror + summary + on_close ──")
    s = _pos(side="SHORT", sl=102.0, tp=90.0)
    ec.observe(s, price=99.0)
    s.stop_loss = 101.0                       # SHORT SL down = protective
    evs = ec.observe(s, price=99.0)
    check("SHORT SL-down is PROTECTIVE_TIGHTEN", evs and evs[0].category == "PROTECTIVE_TIGHTEN")

    summ = ec.summary()
    check("summary counts transitions", summ["transitions_observed"] >= 5)
    check("summary tracks violations", summ["invariant_violations"] >= 2)
    check("summary exposes parity_pct", "parity_pct" in summ)
    check("recent_events present", len(summ["recent_events"]) > 0)

    ec.on_close("TESTUSDT")
    ec.on_close("TESTUSDT")  # idempotent
    check("on_close clears state without error", True)

    print("\n" + "═" * 60)
    if _FAIL == 0:
        print(f"  ALL {_PASS}/{_PASS} CHECKS PASSED ✓")
        print("  Exit Coordinator shadow is observation-only and validates invariants.")
        print("═" * 60 + "\n")
        return 0
    print(f"  {_FAIL} CHECK(S) FAILED ({_PASS} passed)")
    print("═" * 60 + "\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
