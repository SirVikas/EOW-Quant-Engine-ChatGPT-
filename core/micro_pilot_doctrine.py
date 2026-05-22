"""
FTD-GMPD: Ultra-Guarded Micro Pilot Execution Doctrine
& Human Confirmation Exchange Bridge.

Pure analytics — no I/O, no side effects, no execution authority.

Synthesises paper trade history and a session-scoped pilot execution ledger
to assess constitutional pilot governance health, reconcile expected vs actual
execution economics, and generate human-only research recommendations.

Defines:
  - 6 constitutional pilot states (PAPER_ONLY → CONSTITUTION_LOCKDOWN)
  - 6 research classifications (REALITY_CONSISTENT → PILOT_LOCKDOWN_RECOMMENDED)
  - 5 execution reconciliation metrics (fill, slippage, latency, fee drag, hold economics)
  - Confirmation chain integrity (human_confirmed invariant)
  - Kill-switch advisory engine
  - Pilot survivability score
  - Research-only pilot opportunity recommendation
  - Immutable audit entry generation

Hard constitutional rules (non-negotiable, enforced at module level):
  DO NOT enable autonomous order firing
  DO NOT enable autonomous capital scaling
  DO NOT enable autonomous re-entry or averaging down
  DO NOT enable self-authorized execution
  DO NOT weaken human override authority
  DO NOT weaken constitutional lockdown

PHOENIX may NEVER self-fire an exchange order.
PHOENIX must NEVER possess sovereign economic execution authority.

Isolation guarantee: no live engine imports. Fail-open on any exception.
Research only — NOT an execution authority.
"""
from __future__ import annotations

import hashlib
import time as _time
from typing import Dict, List, Optional

# ── Constitutional execution states ───────────────────────────────────────────
PAPER_ONLY               = "PAPER_ONLY"
SHADOW_OBSERVATION       = "SHADOW_OBSERVATION"
HUMAN_ARMED_MICRO        = "HUMAN_ARMED_MICRO"
SINGLE_CONFIRM_EXECUTION = "SINGLE_CONFIRM_EXECUTION"
MANUAL_KILL_SWITCH       = "MANUAL_KILL_SWITCH"
CONSTITUTION_LOCKDOWN    = "CONSTITUTION_LOCKDOWN"

_PILOT_STATE_DESCRIPTIONS: Dict[str, str] = {
    PAPER_ONLY:               "Zero external execution — insufficient readiness evidence for any pilot action.",
    SHADOW_OBSERVATION:       "Live market observation only — accumulating readiness, no capital at risk.",
    HUMAN_ARMED_MICRO:        "Human may pre-arm a single micro execution — constitutional constraints active, one order at a time.",
    SINGLE_CONFIRM_EXECUTION: "One explicit human confirmation required per order — prior execution evidence consistent with expectations.",
    MANUAL_KILL_SWITCH:       "Immediate execution freeze — kill-switch conditions active, human intervention required before any pilot action.",
    CONSTITUTION_LOCKDOWN:    "Absolute constitutional halt — no pilot action permitted until explicit human governance review.",
}

# ── Research classifications ───────────────────────────────────────────────────
REALITY_CONSISTENT         = "REALITY_CONSISTENT"
EXECUTION_DRIFT            = "EXECUTION_DRIFT"
SLIPPAGE_COLLAPSE          = "SLIPPAGE_COLLAPSE"
LIQUIDITY_FAILURE          = "LIQUIDITY_FAILURE"
HUMAN_REVIEW_ESCALATION    = "HUMAN_REVIEW_ESCALATION"
PILOT_LOCKDOWN_RECOMMENDED = "PILOT_LOCKDOWN_RECOMMENDED"

# ── Hard constitutional principles (immutable) ────────────────────────────────
PILOT_HARD_PRINCIPLES: Dict[str, bool] = {
    "human_confirmation_required":    True,
    "execution_authority_human_only": True,
    "immutable_audit_guaranteed":     True,
    "kill_switch_always_available":   True,
    "rollback_always_possible":       True,
    "one_order_at_a_time":            True,
    "fixed_exposure_no_compounding":  True,
    "exposure_scaling_autonomous":    False,
    "retry_execution_autonomous":     False,
    "self_authorized_execution":      False,
    "capital_compounding_automatic":  False,
    "recursive_authority_escalation": False,
    "sovereign_economic_authority":   False,
}


# ── Ledger helpers ─────────────────────────────────────────────────────────────

def _exec_entries(pilot_ledger: List[dict]) -> List[dict]:
    """Return only human-confirmed execution entries from the pilot ledger."""
    return [
        e for e in pilot_ledger
        if isinstance(e, dict)
        and e.get("entry_type") == "EXECUTION"
        and e.get("human_confirmed") is True
    ]


# ── Execution readiness (derived from paper trade history) ────────────────────

def _execution_readiness_metric(trades: List[dict]) -> dict:
    """
    How ready is the paper trade corpus for a guarded pilot?
    Measures corpus size, fee coverage, and slippage coverage.
    Score 0–100; higher = more ready.
    """
    _base = {
        "score": 0.0, "tier": "INSUFFICIENT",
        "trade_count": 0, "fee_coverage": 0.0,
        "slippage_coverage": 0.0, "net_expectancy": 0.0,
    }
    if not trades:
        return _base
    try:
        n = len(trades)
        fee_covered  = sum(
            1 for t in trades
            if isinstance(t, dict)
            and ((t.get("fee_entry") or 0.0) + (t.get("fee_exit") or 0.0)) > 0
        )
        slip_covered = sum(
            1 for t in trades
            if isinstance(t, dict) and (t.get("slippage_cost") or 0.0) > 0
        )
        fee_coverage  = fee_covered  / n
        slip_coverage = slip_covered / n
        net_pnl_vals  = [
            t.get("net_pnl") or 0.0 for t in trades if isinstance(t, dict)
        ]
        net_expectancy = sum(net_pnl_vals) / max(len(net_pnl_vals), 1)

        size_score = min(n / 500.0, 1.0)
        cov_score  = fee_coverage * 0.60 + slip_coverage * 0.40
        raw        = (size_score * 0.40 + cov_score * 0.60) * 100.0
        score      = max(0.0, min(100.0, raw))

        if score >= 70.0:   tier = "ADEQUATE"
        elif score >= 40.0: tier = "DEVELOPING"
        elif score >= 20.0: tier = "EARLY"
        else:               tier = "INSUFFICIENT"

        return {
            "score":             round(score, 2),
            "tier":              tier,
            "trade_count":       n,
            "fee_coverage":      round(fee_coverage, 3),
            "slippage_coverage": round(slip_coverage, 3),
            "net_expectancy":    round(net_expectancy, 4),
        }
    except Exception:
        return _base


# ── Reconciliation metrics (require execution entries in ledger) ───────────────

def _fill_quality_metric(pilot_ledger: List[dict]) -> dict:
    """
    Fill divergence: how far actual fills deviated from expected.
    Score 0–100; higher = worse divergence.
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT", "sample_count": 0, "avg_fill_ratio": None}
    execs = _exec_entries(pilot_ledger)
    if not execs:
        return _base
    try:
        ratios = []
        for e in execs:
            exp = e.get("expected_fill") or 0.0
            act = e.get("actual_fill")   or 0.0
            if abs(exp) > 1e-9:
                ratios.append(act / exp)
        if not ratios:
            return {**_base, "sample_count": len(execs)}
        avg_ratio = sum(ratios) / len(ratios)
        score     = min(100.0, abs(1.0 - avg_ratio) * 100.0)
        if score < 5.0:    tier = "MINIMAL"
        elif score < 15.0: tier = "LOW"
        elif score < 35.0: tier = "MODERATE"
        else:              tier = "HIGH"
        return {"score": round(score, 2), "tier": tier,
                "sample_count": len(ratios), "avg_fill_ratio": round(avg_ratio, 4)}
    except Exception:
        return _base


def _slippage_reconciliation_metric(pilot_ledger: List[dict]) -> dict:
    """
    Slippage divergence: absolute % deviation of actual slippage from expected.
    Score 0–100; higher = worse.
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT", "sample_count": 0, "mean_excess_slippage": None}
    execs = _exec_entries(pilot_ledger)
    if not execs:
        return _base
    try:
        deltas = []
        for e in execs:
            exp = e.get("expected_slippage") or 0.0
            act = e.get("actual_slippage")   or 0.0
            base = max(abs(exp), 1e-9)
            deltas.append(abs(act - exp) / base * 100.0)
        if not deltas:
            return {**_base, "sample_count": len(execs)}
        mean_delta = sum(deltas) / len(deltas)
        score      = min(100.0, mean_delta)
        if score < 10.0:   tier = "LOW"
        elif score < 30.0: tier = "MODERATE"
        elif score < 60.0: tier = "HIGH"
        else:              tier = "CRITICAL"
        return {"score": round(score, 2), "tier": tier,
                "sample_count": len(deltas), "mean_excess_slippage": round(mean_delta, 2)}
    except Exception:
        return _base


def _latency_reconciliation_metric(pilot_ledger: List[dict]) -> dict:
    """
    Latency divergence: excess latency ratio (actual vs expected).
    Score 0–100; higher = more latency inflation.
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT", "sample_count": 0, "mean_latency_ratio": None}
    execs = _exec_entries(pilot_ledger)
    if not execs:
        return _base
    try:
        ratios = []
        for e in execs:
            exp = e.get("expected_latency_ms") or 0.0
            act = e.get("actual_latency_ms")   or 0.0
            if abs(exp) > 1e-9:
                ratios.append(act / exp)
        if not ratios:
            return {**_base, "sample_count": len(execs)}
        mean_ratio = sum(ratios) / len(ratios)
        score      = min(100.0, max(0.0, (mean_ratio - 1.0) * 100.0))
        if score < 10.0:   tier = "LOW"
        elif score < 30.0: tier = "MODERATE"
        elif score < 60.0: tier = "HIGH"
        else:              tier = "CRITICAL"
        return {"score": round(score, 2), "tier": tier,
                "sample_count": len(ratios), "mean_latency_ratio": round(mean_ratio, 4)}
    except Exception:
        return _base


def _fee_drag_reconciliation_metric(pilot_ledger: List[dict]) -> dict:
    """
    Fee drag divergence: absolute % deviation of actual fee from expected.
    Score 0–100; higher = worse.
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT", "sample_count": 0, "mean_fee_drag": None}
    execs = _exec_entries(pilot_ledger)
    if not execs:
        return _base
    try:
        drags = []
        for e in execs:
            exp = e.get("expected_fee") or 0.0
            act = e.get("actual_fee")   or 0.0
            base = max(abs(exp), 1e-9)
            drags.append(abs(act - exp) / base * 100.0)
        if not drags:
            return {**_base, "sample_count": len(execs)}
        mean_drag = sum(drags) / len(drags)
        score     = min(100.0, mean_drag)
        if score < 10.0:   tier = "LOW"
        elif score < 30.0: tier = "MODERATE"
        elif score < 60.0: tier = "HIGH"
        else:              tier = "CRITICAL"
        return {"score": round(score, 2), "tier": tier,
                "sample_count": len(drags), "mean_fee_drag": round(mean_drag, 2)}
    except Exception:
        return _base


def _hold_economics_reconciliation_metric(pilot_ledger: List[dict]) -> dict:
    """
    Hold economics divergence: how much actual net PnL underperformed expectation.
    Score 0–100; higher = worse (actual < expected).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT", "sample_count": 0,
             "mean_pnl_delta": None, "mean_expected_pnl": None}
    execs = _exec_entries(pilot_ledger)
    if not execs:
        return _base
    try:
        deltas, exp_pnls = [], []
        for e in execs:
            exp = e.get("expected_net_pnl") or 0.0
            act = e.get("actual_net_pnl")   or 0.0
            deltas.append(act - exp)
            exp_pnls.append(exp)
        if not deltas:
            return {**_base, "sample_count": len(execs)}
        mean_delta   = sum(deltas) / len(deltas)
        mean_exp_pnl = sum(exp_pnls) / len(exp_pnls)
        base         = max(abs(mean_exp_pnl), 1e-9)
        score        = min(100.0, max(0.0, -mean_delta / base * 100.0))
        if score < 10.0:   tier = "LOW"
        elif score < 30.0: tier = "MODERATE"
        elif score < 60.0: tier = "HIGH"
        else:              tier = "CRITICAL"
        return {"score": round(score, 2), "tier": tier,
                "sample_count": len(deltas),
                "mean_pnl_delta":   round(mean_delta, 4),
                "mean_expected_pnl": round(mean_exp_pnl, 4)}
    except Exception:
        return _base


# ── Confirmation chain integrity ───────────────────────────────────────────────

def _confirmation_chain_integrity(pilot_ledger: List[dict]) -> dict:
    """
    Verify every execution entry in the ledger carries explicit human confirmation
    and that no auto-authorized entries exist. A single violation = VIOLATED.
    """
    if not pilot_ledger:
        return {
            "integrity":               "EMPTY",
            "all_human_confirmed":     True,
            "unauthorized_entries":    0,
            "execution_entries":       0,
            "total_entries":           0,
            "auto_authorized_entries": 0,
        }
    try:
        all_entries  = [e for e in pilot_ledger if isinstance(e, dict)]
        exec_entries = [e for e in all_entries if e.get("entry_type") == "EXECUTION"]
        unauth       = [e for e in exec_entries if not e.get("human_confirmed", False)]
        auto_auth    = [e for e in all_entries  if e.get("auto_authorized") is True]
        all_confirmed = len(unauth) == 0
        integrity     = "INTACT" if (all_confirmed and not auto_auth) else "VIOLATED"
        return {
            "integrity":               integrity,
            "all_human_confirmed":     all_confirmed,
            "unauthorized_entries":    len(unauth),
            "execution_entries":       len(exec_entries),
            "total_entries":           len(all_entries),
            "auto_authorized_entries": len(auto_auth),
        }
    except Exception:
        return {
            "integrity":               "UNKNOWN",
            "all_human_confirmed":     False,
            "unauthorized_entries":    0,
            "execution_entries":       0,
            "total_entries":           len(pilot_ledger),
            "auto_authorized_entries": 0,
        }


# ── Kill-switch advisory ───────────────────────────────────────────────────────

def _kill_switch_advisory(
    reconciliation_metrics: dict,
    confirmation_chain: dict,
) -> dict:
    """
    Evaluate whether kill-switch conditions are active.
    Returns advisory only — no autonomous action is ever taken.
    """
    try:
        reasons = []
        if not confirmation_chain.get("all_human_confirmed", True):
            reasons.append("unauthorized execution entries detected in pilot ledger")
        if confirmation_chain.get("auto_authorized_entries", 0) > 0:
            reasons.append("auto-authorized entries violate constitutional principles")
        for key, label in [
            ("slippage_reconciliation",       "slippage"),
            ("fee_drag_reconciliation",       "fee drag"),
            ("hold_economics_reconciliation", "hold economics"),
        ]:
            tier = reconciliation_metrics.get(key, {}).get("tier", "INSUFFICIENT")
            if tier in ("HIGH", "CRITICAL"):
                score = reconciliation_metrics[key].get("score", 0.0)
                reasons.append(f"critical {label} divergence (score={score:.1f})")
        if reconciliation_metrics.get("fill_quality", {}).get("tier") == "HIGH":
            reasons.append("fill quality severely degraded")
        if reconciliation_metrics.get("latency_reconciliation", {}).get("tier") == "CRITICAL":
            reasons.append("critical latency inflation")
        engage   = len(reasons) > 0
        priority = "CRITICAL" if len(reasons) >= 2 else ("HIGH" if engage else "NONE")
        reason   = "; ".join(reasons) if reasons else "no kill-switch conditions active"
        return {"engage": engage, "reason": reason, "priority": priority,
                "trigger_count": len(reasons)}
    except Exception:
        return {"engage": False, "reason": "advisory error", "priority": "NONE",
                "trigger_count": 0}


# ── Pilot survivability score ──────────────────────────────────────────────────

def _pilot_survivability_score(
    execution_readiness: dict,
    reconciliation_metrics: dict,
) -> dict:
    """
    Composite 0–100 pilot survivability.
    Without execution data: capped at 60 (readiness evidence only).
    With execution data: readiness (30%) + reconciliation quality (70%).
    """
    try:
        exec_data_present = any(
            isinstance(m, dict) and m.get("sample_count", 0) > 0
            for m in reconciliation_metrics.values()
        )
        if not exec_data_present:
            raw = execution_readiness.get("score", 0.0) * 0.60
        else:
            read_score = execution_readiness.get("score", 0.0)
            fill_pen   = reconciliation_metrics.get("fill_quality",                  {}).get("score", 0.0)
            slip_pen   = reconciliation_metrics.get("slippage_reconciliation",       {}).get("score", 0.0)
            lat_pen    = reconciliation_metrics.get("latency_reconciliation",        {}).get("score", 0.0)
            fee_pen    = reconciliation_metrics.get("fee_drag_reconciliation",       {}).get("score", 0.0)
            econ_pen   = reconciliation_metrics.get("hold_economics_reconciliation", {}).get("score", 0.0)
            total_pen  = (fill_pen * 0.25 + slip_pen * 0.25 + lat_pen * 0.15
                          + fee_pen * 0.15 + econ_pen * 0.20)
            raw = read_score * 0.30 + (100.0 - total_pen) * 0.70
        score = max(0.0, min(100.0, raw))
        if score >= 70.0:   tier = "STRONG"
        elif score >= 50.0: tier = "ADEQUATE"
        elif score >= 30.0: tier = "MARGINAL"
        else:               tier = "WEAK"
        return {"score": round(score, 2), "tier": tier}
    except Exception:
        return {"score": 0.0, "tier": "WEAK"}


# ── Pilot classification ───────────────────────────────────────────────────────

def _classify_pilot(
    reconciliation_metrics: dict,
    pilot_survivability: dict,
    confirmation_chain: dict,
    execution_readiness: dict,
) -> str:
    try:
        # Constitutional violations are unconditional lockdown
        if not confirmation_chain.get("all_human_confirmed", True):
            return PILOT_LOCKDOWN_RECOMMENDED
        if confirmation_chain.get("auto_authorized_entries", 0) > 0:
            return PILOT_LOCKDOWN_RECOMMENDED

        surv_score = pilot_survivability.get("score", 0.0)
        has_exec   = any(
            isinstance(m, dict) and m.get("sample_count", 0) > 0
            for m in reconciliation_metrics.values()
        )
        # Only escalate on low survivability if we have enough evidence
        # (INSUFFICIENT readiness tier = no meaningful paper data yet)
        sufficient  = (execution_readiness.get("tier", "INSUFFICIENT") != "INSUFFICIENT") or has_exec

        if surv_score < 20.0 and sufficient:
            return PILOT_LOCKDOWN_RECOMMENDED
        if surv_score < 35.0 and (has_exec or sufficient):
            return HUMAN_REVIEW_ESCALATION

        if has_exec:
            slip_tier = reconciliation_metrics.get("slippage_reconciliation",       {}).get("tier", "INSUFFICIENT")
            fill_tier = reconciliation_metrics.get("fill_quality",                  {}).get("tier", "INSUFFICIENT")
            lat_tier  = reconciliation_metrics.get("latency_reconciliation",        {}).get("tier", "INSUFFICIENT")
            econ_tier = reconciliation_metrics.get("hold_economics_reconciliation", {}).get("tier", "INSUFFICIENT")
            if slip_tier == "CRITICAL":
                return SLIPPAGE_COLLAPSE
            if fill_tier == "HIGH" or lat_tier == "CRITICAL":
                return LIQUIDITY_FAILURE
            if econ_tier in ("HIGH", "CRITICAL") or slip_tier == "HIGH" or fill_tier == "MODERATE":
                return EXECUTION_DRIFT

        return REALITY_CONSISTENT
    except Exception:
        return REALITY_CONSISTENT


# ── Pilot state assessment ─────────────────────────────────────────────────────

def _assess_pilot_state(
    execution_readiness: dict,
    pilot_classification: str,
    pilot_survivability: dict,
    confirmation_chain: dict,
    pilot_ledger_depth: int,
) -> str:
    try:
        if pilot_classification == PILOT_LOCKDOWN_RECOMMENDED:
            return CONSTITUTION_LOCKDOWN
        if (not confirmation_chain.get("all_human_confirmed", True)
                and pilot_ledger_depth > 0):
            return CONSTITUTION_LOCKDOWN
        if pilot_classification in (HUMAN_REVIEW_ESCALATION, SLIPPAGE_COLLAPSE, LIQUIDITY_FAILURE):
            return MANUAL_KILL_SWITCH

        surv_score = pilot_survivability.get("score", 0.0)
        read_score = execution_readiness.get("score", 0.0)
        exec_count = confirmation_chain.get("execution_entries", 0)

        if (pilot_classification == REALITY_CONSISTENT
                and surv_score >= 60.0
                and read_score >= 50.0
                and exec_count > 0):
            return SINGLE_CONFIRM_EXECUTION
        if surv_score >= 50.0 and read_score >= 50.0:
            return HUMAN_ARMED_MICRO
        if read_score >= 30.0:
            return SHADOW_OBSERVATION
        return PAPER_ONLY
    except Exception:
        return PAPER_ONLY


# ── Pilot opportunity (research-only recommendation for human consideration) ──

def _recommend_pilot_opportunity(
    trades: List[dict],
    execution_readiness: dict,
) -> dict:
    _base = {
        "available": False,
        "expected_net_expectancy": 0.0,
        "expected_slippage_pct": 0.0,
        "recommended_exposure": "NONE",
        "constitutional_risk_summary": "No data — PAPER_ONLY state mandatory",
        "auto_authorized": False,
        "human_confirmation_required": True,
    }
    if not trades:
        return _base
    try:
        valid = [t for t in trades if isinstance(t, dict)]
        if not valid:
            return _base
        n            = len(valid)
        net_exp      = sum(t.get("net_pnl") or 0.0 for t in valid) / n
        gross_vals   = [abs(t.get("gross_pnl") or t.get("net_pnl") or 0.0) for t in valid]
        gross_exp    = sum(gross_vals) / n
        mean_slip    = sum(t.get("slippage_cost") or 0.0 for t in valid) / n
        mean_fee     = sum((t.get("fee_entry") or 0.0) + (t.get("fee_exit") or 0.0)
                          for t in valid) / n
        slip_pct     = abs(mean_slip) / max(abs(gross_exp), 1e-9) * 100.0
        read_score   = execution_readiness.get("score", 0.0)
        available    = read_score >= 50.0 and net_exp > 0

        if read_score < 30.0:    exposure = "NONE"
        elif read_score < 50.0:  exposure = "SHADOW_ONLY"
        elif read_score < 70.0:  exposure = "MICRO_FIXED_MINIMUM"
        else:                    exposure = "MICRO_FIXED_CONSERVATIVE"

        return {
            "available":                   available,
            "expected_net_expectancy":     round(net_exp, 4),
            "expected_gross_expectancy":   round(gross_exp, 4),
            "expected_slippage_pct":       round(slip_pct, 2),
            "expected_mean_fee":           round(mean_fee, 4),
            "recommended_exposure":        exposure,
            "constitutional_risk_summary": (
                f"readiness={read_score:.1f} net_exp={net_exp:.4f} "
                f"slip_pct={slip_pct:.1f}% fee={mean_fee:.4f}"
            ),
            "auto_authorized":             False,
            "human_confirmation_required": True,
        }
    except Exception:
        return _base


# ── Recommendation generator ───────────────────────────────────────────────────

def _generate_pilot_recommendations(
    pilot_state: str,
    pilot_classification: str,
    execution_readiness: dict,
    reconciliation_metrics: dict,
    kill_switch: dict,
    pilot_ledger_depth: int,
) -> List[dict]:
    recs: List[dict] = []

    if kill_switch.get("engage"):
        recs.append({
            "priority":       "CRITICAL",
            "type":           "KILL_SWITCH_ADVISORY",
            "summary":        f"Kill-switch active: {kill_switch.get('reason', 'unknown condition')}",
            "action_required": "IMMEDIATE_HUMAN_REVIEW",
            "auto_authorized": False,
        })

    if pilot_state == CONSTITUTION_LOCKDOWN:
        recs.append({
            "priority":       "CRITICAL",
            "type":           "CONSTITUTIONAL_LOCKDOWN",
            "summary":        "Constitutional lockdown — no pilot action permitted until explicit human governance review.",
            "action_required": "HUMAN_GOVERNANCE_REVIEW_REQUIRED",
            "auto_authorized": False,
        })

    read_tier = execution_readiness.get("tier", "INSUFFICIENT")
    if read_tier in ("INSUFFICIENT", "EARLY"):
        recs.append({
            "priority":       "HIGH",
            "type":           "EXECUTION_READINESS",
            "summary":        (
                f"Execution readiness {read_tier.lower()} "
                f"(score={execution_readiness.get('score', 0.0):.1f}) — "
                "continue paper trading accumulation before any pilot consideration."
            ),
            "action_required": "CONTINUE_PAPER_TRADING",
            "auto_authorized": False,
        })

    slip_tier = reconciliation_metrics.get("slippage_reconciliation", {}).get("tier", "INSUFFICIENT")
    if slip_tier in ("HIGH", "CRITICAL"):
        recs.append({
            "priority":       "HIGH",
            "type":           "SLIPPAGE_DIVERGENCE",
            "summary":        (
                f"Slippage divergence {slip_tier.lower()} — "
                "real execution significantly exceeds simulation assumptions."
            ),
            "action_required": "HUMAN_REVIEW_SLIPPAGE_MODEL",
            "auto_authorized": False,
        })

    fee_tier = reconciliation_metrics.get("fee_drag_reconciliation", {}).get("tier", "INSUFFICIENT")
    if fee_tier in ("HIGH", "CRITICAL"):
        recs.append({
            "priority":       "MEDIUM",
            "type":           "FEE_DRAG_DIVERGENCE",
            "summary":        f"Fee drag {fee_tier.lower()} — actual fees exceed simulation assumptions.",
            "action_required": "HUMAN_REVIEW_FEE_MODEL",
            "auto_authorized": False,
        })

    if pilot_ledger_depth == 0:
        recs.append({
            "priority":       "MEDIUM",
            "type":           "PILOT_READINESS",
            "summary":        (
                "No pilot execution history yet — constitutional infrastructure ready for "
                "human-initiated micro pilot consideration."
            ),
            "action_required": "HUMAN_DECISION_REQUIRED",
            "auto_authorized": False,
        })
    elif pilot_classification == EXECUTION_DRIFT:
        recs.append({
            "priority":       "MEDIUM",
            "type":           "EXECUTION_DRIFT",
            "summary":        "Real execution diverging from expectations — reduce exposure and increase monitoring frequency.",
            "action_required": "HUMAN_REVIEW_EXECUTION_MODEL",
            "auto_authorized": False,
        })

    if not recs:
        recs.append({
            "priority":       "LOW",
            "type":           "PILOT_STATUS",
            "summary":        (
                f"Pilot state {pilot_state}: "
                f"{_PILOT_STATE_DESCRIPTIONS.get(pilot_state, 'see pilot state description')}"
            ),
            "action_required": "CONTINUE_MONITORING",
            "auto_authorized": False,
        })

    return recs


# ── Audit entry ────────────────────────────────────────────────────────────────

def _generate_pilot_audit_entry(
    pilot_state: str,
    pilot_classification: str,
    pilot_survivability: dict,
    execution_readiness: dict,
    kill_switch: dict,
    recommendations: List[dict],
) -> dict:
    try:
        ts      = int(_time.time() * 1000)
        payload = (
            f"{ts}|{pilot_state}|{pilot_classification}"
            f"|{pilot_survivability.get('score', 0.0)}"
            f"|{execution_readiness.get('score', 0.0)}"
        )
        fp = hashlib.sha256(payload.encode()).hexdigest()
        return {
            "entry_id":                  f"GMPD-{ts}-{fp[:16]}",
            "timestamp_ms":              ts,
            "entry_type":                "ANALYSIS",
            "pilot_state":               pilot_state,
            "pilot_classification":      pilot_classification,
            "pilot_survivability_score": pilot_survivability.get("score", 0.0),
            "execution_readiness_score": execution_readiness.get("score", 0.0),
            "kill_switch_engaged":       kill_switch.get("engage", False),
            "recommendations_generated": len(recommendations),
            "human_approval_required":   pilot_state != PAPER_ONLY,
            "auto_authorized":           False,
            "immutable":                 True,
        }
    except Exception:
        ts = int(_time.time() * 1000)
        return {
            "entry_id":              f"GMPD-{ts}-error",
            "timestamp_ms":          ts,
            "entry_type":            "ANALYSIS",
            "pilot_state":           PAPER_ONLY,
            "human_approval_required": False,
            "auto_authorized":       False,
            "immutable":             True,
        }


# ── Public entry point ─────────────────────────────────────────────────────────

def compute_guarded_micro_pilot(
    trades: List[dict],
    pilot_ledger: Optional[List[dict]] = None,
) -> dict:
    """
    Produce a constitutional micro-pilot governance assessment.

    Args:
        trades:       Paper trade history (from session + DataLake).
        pilot_ledger: Session-scoped pilot execution ledger (append-only;
                      may contain ANALYSIS and EXECUTION entries).

    Returns a research-only dict. Never raises. Never modifies inputs.
    All recommendations have auto_authorized=False.
    """
    if pilot_ledger is None:
        pilot_ledger = []
    try:
        execution_readiness    = _execution_readiness_metric(trades)
        reconciliation_metrics = {
            "fill_quality":                  _fill_quality_metric(pilot_ledger),
            "slippage_reconciliation":       _slippage_reconciliation_metric(pilot_ledger),
            "latency_reconciliation":        _latency_reconciliation_metric(pilot_ledger),
            "fee_drag_reconciliation":       _fee_drag_reconciliation_metric(pilot_ledger),
            "hold_economics_reconciliation": _hold_economics_reconciliation_metric(pilot_ledger),
        }
        confirmation_chain  = _confirmation_chain_integrity(pilot_ledger)
        pilot_survivability = _pilot_survivability_score(execution_readiness, reconciliation_metrics)
        pilot_classification = _classify_pilot(
            reconciliation_metrics, pilot_survivability, confirmation_chain, execution_readiness,
        )
        kill_switch = _kill_switch_advisory(reconciliation_metrics, confirmation_chain)
        pilot_state = _assess_pilot_state(
            execution_readiness, pilot_classification, pilot_survivability,
            confirmation_chain, len(pilot_ledger),
        )
        recommendations  = _generate_pilot_recommendations(
            pilot_state, pilot_classification, execution_readiness,
            reconciliation_metrics, kill_switch, len(pilot_ledger),
        )
        pilot_opportunity = _recommend_pilot_opportunity(trades, execution_readiness)
        audit_entry = _generate_pilot_audit_entry(
            pilot_state, pilot_classification, pilot_survivability,
            execution_readiness, kill_switch, recommendations,
        )
        return {
            "scope_note": (
                "FTD-GMPD ultra-guarded micro-pilot doctrine — research instrumentation only. "
                "All execution authority remains explicitly human-controlled. "
                "PHOENIX may NEVER self-fire an exchange order or possess sovereign "
                "economic execution authority."
            ),
            "total_trades":                 len(trades),
            "pilot_ledger_depth":           len(pilot_ledger),
            "pilot_state":                  pilot_state,
            "pilot_state_description":      _PILOT_STATE_DESCRIPTIONS.get(pilot_state, ""),
            "pilot_classification":         pilot_classification,
            "pilot_survivability":          pilot_survivability,
            "execution_readiness":          execution_readiness,
            "confirmation_chain_integrity": confirmation_chain,
            "reconciliation_metrics":       reconciliation_metrics,
            "kill_switch_advisory":         kill_switch,
            "recommendations":              recommendations,
            "pilot_opportunity":            pilot_opportunity,
            "pilot_hard_principles":        PILOT_HARD_PRINCIPLES,
            "audit_entry":                  audit_entry,
        }
    except Exception:
        return {
            "scope_note": "FTD-GMPD research instrumentation — analysis error.",
            "error":      "analysis failed",
            "pilot_state": PAPER_ONLY,
            "pilot_hard_principles": PILOT_HARD_PRINCIPLES,
        }
