#!/usr/bin/env python3
"""
XTE Campaign SIMULATOR — ad-hoc evaluation harness (NOT real evidence).

Generates N synthetic XTE observation records (+ per-tick paths) into the archive
so the validation pipeline (calibration / counterfactual / path-counterfactual /
verdict / lifecycle) can be exercised END-TO-END in seconds, without running the
live paper engine to 500 real trades.

⚠️  THIS IS SIMULATED DATA FOR PIPELINE EVALUATION ONLY.
    Every record is tagged "simulated": true. A verdict produced from this data
    is NOT economic proof of XTE. Delete/--reset before a real campaign.

Usage:
    python tools/xte_simulate_campaign.py                      # 500 samples → default archive, prints verdict
    python tools/xte_simulate_campaign.py --n 800 --bias 0.8   # stronger XTE/giveback alignment (→ CANDIDATE)
    python tools/xte_simulate_campaign.py --bias 0.2           # weak alignment (→ REJECT)
    python tools/xte_simulate_campaign.py --reset              # clear archives first
    python tools/xte_simulate_campaign.py --archive /tmp/x.jsonl --paths /tmp/p.jsonl   # redirect (no repo pollution)

`--bias` ∈ [0,1] = how often the XTE advisory correctly reflects reality
(protect iff the trade gave back). High bias → XTE looks useful; low → noise.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import cfg

PROTECT = ["TIGHTEN", "SCALE_OUT", "BREAKEVEN"]
REGIMES = ["TRENDING", "MEAN_REVERTING", "VOLATILITY_EXPANSION"]
_DPR = 0.5   # synthetic dollars-per-R


def _gen_trade(bias: float) -> tuple[dict, dict]:
    side = random.choice(["LONG", "SHORT"])
    regime = random.choice(REGIMES)
    peak_r = round(random.uniform(0.3, 2.6), 3)
    # ~45% base giveback rate so random (low-bias) protective advice sits BELOW the
    # 50% precision bar — letting --bias genuinely drive CANDIDATE vs REJECT.
    gave_back = random.random() < 0.45
    giveback_pct = round(random.uniform(45.0, 95.0) if gave_back else random.uniform(0.0, 25.0), 2)
    # realized exit R after giveback (non-giveback trades hold near peak)
    exit_r = round(max(-0.8, peak_r * (1.0 - giveback_pct / 100.0)), 4)
    net_pnl = round(exit_r * _DPR + random.gauss(0, 0.02), 6)
    won = net_pnl >= 0

    # XTE advisory: with prob=bias it correctly reflects reality (protect iff gave_back)
    if random.random() < bias:
        advisory = random.choice(PROTECT) if gave_back else "HOLD"
    else:
        advisory = random.choice(PROTECT + ["HOLD"])
    protective = advisory in PROTECT
    # A protective advisory is "good" only when the trade actually gave back —
    # then locking near peak beats the realized exit. A protective advisory on a
    # trade that did NOT give back cuts a runner early (worsens the outcome).
    good_protect = protective and gave_back
    # XTE score: low = tighten/protect, high = hold (per engine semantics)
    score = round(random.uniform(15, 35) if protective else random.uniform(55, 85), 1)

    ts = int(time.time() * 1000) + random.randint(0, 10_000)
    rec = {
        "ts": ts, "symbol": "SIMUSDT", "regime": regime,
        "duration_s": round(random.uniform(30, 600), 1),
        "exit_r": exit_r, "peak_r": peak_r, "giveback_pct": giveback_pct,
        "profit_capture": round(exit_r / peak_r, 4) if peak_r else 0.0,
        "volatility_atr_pct": round(random.uniform(0.3, 1.5), 6),
        "net_pnl": net_pnl, "exit_method": "TRAILING_STOP", "won": won,
        "xte_evals": random.randint(5, 40),
        "xte_score_last": score, "xte_score_avg": score,
        "xte_score_peak": min(100.0, score + 10), "xte_score_min": max(0.0, score - 10),
        "xte_advisory_last": advisory, "xte_advisory_transitions": random.randint(0, 3),
        "simulated": True,
    }
    # Path: protective advisory appears near peak_r (so a protective exit would have
    # captured ~peak_r, well above the realized exit_r → path-accurate improvement).
    # Realistic multi-bar path so the NEXT-bar (no-look-ahead) replay is meaningful:
    # climb to peak (HOLD), then a protective signal whose NEXT bar still holds the
    # gain (good) or fired prematurely at a low R (bad), then decay to the exit.
    def _pt(r, adv):
        return {"price": round(100 * (1 + r * 0.01), 4), "current_r": round(r, 4),
                "peak_r": round(peak_r, 4),
                "score": score if adv in PROTECT else 65.0, "advisory": adv}
    path = [_pt(0.2, "HOLD"), _pt(peak_r * 0.5, "HOLD"), _pt(peak_r, "HOLD")]
    if protective:
        if good_protect:
            path.append(_pt(peak_r * 0.95, advisory))   # signal bar (near peak)
            path.append(_pt(peak_r * 0.90, advisory))   # NEXT bar still high → captured
        else:
            path.append(_pt(0.15, advisory))            # premature signal at low R
            path.append(_pt(0.10, advisory))            # NEXT bar still low
    path.append(_pt(exit_r, advisory if protective else "HOLD"))   # realized exit
    path_rec = {"ts": ts, "symbol": "SIMUSDT", "regime": regime,
                "exit_method": "TRAILING_STOP", "exit_r": exit_r, "peak_r": peak_r,
                "won": won, "net_pnl": net_pnl, "path": path, "simulated": True}
    return rec, path_rec


def main() -> int:
    ap = argparse.ArgumentParser(description="XTE campaign simulator (synthetic eval data)")
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--bias", type=float, default=0.7)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--reset", action="store_true", help="truncate archives first")
    ap.add_argument("--archive", default=cfg.XTE_OBSERVE_ARCHIVE)
    ap.add_argument("--paths", default=cfg.XTE_PATH_ARCHIVE)
    args = ap.parse_args()
    if args.seed is not None:
        random.seed(args.seed)

    print("\n" + "!" * 64)
    print("  ⚠  XTE CAMPAIGN SIMULATOR — SIMULATED DATA, NOT REAL EVIDENCE")
    print("     Records are tagged simulated:true. Do not treat the verdict as proof.")
    print("!" * 64)

    # point validation at the chosen archives
    cfg.XTE_OBSERVE_ARCHIVE = args.archive
    cfg.XTE_PATH_ARCHIVE = args.paths
    for p in (args.archive, args.paths):
        d = os.path.dirname(p)
        if d:
            os.makedirs(d, exist_ok=True)
    mode = "w" if args.reset else "a"
    with open(args.archive, mode, encoding="utf-8") as fa, \
         open(args.paths, mode, encoding="utf-8") as fp:
        for _ in range(args.n):
            rec, prec = _gen_trade(args.bias)
            fa.write(json.dumps(rec) + "\n")
            fp.write(json.dumps(prec) + "\n")
    print(f"\n  wrote {args.n} simulated records (bias={args.bias})")
    print(f"    obs : {args.archive}")
    print(f"    path: {args.paths}")

    # import AFTER setting cfg paths so reads hit the chosen archives
    from core.truth import xte_validation as xv
    rep = xv.full_report()
    v = rep["verdict"]
    print("\n  ── FINAL VERDICT (on SIMULATED data) ──")
    if v.get("status") == "INSUFFICIENT_DATA":
        print(f"    status               : INSUFFICIENT_DATA ({v.get('samples')}/{v.get('target')}) "
              "— final verdict needs 500; see INTERIM below.")
    else:
        print(f"    status               : {v.get('status')}")
        print(f"    samples              : {v.get('samples')}")
        print(f"    +R per trade         : {v.get('avg_r_delta_per_trade')}  (bar >= {v.get('success_criteria', {}).get('min_r_per_trade')})  <-- honest metric")
        print(f"    protect_precision_pct: {v.get('protect_precision_pct')}  (bar >= {v.get('success_criteria', {}).get('min_protect_precision_pct')}%)")
        print(f"    gain concentration   : top 5% trades = {v.get('gain_concentration_top5pct')}% of gain")
        print(f"    uplift% (context)    : {v.get('economic_uplift_pct')}  (unreliable near breakeven)")
    pcf = rep["path_counterfactual"]
    print(f"    path: improved={pcf.get('improved')} worsened={pcf.get('worsened')} "
          f"net_r_delta={pcf.get('net_r_delta')} net_usd_delta={pcf.get('net_usd_delta')}")
    iv = rep["interim_verdict"]
    print(f"\n  ── INTERIM (early-stop) at n={iv.get('n')} ──")
    print(f"    status: {iv.get('status')}  |  {iv.get('reason')}")
    print(f"\n    recommendation: {v.get('recommendation')}")
    print("\n  Inspect full report:  GET /api/truth/xte/validation")
    print("  Reset before real run: python tools/xte_simulate_campaign.py --reset --n 0  (or delete the jsonl)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
