"""
FTD-GRVL: Guarded Reality Verification Layer.

Pure analytics — no I/O, no side effects, no execution authority.

Measures divergence between simulated paper-trading assumptions and what real-world
execution friction would impose. Provides guarded pilot governance doctrine over six
constitutional pilot states and six reality-alignment research classifications.

Strategy:
  Paper friction (fees, estimated slippage) already present in trade records is used
  as a lower-bound proxy for real execution friction. If edge barely survives paper
  friction, it is unlikely to survive real market execution. Each metric quantifies
  one dimension of this fragility.

Hard constitutional rules:
  DO NOT enable autonomous real trading
  DO NOT enable automatic capital scaling
  DO NOT enable self-authorised deployment
  DO NOT enable unsupervised pilot escalation
  DO NOT weaken human override authority

PHOENIX must NEVER self-grant real-world economic authority.

Isolation guarantee: imports only from core analytics modules and stdlib. Zero live
engine imports.
"""
from __future__ import annotations

import hashlib
import json
import math
import time as _time
from typing import Dict, List, Optional

from core.economic_truth import compute_economic_ground_truth

# ── Pilot state constants ──────────────────────────────────────────────────────
PAPER_ONLY             = "PAPER_ONLY"              # default: no external execution
SHADOW_MARKET          = "SHADOW_MARKET"            # observe live orderbook, no execution
MICRO_PILOT            = "MICRO_PILOT"              # tiny supervised exposure only
HUMAN_CONFIRM_REQUIRED = "HUMAN_CONFIRM_REQUIRED"  # every execution requires human approval
AUTO_DISABLED          = "AUTO_DISABLED"             # emergency freeze
CONSTITUTION_LOCKDOWN  = "CONSTITUTION_LOCKDOWN"    # absolute halt

# ── Reality classification labels ──────────────────────────────────────────────
REALITY_ALIGNED          = "REALITY_ALIGNED"           # simulation closely matches reality
FRICTION_EROSION         = "FRICTION_EROSION"           # fees/slippage destroy edge
LIQUIDITY_FRAGILE        = "LIQUIDITY_FRAGILE"          # alpha collapses under realistic fills
LATENCY_SENSITIVE        = "LATENCY_SENSITIVE"          # timing assumptions unstable
MICROSTRUCTURE_DEPENDENT = "MICROSTRUCTURE_DEPENDENT"   # edge requires unrealistic execution
PILOT_NOT_RECOMMENDED    = "PILOT_NOT_RECOMMENDED"      # reality divergence too high

# ── Pilot state descriptions ───────────────────────────────────────────────────
PILOT_STATE_DESCRIPTIONS: Dict[str, str] = {
    PAPER_ONLY:             "Default state: paper simulation only, no external execution.",
    SHADOW_MARKET:          "Observe live orderbook only — no execution, no capital at risk.",
    MICRO_PILOT:            "Tiny supervised exposure: minimal size, human oversight mandatory.",
    HUMAN_CONFIRM_REQUIRED: "Every execution requires explicit human confirmation before fill.",
    AUTO_DISABLED:          "Emergency freeze: governance halt due to detected reality divergence.",
    CONSTITUTION_LOCKDOWN:  "Absolute halt: constitutional emergency — no execution under any terms.",
}

# ── Constitutional pilot principles ────────────────────────────────────────────
PILOT_HARD_PRINCIPLES: Dict[str, bool] = {
    "human_supremacy":                True,
    "explicit_approval_required":     True,
    "rollback_capable":               True,
    "audit_history_immutable":        True,
    "capital_scaling_automatic":      False,
    "self_authorized_deployment":     False,
    "autonomous_live_trading":        False,
    "unsupervised_pilot_escalation":  False,
    "self_granted_economic_authority":False,
}

# ── Threshold constants ────────────────────────────────────────────────────────
MIN_ANALYSIS_TRADES          = 5
FILL_DIV_HIGH                = 50.0   # fill divergence ≥ → MICROSTRUCTURE_DEPENDENT
FILL_DIV_CRITICAL            = 70.0   # fill divergence ≥ → PILOT_NOT_RECOMMENDED
LIQ_SURV_FRAGILE             = 50.0   # liquidity survivability < → LIQUIDITY_FRAGILE
LAT_DIV_SENSITIVE            = 60.0   # latency divergence ≥ → LATENCY_SENSITIVE
SLIP_DIV_FRICTION            = 50.0   # slippage divergence ≥ → FRICTION_EROSION
SPREAD_FRAG_FRICTION         = 60.0   # spread fragility ≥ → FRICTION_EROSION
PILOT_SCORE_CRITICAL         = 30.0   # pilot score < → PILOT_NOT_RECOMMENDED
PILOT_SCORE_AUTO_DISABLED    = 20.0   # pilot score < → AUTO_DISABLED
PILOT_SCORE_LOCKDOWN         = 30.0   # combined with PILOT_NOT_RECOMMENDED classification
PILOT_SCORE_MICRO_PILOT      = 60.0   # pilot score ≥ → eligible for MICRO_PILOT
PILOT_SCORE_SHADOW_MARKET    = 40.0   # pilot score ≥ → eligible for SHADOW_MARKET
AUTO_DISABLED_CONF_FLOOR     = 50.0   # confidence ≥ required for AUTO_DISABLED trigger
LOCKDOWN_CONF_FLOOR          = 60.0   # confidence ≥ combined with NOT_RECOMMENDED → LOCKDOWN


# ── Tier helpers ──────────────────────────────────────────────────────────────

def _div_tier(score: float) -> str:
    """Divergence tier — higher = more divergence = worse."""
    if score >= 70:  return "HIGH"
    if score >= 40:  return "MODERATE"
    if score >= 20:  return "LOW"
    return "MINIMAL"


def _surv_tier(score: float) -> str:
    """Survivability tier — higher = better."""
    if score >= 70:  return "STRONG"
    if score >= 50:  return "ADEQUATE"
    if score >= 30:  return "FRAGILE"
    return "CRITICAL"


def _pilot_tier(score: float) -> str:
    """Pilot readiness tier."""
    if score >= 70:  return "PILOT_READY"
    if score >= 50:  return "CONDITIONAL"
    if score >= 30:  return "HIGH_RISK"
    return "NOT_RECOMMENDED"


def _conf_tier(score: float) -> str:
    if score >= 75:  return "HIGH"
    if score >= 50:  return "MODERATE"
    if score >= 25:  return "LOW"
    return "INSUFFICIENT"


# ── Divergence metric functions ────────────────────────────────────────────────

def _fill_divergence_metric(trades: List[dict]) -> dict:
    """
    Ratio of total slippage cost to total absolute gross PnL.

    Measures how much execution shortfall (slippage) consumes gross edge.
    High ratio → fills materially worse than frictionless assumption.
    Score 0–100: higher = more fill divergence = worse execution quality.
    """
    total_slippage = sum(
        abs(float(t.get("slippage_cost", 0) or 0)) for t in trades
    )
    total_gross = sum(
        abs(float(t.get("gross_pnl", 0) or 0)) for t in trades
    )
    if total_gross == 0.0:
        return {"score": 0.0, "tier": "MINIMAL", "ratio_pct": 0.0}

    ratio_pct = total_slippage / total_gross * 100.0
    score     = round(min(100.0, ratio_pct), 1)
    return {"score": score, "tier": _div_tier(score), "ratio_pct": round(ratio_pct, 2)}


def _slippage_divergence_metric(trades: List[dict]) -> dict:
    """
    Mean per-trade slippage as % of |gross_pnl|, scaled to 0–100.

    Measures average per-trade execution shortfall. Score 0–100: higher = worse.
    """
    ratios: List[float] = []
    for t in trades:
        gross = abs(float(t.get("gross_pnl", 0) or 0))
        slip  = abs(float(t.get("slippage_cost", 0) or 0))
        if gross > 0:
            ratios.append(slip / gross * 100.0)

    if not ratios:
        return {"score": 0.0, "tier": "MINIMAL", "mean_ratio_pct": 0.0}

    mean_ratio = sum(ratios) / len(ratios)
    # Scale: 50% mean ratio → score 100
    score = round(min(100.0, mean_ratio * 2.0), 1)
    return {"score": score, "tier": _div_tier(score), "mean_ratio_pct": round(mean_ratio, 2)}


def _latency_divergence_metric(trades: List[dict]) -> dict:
    """
    Coefficient of variation (CV) of hold durations as a timing uncertainty proxy.

    High CV = erratic hold times = execution timing is unstable. Score 0–100: higher = worse.
    CV of 2.0 maps to score 100.
    """
    hold_minutes: List[float] = []
    for t in trades:
        entry_ts = float(t.get("entry_ts", 0) or 0)
        exit_ts  = float(t.get("exit_ts",  0) or 0)
        if exit_ts > entry_ts:
            hold_minutes.append((exit_ts - entry_ts) / 60.0)

    if len(hold_minutes) < 2:
        return {"score": 0.0, "tier": "MINIMAL", "cv": 0.0, "mean_hold_min": 0.0}

    n         = len(hold_minutes)
    mean_hold = sum(hold_minutes) / n
    if mean_hold == 0.0:
        return {"score": 0.0, "tier": "MINIMAL", "cv": 0.0, "mean_hold_min": 0.0}

    variance  = sum((h - mean_hold) ** 2 for h in hold_minutes) / n
    cv        = math.sqrt(variance) / mean_hold
    score     = round(min(100.0, cv * 50.0), 1)
    return {
        "score":        score,
        "tier":         _div_tier(score),
        "cv":           round(cv, 3),
        "mean_hold_min": round(mean_hold, 1),
    }


def _liquidity_survivability_metric(trades: List[dict]) -> dict:
    """
    Fraction of trades (%) that remain profitable after applying a 2× spread stress.

    Simulates doubling the entry-side cost (wider bid-ask spread). Surviving trades
    retain positive net PnL after this adjustment.
    Score 0–100: higher = more trades survive = better liquidity resilience.
    """
    if not trades:
        return {"score": 100.0, "tier": "STRONG", "surviving_pct": 100.0}

    surviving = 0
    for t in trades:
        net       = float(t.get("net_pnl", 0) or 0)
        fee_entry = abs(float(t.get("fee_entry", 0) or 0))
        # Simulate one additional fee_entry worth of spread cost
        if (net - fee_entry) > 0:
            surviving += 1

    score = round(surviving / len(trades) * 100.0, 1)
    return {"score": score, "tier": _surv_tier(score), "surviving_pct": score}


def _spread_fragility_metric(trades: List[dict]) -> dict:
    """
    Win-rate erosion under 2×, 5×, 10× spread stress scenarios.

    For each multiplier, simulates applying (multiplier − 1) extra fee_entry costs
    to every trade and counts the surviving (still profitable) fraction.
    Score 0–100: higher = more fragility = worse (score = 100 - survival_5x).
    """
    if not trades:
        return {
            "score": 0.0, "tier": "MINIMAL",
            "stress_scenarios": {},
        }

    scenarios: Dict[str, dict] = {}
    for multiplier, label in ((2, "2x_spread"), (5, "5x_spread"), (10, "10x_spread")):
        surviving = 0
        for t in trades:
            net       = float(t.get("net_pnl", 0) or 0)
            fee_entry = abs(float(t.get("fee_entry", 0) or 0))
            extra     = fee_entry * (multiplier - 1)
            if (net - extra) > 0:
                surviving += 1
        scenarios[label] = {
            "surviving_pct": round(surviving / len(trades) * 100.0, 1),
        }

    # Score driven by 5× scenario (moderately adverse but realistic)
    survival_5x = scenarios.get("5x_spread", {}).get("surviving_pct", 100.0)
    score       = round(max(0.0, 100.0 - survival_5x), 1)
    return {
        "score":            score,
        "tier":             _div_tier(score),
        "stress_scenarios": scenarios,
    }


def _market_impact_sensitivity(trades: List[dict], base_ne: float) -> dict:
    """
    Net expectancy sensitivity to 2× fee stress — proxy for market-impact fragility.

    Simulates doubling all entry and exit fees and recomputes NE. If NE drops
    significantly, the strategy is highly sensitive to real transaction costs.
    Score 0–100: higher = more NE sensitivity = worse (normalised drop × 100).
    """
    if len(trades) < MIN_ANALYSIS_TRADES:
        return {"score": 0.0, "tier": "MINIMAL", "note": "insufficient_data"}

    stressed: List[dict] = []
    for t in trades:
        st         = dict(t)
        fee_e      = abs(float(t.get("fee_entry", 0) or 0))
        fee_x      = abs(float(t.get("fee_exit",  0) or 0))
        extra_cost = fee_e + fee_x                   # one extra copy of both fees
        st["net_pnl"] = float(t.get("net_pnl", 0) or 0) - extra_cost
        stressed.append(st)

    try:
        stressed_eco = compute_economic_ground_truth(stressed)
        stressed_ne  = float(stressed_eco.get("net_expectancy") or 0.0)
    except Exception as exc:
        return {"score": 50.0, "tier": "MODERATE", "note": f"stress_failed: {exc}"}

    ne_delta = stressed_ne - base_ne

    if base_ne == 0.0:
        sensitivity = 50.0
    else:
        drop_ratio  = abs(ne_delta) / max(abs(base_ne), 1e-9)
        sensitivity = min(100.0, drop_ratio * 100.0)

    score = round(sensitivity, 1)
    return {
        "score":       score,
        "tier":        _div_tier(score),
        "base_ne":     round(base_ne, 6),
        "stressed_ne": round(stressed_ne, 6),
        "ne_delta":    round(ne_delta, 6),
    }


# ── Composite metrics ─────────────────────────────────────────────────────────

def _pilot_survivability_score(divergence_metrics: dict) -> dict:
    """
    Composite pilot-readiness score (0–100). Penalties from divergence metrics;
    bonus from liquidity survivability.

    Higher score = greater chance that paper alpha survives real execution friction.
    """
    fill_div  = float((divergence_metrics.get("fill_divergence",          {}) or {}).get("score", 0))
    slip_div  = float((divergence_metrics.get("slippage_divergence",      {}) or {}).get("score", 0))
    lat_div   = float((divergence_metrics.get("latency_divergence",       {}) or {}).get("score", 0))
    liq_score = float((divergence_metrics.get("liquidity_survivability",  {}) or {}).get("score", 50))
    spread_fr = float((divergence_metrics.get("spread_fragility",         {}) or {}).get("score", 0))
    impact    = float((divergence_metrics.get("market_impact_sensitivity",{}) or {}).get("score", 0))

    penalty = (
        fill_div  * 0.20 +
        slip_div  * 0.15 +
        lat_div   * 0.10 +
        spread_fr * 0.20 +
        impact    * 0.15
    )
    # Liquidity: contribution relative to 50% baseline (+10 if perfect, −10 if zero)
    liq_bonus = (liq_score - 50.0) * 0.20

    raw   = 100.0 - penalty + liq_bonus
    score = round(max(0.0, min(100.0, raw)), 1)
    return {"score": score, "tier": _pilot_tier(score)}


def _simulation_reality_confidence(trades: List[dict]) -> dict:
    """
    Confidence in divergence estimates (0–100): driven by corpus size and data quality
    (presence of fee and slippage fields).

    Higher confidence = divergence metrics are statistically more reliable.
    """
    n = len(trades)
    if n == 0:
        return {"score": 0.0, "tier": "INSUFFICIENT", "fee_coverage_pct": 0.0, "trade_corpus_size": 0}

    fee_count  = sum(
        1 for t in trades
        if (float(t.get("fee_entry", 0) or 0) > 0 or float(t.get("fee_exit", 0) or 0) > 0)
    )
    slip_count = sum(
        1 for t in trades
        if float(t.get("slippage_cost", 0) or 0) != 0
    )

    fee_cov  = fee_count  / n
    slip_cov = slip_count / n
    quality  = fee_cov * 0.70 + slip_cov * 0.30

    if   n >= 500: size_score = 1.0
    elif n >= 200: size_score = 0.80
    elif n >= 100: size_score = 0.60
    elif n >= 50:  size_score = 0.40
    else:          size_score = 0.20

    raw   = (quality * 0.60 + size_score * 0.40) * 100.0
    score = round(min(100.0, max(0.0, raw)), 1)
    return {
        "score":             score,
        "tier":              _conf_tier(score),
        "fee_coverage_pct":  round(fee_cov * 100.0, 1),
        "trade_corpus_size": n,
    }


# ── Reality classification ─────────────────────────────────────────────────────

def _classify_reality(pilot_score: float, divergence_metrics: dict) -> str:
    """
    Classify the strategy's reality-alignment into one of 6 research categories.

    Priority order (first match wins):
      PILOT_NOT_RECOMMENDED    — pilot score < 30 or fill divergence ≥ 70
      MICROSTRUCTURE_DEPENDENT — fill divergence ≥ 50 (execution quality dependent)
      LIQUIDITY_FRAGILE        — liquidity survivability < 50%
      LATENCY_SENSITIVE        — latency divergence ≥ 60
      FRICTION_EROSION         — slippage > 50% or spread fragility > 60
      REALITY_ALIGNED          — default (all metrics within acceptable bounds)

    Research label only — not an execution authority.
    """
    fill_div  = float((divergence_metrics.get("fill_divergence",         {}) or {}).get("score", 0))
    liq_score = float((divergence_metrics.get("liquidity_survivability", {}) or {}).get("score", 100))
    lat_div   = float((divergence_metrics.get("latency_divergence",      {}) or {}).get("score", 0))
    slip_div  = float((divergence_metrics.get("slippage_divergence",     {}) or {}).get("score", 0))
    spread_fr = float((divergence_metrics.get("spread_fragility",        {}) or {}).get("score", 0))

    if pilot_score < PILOT_SCORE_CRITICAL or fill_div >= FILL_DIV_CRITICAL:
        return PILOT_NOT_RECOMMENDED

    if fill_div >= FILL_DIV_HIGH:
        return MICROSTRUCTURE_DEPENDENT

    if liq_score < LIQ_SURV_FRAGILE:
        return LIQUIDITY_FRAGILE

    if lat_div >= LAT_DIV_SENSITIVE:
        return LATENCY_SENSITIVE

    if slip_div >= SLIP_DIV_FRICTION or spread_fr >= SPREAD_FRAG_FRICTION:
        return FRICTION_EROSION

    return REALITY_ALIGNED


# ── Pilot state assessment ─────────────────────────────────────────────────────

def _assess_pilot_state(
    pilot_score:    float,
    classification: str,
    confidence:     dict,
) -> str:
    """
    Assess the appropriate constitutional pilot deployment state.

    Priority order (most restrictive first):
      AUTO_DISABLED         — score < 20 AND confidence ≥ 50 (confident it's bad)
      CONSTITUTION_LOCKDOWN — classification PILOT_NOT_RECOMMENDED AND confidence ≥ 60
      HUMAN_CONFIRM_REQUIRED — fragile/friction/microstructure dependent
      MICRO_PILOT           — aligned AND score ≥ 60 AND confidence ≥ 50
      SHADOW_MARKET         — score ≥ 40 (observe, don't execute)
      PAPER_ONLY            — default baseline

    Research label only — not an execution authority.
    """
    conf_score = float((confidence or {}).get("score", 0))

    if pilot_score < PILOT_SCORE_AUTO_DISABLED and conf_score >= AUTO_DISABLED_CONF_FLOOR:
        return AUTO_DISABLED

    if classification == PILOT_NOT_RECOMMENDED and conf_score >= LOCKDOWN_CONF_FLOOR:
        return CONSTITUTION_LOCKDOWN

    if classification in (FRICTION_EROSION, LIQUIDITY_FRAGILE, MICROSTRUCTURE_DEPENDENT):
        return HUMAN_CONFIRM_REQUIRED

    if (classification == REALITY_ALIGNED
            and pilot_score >= PILOT_SCORE_MICRO_PILOT
            and conf_score  >= AUTO_DISABLED_CONF_FLOOR):
        return MICRO_PILOT

    if pilot_score >= PILOT_SCORE_SHADOW_MARKET:
        return SHADOW_MARKET

    return PAPER_ONLY


# ── Recommendation generation ──────────────────────────────────────────────────

def _generate_pilot_recommendations(
    classification: str,
    pilot_state:    str,
    divergence_metrics: dict,
    confidence:     dict,
    pilot_score:    float,
) -> List[dict]:
    """
    Generate research-only pilot governance recommendations.

    Constitutional guarantee: auto_authorized is ALWAYS False.
    System may recommend, explain, quantify divergence, suggest guarded pilot suitability.
    System may NEVER self-authorize capital, self-scale exposure, or bypass constitutional states.
    """
    recs: List[dict] = []

    if classification == PILOT_NOT_RECOMMENDED:
        recs.append({
            "type":            "PILOT_NOT_RECOMMENDED_WARNING",
            "priority":        "CRITICAL",
            "summary":         (
                f"Reality divergence analysis indicates pilot readiness score of "
                f"{pilot_score:.0f}/100 — below the 30-point viability threshold. "
                "Paper alpha unlikely to survive real execution friction. "
                "Human review and extended paper evidence required."
            ),
            "evidence":        {"classification": classification, "pilot_score": pilot_score},
            "action_required": "EXTENDED_PAPER_ONLY",
            "auto_authorized": False,
        })

    if classification == MICROSTRUCTURE_DEPENDENT:
        fill_div = float((divergence_metrics.get("fill_divergence", {}) or {}).get("score", 0))
        recs.append({
            "type":            "MICROSTRUCTURE_DEPENDENCY_WARNING",
            "priority":        "HIGH",
            "summary":         (
                f"Fill divergence score {fill_div:.0f}/100 suggests edge may depend on "
                "unrealistic fill assumptions. Slippage impact significantly erodes gross "
                "PnL. Strategy may be microstructure-dependent."
            ),
            "evidence":        {"fill_divergence_score": fill_div},
            "action_required": "HUMAN_REVIEW",
            "auto_authorized": False,
        })

    if classification == LIQUIDITY_FRAGILE:
        liq = float((divergence_metrics.get("liquidity_survivability", {}) or {}).get("score", 0))
        recs.append({
            "type":            "LIQUIDITY_FRAGILITY_WARNING",
            "priority":        "HIGH",
            "summary":         (
                f"Liquidity survivability at {liq:.0f}% — below 50% threshold. "
                "Strategy win rate collapses under realistic spread conditions. "
                "Not suitable for execution-side exposure without further edge validation."
            ),
            "evidence":        {"liquidity_survivability_score": liq},
            "action_required": "HUMAN_REVIEW",
            "auto_authorized": False,
        })

    if classification == LATENCY_SENSITIVE:
        lat = float((divergence_metrics.get("latency_divergence", {}) or {}).get("score", 0))
        recs.append({
            "type":            "LATENCY_SENSITIVITY_WARNING",
            "priority":        "MEDIUM",
            "summary":         (
                f"Hold-time variation index {lat:.0f}/100 indicates high timing uncertainty. "
                "Strategy economics may be sensitive to execution latency and fill timing. "
                "Shadow market observation recommended before any exposure."
            ),
            "evidence":        {"latency_divergence_score": lat},
            "action_required": "SHADOW_MARKET_OBSERVATION",
            "auto_authorized": False,
        })

    if classification == FRICTION_EROSION:
        slip = float((divergence_metrics.get("slippage_divergence", {}) or {}).get("score", 0))
        recs.append({
            "type":            "FRICTION_EROSION_WARNING",
            "priority":        "HIGH",
            "summary":         (
                f"Slippage divergence score {slip:.0f}/100 — transaction costs significantly "
                "erode simulated edge. Real-world fee and spread friction may eliminate "
                "economic viability. Requires human review of cost architecture."
            ),
            "evidence":        {"slippage_divergence_score": slip},
            "action_required": "HUMAN_REVIEW",
            "auto_authorized": False,
        })

    if classification == REALITY_ALIGNED and pilot_score >= PILOT_SCORE_MICRO_PILOT:
        recs.append({
            "type":            "MICRO_PILOT_ELIGIBLE",
            "priority":        "MEDIUM",
            "summary":         (
                f"Pilot readiness score {pilot_score:.0f}/100 meets threshold for "
                "supervised micro-pilot consideration. Reality divergence within acceptable "
                "bounds. All pilot transitions require explicit human authorisation."
            ),
            "evidence":        {
                "pilot_score":    pilot_score,
                "classification": classification,
                "confidence_tier": (confidence or {}).get("tier", "?"),
            },
            "action_required": "HUMAN_AUTHORISATION_REQUIRED",
            "auto_authorized": False,
        })

    conf_score = float((confidence or {}).get("score", 0))
    if conf_score < 40:
        recs.append({
            "type":            "LOW_CONFIDENCE_WARNING",
            "priority":        "MEDIUM",
            "summary":         (
                f"Simulation-reality confidence score {conf_score:.0f}/100 — insufficient "
                "trade corpus or fee data coverage for reliable divergence estimates. "
                "Accumulate more trade history before pilot consideration."
            ),
            "evidence":        {"confidence_score": conf_score},
            "action_required": "ACCUMULATE_MORE_DATA",
            "auto_authorized": False,
        })

    if not recs:
        recs.append({
            "type":            "REALITY_ALIGNMENT_AFFIRMATION",
            "priority":        "LOW",
            "summary":         (
                "No critical reality divergence signals detected. Paper trading metrics "
                "suggest simulation assumptions are within reasonable alignment bounds."
            ),
            "evidence":        {"pilot_score": pilot_score, "classification": classification},
            "action_required": "NONE",
            "auto_authorized": False,
        })

    return recs


# ── Immutable audit entry ──────────────────────────────────────────────────────

def _generate_pilot_audit_entry(
    pilot_state:         str,
    classification:      str,
    pilot_score:         float,
    confidence:          dict,
    recommendations:     List[dict],
) -> dict:
    """
    Generate an immutable audit entry for this reality verification assessment.

    Constitutional guarantee: auto_authorized is ALWAYS False.
    """
    ts = int(_time.time() * 1000)

    payload = json.dumps({
        "ts":    ts,
        "state": pilot_state,
        "cls":   classification,
        "score": round(pilot_score, 1),
    }, sort_keys=True)
    fingerprint = hashlib.sha256(payload.encode()).hexdigest()[:16]

    return {
        "entry_id":                  f"GRVL-{ts}-{fingerprint}",
        "timestamp_ms":              ts,
        "pilot_state":               pilot_state,
        "reality_classification":    classification,
        "pilot_survivability_score": round(pilot_score, 1),
        "simulation_reality_confidence_tier": (confidence or {}).get("tier", "?"),
        "recommendations_generated": len(recommendations),
        "human_approval_required":   pilot_state != PAPER_ONLY,
        "auto_authorized":           False,   # constitutional guarantee — never True
        "immutable":                 True,
    }


# ── Main entry point ──────────────────────────────────────────────────────────

def compute_reality_verification(trades: List[dict]) -> dict:
    """
    Measure divergence between simulated paper-trading assumptions and real-world
    execution friction across eight reality-alignment dimensions.

    For each dimension:
      1. Compute metric from trade records (fees, slippage, timestamps, PnL)
      2. Score on 0–100 scale (divergence) or 0–100% (survivability)
      3. Assign tier label

    Compose into:
      - Pilot survivability score (0–100)
      - Simulation-reality confidence (0–100)
      - Reality classification (6 research categories)
      - Pilot state assessment (6 constitutional states)
      - Research-only recommendations (auto_authorized always False)
      - Immutable audit entry

    Constitutional guarantee: all recommendations are research-only, never
    auto-authorised. No capital is scaled, no execution is enabled, no
    constitutional safeguards are weakened.

    Isolation guarantee: no live engine state read or written.
    Never raises — fail-open contract.
    """
    SCOPE = (
        "FTD-GRVL: Guarded Reality Verification Layer. "
        "Research instrumentation only — non-governing. "
        "Measures divergence between simulated paper-trading assumptions and real-world "
        "execution friction. No production state is read or written. "
        "No execution behavior is altered. No capital is at risk. "
        "DO NOT enable autonomous live trading, automatic capital scaling, or "
        "self-authorised deployment based on these outputs. "
        "PHOENIX must NEVER self-grant real-world economic authority. "
        "Not an execution authority. All decisions at developer discretion."
    )

    try:
        if not trades or not isinstance(trades, list):
            return {
                "scope_note":   SCOPE,
                "total_trades": 0,
                "note":         "No trades provided for reality verification.",
            }

        total = len(trades)
        if total < MIN_ANALYSIS_TRADES:
            return {
                "scope_note":   SCOPE,
                "total_trades": total,
                "note": (
                    f"Insufficient trades (< {MIN_ANALYSIS_TRADES}). "
                    "Reality verification requires more historical data."
                ),
            }

        # ── Baseline NE (used by market impact sensitivity) ───────────────────
        try:
            baseline_eco = compute_economic_ground_truth(trades)
            base_ne      = float(baseline_eco.get("net_expectancy") or 0.0)
        except Exception:
            baseline_eco = {}
            base_ne      = 0.0

        # ── Divergence metrics ────────────────────────────────────────────────
        divergence_metrics = {
            "fill_divergence":           _fill_divergence_metric(trades),
            "slippage_divergence":       _slippage_divergence_metric(trades),
            "latency_divergence":        _latency_divergence_metric(trades),
            "liquidity_survivability":   _liquidity_survivability_metric(trades),
            "spread_fragility":          _spread_fragility_metric(trades),
            "market_impact_sensitivity": _market_impact_sensitivity(trades, base_ne),
        }

        # ── Composite scores ──────────────────────────────────────────────────
        pilot_survivability = _pilot_survivability_score(divergence_metrics)
        pilot_score         = pilot_survivability["score"]
        confidence          = _simulation_reality_confidence(trades)

        # ── Classification & state ────────────────────────────────────────────
        classification = _classify_reality(pilot_score, divergence_metrics)
        pilot_state    = _assess_pilot_state(pilot_score, classification, confidence)

        # ── Recommendations ───────────────────────────────────────────────────
        recommendations = _generate_pilot_recommendations(
            classification, pilot_state, divergence_metrics, confidence, pilot_score,
        )

        # ── Audit entry ───────────────────────────────────────────────────────
        audit_entry = _generate_pilot_audit_entry(
            pilot_state, classification, pilot_score, confidence, recommendations,
        )

        return {
            "scope_note":                        SCOPE,
            "total_trades":                      total,
            "pilot_state":                       pilot_state,
            "pilot_state_description":           PILOT_STATE_DESCRIPTIONS.get(pilot_state, ""),
            "reality_classification":            classification,
            "pilot_survivability":               pilot_survivability,
            "simulation_reality_confidence":     confidence,
            "divergence_metrics":                divergence_metrics,
            "baseline_economics": {
                "net_expectancy":        base_ne,
                "survivability_score":   (baseline_eco.get("survivability_score", {}) or {}).get("score"),
                "win_rate_pct":          (baseline_eco.get("payoff_geometry", {}) or {}).get("fee_adjusted_win_rate_pct"),
                "fee_drag_mean_pct":     (baseline_eco.get("fee_drag_distribution", {}) or {}).get("mean"),
            },
            "recommendations":               recommendations,
            "pilot_hard_principles":         PILOT_HARD_PRINCIPLES,
            "audit_entry":                   audit_entry,
        }

    except Exception as exc:
        return {
            "scope_note": SCOPE,
            "error":      str(exc),
        }
