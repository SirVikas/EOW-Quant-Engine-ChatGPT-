"""
PRP-PHASED.7 — Economic Truth Orchestrator.

Centralised economic survivability governance. Runs all 6 Phase-D engines,
generates a unified ECONOMIC_TRUTH_REPORT with a deterministic lineage ID
and replay-safe economic synthesis.

Economic ID format: ECO-{ts_ms}-{sha256[:16]}

DIAGNOSTIC ONLY — no execution authority, no deployment authority.

Pure module — accepts trades: List[dict], no side effects. Import-safe.
"""
from __future__ import annotations

import hashlib
import json
import time as _time
from statistics import mean
from typing import Any, Dict, List, Optional


def _make_economic_id(ts_ms: int, payload: str) -> str:
    digest = hashlib.sha256(payload.encode("utf-8", errors="replace")).hexdigest()
    return f"ECO-{ts_ms}-{digest[:16]}"


def _score_tier(score: int) -> str:
    if score >= 75:
        return "VIABLE"
    if score >= 50:
        return "MARGINAL"
    if score >= 25:
        return "WEAK"
    return "CRITICAL"


def run_economic_truth(trades: List[dict]) -> dict:
    """
    PRP-PHASED.7 — Run all Phase-D economic truth engines and synthesise results.

    Engine execution order:
      1. expectancy_reconstruction     → EXPECTANCY_RECONSTRUCTION_REPORT
      2. fee_drag_intelligence         → FEE_DRAG_INTELLIGENCE_REPORT
      3. survivable_alpha_detector     → SURVIVABLE_ALPHA_REPORT
      4. ecological_collapse_detector  → ECOLOGICAL_COLLAPSE_REPORT
      5. regime_survivability_engine   → REGIME_SURVIVABILITY_REPORT
      6. adaptive_signal_filtration    → ADAPTIVE_SIGNAL_FILTRATION_REPORT

    Args:
        trades: Combined session + historical trade dicts.

    Returns ECONOMIC_TRUTH_REPORT; never raises.
    """
    ts_ms: int = int(_time.time() * 1000)
    domain_reports: Dict[str, Any] = {}
    domain_errors:  List[str]      = []

    # ── Engine 1: Expectancy Reconstruction ──────────────────────────────────
    try:
        from core.economic_truth_reconstruction.expectancy_reconstruction import (
            compute_expectancy_reconstruction,
        )
        r = compute_expectancy_reconstruction(trades)
        domain_reports["expectancy"] = r
    except Exception as exc:
        domain_errors.append(f"expectancy: {exc}")
        domain_reports["expectancy"] = {"error": str(exc)}

    # ── Engine 2: Fee Drag Intelligence ───────────────────────────────────────
    try:
        from core.economic_truth_reconstruction.fee_drag_intelligence import (
            compute_fee_drag_intelligence,
        )
        r = compute_fee_drag_intelligence(trades)
        domain_reports["fee_drag"] = r
    except Exception as exc:
        domain_errors.append(f"fee_drag: {exc}")
        domain_reports["fee_drag"] = {"error": str(exc)}

    # ── Engine 3: Survivable Alpha ─────────────────────────────────────────────
    try:
        from core.economic_truth_reconstruction.survivable_alpha_detector import (
            detect_survivable_alpha,
        )
        r = detect_survivable_alpha(trades)
        domain_reports["alpha"] = r
    except Exception as exc:
        domain_errors.append(f"alpha: {exc}")
        domain_reports["alpha"] = {"error": str(exc)}

    # ── Engine 4: Ecological Collapse ─────────────────────────────────────────
    try:
        from core.economic_truth_reconstruction.ecological_collapse_detector import (
            detect_ecological_collapse,
        )
        r = detect_ecological_collapse(trades)
        domain_reports["ecology"] = r
    except Exception as exc:
        domain_errors.append(f"ecology: {exc}")
        domain_reports["ecology"] = {"error": str(exc)}

    # ── Engine 5: Regime Survivability ────────────────────────────────────────
    try:
        from core.economic_truth_reconstruction.regime_survivability_engine import (
            compute_regime_survivability,
        )
        r = compute_regime_survivability(trades)
        domain_reports["regime"] = r
    except Exception as exc:
        domain_errors.append(f"regime: {exc}")
        domain_reports["regime"] = {"error": str(exc)}

    # ── Engine 6: Adaptive Signal Filtration ──────────────────────────────────
    try:
        from core.economic_truth_reconstruction.adaptive_signal_filtration import (
            compute_adaptive_filtration,
        )
        r = compute_adaptive_filtration(trades)
        domain_reports["filtration"] = r
    except Exception as exc:
        domain_errors.append(f"filtration: {exc}")
        domain_reports["filtration"] = {"error": str(exc)}

    # ── Synthesis ─────────────────────────────────────────────────────────────
    trade_count = len(trades)

    # Expectancy condition
    exp_report   = domain_reports.get("expectancy", {})
    verdict      = exp_report.get("survivability_verdict", "UNKNOWN")
    overall_net  = exp_report.get("overall_net_expectancy")
    overall_gross = exp_report.get("overall_gross_expectancy")

    # Fee drag state
    fee_report   = domain_reports.get("fee_drag", {})
    fee_cas      = fee_report.get("cost_adjusted_survivability", "UNKNOWN")
    fee_tft      = fee_report.get("trade_frequency_toxicity", "UNKNOWN")

    # Survivability score (0-100, derived from available signals)
    survivability_score = 0
    score_evidence: Dict[str, Any] = {}

    # +30: net expectancy positive
    if overall_net is not None and overall_net > 0:
        survivability_score += 30
        score_evidence["net_positive"] = True
    else:
        score_evidence["net_positive"] = False

    # +20: cost-adjusted survivability not FEE_COLLAPSED/NOT_SURVIVABLE
    if fee_cas in ("SURVIVABLE", "MARGINALLY_SURVIVABLE"):
        survivability_score += 20
        score_evidence["fee_survivable"] = True
    else:
        score_evidence["fee_survivable"] = False

    # +20: at least 1 survivable alpha pocket
    alpha_report   = domain_reports.get("alpha", {})
    pocket_count   = alpha_report.get("pocket_count", 0)
    if pocket_count >= 1:
        survivability_score += 20
        score_evidence["alpha_pockets_found"] = True
    else:
        score_evidence["alpha_pockets_found"] = False

    # +15: ecological collapse severity not CRITICAL
    eco_report = domain_reports.get("ecology", {})
    collapse_severity = eco_report.get("collapse_severity", "CRITICAL")
    if collapse_severity not in ("CRITICAL", "HIGH"):
        survivability_score += 15
        score_evidence["ecology_stable"] = True
    else:
        score_evidence["ecology_stable"] = False

    # +15: at least 1 survivable regime
    regime_report = domain_reports.get("regime", {})
    surv_regimes  = regime_report.get("survivable_regimes", [])
    if surv_regimes:
        survivability_score += 15
        score_evidence["regime_survivable"] = True
    else:
        score_evidence["regime_survivable"] = False

    survivability_score = max(0, min(100, survivability_score))

    # ── Economic ID (deterministic lineage) ───────────────────────────────────
    key_data = {
        "trade_count":   trade_count,
        "verdict":       verdict,
        "surv_score":    survivability_score,
        "domain_errors": len(domain_errors),
    }
    economic_id = _make_economic_id(ts_ms, json.dumps(key_data, sort_keys=True))

    # ── Dominant regime condition ─────────────────────────────────────────────
    dominant_regime = regime_report.get("dominant_regime", "UNKNOWN")
    overall_regime_health = regime_report.get("overall_regime_health", "UNKNOWN")

    # ── Alpha concentration status ────────────────────────────────────────────
    global_alpha_state = alpha_report.get("global_alpha_state", "UNKNOWN")
    if pocket_count >= 3:
        alpha_status = "CONCENTRATED"
    elif pocket_count >= 1:
        alpha_status = "LOCALIZED"
    else:
        alpha_status = "ABSENT"

    return {
        "report":                   "ECONOMIC_TRUTH_REPORT",
        "economic_id":              economic_id,
        "trade_count":              trade_count,
        "survivability_score":      survivability_score,
        "survivability_tier":       _score_tier(survivability_score),
        "survivability_verdict":    verdict,
        "overall_net_expectancy":   overall_net,
        "overall_gross_expectancy": overall_gross,
        "expectancy_condition":     verdict,
        "fee_drag_state":           fee_cas,
        "trade_frequency_toxicity": fee_tft,
        "alpha_pocket_count":       pocket_count,
        "alpha_concentration":      alpha_status,
        "global_alpha_state":       global_alpha_state,
        "ecological_collapse_severity": collapse_severity,
        "survivable_regimes":       surv_regimes,
        "dominant_regime":          dominant_regime,
        "overall_regime_health":    overall_regime_health,
        "score_evidence":           score_evidence,
        "domain_reports":           domain_reports,
        "domain_errors":            domain_errors,
        "lineage_preserved":        True,
        "replay_safe":              True,
        "diagnostic_only":          True,
        "auto_authorized":          False,
        "generated_ts":             ts_ms,
    }


def get_economic_health(trades: List[dict]) -> dict:
    """
    Lightweight economic health probe — returns scores and condition without
    full domain report details. Suitable for boot-time logging.

    Returns a self-contained dict; never raises.
    """
    try:
        full = run_economic_truth(trades)
        return {
            "report":                "ECONOMIC_HEALTH",
            "economic_id":           full.get("economic_id", ""),
            "trade_count":           full.get("trade_count", 0),
            "survivability_score":   full.get("survivability_score", 0),
            "survivability_tier":    full.get("survivability_tier", "CRITICAL"),
            "expectancy_condition":  full.get("expectancy_condition", "UNKNOWN"),
            "fee_drag_state":        full.get("fee_drag_state", "UNKNOWN"),
            "alpha_concentration":   full.get("alpha_concentration", "UNKNOWN"),
            "ecological_collapse_severity": full.get("ecological_collapse_severity", "UNKNOWN"),
            "dominant_regime":       full.get("dominant_regime"),
            "domain_errors":         full.get("domain_errors", []),
            "diagnostic_only":       True,
            "auto_authorized":       False,
            "generated_ts":          full.get("generated_ts", int(_time.time() * 1000)),
        }
    except Exception as exc:
        return {
            "report":                "ECONOMIC_HEALTH",
            "error":                 str(exc),
            "trade_count":           0,
            "survivability_score":   0,
            "survivability_tier":    "CRITICAL",
            "expectancy_condition":  "UNAVAILABLE",
            "fee_drag_state":        "UNAVAILABLE",
            "alpha_concentration":   "UNKNOWN",
            "ecological_collapse_severity": "UNKNOWN",
            "dominant_regime":       None,
            "domain_errors":         [str(exc)],
            "diagnostic_only":       True,
            "auto_authorized":       False,
            "generated_ts":          int(_time.time() * 1000),
        }
