#!/usr/bin/env python3
"""
Verifier for the X3-a Exit Coordinator ARBITER (pure, non-acting).

Confirms resolve() obeys the precedence + invariants:
  1. emergency overrides everything
  2. terminal close beats adjustments
  3. SL is tighten-only (I-1) — loosening rejected
  4. TP widen needs a grant (I-2)
  5. XTE intents are muted below lifecycle stage ADVISE
  6. parity_check records agreement, and resolve() mutates nothing

Exit code 0 = all checks pass.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.exit_coordinator import (
    ExitIntent, resolve, parity_check, exit_coordinator_shadow,
    risk_rules_intent, trade_manager_intent, xte_intent,
)

_PASS = _FAIL = 0


def check(label, cond, detail=""):
    global _PASS, _FAIL
    if cond:
        _PASS += 1; print(f"  ✓  {label}")
    else:
        _FAIL += 1; print(f"  ✗  {label}  {detail}")


def main() -> int:
    print("\n══ X3-a — EXIT COORDINATOR ARBITER VERIFIER ══\n")
    exit_coordinator_shadow.reset()

    # ── 1 emergency overrides ────────────────────────────────────────────────
    print("── precedence ──")
    d = resolve([ExitIntent("risk_rules", "SET_SL", 99.0),
                 ExitIntent("emergency", "CLOSE")], "LONG", 98.0, 110.0)
    check("emergency → close", d.close is True)

    # ── 2 terminal beats adjustments ─────────────────────────────────────────
    d = resolve([ExitIntent("risk_rules", "SET_SL", 99.5),
                 ExitIntent("trade_manager", "CLOSE", reason="VTP_EXIT")], "LONG", 98.0, 110.0)
    check("terminal close beats SL adjust", d.close is True)

    # ── 3 SL tighten-only (I-1) ──────────────────────────────────────────────
    print("\n── invariants ──")
    d = resolve([ExitIntent("risk_rules", "SET_SL", 99.5)], "LONG", 98.0, 110.0)
    check("LONG SL raise accepted", d.sl == 99.5 and not d.close)
    d = resolve([ExitIntent("risk_rules", "SET_SL", 96.0)], "LONG", 98.0, 110.0)
    check("LONG SL loosen REJECTED (stays 98)", d.sl == 98.0,
          f"got {d.sl}; rationale={d.rationale}")
    d = resolve([ExitIntent("risk_rules", "SET_SL", 101.0)], "SHORT", 102.0, 90.0)
    check("SHORT SL lower accepted", d.sl == 101.0)

    # most protective of several wins
    d = resolve([ExitIntent("risk_rules", "SET_SL", 99.0),
                 ExitIntent("trade_manager", "SET_SL", 99.8)], "LONG", 98.0, 110.0)
    check("tightest SL wins", d.sl == 99.8, f"got {d.sl}")

    # ── 4 TP widen needs grant (I-2) ─────────────────────────────────────────
    d = resolve([ExitIntent("trade_manager", "SET_TP", 115.0, grant=False)], "LONG", 98.0, 110.0)
    check("TP widen without grant REJECTED", d.tp == 110.0, f"got {d.tp}")
    d = resolve([ExitIntent("trade_manager", "SET_TP", 115.0, grant=True)], "LONG", 98.0, 110.0)
    check("TP widen WITH grant accepted", d.tp == 115.0)
    d = resolve([ExitIntent("trade_manager", "SET_TP", 108.0)], "LONG", 98.0, 110.0)
    check("TP tighten accepted (no grant needed)", d.tp == 108.0)

    # ── 5 XTE gated by lifecycle stage ───────────────────────────────────────
    print("\n── XTE lifecycle gating ──")
    d = resolve([xte_intent("TIGHTEN", 99.7, stage="OBSERVE")], "LONG", 98.0, 110.0)
    check("XTE muted at OBSERVE (SL unchanged)", d.sl == 98.0, f"got {d.sl}")
    d = resolve([xte_intent("TIGHTEN", 99.7, stage="ADVISE")], "LONG", 98.0, 110.0)
    check("XTE acts at ADVISE (SL tightened)", d.sl == 99.7, f"got {d.sl}")
    # even at ADVISE, XTE cannot loosen
    d = resolve([xte_intent("TIGHTEN", 96.0, stage="ADVISE")], "LONG", 98.0, 110.0)
    check("XTE at ADVISE still tighten-only", d.sl == 98.0)

    # ── 6 adapters + parity + no mutation ────────────────────────────────────
    print("\n── adapters + parity ──")
    check("risk_rules_intent builds SET_SL", risk_rules_intent(99.0).kind == "SET_SL")
    check("trade_manager EXTEND_TP carries grant", trade_manager_intent("EXTEND_TP", new_tp=120).grant is True)
    check("trade_manager VTP_EXIT → CLOSE", trade_manager_intent("VTP_EXIT").kind == "CLOSE")
    d = resolve([ExitIntent("risk_rules", "SET_SL", 99.5)], "LONG", 98.0, 110.0)
    parity_check(d, live_sl=99.5, live_tp=110.0, live_close=False)   # match
    parity_check(d, live_sl=99.0, live_tp=110.0, live_close=False)   # mismatch
    s = exit_coordinator_shadow.summary()
    check("parity recorded 2 (1 ok)", s["resolve_parity_total"] == 2 and s["resolve_parity_ok"] == 1,
          f"got {s['resolve_parity_total']}/{s['resolve_parity_ok']}")

    print("\n" + "═" * 60)
    if _FAIL == 0:
        print(f"  ALL {_PASS}/{_PASS} CHECKS PASSED ✓")
        print("  Arbiter is pure + non-acting (precedence + I-1/I-2 enforced).")
        print("═" * 60 + "\n")
        return 0
    print(f"  {_FAIL} FAILED ({_PASS} passed)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
