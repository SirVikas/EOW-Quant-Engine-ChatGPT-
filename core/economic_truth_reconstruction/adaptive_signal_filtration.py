"""
PRP-PHASED.6 — Adaptive Signal Filtration Engine.

Identifies low-quality signal clusters for operator awareness. Does NOT
autonomously suppress or filter trades — it reports what would be filtered
and why, leaving the filtering decision to human governance.

Filtration targets:
  - low-quality signal clusters (consistently negative expectancy groups)
  - unstable expectancy zones (high variance, low evidence)
  - fee-toxic trade patterns (fee drag dominant)
  - ecological saturation (too many trades in collapsed ecology)
  - volatility traps (high vol regime with adverse outcomes)
  - confidence hallucinations (high-confidence trades with negative outcomes)

Doctrine: Never inflate results, hide losses, cherry-pick survivability,
or suppress contradictory evidence.

DIAGNOSTIC ONLY — no execution authority, no deployment authority.

Pure module — accepts trades: List[dict], no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from collections import defaultdict
from statistics import mean, stdev
from typing import Any, Dict, List, Optional


_MIN_CLUSTER_SAMPLE = 5
_FEE_DRAG_TOXIC_THRESHOLD = 70.0  # % of gross consumed by fees = toxic
_HIGH_CONFIDENCE_THRESHOLD = 0.75  # decision_snapshot.confidence above this = "high confidence"


def _net(t: dict) -> float:
    return t.get("net_pnl", 0.0)


def _gross(t: dict) -> float:
    return t.get("gross_pnl", 0.0)


def _fees(t: dict) -> float:
    return t.get("fee_entry", 0.0) + t.get("fee_exit", 0.0) + t.get("slippage_cost", 0.0)


def _fee_drag_pct(t: dict) -> Optional[float]:
    gross = _gross(t)
    if gross <= 1e-9:
        return None
    fee = _fees(t)
    return round(fee / gross * 100.0, 2)


def _cluster_stats(trades: List[dict]) -> Dict[str, Any]:
    nets = [_net(t) for t in trades]
    net_exp = round(mean(nets), 4)
    wins = [t for t in trades if _net(t) > 0]
    stability: Optional[float] = None
    if len(nets) >= 3 and abs(net_exp) > 1e-9:
        try:
            stability = round(stdev(nets) / abs(net_exp), 2)
        except Exception:
            pass
    return {
        "count":         len(trades),
        "net_expectancy": net_exp,
        "win_rate":       round(len(wins) / len(trades) * 100, 1),
        "stability_coeff": stability,
    }


def compute_adaptive_filtration(trades: List[dict]) -> dict:
    """
    PRP-PHASED.6 — Identify signal clusters qualifying for adaptive filtration.

    Reports what would be filtered and why. Filtering is advisory — no trades
    are suppressed, no results are cherry-picked.

    Args:
        trades: Combined session + historical trade dicts.

    Returns ADAPTIVE_SIGNAL_FILTRATION_REPORT; never raises.
    """
    filtration_candidates: List[dict] = []  # clusters recommended for filtration
    contradictory_evidence: List[dict] = []  # evidence that contradicts filtration

    try:
        if not trades:
            return {
                "report":                  "ADAPTIVE_SIGNAL_FILTRATION_REPORT",
                "total_trades":            0,
                "note":                    "No trades available.",
                "filtration_candidates":   [],
                "candidate_count":         0,
                "contradictory_evidence":  [],
                "filtration_score":        0,
                "filtration_verdict":      "NO_DATA",
                "cluster_analysis":        {},
                "diagnostic_only":         True,
                "auto_authorized":         False,
                "generated_ts":            int(_time.time() * 1000),
            }

        cluster_analysis: Dict[str, Any] = {}

        # ── Filter 1: Low-quality signal clusters (by session + regime) ────────
        dim_groups: Dict[str, List[dict]] = defaultdict(list)
        for t in trades:
            key = (
                f"{t.get('origin_session', 'UNKNOWN') or 'UNKNOWN'}"
                f"|{t.get('regime', 'UNKNOWN') or 'UNKNOWN'}"
            )
            dim_groups[key].append(t)

        low_quality: List[dict] = []
        for key, group in sorted(dim_groups.items()):
            if len(group) < _MIN_CLUSTER_SAMPLE:
                continue
            stats = _cluster_stats(group)
            if stats["net_expectancy"] < 0 and stats["win_rate"] < 35:
                low_quality.append({
                    "filter": "LOW_QUALITY_CLUSTER",
                    "cluster": key,
                    **stats,
                    "rationale": "Consistently negative expectancy and sub-35% win rate",
                })
        cluster_analysis["low_quality_clusters"] = low_quality
        filtration_candidates.extend(low_quality)

        # ── Filter 2: Unstable expectancy zones (high variance) ───────────────
        unstable: List[dict] = []
        for key, group in sorted(dim_groups.items()):
            if len(group) < _MIN_CLUSTER_SAMPLE:
                continue
            stats = _cluster_stats(group)
            sc = stats.get("stability_coeff")
            if sc is not None and sc > 3.0 and len(group) < 20:
                unstable.append({
                    "filter": "UNSTABLE_EXPECTANCY",
                    "cluster": key,
                    **stats,
                    "rationale": f"High variance (stability_coeff={sc}) with low evidence",
                })
        cluster_analysis["unstable_zones"] = unstable
        filtration_candidates.extend(unstable)

        # ── Filter 3: Fee-toxic trade patterns ────────────────────────────────
        fee_toxic_trades = [t for t in trades
                             if _fee_drag_pct(t) is not None
                             and _fee_drag_pct(t) >= _FEE_DRAG_TOXIC_THRESHOLD]
        fee_toxic_pct = round(len(fee_toxic_trades) / len(trades) * 100, 1)
        if fee_toxic_pct >= 30:
            filtration_candidates.append({
                "filter": "FEE_TOXIC_PATTERNS",
                "cluster": "GLOBAL",
                "count": len(fee_toxic_trades),
                "fee_toxic_pct": fee_toxic_pct,
                "rationale": (
                    f"{fee_toxic_pct}% of trades have fee drag ≥{_FEE_DRAG_TOXIC_THRESHOLD}% "
                    "— execution cost destroying gross edge"
                ),
            })
        cluster_analysis["fee_toxic"] = {
            "count": len(fee_toxic_trades),
            "pct":   fee_toxic_pct,
        }

        # ── Filter 4: Ecological saturation (fast trade clusters) ─────────────
        fast_trades = [t for t in trades
                       if max(0.0, (t.get("exit_ts", 0) or 0) - (t.get("entry_ts", 0) or 0)) / 1000 < 60]
        if len(fast_trades) >= _MIN_CLUSTER_SAMPLE:
            fast_stats = _cluster_stats(fast_trades)
            if fast_stats["net_expectancy"] < 0:
                filtration_candidates.append({
                    "filter": "ECOLOGICAL_SATURATION",
                    "cluster": "FAST_TRADES",
                    **fast_stats,
                    "rationale": "Fast trades (<60s) have negative expectancy — ecological overload",
                })
        cluster_analysis["fast_trades"] = {"count": len(fast_trades)}

        # ── Filter 5: Volatility traps ────────────────────────────────────────
        vol_exp_trades = [t for t in trades
                          if (t.get("regime") or "").upper() == "VOLATILITY_EXPANSION"]
        if len(vol_exp_trades) >= _MIN_CLUSTER_SAMPLE:
            vol_stats = _cluster_stats(vol_exp_trades)
            if vol_stats["net_expectancy"] < 0:
                filtration_candidates.append({
                    "filter": "VOLATILITY_TRAP",
                    "cluster": "VOLATILITY_EXPANSION",
                    **vol_stats,
                    "rationale": "VOLATILITY_EXPANSION regime producing negative expectancy",
                })
        cluster_analysis["volatility_trap"] = {"count": len(vol_exp_trades)}

        # ── Filter 6: Confidence hallucinations ───────────────────────────────
        high_conf_trades = [t for t in trades
                             if (t.get("decision_snapshot") or {}).get("confidence", 0.0) or 0.0
                             >= _HIGH_CONFIDENCE_THRESHOLD]
        if len(high_conf_trades) >= _MIN_CLUSTER_SAMPLE:
            hc_stats = _cluster_stats(high_conf_trades)
            if hc_stats["net_expectancy"] < 0:
                filtration_candidates.append({
                    "filter": "CONFIDENCE_HALLUCINATION",
                    "cluster": "HIGH_CONFIDENCE",
                    **hc_stats,
                    "rationale": (
                        f"High-confidence trades (conf≥{_HIGH_CONFIDENCE_THRESHOLD}) "
                        "produce negative expectancy — confidence signal unreliable"
                    ),
                })
        cluster_analysis["confidence_hallucination"] = {"count": len(high_conf_trades)}

        # ── Contradictory evidence (NEVER suppressed) ─────────────────────────
        # Positive pockets that contradict the filtration narrative
        for key, group in sorted(dim_groups.items()):
            if len(group) < _MIN_CLUSTER_SAMPLE:
                continue
            stats = _cluster_stats(group)
            if stats["net_expectancy"] > 0 and stats["win_rate"] >= 40:
                contradictory_evidence.append({
                    "cluster": key,
                    **stats,
                    "note": "Positive pocket — contradicts filtration narrative",
                })

        # ── Filtration scoring ────────────────────────────────────────────────
        total = len(trades)
        candidate_trade_count = sum(c.get("count", 0) for c in filtration_candidates
                                     if "count" in c)
        filtration_score = round(
            min(100, candidate_trade_count / total * 100)
        ) if total else 0

        if filtration_score >= 60:
            verdict = "HIGH_FILTRATION_NEED"
        elif filtration_score >= 30:
            verdict = "MODERATE_FILTRATION_NEED"
        elif filtration_score >= 10:
            verdict = "LOW_FILTRATION_NEED"
        else:
            verdict = "MINIMAL_FILTRATION_NEED"

        return {
            "report":                  "ADAPTIVE_SIGNAL_FILTRATION_REPORT",
            "total_trades":            total,
            "filtration_candidates":   filtration_candidates,
            "candidate_count":         len(filtration_candidates),
            "contradictory_evidence":  contradictory_evidence,
            "contradictory_count":     len(contradictory_evidence),
            "filtration_score":        filtration_score,
            "filtration_verdict":      verdict,
            "cluster_analysis":        cluster_analysis,
            "diagnostic_only":         True,
            "auto_authorized":         False,
            "generated_ts":            int(_time.time() * 1000),
        }

    except Exception as exc:
        return {
            "report":                  "ADAPTIVE_SIGNAL_FILTRATION_REPORT",
            "error":                   str(exc),
            "total_trades":            len(trades) if trades else 0,
            "filtration_candidates":   [],
            "candidate_count":         0,
            "contradictory_evidence":  [],
            "contradictory_count":     0,
            "filtration_score":        0,
            "filtration_verdict":      "ERROR",
            "cluster_analysis":        {},
            "diagnostic_only":         True,
            "auto_authorized":         False,
            "generated_ts":            int(_time.time() * 1000),
        }
