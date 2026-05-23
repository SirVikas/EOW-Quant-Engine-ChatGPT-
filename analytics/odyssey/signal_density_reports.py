"""
PRP-002 Analytics — Signal Density Reports

Generates density, filter, and ecology forensic reports from:
  - SignalDensityEngine (signal flow health)
  - AdaptiveRSIGovernor (band-adaptive RSI governance)
  - OpportunityEcology (ecosystem coordination)

Reports produced:
  01_signal_density_health
  02_filter_survival_matrix
  06_signal_pipeline_heatmap
  07_filter_aggression_monitor
  09_participation_balance_report
  10_opportunity_ecology_report

Pure module — no I/O, no side effects. Fail-open on any engine error.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List


# ── Lazily imported to avoid circular startup issues ──────────────────────────

def _density():
    from core.signal_ecology.signal_density_engine import signal_density_engine
    return signal_density_engine

def _rsi_gov():
    from core.signal_ecology.adaptive_rsi_governor import adaptive_rsi_governor
    return adaptive_rsi_governor

def _ecology():
    from core.signal_ecology.opportunity_ecology import opportunity_ecology
    return opportunity_ecology


# ── Individual report generators ──────────────────────────────────────────────

def report_01_signal_density_health() -> Dict[str, Any]:
    """
    Current signal density health: signals/hr, survival rate,
    drought/starvation state, auto-recovery history.
    """
    try:
        t = _density().get_telemetry()
        survival = t.get("survival_rate", 0.0)
        sph      = t.get("signals_per_hr", 0.0)
        drought  = t.get("drought_seconds", 0.0)

        if t.get("is_starvation"):
            health_tier = "STARVATION"
        elif t.get("is_drought"):
            health_tier = "DROUGHT"
        elif survival < 0.10:
            health_tier = "CRITICAL"
        elif survival < 0.25:
            health_tier = "WEAK"
        elif survival < 0.50:
            health_tier = "ADEQUATE"
        else:
            health_tier = "HEALTHY"

        return {
            "report":            "01_signal_density_health",
            "prp":               "002",
            "health_tier":       health_tier,
            "signals_per_hr":    sph,
            "survival_rate":     survival,
            "is_drought":        t.get("is_drought", False),
            "is_starvation":     t.get("is_starvation", False),
            "drought_seconds":   drought,
            "total_evaluated":   t.get("total_evaluated", 0),
            "total_passed":      t.get("total_passed", 0),
            "total_blocked":     t.get("total_blocked", 0),
            "auto_recover_count": t.get("auto_recover_count", 0),
            "recent_snapshots":  t.get("recent_snapshots", [])[-10:],
            "generated_ts":      int(time.time() * 1000),
        }
    except Exception as exc:
        return {"report": "01_signal_density_health", "prp": "002", "error": str(exc),
                "generated_ts": int(time.time() * 1000)}


def report_02_filter_survival_matrix() -> Dict[str, Any]:
    """
    Filter survival matrix: per-regime survival rates and block-reason breakdown.
    Exposes which filters are killing the most opportunities.
    """
    try:
        t = _density().get_telemetry()
        regime_breakdown = t.get("regime_breakdown", {})
        block_reasons    = t.get("top_block_reasons", [])

        # Build regime matrix sorted by survival (worst first)
        regime_matrix = [
            {
                "regime":    r,
                "evaluated": d.get("evaluated", 0),
                "passed":    d.get("passed", 0),
                "survival":  d.get("survival", 0.0),
                "blocked":   d.get("evaluated", 0) - d.get("passed", 0),
            }
            for r, d in regime_breakdown.items()
        ]
        regime_matrix.sort(key=lambda x: x["survival"])

        total_blocked = t.get("total_blocked", 0)
        primary_killer = block_reasons[0]["reason"] if block_reasons else "none"

        return {
            "report":          "02_filter_survival_matrix",
            "prp":             "002",
            "regime_matrix":   regime_matrix,
            "block_reasons":   block_reasons,
            "primary_killer":  primary_killer,
            "total_blocked":   total_blocked,
            "regime_count":    len(regime_matrix),
            "generated_ts":    int(time.time() * 1000),
        }
    except Exception as exc:
        return {"report": "02_filter_survival_matrix", "prp": "002", "error": str(exc),
                "generated_ts": int(time.time() * 1000)}


def report_06_signal_pipeline_heatmap() -> Dict[str, Any]:
    """
    Signal pipeline heatmap: rolling survival/density snapshots over recent
    history, showing healthy and starvation periods across time.
    """
    try:
        t       = _density().get_telemetry()
        snaps   = t.get("recent_snapshots", [])
        rsi_t   = _rsi_gov().get_telemetry()

        drought_periods = [s for s in snaps if s.get("is_drought")]
        starv_periods   = [s for s in snaps if s.get("is_starvation")]

        avg_survival = (
            sum(s.get("survival_rate", 0) for s in snaps) / len(snaps)
            if snaps else 0.0
        )
        avg_sph = (
            sum(s.get("signals_per_hr", 0) for s in snaps) / len(snaps)
            if snaps else 0.0
        )

        band_state = rsi_t.get("bands", {})
        adapt_log  = rsi_t.get("adapt_log", [])[-10:]

        return {
            "report":              "06_signal_pipeline_heatmap",
            "prp":                 "002",
            "snapshot_count":      len(snaps),
            "drought_period_count": len(drought_periods),
            "starvation_period_count": len(starv_periods),
            "avg_survival_rate":   round(avg_survival, 4),
            "avg_signals_per_hr":  round(avg_sph, 2),
            "rsi_band_state":      band_state,
            "rsi_adapt_log":       adapt_log,
            "survival_by_regime":  rsi_t.get("survival_by_regime", {}),
            "heatmap_snapshots":   snaps[-20:],
            "generated_ts":        int(time.time() * 1000),
        }
    except Exception as exc:
        return {"report": "06_signal_pipeline_heatmap", "prp": "002", "error": str(exc),
                "generated_ts": int(time.time() * 1000)}


def report_07_filter_aggression_monitor() -> Dict[str, Any]:
    """
    Filter aggression monitor: evaluates whether RSI bands have drifted
    into hyper-suppression territory.
    """
    try:
        rsi_t = _rsi_gov().get_telemetry()
        bands = rsi_t.get("bands", {})
        total_eval   = rsi_t.get("total_evaluated", 0)
        total_passed = rsi_t.get("total_passed", 0)
        global_sr    = rsi_t.get("global_survival_rate", 0.0)

        # Score aggression: lower survival rate = higher aggression
        if global_sr < 0.05:
            aggression = "EXTREME"
        elif global_sr < 0.15:
            aggression = "HIGH"
        elif global_sr < 0.30:
            aggression = "MODERATE"
        elif global_sr < 0.50:
            aggression = "LOW"
        else:
            aggression = "BALANCED"

        band_tightness = {}
        for regime, state in bands.items():
            # Compute band width (long_rsi - short_rsi = total allowed window)
            long_rsi  = state.get("long_rsi", 70)
            short_rsi = state.get("short_rsi", 30)
            window    = long_rsi - short_rsi
            band_tightness[regime] = {
                "long_rsi":   long_rsi,
                "short_rsi":  short_rsi,
                "window_width": round(window, 2),
                "tight":      window < 20,
            }

        recent_decisions = rsi_t.get("recent_decisions", [])[-10:]
        passed_in_recent = sum(1 for d in recent_decisions if d.get("passed", False))

        return {
            "report":           "07_filter_aggression_monitor",
            "prp":              "002",
            "aggression_tier":  aggression,
            "global_survival":  global_sr,
            "total_evaluated":  total_eval,
            "total_passed":     total_passed,
            "band_tightness":   band_tightness,
            "recent_pass_rate": round(passed_in_recent / max(len(recent_decisions), 1), 3),
            "survival_by_regime": rsi_t.get("survival_by_regime", {}),
            "generated_ts":     int(time.time() * 1000),
        }
    except Exception as exc:
        return {"report": "07_filter_aggression_monitor", "prp": "002", "error": str(exc),
                "generated_ts": int(time.time() * 1000)}


def report_09_participation_balance_report() -> Dict[str, Any]:
    """
    Participation balance: overall pass/block ratio and ecological equilibrium.
    Assesses whether the organism is balanced vs fear-conditioned.
    """
    try:
        d_t = _density().get_telemetry()
        r_t = _rsi_gov().get_telemetry()

        total_eval   = d_t.get("total_evaluated", 0)
        total_passed = d_t.get("total_passed", 0)
        total_blocked = d_t.get("total_blocked", 0)
        survival     = d_t.get("survival_rate", 0.0)

        # Ecological balance score: 0-100
        # Target: survival rate 30-60% = balanced participation
        if 0.30 <= survival <= 0.60:
            balance_score = 100
            balance_label = "BALANCED"
        elif survival > 0.60:
            balance_score = max(0, int(100 - (survival - 0.60) * 200))
            balance_label = "UNDER_FILTERED"
        else:
            balance_score = max(0, int(survival / 0.30 * 100))
            if survival < 0.05:
                balance_label = "PARALYSIS"
            elif survival < 0.15:
                balance_label = "FEAR_CONDITIONED"
            else:
                balance_label = "SUPPRESSED"

        regime_balance = {}
        for regime, state in r_t.get("survival_by_regime", {}).items():
            sr = state if isinstance(state, float) else 0.0
            regime_balance[regime] = {
                "survival":   sr,
                "balanced":   0.20 <= sr <= 0.70,
                "fear_state": sr < 0.10,
            }

        return {
            "report":          "09_participation_balance_report",
            "prp":             "002",
            "balance_label":   balance_label,
            "balance_score":   balance_score,
            "survival_rate":   survival,
            "total_evaluated": total_eval,
            "total_passed":    total_passed,
            "total_blocked":   total_blocked,
            "pass_rate":       round(total_passed / total_eval, 4) if total_eval else 0.0,
            "regime_balance":  regime_balance,
            "is_drought":      d_t.get("is_drought", False),
            "is_starvation":   d_t.get("is_starvation", False),
            "generated_ts":    int(time.time() * 1000),
        }
    except Exception as exc:
        return {"report": "09_participation_balance_report", "prp": "002", "error": str(exc),
                "generated_ts": int(time.time() * 1000)}


def report_10_opportunity_ecology_report() -> Dict[str, Any]:
    """
    Full opportunity ecology summary: composite health score from all
    signal ecology sub-engines.
    """
    try:
        eco_t = _ecology().get_telemetry()
        d_t   = _density().get_telemetry()
        r_t   = _rsi_gov().get_telemetry()

        total_eval     = eco_t.get("total_evaluated", 0)
        total_approved = eco_t.get("total_approved", 0)
        approval_rate  = eco_t.get("approval_rate", 0.0)
        survival_rate  = d_t.get("survival_rate", 0.0)

        # Composite ecology score: simple heuristic
        s1 = min(100, int(survival_rate * 200))        # survival contribution (0-100, target 0.5 = 100)
        s2 = min(100, int(approval_rate * 200))        # approval contribution
        s3 = 100 if not d_t.get("is_drought") else 0  # drought penalty
        s4 = 100 if not d_t.get("is_starvation") else 0  # starvation penalty
        ecology_score = int((s1 + s2 + s3 + s4) / 4)

        if ecology_score >= 80:
            ecology_tier = "HEALTHY"
        elif ecology_score >= 60:
            ecology_tier = "ADEQUATE"
        elif ecology_score >= 40:
            ecology_tier = "WEAK"
        else:
            ecology_tier = "CRITICAL"

        return {
            "report":              "10_opportunity_ecology_report",
            "prp":                 "002",
            "ecology_tier":        ecology_tier,
            "ecology_score":       ecology_score,
            "approval_rate":       approval_rate,
            "survival_rate":       survival_rate,
            "total_evaluated":     total_eval,
            "total_approved":      total_approved,
            "total_rsi_blocked":   eco_t.get("total_rsi_blocked", 0),
            "total_ctx_blocked":   eco_t.get("total_ctx_blocked", 0),
            "total_recovery_trades": eco_t.get("total_recovery_trades", 0),
            "is_drought":          d_t.get("is_drought", False),
            "is_starvation":       d_t.get("is_starvation", False),
            "global_survival":     r_t.get("global_survival_rate", 0.0),
            "auto_recover_count":  d_t.get("auto_recover_count", 0),
            "generated_ts":        int(time.time() * 1000),
        }
    except Exception as exc:
        return {"report": "10_opportunity_ecology_report", "prp": "002", "error": str(exc),
                "generated_ts": int(time.time() * 1000)}


# ── Bundle API ────────────────────────────────────────────────────────────────

def generate_all_reports() -> Dict[str, Any]:
    """Generate all density-side PRP-002 forensic reports as a bundle."""
    return {
        "prp":          "002",
        "module":       "signal_density_reports",
        "generated_ts": int(time.time() * 1000),
        "reports": {
            "01_signal_density_health":      report_01_signal_density_health(),
            "02_filter_survival_matrix":     report_02_filter_survival_matrix(),
            "06_signal_pipeline_heatmap":    report_06_signal_pipeline_heatmap(),
            "07_filter_aggression_monitor":  report_07_filter_aggression_monitor(),
            "09_participation_balance_report": report_09_participation_balance_report(),
            "10_opportunity_ecology_report": report_10_opportunity_ecology_report(),
        },
    }
