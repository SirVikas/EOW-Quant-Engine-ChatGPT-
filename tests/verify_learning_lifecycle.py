#!/usr/bin/env python3
"""
Verifier for Learning Lifecycle Governance (GAP-H1 + D1/D2/D3).

Confirms (no live engine):
  1. advisor registers in OBSERVE
  2. auto-advances OBSERVE→VALIDATE when sample target met (D1 campaign)
  3. completion trigger fires at target (D2)
  4. auto-advances VALIDATE→APPROVE on CANDIDATE verdict
  5. does NOT auto-enter an acting stage; requires explicit approval (D3 framework)
  6. approval promotes into ADVISE

Uses a manual (non-XTE) advisor so metrics are injectable.
Exit code 0 = all checks pass.
"""
from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import core.governance.learning_lifecycle as ll

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


def main() -> int:
    print("\n══ GAP-H1 — LEARNING LIFECYCLE VERIFIER ══\n")
    # isolate persistence
    tmp = tempfile.mkdtemp(prefix="lifecycle_")
    ll._STATE_PATH = os.path.join(tmp, "lifecycle.json")
    lc = ll.LearningLifecycle()
    lc.reset()

    NAME = "TEST_ADVISOR"
    lc.register(NAME, sample_target=500)
    check("registers in OBSERVE", lc.eligibility(NAME)["current_stage"] == "OBSERVE")

    # ── below target: no advance, campaign incomplete ────────────────────────
    print("\n── below target ──")
    lc.record_metrics(NAME, samples=120)
    lc.advance(NAME)
    check("stays in OBSERVE below target", lc._advisors[NAME]["stage"] == "OBSERVE")
    cs = lc.campaign_status(NAME)
    check("campaign progress reported", cs["progress_pct"] == 24.0, f"got {cs['progress_pct']}")
    check("campaign not complete", cs["complete"] is False)

    # ── target met: auto-advance + completion trigger ────────────────────────
    print("\n── target met (D1/D2) ──")
    lc.record_metrics(NAME, samples=500)
    cs = lc.campaign_status(NAME)
    check("completion trigger fires at target", cs["complete"] is True)
    check("completion timestamp set", cs["completion_ts"] is not None)
    lc.advance(NAME)
    check("auto-advances OBSERVE→VALIDATE", lc._advisors[NAME]["stage"] == "VALIDATE")

    # ── CANDIDATE verdict: advance to APPROVE ────────────────────────────────
    print("\n── verdict CANDIDATE ──")
    lc.record_metrics(NAME, verdict_status="CANDIDATE")
    lc.advance(NAME)
    check("auto-advances VALIDATE→APPROVE", lc._advisors[NAME]["stage"] == "APPROVE")

    # ── acting stage requires approval (D3) ──────────────────────────────────
    print("\n── acting stage gated by approval (D3) ──")
    e = lc.eligibility(NAME)
    check("next stage is ADVISE", e["next_stage"] == "ADVISE")
    check("ADVISE requires_approval True", e["requires_approval"] is True)
    check("ADVISE not yet met (no approval)", e["criteria_met"] is False)
    lc.advance(NAME)
    check("does NOT auto-enter ADVISE", lc._advisors[NAME]["stage"] == "APPROVE")

    # explicit approval promotes
    res = lc.approve(NAME, "ADVISE", approver="operator", note="validated uplift")
    check("approval promotes to ADVISE", res["stage"] == "ADVISE", f"got {res['stage']}")
    check("approval recorded", len(lc._advisors[NAME]["approvals"]) == 1)

    # ── summary shape ────────────────────────────────────────────────────────
    print("\n── summary ──")
    s = lc.summary()
    check("summary lists STAGES", s["stages"] == ll.STAGES)
    check("summary includes advisor", NAME in s["advisors"])
    check("acting_stages disclosed", "ADVISE" in s["acting_stages"])

    print("\n" + "═" * 60)
    if _FAIL == 0:
        print(f"  ALL {_PASS}/{_PASS} CHECKS PASSED ✓")
        print("  Learning Lifecycle governs without acting (human-gated acting stages).")
        print("═" * 60 + "\n")
        return 0
    print(f"  {_FAIL} CHECK(S) FAILED ({_PASS} passed)")
    print("═" * 60 + "\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
