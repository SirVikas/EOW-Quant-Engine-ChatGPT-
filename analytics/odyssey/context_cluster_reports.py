"""
PRP-002 Analytics — Context Cluster Reports

Generates alpha context memory and recurrence forensic reports from:
  - AlphaContextMemory (profitable/toxic context tracking)

Reports produced:
  04_alpha_context_clusters
  05_context_recurrence_engine

Also exposes generate_full_prp002_bundle() which assembles all 10 PRP-002
reports from the three analytics modules into one exportable payload.

Pure module — no I/O, no side effects. Fail-open on any engine error.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List


def _acm():
    from core.signal_ecology.alpha_context_memory import alpha_context_memory
    return alpha_context_memory


# ── Individual report generators ──────────────────────────────────────────────

def report_04_alpha_context_clusters() -> Dict[str, Any]:
    """
    Alpha context clusters: top profitable, top toxic, and neutral context
    distribution. Reveals which regime/hour/strategy combinations have
    demonstrated economically meaningful edge.
    """
    try:
        t = _acm().get_telemetry()
        clusters = _acm().context_clusters(n=50)

        profitable = [c for c in clusters if c.get("context_type") == "PROFITABLE"
                      if c.get("avg_pnl", 0) > 0]
        toxic      = [c for c in clusters if c.get("avg_pnl", 0) < -0.30
                      and c.get("n_trades", 0) >= 5]

        # Parse regime distribution from context keys
        regime_dist: Dict[str, int] = {}
        for c in clusters:
            key = c.get("context_key", "")
            parts = key.split("|")
            regime = parts[0] if parts else "UNKNOWN"
            regime_dist[regime] = regime_dist.get(regime, 0) + 1

        # Best and worst contexts
        top5_profitable = sorted(clusters, key=lambda c: c.get("avg_pnl", 0), reverse=True)[:5]
        top5_toxic      = sorted(clusters, key=lambda c: c.get("avg_pnl", 0))[:5]

        return {
            "report":             "04_alpha_context_clusters",
            "prp":                "002",
            "total_contexts":     t.get("total_contexts", 0),
            "profitable_count":   t.get("profitable_count", 0),
            "toxic_count":        t.get("toxic_count", 0),
            "lookup_count":       t.get("lookup_count", 0),
            "boost_count":        t.get("boost_count", 0),
            "block_count":        t.get("block_count", 0),
            "regime_distribution": regime_dist,
            "top_profitable":     top5_profitable,
            "top_toxic":          top5_toxic,
            "all_clusters":       clusters[:20],
            "generated_ts":       int(time.time() * 1000),
        }
    except Exception as exc:
        return {"report": "04_alpha_context_clusters", "prp": "002", "error": str(exc),
                "generated_ts": int(time.time() * 1000)}


def report_05_context_recurrence_engine() -> Dict[str, Any]:
    """
    Context recurrence analysis: which contexts appear most often,
    boost-to-block ratio, and amplification effectiveness summary.
    """
    try:
        t = _acm().get_telemetry()
        clusters = _acm().context_clusters(n=100)

        total_contexts = t.get("total_contexts", 0)
        boost_count    = t.get("boost_count", 0)
        block_count    = t.get("block_count", 0)
        lookup_count   = t.get("lookup_count", 0)

        # Recurrence by visit count
        high_recurrence  = [c for c in clusters if c.get("n_trades", 0) >= 20]
        mid_recurrence   = [c for c in clusters if 10 <= c.get("n_trades", 0) < 20]
        low_recurrence   = [c for c in clusters if 5  <= c.get("n_trades", 0) < 10]

        # Amplification effectiveness
        boost_rate = round(boost_count / lookup_count, 4) if lookup_count else 0.0
        block_rate = round(block_count / lookup_count, 4) if lookup_count else 0.0

        # Most-visited contexts
        top_visited = sorted(clusters, key=lambda c: c.get("n_trades", 0), reverse=True)[:10]

        # Regime-hour heat: find densest (regime, hour) combinations
        regime_hour_map: Dict[str, Dict] = {}
        for c in clusters:
            key = c.get("context_key", "")
            parts = key.split("|")
            if len(parts) >= 2:
                rh_key = f"{parts[0]}|{parts[1]}"
                if rh_key not in regime_hour_map:
                    regime_hour_map[rh_key] = {"trades": 0, "contexts": 0, "total_pnl": 0.0}
                regime_hour_map[rh_key]["trades"]    += c.get("n_trades", 0)
                regime_hour_map[rh_key]["contexts"]  += 1
                regime_hour_map[rh_key]["total_pnl"] += c.get("avg_pnl", 0.0) * c.get("n_trades", 0)

        hottest_regime_hours = sorted(
            [{"key": k, **v} for k, v in regime_hour_map.items()],
            key=lambda x: x["trades"], reverse=True
        )[:10]

        return {
            "report":                "05_context_recurrence_engine",
            "prp":                   "002",
            "total_contexts":        total_contexts,
            "high_recurrence_count": len(high_recurrence),
            "mid_recurrence_count":  len(mid_recurrence),
            "low_recurrence_count":  len(low_recurrence),
            "lookup_count":          lookup_count,
            "boost_rate":            boost_rate,
            "block_rate":            block_rate,
            "top_visited_contexts":  top_visited,
            "hottest_regime_hours":  hottest_regime_hours,
            "generated_ts":          int(time.time() * 1000),
        }
    except Exception as exc:
        return {"report": "05_context_recurrence_engine", "prp": "002", "error": str(exc),
                "generated_ts": int(time.time() * 1000)}


# ── Bundle API ────────────────────────────────────────────────────────────────

def generate_all_reports() -> Dict[str, Any]:
    """Generate all context-side PRP-002 forensic reports as a bundle."""
    return {
        "prp":          "002",
        "module":       "context_cluster_reports",
        "generated_ts": int(time.time() * 1000),
        "reports": {
            "04_alpha_context_clusters":    report_04_alpha_context_clusters(),
            "05_context_recurrence_engine": report_05_context_recurrence_engine(),
        },
    }


def generate_full_prp002_bundle() -> Dict[str, Any]:
    """
    Assemble all 10 PRP-002 forensic reports into a single exportable bundle.

    Pulls from all three analytics modules:
      signal_density_reports  → 01, 02, 06, 07, 09, 10
      exploration_reports     → 03, 08
      context_cluster_reports → 04, 05
    """
    try:
        from analytics.odyssey.signal_density_reports import generate_all_reports as density_reports
        from analytics.odyssey.exploration_reports     import generate_all_reports as explore_reports

        density_bundle  = density_reports().get("reports", {})
        explore_bundle  = explore_reports().get("reports", {})
        context_bundle  = generate_all_reports().get("reports", {})

        all_reports = {
            **density_bundle,
            **explore_bundle,
            **context_bundle,
        }
        report_count = len(all_reports)

        return {
            "prp":            "002",
            "phase":          "OPPORTUNITY_ECOLOGY_RECOVERY",
            "report_count":   report_count,
            "complete":       report_count == 10,
            "generated_ts":   int(time.time() * 1000),
            "reports":        all_reports,
        }
    except Exception as exc:
        return {
            "prp":          "002",
            "phase":        "OPPORTUNITY_ECOLOGY_RECOVERY",
            "report_count": 0,
            "complete":     False,
            "error":        str(exc),
            "generated_ts": int(time.time() * 1000),
        }
