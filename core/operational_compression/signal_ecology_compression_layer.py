"""
PRP-PHASEC.4 — Signal Ecology Compression Layer.

Compresses signal ecology intelligence across 8 operational domains into a
single operator-readable report. Truth density is prioritised — results are
reported without optimistic inflation even when states are negative.

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from typing import Any, Dict, List, Optional


def _score_tier(score: int) -> str:
    if score >= 80:
        return "HEALTHY"
    if score >= 60:
        return "ADEQUATE"
    if score >= 40:
        return "DEGRADED"
    return "CRITICAL"


def _density() -> Any:
    from core.signal_ecology.signal_density_engine import signal_density_engine
    return signal_density_engine


def _ecology() -> Any:
    from core.signal_ecology.opportunity_ecology import opportunity_ecology
    return opportunity_ecology


def _rsi() -> Any:
    from core.signal_ecology.adaptive_rsi_governor import adaptive_rsi_governor
    return adaptive_rsi_governor


def _recovery() -> Any:
    from core.signal_ecology.exploration_recovery import exploration_recovery_governor
    return exploration_recovery_governor


def _acm() -> Any:
    from core.signal_ecology.alpha_context_memory import alpha_context_memory
    return alpha_context_memory


def compress_signal_ecology() -> dict:
    """
    PRP-PHASEC.4 — Compress signal ecology state into operator-readable view.

    Domains covered:
      signal_survivability, expectancy_condition, fee_drag_state,
      ecological_collapse_risk, session_viability, strategy_density,
      alpha_concentration, regime_instability.

    Returns a self-contained dict; never raises.
    """
    domains: Dict[str, Any] = {}
    alerts: List[str] = []
    score_sum: float = 0.0
    domain_count: int = 0

    # ── Domain 1: Signal Survivability ────────────────────────────────────────
    try:
        t = _density().get_telemetry()
        survival_rate = t.get("survival_rate", 0.0)
        is_drought    = t.get("is_drought", False)
        is_starvation = t.get("is_starvation", False)
        drought_sec   = t.get("drought_seconds", 0.0)
        sph           = t.get("signals_per_hr", 0.0)

        if is_starvation:
            sv_score = 20
            sv_state = "STARVATION"
            alerts.append("Signal starvation active")
        elif is_drought:
            sv_score = 45
            sv_state = "DROUGHT"
            alerts.append("Signal drought detected")
        elif survival_rate < 0.10:
            sv_score = 50
            sv_state = "LOW_SURVIVAL"
        else:
            sv_score = min(100, round(survival_rate * 100))
            sv_state = "NORMAL"

        domains["signal_survivability"] = {
            "state":         sv_state,
            "survival_rate": round(survival_rate, 4),
            "signals_per_hr": sph,
            "is_drought":    is_drought,
            "is_starvation": is_starvation,
            "drought_sec":   round(drought_sec, 1),
            "score":         sv_score,
        }
        score_sum   += sv_score
        domain_count += 1
    except Exception as exc:
        domains["signal_survivability"] = {"state": "UNKNOWN", "error": str(exc), "score": 0}
        score_sum   += 0
        domain_count += 1

    # ── Domain 2: Expectancy Condition ────────────────────────────────────────
    try:
        t = _ecology().get_telemetry()
        approval_rate = t.get("approval_rate", 0.0)
        total_eval    = t.get("total_evaluated", 0)
        total_appr    = t.get("total_approved", 0)

        if approval_rate >= 0.40:
            ex_score = 90
            ex_state = "STRONG"
        elif approval_rate >= 0.20:
            ex_score = 65
            ex_state = "MODERATE"
        elif approval_rate >= 0.05:
            ex_score = 40
            ex_state = "WEAK"
        elif total_eval == 0:
            ex_score = 50  # no data yet — neutral
            ex_state = "NO_DATA"
        else:
            ex_score = 20
            ex_state = "COLLAPSED"
            alerts.append("Ecology approval collapsed")

        domains["expectancy_condition"] = {
            "state":         ex_state,
            "approval_rate": round(approval_rate, 4),
            "total_evaluated": total_eval,
            "total_approved":  total_appr,
            "score":           ex_score,
        }
        score_sum   += ex_score
        domain_count += 1
    except Exception as exc:
        domains["expectancy_condition"] = {"state": "UNKNOWN", "error": str(exc), "score": 0}
        score_sum   += 0
        domain_count += 1

    # ── Domain 3: Fee Drag State ──────────────────────────────────────────────
    # Estimated from block reasons; we flag if fee-related blocks are prominent.
    try:
        t = _density().get_telemetry()
        top_reasons = t.get("top_block_reasons", [])
        total_blocked = t.get("total_blocked", 0)
        fee_blocks = sum(r["count"] for r in top_reasons
                         if "fee" in r.get("reason", "").lower())
        fee_drag_pct = round(fee_blocks / total_blocked * 100, 1) if total_blocked > 0 else 0.0

        if fee_drag_pct >= 40:
            fd_score = 30
            fd_state = "CRITICAL"
            alerts.append(f"Fee drag dominant: {fee_drag_pct}% of blocks")
        elif fee_drag_pct >= 20:
            fd_score = 60
            fd_state = "ELEVATED"
        else:
            fd_score = 90
            fd_state = "ACCEPTABLE"

        domains["fee_drag_state"] = {
            "state":        fd_state,
            "fee_drag_pct": fee_drag_pct,
            "fee_blocks":   fee_blocks,
            "total_blocked": total_blocked,
            "score":        fd_score,
        }
        score_sum   += fd_score
        domain_count += 1
    except Exception as exc:
        domains["fee_drag_state"] = {"state": "UNKNOWN", "error": str(exc), "score": 50}
        score_sum   += 50
        domain_count += 1

    # ── Domain 4: Ecological Collapse Risk ───────────────────────────────────
    try:
        t = _recovery().get_telemetry()
        consec_blocks  = t.get("consecutive_blocks", 0)
        active_cycle   = t.get("active_cycle_id")
        total_rec      = t.get("total_recoveries", 0)
        drought_sec    = t.get("drought_seconds", 0.0)

        if consec_blocks >= 200 or drought_sec >= 900:
            ecr_score = 10
            ecr_state = "CRITICAL_RISK"
            alerts.append("Ecological collapse risk: CRITICAL")
        elif consec_blocks >= 100 or drought_sec >= 600:
            ecr_score = 30
            ecr_state = "HIGH_RISK"
            alerts.append("Ecological collapse risk: HIGH")
        elif consec_blocks >= 50 or drought_sec >= 300:
            ecr_score = 55
            ecr_state = "MODERATE_RISK"
        elif active_cycle:
            ecr_score = 70
            ecr_state = "RECOVERY_ACTIVE"
        else:
            ecr_score = 90
            ecr_state = "NOMINAL"

        domains["ecological_collapse_risk"] = {
            "state":            ecr_state,
            "consecutive_blocks": consec_blocks,
            "active_recovery":  bool(active_cycle),
            "total_recoveries": total_rec,
            "drought_sec":      round(drought_sec, 1),
            "score":            ecr_score,
        }
        score_sum   += ecr_score
        domain_count += 1
    except Exception as exc:
        domains["ecological_collapse_risk"] = {"state": "UNKNOWN", "error": str(exc), "score": 0}
        score_sum   += 0
        domain_count += 1

    # ── Domain 5: Session Viability ──────────────────────────────────────────
    try:
        t = _ecology().get_telemetry()
        density_snap  = t.get("density_snapshot", {})
        sph           = density_snap.get("signals_per_hr", 0.0)
        is_starvation = density_snap.get("is_starvation", False)
        is_drought    = density_snap.get("is_drought", False)

        if is_starvation:
            sv2_score = 15
            sv2_state = "NOT_VIABLE"
            alerts.append("Session viability: NOT VIABLE")
        elif is_drought:
            sv2_score = 40
            sv2_state = "MARGINAL"
        elif sph < 1.0:
            sv2_score = 55
            sv2_state = "LOW_ACTIVITY"
        elif sph >= 10.0:
            sv2_score = 100
            sv2_state = "HIGH_ACTIVITY"
        else:
            sv2_score = 80
            sv2_state = "NORMAL"

        domains["session_viability"] = {
            "state":         sv2_state,
            "signals_per_hr": sph,
            "is_starvation": is_starvation,
            "is_drought":    is_drought,
            "score":         sv2_score,
        }
        score_sum   += sv2_score
        domain_count += 1
    except Exception as exc:
        domains["session_viability"] = {"state": "UNKNOWN", "error": str(exc), "score": 0}
        score_sum   += 0
        domain_count += 1

    # ── Domain 6: Strategy Density ───────────────────────────────────────────
    try:
        t = _rsi().get_telemetry()
        global_sr   = t.get("global_survival_rate", 0.0)
        sr_by_regime = t.get("survival_by_regime", {})
        regime_count = len(sr_by_regime)

        active_regimes = sum(1 for v in sr_by_regime.values() if v >= 0.10)

        if global_sr >= 0.40:
            sd_score = 90
            sd_state = "DENSE"
        elif global_sr >= 0.20:
            sd_score = 65
            sd_state = "ADEQUATE"
        elif global_sr >= 0.05:
            sd_score = 40
            sd_state = "SPARSE"
        else:
            sd_score = 15
            sd_state = "DEPLETED"
            if regime_count > 0:
                alerts.append("Strategy density depleted")

        domains["strategy_density"] = {
            "state":          sd_state,
            "global_survival": round(global_sr, 4),
            "regime_count":   regime_count,
            "active_regimes": active_regimes,
            "score":          sd_score,
        }
        score_sum   += sd_score
        domain_count += 1
    except Exception as exc:
        domains["strategy_density"] = {"state": "UNKNOWN", "error": str(exc), "score": 0}
        score_sum   += 0
        domain_count += 1

    # ── Domain 7: Alpha Concentration ────────────────────────────────────────
    try:
        t = _acm().get_telemetry()
        total_ctx   = t.get("total_contexts", 0)
        profitable  = t.get("profitable_count", 0)
        toxic       = t.get("toxic_count", 0)
        boost_count = t.get("boost_count", 0)
        block_count = t.get("block_count", 0)

        if total_ctx == 0:
            ac_score = 50
            ac_state = "NO_DATA"
        else:
            profit_ratio = profitable / total_ctx
            toxic_ratio  = toxic / total_ctx
            if profit_ratio >= 0.40:
                ac_score = 90
                ac_state = "HIGH_ALPHA"
            elif profit_ratio >= 0.20:
                ac_score = 70
                ac_state = "MODERATE_ALPHA"
            elif toxic_ratio >= 0.40:
                ac_score = 20
                ac_state = "TOXIC_DOMINANT"
                alerts.append("Alpha concentration: toxic dominant")
            else:
                ac_score = 45
                ac_state = "LOW_ALPHA"

        domains["alpha_concentration"] = {
            "state":          ac_state,
            "total_contexts": total_ctx,
            "profitable":     profitable,
            "toxic":          toxic,
            "boost_count":    boost_count,
            "block_count":    block_count,
            "score":          ac_score,
        }
        score_sum   += ac_score
        domain_count += 1
    except Exception as exc:
        domains["alpha_concentration"] = {"state": "UNKNOWN", "error": str(exc), "score": 0}
        score_sum   += 0
        domain_count += 1

    # ── Domain 8: Regime Instability ─────────────────────────────────────────
    try:
        t = _rsi().get_telemetry()
        sr_by_regime  = t.get("survival_by_regime", {})
        adapt_log     = t.get("adapt_log", [])

        if not sr_by_regime:
            ri_score = 50
            ri_state = "NO_DATA"
            instability_count = 0
        else:
            rates     = list(sr_by_regime.values())
            avg_rate  = sum(rates) / len(rates) if rates else 0.0
            variance  = (sum((r - avg_rate) ** 2 for r in rates) / len(rates)) if rates else 0.0
            std_dev   = variance ** 0.5
            adapt_count = len(adapt_log)
            instability_count = adapt_count

            if std_dev >= 0.30 or adapt_count >= 20:
                ri_score = 25
                ri_state = "HIGH_INSTABILITY"
                alerts.append("Regime instability: HIGH")
            elif std_dev >= 0.15 or adapt_count >= 10:
                ri_score = 55
                ri_state = "MODERATE_INSTABILITY"
            else:
                ri_score = 85
                ri_state = "STABLE"

        domains["regime_instability"] = {
            "state":              ri_state,
            "regimes_tracked":    len(sr_by_regime),
            "instability_events": instability_count,
            "survival_by_regime": sr_by_regime,
            "score":              ri_score,
        }
        score_sum   += ri_score
        domain_count += 1
    except Exception as exc:
        domains["regime_instability"] = {"state": "UNKNOWN", "error": str(exc), "score": 0}
        score_sum   += 0
        domain_count += 1

    # ── Composite ecology score ───────────────────────────────────────────────
    ecology_score = round(score_sum / domain_count) if domain_count else 0
    ecology_score = max(0, min(100, ecology_score))

    return {
        "report":          "SIGNAL_ECOLOGY_SUMMARY_REPORT",
        "ecology_score":   ecology_score,
        "ecology_tier":    _score_tier(ecology_score),
        "domain_count":    domain_count,
        "domains":         domains,
        "alerts":          alerts,
        "alert_count":     len(alerts),
        "auto_authorized": False,
        "generated_ts":    int(_time.time() * 1000),
    }
