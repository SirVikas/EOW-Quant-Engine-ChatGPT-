#!/usr/bin/env python3
"""
XTE FORWARD CONFIRMATION CHECK — the gate a backtest cannot satisfy.

The historical backfill showed +0.235R/observed (broad, robust) — but it is
retrospective. Before XTE may EVER influence a live exit (X3-e), the live forward
campaign must independently reproduce it. This tool compares the forward (live)
archive against the backtest (backfill) archive and gives a CONFIRM / HALT / WAIT.

Run periodically while the forward campaign (start_xte_campaign.bat) accumulates.

Usage:
    python tools/xte_forward_check.py
    python tools/xte_forward_check.py --forward-obs reports/xte_observations/xte_observations.jsonl \
        --backtest-obs reports/xte_observations/backfill_obs.jsonl
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import cfg

MIN_FORWARD_N = 300
MIN_FORWARD_R = 0.10   # forward must clear this to confirm (stricter than the 0.05 design bar)


def _report(obs, paths):
    cfg.XTE_OBSERVE_ARCHIVE = obs
    cfg.XTE_PATH_ARCHIVE = paths
    # import fresh each call so it reads the just-set cfg paths
    from core.truth import xte_validation as xv
    pcf = xv.path_counterfactual()
    sa = xv.stratified_audit()
    return {
        "n": pcf.get("samples", 0),
        "avg_r_observed": pcf.get("avg_r_delta_per_observed"),
        "broad_based": sa.get("broad_based"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="XTE forward-vs-backtest confirmation gate")
    ap.add_argument("--forward-obs", default="reports/xte_observations/xte_observations.jsonl")
    ap.add_argument("--forward-paths", default="reports/xte_observations/xte_paths.jsonl")
    ap.add_argument("--backtest-obs", default="reports/xte_observations/backfill_obs.jsonl")
    ap.add_argument("--backtest-paths", default="reports/xte_observations/backfill_paths.jsonl")
    args = ap.parse_args()

    bt = _report(args.backtest_obs, args.backtest_paths)
    fw = _report(args.forward_obs, args.forward_paths)

    print("\n  XTE FORWARD CONFIRMATION CHECK")
    print(f"    backtest : n={bt['n']}  +R/observed={bt['avg_r_observed']}  broad={bt['broad_based']}")
    print(f"    forward  : n={fw['n']}  +R/observed={fw['avg_r_observed']}  broad={fw['broad_based']}")

    fr = fw["avg_r_observed"]
    if fw["n"] < MIN_FORWARD_N:
        verdict = f"WAIT — only {fw['n']} forward trades (need >= {MIN_FORWARD_N}). Keep the campaign running."
    elif fr is not None and fr >= MIN_FORWARD_R and fw["broad_based"]:
        verdict = (f"CONFIRM — forward +{fr}R/observed >= {MIN_FORWARD_R} and broad_based. "
                   "Backtest reproduced live → XTE may proceed to X3-e (with ADR).")
    else:
        verdict = (f"HALT — forward +{fr}R/observed did NOT reproduce the backtest "
                   "(below bar or not broad). Do NOT let XTE act; the backtest was regime-specific.")
    print(f"\n    GATE: {verdict}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
