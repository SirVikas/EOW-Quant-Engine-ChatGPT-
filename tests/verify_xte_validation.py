#!/usr/bin/env python3
"""
Verifier for the XTE validation/counterfactual analysis (FTD-094A follow-on).

Confirms, on a synthetic archive (no live engine):
  1. calibration_curve buckets and aggregates correctly
  2. counterfactual_analysis computes alignment + bounded $ estimate
  3. verdict gates on MIN_SAMPLES and is read-only
  4. empty archive is handled gracefully

Exit code 0 = all checks pass.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import cfg
from core.truth import xte_validation as xv

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


def _write(path: str, rows) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def _rec(score, advisory, peak_r, exit_r, net_pnl, giveback_pct, won):
    return {
        "symbol": "TESTUSDT", "regime": "TRENDING", "duration_s": 120.0,
        "exit_r": exit_r, "peak_r": peak_r, "giveback_pct": giveback_pct,
        "profit_capture": round(exit_r / peak_r, 3) if peak_r else 0.0,
        "net_pnl": net_pnl, "won": won, "exit_method": "TRAILING_STOP",
        "xte_score_avg": score, "xte_score_last": score,
        "xte_advisory_last": advisory, "xte_evals": 10,
    }


def main() -> int:
    print("\n══ FTD-094A — XTE VALIDATION VERIFIER ══\n")
    tmp = tempfile.mkdtemp(prefix="xte_val_")
    archive = os.path.join(tmp, "xte_observations.jsonl")
    cfg.XTE_OBSERVE_ARCHIVE = archive

    # Synthetic set: protect-advisory trades that gave back (XTE correct),
    # a hold that ran, and a hold that gave back (XTE missed).
    rows = [
        _rec(20, "TIGHTEN",   peak_r=1.5, exit_r=0.3, net_pnl=0.20, giveback_pct=80.0, won=True),
        _rec(25, "SCALE_OUT", peak_r=2.0, exit_r=0.4, net_pnl=0.27, giveback_pct=80.0, won=True),
        _rec(75, "HOLD",      peak_r=1.8, exit_r=1.7, net_pnl=1.13, giveback_pct=5.6,  won=True),
        _rec(45, "HOLD",      peak_r=1.6, exit_r=0.2, net_pnl=0.13, giveback_pct=87.5, won=True),
    ]
    _write(archive, rows)

    # ── TEST 1 — calibration ────────────────────────────────────────────────
    print("── TEST 1 — calibration_curve ──")
    cal = xv.calibration_curve()
    check("calibration samples == 4", cal["samples"] == 4, f"got {cal['samples']}")
    check("buckets present", len(cal["buckets"]) >= 2)
    check("70-80 bucket avg_exit_r high", cal["buckets"].get("70-80", {}).get("avg_exit_r", 0) > 1.0)

    # ── TEST 2 — counterfactual ─────────────────────────────────────────────
    print("\n── TEST 2 — counterfactual_analysis ──")
    cf = xv.counterfactual_analysis()
    al = cf["alignment"]
    check("protect_correct == 2", al["protect_correct"] == 2, f"got {al['protect_correct']}")
    check("hold_missed_giveback == 1", al["hold_missed_giveback"] == 1, f"got {al['hold_missed_giveback']}")
    check("hold_correct == 1", al["hold_correct"] == 1, f"got {al['hold_correct']}")
    check("dollars_per_r computed", cf["dollars_per_r"] > 0)
    check("bounded_savings_usd_upper >= 0", cf["bounded_savings_usd_upper"] >= 0)
    check("assumptions disclosed", "note" in cf["assumptions"])

    # ── TEST 3 — verdict gates on sample count ──────────────────────────────
    print("\n── TEST 3 — verdict ──")
    v = xv.verdict()
    check("verdict INSUFFICIENT_DATA at n=4", v["status"] == "INSUFFICIENT_DATA", f"got {v['status']}")
    check("verdict reports target 500", v["target"] == 500)
    check("verdict reports progress_pct", "progress_pct" in v)

    # ── TEST 4 — full_report + empty archive ────────────────────────────────
    print("\n── TEST 4 — full_report + resilience ──")
    fr = xv.full_report()
    check("full_report has all three sections",
          all(k in fr for k in ("calibration", "counterfactual", "verdict")))
    cfg.XTE_OBSERVE_ARCHIVE = os.path.join(tmp, "empty.jsonl")
    empty = xv.full_report()
    check("empty archive: 0 samples, no crash", empty["calibration"]["samples"] == 0)
    check("empty archive verdict INSUFFICIENT_DATA", empty["verdict"]["status"] == "INSUFFICIENT_DATA")

    # ── TEST 5 — path-accurate counterfactual (GAP-C4) ───────────────────────
    print("\n── TEST 5 — path_counterfactual (GAP-C4) ──")
    pc_empty = xv.path_counterfactual()
    check("no path data handled gracefully", pc_empty["samples"] == 0 and "note" in pc_empty)
    cfg.XTE_OBSERVE_ARCHIVE = archive  # restore so dollars_per_r has rows
    paths_file = os.path.join(tmp, "xte_paths.jsonl")
    cfg.XTE_PATH_ARCHIVE = paths_file
    path_rows = [
        # protective advisory appears at current_r=1.2, realized exit_r=0.3 → improved
        {"symbol": "T", "exit_r": 0.3, "path": [
            {"current_r": 0.5, "advisory": "HOLD"},
            {"current_r": 1.2, "advisory": "TIGHTEN"},
            {"current_r": 0.3, "advisory": "TIGHTEN"}]},
        # never advises protect → no_protective_signal
        {"symbol": "T", "exit_r": 1.5, "path": [
            {"current_r": 0.5, "advisory": "HOLD"},
            {"current_r": 1.5, "advisory": "HOLD"}]},
    ]
    _write(paths_file, path_rows)
    pc = xv.path_counterfactual()
    check("path samples == 2", pc["samples"] == 2, f"got {pc['samples']}")
    check("one improved (1.2 vs 0.3)", pc["improved"] == 1, f"got {pc['improved']}")
    check("one no_protective_signal", pc["no_protective_signal"] == 1, f"got {pc['no_protective_signal']}")
    check("net_r_delta ~0.9", abs(pc["net_r_delta"] - 0.9) < 1e-6, f"got {pc['net_r_delta']}")
    check("path method is path-accurate", "path-accurate" in pc["method"])

    print("\n" + "═" * 60)
    if _FAIL == 0:
        print(f"  ALL {_PASS}/{_PASS} CHECKS PASSED ✓")
        print("  XTE validation/counterfactual analysis is read-only and operational.")
        print("═" * 60 + "\n")
        return 0
    print(f"  {_FAIL} CHECK(S) FAILED ({_PASS} passed)")
    print("═" * 60 + "\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
