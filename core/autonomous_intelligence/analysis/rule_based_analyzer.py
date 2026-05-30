"""
FTD-AIL-001: Rule-Based Analyzer.
Fires threshold-based rules against collected snapshots, no external API needed.
"""
from __future__ import annotations
from typing import Any

from core.autonomous_intelligence.correlation.trend_engine import compute_trend


def analyze(snapshots: dict[str, Any], win_rate_history: list[float] | None = None) -> list[dict]:
    """
    Run all rules against current snapshots.
    Returns list of raw rule-hit dicts (not yet Finding objects).
    """
    hits: list[dict] = []
    _genome_starvation(snapshots, hits)
    _cost_drag_critical(snapshots, hits)
    _be_trigger_unprotected(snapshots, hits)
    _win_rate_declining(snapshots, hits, win_rate_history or [])
    _loss_run_excessive(snapshots, hits)
    _no_promotions(snapshots, hits)
    _recovery_boost_harmful(snapshots, hits)
    _peak_r_insufficient(snapshots, hits)
    _promotion_gate_impossible(snapshots, hits)
    return hits


def _genome_starvation(snapshots: dict, hits: list) -> None:
    genome = snapshots.get("Genome Exposure Audit", {})
    if "error" in genome:
        return
    activated = genome.get("activated", 0)
    executed  = genome.get("executed", 0)
    if activated > 0 and (executed / activated) < 0.10:
        hits.append({
            "rule": "GENOME_STARVATION",
            "category": "GENOME",
            "severity": "MEDIUM",
            "title": "Genome execution rate below 10%",
            "evidence": [genome],
            "confidence_score": 0.85,
            "sample_size": activated,
            "economic_impact_est": "MEDIUM",
            "risk_level": "MEDIUM",
            "recommendation": (
                f"Genome activation={activated} but only {executed} executed "
                f"({executed/activated*100:.1f}%). Investigate exposure guarantee or filter thresholds."
            ),
            "source_reports": ["Genome Exposure Audit"],
        })


def _cost_drag_critical(snapshots: dict, hits: list) -> None:
    rec = snapshots.get("Recovery Cycle Audit", {})
    by_strategy = rec.get("by_strategy", {})
    for strat, data in by_strategy.items():
        drag = data.get("cost_drag_pct", 0)
        if drag > 60:
            hits.append({
                "rule": "COST_DRAG_CRITICAL",
                "category": "COST",
                "severity": "HIGH",
                "title": f"Critical cost drag on {strat}: {drag:.1f}%",
                "evidence": [{"strategy": strat, "cost_drag_pct": drag}],
                "confidence_score": 0.90,
                "sample_size": data.get("trade_count", 0),
                "economic_impact_est": "HIGH",
                "risk_level": "HIGH",
                "recommendation": (
                    f"{strat} has {drag:.1f}% of gross PnL consumed by fees. "
                    "Investigate trade frequency and average win size vs fee cost."
                ),
                "source_reports": ["Recovery Cycle Audit"],
            })


def _be_trigger_unprotected(snapshots: dict, hits: list) -> None:
    be = snapshots.get("Breakeven Impact Audit", {})
    pct = be.get("pct_wins_unprotected", 0)
    if pct > 80:
        hits.append({
            "rule": "BE_TRIGGER_UNPROTECTED",
            "category": "RISK",
            "severity": "HIGH",
            "title": f"{pct:.1f}% of wins closed without BE protection",
            "evidence": [be],
            "confidence_score": 0.88,
            "sample_size": be.get("total_wins", 0),
            "economic_impact_est": "HIGH",
            "risk_level": "HIGH",
            "recommendation": (
                f"{pct:.1f}% wins are unprotected by breakeven trigger. "
                "Review BREAKEVEN_TRIGGER_R threshold — may need further reduction."
            ),
            "source_reports": ["Breakeven Impact Audit"],
        })


def _win_rate_declining(snapshots: dict, hits: list, history: list[float]) -> None:
    if len(history) < 3:
        return
    trend = compute_trend(history)
    if trend == "FALLING":
        hits.append({
            "rule": "WIN_RATE_DECLINING",
            "category": "PERFORMANCE",
            "severity": "MEDIUM",
            "title": "Win rate declining over recent collections",
            "evidence": [{"win_rate_history": history[-5:], "trend": trend}],
            "confidence_score": 0.75,
            "sample_size": len(history),
            "economic_impact_est": "MEDIUM",
            "risk_level": "MEDIUM",
            "recommendation": "Win rate trend is FALLING over 3+ collections. Review filter conditions and market regime alignment.",
            "source_reports": ["Performance Status"],
        })


def _loss_run_excessive(snapshots: dict, hits: list) -> None:
    perf = snapshots.get("Performance Status", {})
    avg_win  = perf.get("avg_win_run", 0)
    avg_loss = perf.get("avg_loss_run", 0)
    if avg_win > 0 and avg_loss > avg_win * 5:
        hits.append({
            "rule": "LOSS_RUN_EXCESSIVE",
            "category": "RISK",
            "severity": "HIGH",
            "title": f"Average loss run {avg_loss:.3f}R is >5× average win run {avg_win:.3f}R",
            "evidence": [{"avg_win_run": avg_win, "avg_loss_run": avg_loss}],
            "confidence_score": 0.92,
            "sample_size": perf.get("total_trades", 0),
            "economic_impact_est": "HIGH",
            "risk_level": "HIGH",
            "recommendation": (
                f"Loss R-multiple ({avg_loss:.3f}) is {avg_loss/avg_win:.1f}× the win R-multiple ({avg_win:.3f}). "
                "Investigate stop-loss placement and trade holding behavior."
            ),
            "source_reports": ["Performance Status"],
        })


def _no_promotions(snapshots: dict, hits: list) -> None:
    promo = snapshots.get("Promotion Watch", {})
    promoted = promo.get("total_promoted", -1)
    cycles   = promo.get("total_cycles", 0)
    if promoted == 0 and cycles > 100:
        hits.append({
            "rule": "NO_PROMOTIONS",
            "category": "GENOME",
            "severity": "MEDIUM",
            "title": f"Zero genome promotions after {cycles} cycles",
            "evidence": [promo],
            "confidence_score": 0.80,
            "sample_size": cycles,
            "economic_impact_est": "MEDIUM",
            "risk_level": "MEDIUM",
            "recommendation": (
                f"No genome promoted after {cycles} cycles. "
                "Review promotion gate thresholds — may be too strict for current market."
            ),
            "source_reports": ["Promotion Watch"],
        })


def _recovery_boost_harmful(snapshots: dict, hits: list) -> None:
    rec = snapshots.get("Recovery Cycle Audit", {})
    delta = rec.get("boost_vs_normal_pnl_delta", 0)
    if delta < -0.05:
        hits.append({
            "rule": "RECOVERY_BOOST_HARMFUL",
            "category": "PERFORMANCE",
            "severity": "HIGH",
            "title": f"Recovery boost producing negative PnL delta: {delta:.3f}",
            "evidence": [{"boost_vs_normal_pnl_delta": delta}],
            "confidence_score": 0.85,
            "sample_size": rec.get("recovery_trade_count", 0),
            "economic_impact_est": "HIGH",
            "risk_level": "HIGH",
            "recommendation": (
                f"Boosted recovery trades show {delta:.3f} PnL delta vs normal. "
                "Fix B (boost suppression during recovery) should address this — verify it is active."
            ),
            "source_reports": ["Recovery Cycle Audit"],
        })


def _peak_r_insufficient(snapshots: dict, hits: list) -> None:
    perf = snapshots.get("Performance Status", {})
    peak_r = perf.get("peak_r_trades", 0)
    if peak_r < 300:
        hits.append({
            "rule": "PEAK_R_INSUFFICIENT",
            "category": "SYSTEM",
            "severity": "INFO",
            "title": f"Peak-R sample insufficient: {peak_r} trades",
            "evidence": [{"peak_r_trades": peak_r}],
            "confidence_score": 0.70,
            "sample_size": peak_r,
            "economic_impact_est": "LOW",
            "risk_level": "LOW",
            "recommendation": (
                f"Only {peak_r} trades have peak_r data (need 300+ for Fix C). "
                "This is INFO only — instrumentation is accumulating."
            ),
            "source_reports": ["Performance Status"],
        })


def _promotion_gate_impossible(snapshots: dict, hits: list) -> None:
    """
    PROMOTION_GATE_IMPOSSIBLE: fires when promotion_failure_audit verdict indicates
    a gate is structurally blocking every candidate, not just the unlucky ones.
    Requires Promotion Failure Audit snapshot to be present.
    """
    audit = snapshots.get("Promotion Failure Audit", {})
    verdict = audit.get("verdict", "")
    if verdict != "GATE_MAY_BE_STRUCTURALLY_IMPOSSIBLE":
        return
    metrics = audit.get("rejected_candidate_metrics", {})
    gate_breakdown = audit.get("gate_failure_breakdown", {})
    total_rejected = audit.get("summary", {}).get("total_rejected", 0)
    if total_rejected < 20:  # need meaningful sample before flagging
        return
    hits.append({
        "rule": "PROMOTION_GATE_IMPOSSIBLE",
        "category": "GENOME",
        "severity": "HIGH",
        "title": f"Genome promotion gate may be structurally impossible — {total_rejected} rejections, 0 promotions",
        "evidence": [{"verdict": verdict, "gate_breakdown": gate_breakdown, "metrics": metrics}],
        "confidence_score": 0.80,
        "sample_size": total_rejected,
        "economic_impact_est": "HIGH",
        "risk_level": "HIGH",
        "recommendation": (
            f"{audit.get('verdict_detail', '')} "
            "Human review required: determine whether threshold calibration is justified "
            "for current market conditions before any change."
        ),
        "source_reports": ["Promotion Failure Audit"],
    })
