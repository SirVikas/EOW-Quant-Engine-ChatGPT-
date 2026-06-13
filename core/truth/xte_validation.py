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

    # Honest primary gate = R improvement averaged over ALL OBSERVED trades
    # (holds count as 0), NOT just the subset XTE signaled on — that subset is
    # self-selected toward developed trades and overstates the population effect.
    avg_signaled = pcf.get("avg_r_delta_per_trade", 0.0) if pcf.get("evaluated") else 0.0
    avg_r = pcf.get("avg_r_delta_per_observed", 0.0) if pcf.get("evaluated") else 0.0
    basis = "path-accurate R/observed-trade" if pcf.get("evaluated") else "no-path-data"

    min_r = float(getattr(cfg, "XTE_SUCCESS_MIN_R_PER_TRADE", 0.05))
    min_prec = float(getattr(cfg, "XTE_SUCCESS_MIN_PROTECT_PRECISION", 50.0))
    success = (avg_r >= min_r) and (prec >= min_prec)

    concentration = pcf.get("gain_concentration_top5pct")
    if success:
        status = "CANDIDATE"
        rec = (f"PROMOTION CANDIDATE — +{round(avg_r,4)}R/observed-trade >= {min_r}R "
               f"(+{round(avg_signaled,4)}R on signaled subset), precision {prec}% >= {min_prec}%. "
               f"CAVEATS before X3: retrospective; top-5% = {concentration}% of gain; "
               "confirm candle-coverage selection bias is resolved + a forward slice.")
    else:
        status = "REJECT"
        rec = (f"REJECT / REDESIGN — +{round(avg_r,4)}R/observed-trade (need >= {min_r}R) or "
               f"precision {prec}% (need >= {min_prec}%) below the success bar.")
    return {
        "status": status,
        "samples": n,
        "protect_precision_pct": prec,
        "avg_r_delta_per_observed": round(avg_r, 4),    # primary (population)
        "avg_r_delta_per_signaled": round(avg_signaled, 4),  # subset (context)
        "economic_basis": basis,
        "gain_concentration_top5pct": concentration,
        "success_criteria": {
            "min_r_per_trade": min_r,
            "min_protect_precision_pct": min_prec,
            "note": "Primary gate = R per OBSERVED trade (population), not per signaled trade.",
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
    """GAP-C4 — PATH-ACCURATE counterfactual with honest accounting.

    For each trade: find the FIRST tick XTE advised protection, then exit at the
    NEXT bar (no same-bar look-ahead — you cannot act on a bar using that same
    bar's close), and compare that R to the realized exit R.

    Reports per-trade R/$ as the PRIMARY metric. The percent-vs-realized figure is
    secondary and flagged unreliable when realized PnL is near breakeven (a tiny
    denominator otherwise explodes the %). Also reports gain concentration so a
    result driven by a handful of trades is visible.
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
    r_deltas: List[float] = []
    for p in paths:
        actual_r = p.get("exit_r", 0.0) or 0.0
        pts = p.get("path", [])
        cf_r = None
        for i, pt in enumerate(pts):
            if pt.get("advisory") in PROTECT_LABELS:
                nxt = pts[i + 1] if i + 1 < len(pts) else pt   # NEXT-bar exit; fallback if last
                cf_r = nxt.get("current_r", pt.get("current_r", 0.0))
                break
        if cf_r is None:
            no_signal += 1
            continue
        d = cf_r - actual_r
        r_deltas.append(d)
        if d > 0.01:
            improved += 1
        elif d < -0.01:
            worsened += 1
        else:
            neutral += 1
    evaluated = len(r_deltas)
    net_r = sum(r_deltas)
    avg_r = net_r / evaluated if evaluated else 0.0           # per trade XTE SIGNALED on
    avg_r_observed = net_r / n if n else 0.0                  # per trade OBSERVED (holds count as 0)
    net_usd = net_r * dpr
    total_realized = sum(r.get("net_pnl", 0.0) for r in rows)
    # gain concentration: share of positive delta from the top 5% of trades
    gains = sorted((d for d in r_deltas if d > 0), reverse=True)
    top5 = sum(gains[: max(1, len(gains) // 20)]) if gains else 0.0
    concentration = round(top5 / net_r * 100, 1) if net_r > 1e-9 else None
    denom_ok = abs(total_realized) > max(1.0, 0.05 * evaluated)
    uplift_pct = round(net_usd / abs(total_realized) * 100, 2) if denom_ok else None
    return {
        "samples": n,
        "evaluated": evaluated,
        "no_protective_signal": no_signal,
        "improved": improved,
        "worsened": worsened,
        "neutral": neutral,
        "avg_r_delta_per_trade": round(avg_r, 4),          # per trade XTE signaled on (subset)
        "avg_r_delta_per_observed": round(avg_r_observed, 4),  # PRIMARY: per observed trade (population)
        "avg_usd_delta_per_trade": round(net_usd / evaluated, 6) if evaluated else 0.0,
        "net_r_delta": round(net_r, 4),
        "net_usd_delta": round(net_usd, 6),
        "total_realized_usd": round(total_realized, 4),
        "uplift_pct_vs_realized": uplift_pct,          # secondary; None if unreliable
        "denominator_reliable": denom_ok,
        "gain_concentration_top5pct": concentration,
        "dollars_per_r": round(dpr, 6),
        "method": "next-bar exit after first protective advisory (no same-bar look-ahead)",
        "caveats": "retrospective backtest; % unreliable near breakeven — judge avg_r_delta_per_trade; check concentration + selection bias (skipped trades).",
    }


def _data_basis(rows: List[dict]) -> str:
    sample = rows[:20]
    if any(r.get("simulated") for r in sample):
        return "SIMULATED (not proof)"
    if any(r.get("source") == "historical_backfill" for r in sample):
        return "real (historical backtest)"
    return "real (live)"


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
    min_r = float(getattr(cfg, "XTE_SUCCESS_MIN_R_PER_TRADE", 0.05))
    min_prec = float(getattr(cfg, "XTE_SUCCESS_MIN_PROTECT_PRECISION", 50.0))
    rej_n = int(getattr(cfg, "XTE_EARLY_REJECT_MIN_N", 100))
    cand_n = int(getattr(cfg, "XTE_EARLY_CANDIDATE_MIN_N", 300))

    if n < rej_n:
        return {"status": "INSUFFICIENT", "n": n, "next_checkpoint": rej_n,
                "data_basis": _data_basis(rows),
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

    # per-trade path r-delta CI — NEXT-bar exit (no same-bar look-ahead)
    deltas = []
    for pth in _read_paths():
        ar = pth.get("exit_r", 0.0) or 0.0
        pts = pth.get("path", [])
        for i, pt in enumerate(pts):
            if pt.get("advisory") in PROTECT_LABELS:
                nxt = pts[i + 1] if i + 1 < len(pts) else pt
                deltas.append((nxt.get("current_r", pt.get("current_r", 0.0)) or 0.0) - ar)
                break
    dm, dsd = _mean_std(deltas)
    k = len(deltas)
    dmargin = _Z * dsd / math.sqrt(k) if k > 1 else (abs(dm) if k == 1 else 0.0)
    d_lo, d_hi = dm - dmargin, dm + dmargin

    pcf = path_counterfactual()
    concentration = pcf.get("gain_concentration_top5pct")

    # decision — reject earlier than accept. Gate on R/trade (denominator-safe).
    status, reason = "CONTINUE", f"inconclusive at n={n}; keep collecting"
    reject = (prec_hi is not None and prec_hi < min_prec) or (k >= 2 and d_hi <= 0.0)
    if reject:
        status = "EARLY_REJECT"
        reason = (f"even optimistically below bar at n={n} "
                  f"(precision upper CI {round(prec_hi,1) if prec_hi is not None else 'NA'}% vs {min_prec}%, "
                  f"r-delta upper CI {round(d_hi,3)}) — STOP, do not advance.")
    elif n >= cand_n and prec_lo is not None and prec_lo >= min_prec and k >= 2 and d_lo > 0.0 and dm >= min_r:
        status = "EARLY_CANDIDATE"
        reason = (f"confidently above bar at n={n} (precision lower CI {round(prec_lo,1)}% >= {min_prec}%, "
                  f"+{round(dm,3)}R/trade, r-delta lower CI {round(d_lo,3)} > 0) — may advance to X3 "
                  f"DESIGN; CAVEATS: retrospective, top-5%={concentration}% of gain, check selection bias.")

    return {
        "status": status,
        "n": n,
        "checkpoints": {"early_reject_min_n": rej_n, "early_candidate_min_n": cand_n, "final_n": MIN_SAMPLES},
        "protect_precision_ci_pct": [round(prec_lo, 1), round(prec_hi, 1)] if prec_lo is not None else None,
        "path_r_delta_ci": [round(d_lo, 3), round(d_hi, 3)] if k else None,
        "avg_r_delta_per_trade": round(dm, 4) if k else None,
        "gain_concentration_top5pct": concentration,
        "uplift_pct_vs_realized": pcf.get("uplift_pct_vs_realized"),
        "reason": reason,
        "data_basis": _data_basis(rows),
    }


def robustness_split(segments: int = 2) -> dict:
    """Walk-forward check: split history chronologically (by trade exit_ts) into
    `segments` and report R/trade + precision per segment. A real signal holds in
    EVERY segment; a one-regime fluke shows up as a segment that fails. Guards
    against trusting a single-period backtest before X3."""
    paths = [p for p in _read_paths() if p.get("exit_ts")]
    if len(paths) < segments * 20:
        return {"segments": segments, "note": "insufficient time-stamped path data for a walk-forward split",
                "n": len(paths)}
    paths.sort(key=lambda p: p["exit_ts"])
    min_r = float(getattr(cfg, "XTE_SUCCESS_MIN_R_PER_TRADE", 0.05))
    size = len(paths) // segments
    out = []
    consistent = True
    for s in range(segments):
        chunk = paths[s * size:] if s == segments - 1 else paths[s * size:(s + 1) * size]
        deltas = []
        for p in chunk:
            ar = p.get("exit_r", 0.0) or 0.0
            pts = p.get("path", [])
            for i, pt in enumerate(pts):
                if pt.get("advisory") in PROTECT_LABELS:
                    nxt = pts[i + 1] if i + 1 < len(pts) else pt
                    deltas.append((nxt.get("current_r", pt.get("current_r", 0.0)) or 0.0) - ar)
                    break
        avg_r = round(sum(deltas) / len(deltas), 4) if deltas else 0.0
        seg_ok = avg_r >= min_r
        consistent = consistent and seg_ok
        out.append({"segment": s + 1, "n": len(chunk), "evaluated": len(deltas),
                    "avg_r_delta_per_trade": avg_r, "passes_bar": seg_ok,
                    "exit_ts_range": [chunk[0]["exit_ts"], chunk[-1]["exit_ts"]]})
    return {"segments": segments, "min_r_per_trade": min_r,
            "consistent_across_time": consistent, "per_segment": out,
            "interpretation": ("signal holds across all time segments — robust"
                               if consistent else
                               "signal FAILS in >=1 segment — likely regime-dependent, NOT robust")}


def full_report() -> dict:
    return {
        "calibration": calibration_curve(),
        "counterfactual": counterfactual_analysis(),
        "path_counterfactual": path_counterfactual(),
        "robustness_split": robustness_split(),
        "interim_verdict": interim_verdict(),
        "verdict": verdict(),
    }
