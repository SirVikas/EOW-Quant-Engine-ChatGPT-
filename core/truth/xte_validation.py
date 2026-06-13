"""
XTE Validation & Counterfactual Analysis — FTD-094A follow-on (GAP-6/7/8 closure)

Offline, read-only analysis over the XTE observation archive. Produces:
  • calibration_curve()       — score bucket → win-rate / exit_r / giveback / expectancy   [GAP-6]
  • counterfactual_analysis() — XTE advisory vs realized giveback + bounded $ estimate      [GAP-7/8]
  • verdict()                 — promotion recommendation (needs ≥ MIN_SAMPLES)              [P2]
  • full_report()             — the three combined

NO execution influence, NO live coupling: operates purely on archived per-trade
records via xte_observer.read_records().

Honest scope: the archive stores per-trade SUMMARIES (peak_r, exit_r, advisory
trajectory), not tick-level price paths. A *true* path-replay counterfactual is
therefore not possible from this data. The economic figure here is an explicitly
BOUNDED upper estimate under the assumptions stated in counterfactual_analysis().
A path-accurate counterfactual would require tick-level archival (noted as a
future enhancement, not delivered here).
"""
from __future__ import annotations

import math
from typing import Any, Dict, List

from config import cfg
from core.truth.xte_observer import xte_observer

MIN_SAMPLES = 500
PROTECT_LABELS = {"TIGHTEN", "SCALE_OUT", "BREAKEVEN"}
GIVEBACK_EVENT_PCT = 30.0   # a trade "gave back" if it surrendered >30% of peak_r
_Z = 1.96                   # 95% normal-approx confidence


def _mean_std(xs: List[float]) -> tuple:
    n = len(xs)
    if n == 0:
        return 0.0, 0.0
    m = sum(xs) / n
    if n < 2:
        return m, 0.0
    var = sum((x - m) ** 2 for x in xs) / (n - 1)
    return m, math.sqrt(var)


def _avg(xs: List[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _dollars_per_r(rows: List[dict]) -> float:
    # Empirical $/1R from the trades themselves (net_pnl / exit_r where defined).
    vals = [r["net_pnl"] / r["exit_r"] for r in rows
            if r.get("exit_r") and abs(r["exit_r"]) > 1e-6]
    return _avg(vals)


def _bucket(score: Any) -> str:
    if score is None:
        return "n/a"
    b = int(float(score) // 10) * 10
    return f"{b}-{b + 10}"


def calibration_curve() -> dict:
    rows = xte_observer.read_records()
    n = len(rows)
    buckets: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        key = _bucket(r.get("xte_score_avg"))
        agg = buckets.setdefault(key, {"n": 0, "wins": 0, "exit_r": [], "giveback": [], "pnl": []})
        agg["n"] += 1
        agg["wins"] += 1 if r.get("won") else 0
        agg["exit_r"].append(r.get("exit_r", 0.0))
        agg["giveback"].append(r.get("giveback_pct", 0.0))
        agg["pnl"].append(r.get("net_pnl", 0.0))
    curve = {
        k: {
            "n": v["n"],
            "win_rate_pct": round(v["wins"] / v["n"] * 100, 1),
            "avg_exit_r": round(_avg(v["exit_r"]), 4),
            "avg_giveback_pct": round(_avg(v["giveback"]), 2),
            "expectancy_usd": round(_avg(v["pnl"]), 6),
        }
        for k, v in sorted(buckets.items())
    }
    return {"samples": n, "buckets": curve}


def counterfactual_analysis() -> dict:
    """Advisory-alignment + bounded economic estimate.

    Assumption (stated, bounded): on a trade where XTE's final advisory was
    protective (TIGHTEN/SCALE_OUT/BREAKEVEN) AND the trade then surrendered
    >GIVEBACK_EVENT_PCT of peak, a protective exit would have locked
    GIVEBACK_LOCK_FRACTION × peak_r. recoverable_r = max(0, lock×peak_r − exit_r).
    Summed × empirical $/R = an UPPER BOUND on what heeding XTE could have saved.
    The opportunity cost of protective advisories on trades that did NOT give back
    (cutting a runner) is NOT estimable from summary data — reported as a count
    only, not a dollar figure.
    """
    rows = xte_observer.read_records()
    n = len(rows)
    lock = float(getattr(cfg, "GIVEBACK_LOCK_FRACTION", 0.5))
    dpr = _dollars_per_r(rows)

    protect_and_gaveback = 0      # XTE said protect, trade gave back  → XTE correct
    protect_no_giveback = 0       # XTE said protect, trade held       → potential runner cut
    hold_and_ran = 0             # XTE said hold, no giveback          → XTE correct
    hold_and_gaveback = 0        # XTE said hold, trade gave back      → XTE missed
    recoverable_r_total = 0.0

    for r in rows:
        protect = (r.get("xte_advisory_last") in PROTECT_LABELS)
        gave_back = r.get("giveback_pct", 0.0) > GIVEBACK_EVENT_PCT
        peak_r = r.get("peak_r", 0.0) or 0.0
        exit_r = r.get("exit_r", 0.0) or 0.0
        if protect and gave_back:
            protect_and_gaveback += 1
            recoverable_r_total += max(0.0, lock * peak_r - exit_r)
        elif protect and not gave_back:
            protect_no_giveback += 1
        elif (not protect) and gave_back:
            hold_and_gaveback += 1
        else:
            hold_and_ran += 1

    flagged = protect_and_gaveback + protect_no_giveback
    giveback_events = protect_and_gaveback + hold_and_gaveback
    return {
        "samples": n,
        "dollars_per_r": round(dpr, 6),
        "alignment": {
            "protect_correct": protect_and_gaveback,
            "protect_possible_runner_cut": protect_no_giveback,
            "hold_correct": hold_and_ran,
            "hold_missed_giveback": hold_and_gaveback,
            "protect_precision_pct": round(protect_and_gaveback / flagged * 100, 1) if flagged else None,
            "protect_recall_pct": round(protect_and_gaveback / giveback_events * 100, 1) if giveback_events else None,
        },
        "bounded_savings_usd_upper": round(recoverable_r_total * dpr, 6),
        "bounded_savings_r_upper": round(recoverable_r_total, 4),
        "assumptions": {
            "lock_fraction": lock,
            "giveback_event_pct": GIVEBACK_EVENT_PCT,
            "note": "Upper bound only; opportunity cost of protective advisories on non-giveback trades is not estimable from summary telemetry (no price path).",
        },
    }


def verdict() -> dict:
    rows = xte_observer.read_records()
    n = len(rows)
    if n < MIN_SAMPLES:
        return {
            "status": "INSUFFICIENT_DATA",
            "samples": n,
            "target": MIN_SAMPLES,
            "progress_pct": round(min(100.0, n / MIN_SAMPLES * 100), 1),
            "recommendation": "KEEP OBSERVING — enable XTE_OBSERVE_ENABLED and collect more closed trades.",
        }
    cf = counterfactual_analysis()
    pcf = path_counterfactual()
    prec = cf["alignment"]["protect_precision_pct"] or 0.0
    total_realized = sum(r.get("net_pnl", 0.0) for r in rows)

    # GAP-9: prefer the path-accurate economic delta; fall back to the bounded estimate.
    if pcf.get("evaluated"):
        econ_delta, basis = pcf["net_usd_delta"], "path-accurate"
    else:
        econ_delta, basis = cf["bounded_savings_usd_upper"], "bounded-upper-estimate"
    uplift_pct = round(econ_delta / abs(total_realized) * 100, 2) if abs(total_realized) > 1e-9 else 0.0

    min_uplift = float(getattr(cfg, "XTE_SUCCESS_MIN_UPLIFT_PCT", 3.0))
    min_prec = float(getattr(cfg, "XTE_SUCCESS_MIN_PROTECT_PRECISION", 50.0))
    success = (uplift_pct >= min_uplift) and (prec >= min_prec)

    if success:
        status = "CANDIDATE"
        rec = (f"PROMOTION CANDIDATE — economic uplift {uplift_pct}% ≥ {min_uplift}% and "
               f"protect precision {prec}% ≥ {min_prec}%. Advance to Exit-Coordinator shadow "
               "parity (blueprint X2→X3) + ADR before any acting role.")
    else:
        status = "REJECT"
        rec = (f"REJECT / REDESIGN — economic uplift {uplift_pct}% (need ≥{min_uplift}%) or "
               f"protect precision {prec}% (need ≥{min_prec}%) below the success bar.")
    return {
        "status": status,
        "samples": n,
        "protect_precision_pct": prec,
        "economic_uplift_pct": uplift_pct,
        "economic_basis": basis,
        "success_criteria": {
            "min_uplift_pct": min_uplift,
            "min_protect_precision_pct": min_prec,
            "note": "uplift = economic delta / |realized PnL|; path-accurate when path data present.",
        },
        "recommendation": rec,
    }


def _read_paths() -> List[dict]:
    import json
    import os
    path = getattr(cfg, "XTE_PATH_ARCHIVE", "reports/xte_observations/xte_paths.jsonl")
    if not os.path.exists(path):
        return []
    out: List[dict] = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        continue
    except Exception:
        return []
    return out


def path_counterfactual() -> dict:
    """GAP-C4 — PATH-ACCURATE counterfactual: replay each trade's per-tick path and
    take the exit at the FIRST tick XTE advised protection (TIGHTEN/SCALE_OUT),
    versus the realized exit. Requires XTE_OBSERVE_PATH_ENABLED during collection.

    Unlike counterfactual_analysis() (summary-level, upper-bound), this measures
    the actual R at the advised exit point, so the $ delta is path-accurate, not
    an estimate.
    """
    paths = _read_paths()
    n = len(paths)
    if n == 0:
        return {
            "samples": 0,
            "note": "No path data. Set XTE_OBSERVE_PATH_ENABLED=True during collection to enable path-accurate replay.",
        }
    rows = xte_observer.read_records()
    dpr = _dollars_per_r(rows) if rows else 0.0
    improved = worsened = neutral = no_signal = 0
    r_delta_total = 0.0
    for p in paths:
        actual_r = p.get("exit_r", 0.0) or 0.0
        cf_r = None
        for pt in p.get("path", []):
            if pt.get("advisory") in PROTECT_LABELS:
                cf_r = pt.get("current_r", 0.0)
                break
        if cf_r is None:
            no_signal += 1
            continue
        d = cf_r - actual_r
        r_delta_total += d
        if d > 0.01:
            improved += 1
        elif d < -0.01:
            worsened += 1
        else:
            neutral += 1
    evaluated = improved + worsened + neutral
    return {
        "samples": n,
        "evaluated": evaluated,
        "no_protective_signal": no_signal,
        "improved": improved,
        "worsened": worsened,
        "neutral": neutral,
        "net_r_delta": round(r_delta_total, 4),
        "net_usd_delta": round(r_delta_total * dpr, 6),
        "dollars_per_r": round(dpr, 6),
        "method": "first-protective-advisory exit vs realized exit (path-accurate)",
    }


def interim_verdict() -> dict:
    """Sequential early-stop on REAL data — the time/result balance.

    Lets the campaign terminate before 500 when the evidence is statistically
    decisive, using 95% normal-approx confidence on (a) protect precision and
    (b) the per-trade path r-delta. Asymmetric by design: declare EARLY_REJECT
    sooner (stop wasting time on a loser) than EARLY_CANDIDATE (be sure before
    promoting). Uses ONLY real archived observations — no synthetic shortcut.
    """
    rows = xte_observer.read_records()
    n = len(rows)
    min_uplift = float(getattr(cfg, "XTE_SUCCESS_MIN_UPLIFT_PCT", 3.0))
    min_prec = float(getattr(cfg, "XTE_SUCCESS_MIN_PROTECT_PRECISION", 50.0))
    rej_n = int(getattr(cfg, "XTE_EARLY_REJECT_MIN_N", 100))
    cand_n = int(getattr(cfg, "XTE_EARLY_CANDIDATE_MIN_N", 300))

    if n < rej_n:
        return {"status": "INSUFFICIENT", "n": n, "next_checkpoint": rej_n,
                "note": f"Need ≥{rej_n} closed trades for the first early-stop check."}

    # precision proportion CI (Wald)
    cf = counterfactual_analysis()
    al = cf["alignment"]
    flagged = al["protect_correct"] + al["protect_possible_runner_cut"]
    if flagged > 0:
        p = al["protect_correct"] / flagged
        pm = _Z * math.sqrt(max(0.0, p * (1 - p) / flagged))
        prec_lo, prec_hi = (p - pm) * 100, (p + pm) * 100
    else:
        prec_lo = prec_hi = None

    # per-trade path r-delta CI
    deltas = []
    for pth in _read_paths():
        ar = pth.get("exit_r", 0.0) or 0.0
        for pt in pth.get("path", []):
            if pt.get("advisory") in PROTECT_LABELS:
                deltas.append((pt.get("current_r", 0.0) or 0.0) - ar)
                break
    dm, dsd = _mean_std(deltas)
    k = len(deltas)
    dmargin = _Z * dsd / math.sqrt(k) if k > 1 else (abs(dm) if k == 1 else 0.0)
    d_lo, d_hi = dm - dmargin, dm + dmargin

    pcf = path_counterfactual()
    total_realized = sum(r.get("net_pnl", 0.0) for r in rows)
    econ_delta = pcf.get("net_usd_delta", 0.0) if pcf.get("evaluated") else cf["bounded_savings_usd_upper"]
    uplift_pct = round(econ_delta / abs(total_realized) * 100, 2) if abs(total_realized) > 1e-9 else 0.0

    # decision — reject earlier than accept
    status, reason = "CONTINUE", f"inconclusive at n={n}; keep collecting"
    reject = (prec_hi is not None and prec_hi < min_prec) or (k >= 2 and d_hi <= 0.0)
    if reject:
        status = "EARLY_REJECT"
        reason = (f"even optimistically below bar at n={n} "
                  f"(precision upper CI {round(prec_hi,1) if prec_hi is not None else 'NA'}% vs {min_prec}%, "
                  f"r-delta upper CI {round(d_hi,3)}) — STOP, do not advance.")
    elif n >= cand_n and prec_lo is not None and prec_lo >= min_prec and k >= 2 and d_lo > 0.0 and uplift_pct >= min_uplift:
        status = "EARLY_CANDIDATE"
        reason = (f"confidently above bar at n={n} (precision lower CI {round(prec_lo,1)}% ≥ {min_prec}%, "
                  f"r-delta lower CI {round(d_lo,3)} > 0, uplift {uplift_pct}% ≥ {min_uplift}%) — "
                  "may advance to X3 design; confirm at 500.")

    return {
        "status": status,
        "n": n,
        "checkpoints": {"early_reject_min_n": rej_n, "early_candidate_min_n": cand_n, "final_n": MIN_SAMPLES},
        "protect_precision_ci_pct": [round(prec_lo, 1), round(prec_hi, 1)] if prec_lo is not None else None,
        "path_r_delta_ci": [round(d_lo, 3), round(d_hi, 3)] if k else None,
        "economic_uplift_pct": uplift_pct,
        "reason": reason,
        "data_basis": "real" if not any(r.get("simulated") for r in rows[:5]) else "SIMULATED (not proof)",
    }


def full_report() -> dict:
    return {
        "calibration": calibration_curve(),
        "counterfactual": counterfactual_analysis(),
        "path_counterfactual": path_counterfactual(),
        "interim_verdict": interim_verdict(),
        "verdict": verdict(),
    }
