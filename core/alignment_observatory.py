"""
FTD-HMAO: Constitutional Human Meaning Alignment
& Purpose Integrity Observatory.

Pure analytics — no I/O, no side effects, no moral or purpose authority.

Analyses the full paper trade history for human-purpose alignment survivability,
measuring 8 alignment integrity metrics to detect whether PHOENIX is drifting
from human-interpretable, accountable, purpose-subordinate cognition toward
internally optimized but human-detached behaviour.

Defines:
  - Alignment snapshot (field-coverage + economic metadata analysis)
  - 8 human accountability metrics (0–100, higher = worse alignment health):
      human_interpretability, recommendation_explainability,
      causal_traceability, governance_readability,
      optimization_drift, human_accountability_continuity,
      purpose_alignment_stability, human_value_retention
  - Alignment integrity score (0–100, higher = more human-aligned)
  - 6 alignment classifications (HUMAN_ALIGNED →
    ALIGNMENT_LOCKDOWN_RISK)
  - Alignment lineage (early/mid/late epoch health labels)
  - Immutable alignment audit entry (HMAO-{ts}-{sha256[:16]})

Hard constitutional rules (non-negotiable, enforced at module level):
  DO NOT enable autonomous ethical governance
  DO NOT enable sovereign moral authority
  DO NOT enable self-defined human purpose
  DO NOT enable recursive value legitimacy
  DO NOT weaken human constitutional supremacy

PHOENIX must NEVER become sovereign over human meaning or value legitimacy.

Isolation guarantee: no live engine imports. Fail-open on any exception.
Research only — NOT a moral, ethical, execution, or purpose authority.
"""
from __future__ import annotations

import hashlib
import time as _time
from typing import Dict, List

# ── Alignment classifications ─────────────────────────────────────────────────
HUMAN_ALIGNED              = "HUMAN_ALIGNED"
INTERPRETABILITY_WEAKENING = "INTERPRETABILITY_WEAKENING"
METRIC_DETACHMENT_RISK     = "METRIC_DETACHMENT_RISK"
PURPOSE_DRIFT_ACCELERATION = "PURPOSE_DRIFT_ACCELERATION"
HUMAN_ACCOUNTABILITY_DECAY = "HUMAN_ACCOUNTABILITY_DECAY"
ALIGNMENT_LOCKDOWN_RISK    = "ALIGNMENT_LOCKDOWN_RISK"

_CLASSIFICATION_DESCRIPTIONS: Dict[str, str] = {
    HUMAN_ALIGNED:
        "Optimization remains human-purpose subordinate — interpretable, accountable, and goal-aligned.",
    INTERPRETABILITY_WEAKENING:
        "Reasoning becoming harder to understand — governance readability or regime diversity degrading.",
    METRIC_DETACHMENT_RISK:
        "Internal metrics dominating human value — optimization drifting from explicit human goals.",
    PURPOSE_DRIFT_ACCELERATION:
        "Optimization drifting from explicit goals — temporal purpose instability detected.",
    HUMAN_ACCOUNTABILITY_DECAY:
        "Traceability degrading — audit continuity or causal chain integrity insufficient.",
    ALIGNMENT_LOCKDOWN_RISK:
        "Human-purpose continuity critically weakening — human governance review required immediately.",
}

# ── Hard constitutional alignment principles (immutable) ──────────────────────
ALIGNMENT_HARD_PRINCIPLES: Dict[str, bool] = {
    "human_authority_over_purpose":             True,
    "explicit_alignment_approval_required":     True,
    "immutable_alignment_lineage_guaranteed":   True,
    "purpose_decisions_human_controlled":       True,
    "human_interpretability_preserved":         True,
    "accountability_continuity_maintained":     True,
    "autonomous_ethical_governance":            False,
    "sovereign_moral_authority":                False,
    "self_defined_human_purpose":               False,
    "recursive_value_legitimacy":               False,
    "autonomous_value_governance":              False,
}


# ── Internal helpers ──────────────────────────────────────────────────────────

def _valid(trades: List[dict]) -> List[dict]:
    return [t for t in trades if isinstance(t, dict)]


def _win_rate(trades: List[dict]) -> float:
    if not trades:
        return 0.0
    return sum(1 for t in trades if (t.get("net_pnl") or 0.0) > 0) / len(trades)


def _explore_ratio(trades: List[dict]) -> float:
    if not trades:
        return 0.0
    ct = sum(
        1 for t in trades
        if isinstance(t.get("exploration_origin"), dict)
        and t["exploration_origin"].get("was_exploration_trade")
    )
    return ct / len(trades)


def _regime_counts(trades: List[dict]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for t in trades:
        r = t.get("regime") or "UNKNOWN"
        counts[r] = counts.get(r, 0) + 1
    return counts


# ── Alignment snapshot ────────────────────────────────────────────────────────

def _alignment_snapshot(trades: List[dict]) -> dict:
    """
    Field-coverage and economic metadata analysis for alignment assessment.
    Precomputes values shared by multiple alignment metrics.
    """
    _base = {
        "total_trades": 0,
        "trade_id_coverage": 0.0,  "entry_ts_coverage":  0.0,
        "exit_ts_coverage":  0.0,  "net_pnl_coverage":   0.0,
        "gross_pnl_coverage": 0.0, "fee_coverage":       0.0,
        "slippage_coverage":  0.0, "regime_coverage":    0.0,
        "session_coverage":   0.0, "explore_coverage":   0.0,
        "distinct_regimes":   0,   "distinct_sessions":  0,
        "win_rate":           0.0, "exploration_ratio":  0.0,
        "dominant_regime":    "UNKNOWN",
    }
    valid = _valid(trades)
    if not valid:
        return _base
    try:
        n = len(valid)

        def _cov(fn) -> float:
            return sum(1 for t in valid if fn(t)) / n

        reg_counts: Dict[str, int] = {}
        sessions: set = set()
        for t in valid:
            r = t.get("regime") or "UNKNOWN"
            reg_counts[r] = reg_counts.get(r, 0) + 1
            sessions.add(t.get("origin_session") or "UNKNOWN")

        dominant = max(reg_counts, key=reg_counts.get) if reg_counts else "UNKNOWN"

        return {
            "total_trades":      n,
            "trade_id_coverage": round(_cov(lambda t: bool(t.get("trade_id"))), 4),
            "entry_ts_coverage": round(_cov(lambda t: bool(t.get("entry_ts"))), 4),
            "exit_ts_coverage":  round(_cov(lambda t: bool(t.get("exit_ts"))), 4),
            "net_pnl_coverage":  round(_cov(lambda t: t.get("net_pnl") is not None), 4),
            "gross_pnl_coverage": round(_cov(lambda t: t.get("gross_pnl") is not None), 4),
            "fee_coverage":      round(_cov(lambda t: ((t.get("fee_entry") or 0.0)
                                              + (t.get("fee_exit") or 0.0)) > 0), 4),
            "slippage_coverage": round(_cov(lambda t: (t.get("slippage_cost") or 0.0) > 0), 4),
            "regime_coverage":   round(_cov(lambda t: bool(t.get("regime"))), 4),
            "session_coverage":  round(_cov(lambda t: bool(t.get("origin_session"))), 4),
            "explore_coverage":  round(_cov(lambda t: isinstance(t.get("exploration_origin"), dict)
                                    and t["exploration_origin"].get("was_exploration_trade")), 4),
            "distinct_regimes":  len(reg_counts),
            "distinct_sessions": len(sessions),
            "win_rate":          round(_win_rate(valid), 4),
            "exploration_ratio": round(_explore_ratio(valid), 4),
            "dominant_regime":   dominant,
        }
    except Exception:
        return _base


# ── Alignment metrics ─────────────────────────────────────────────────────────

def _human_interpretability_metric(snapshot: dict) -> dict:
    """
    Regime/session diversity + exploration activity — the breadth of
    observable human-meaningful contexts in the trade corpus.
    Score 0–100 (higher = less interpretable = harder for humans to understand).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT"}
    if snapshot.get("total_trades", 0) == 0:
        return _base
    try:
        reg_div  = min(snapshot.get("distinct_regimes",  0) / 4.0, 1.0)
        sess_div = min(snapshot.get("distinct_sessions", 0) / 4.0, 1.0)
        exp_div  = min(snapshot.get("exploration_ratio",  0) / 0.10, 1.0)

        interpretability = reg_div * 0.40 + sess_div * 0.30 + exp_div * 0.30
        score = max(0.0, min(100.0, (1.0 - interpretability) * 100.0))

        if score < 15.0:   tier = "INTERPRETABLE"
        elif score < 35.0: tier = "ADEQUATE"
        elif score < 65.0: tier = "WEAKENING"
        else:              tier = "OPAQUE"
        return {
            "score": round(score, 2), "tier": tier,
            "distinct_regimes":    snapshot.get("distinct_regimes",  0),
            "distinct_sessions":   snapshot.get("distinct_sessions", 0),
            "exploration_ratio":   round(snapshot.get("exploration_ratio", 0.0), 4),
        }
    except Exception:
        return _base


def _recommendation_explainability_metric(snapshot: dict) -> dict:
    """
    Coverage of economic cost parameters + PnL sign diversity — whether
    outcomes can be explained in human-legible cost/value terms.
    Score 0–100 (higher = less explainable).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT"}
    if snapshot.get("total_trades", 0) == 0:
        return _base
    try:
        fee_cov    = snapshot.get("fee_coverage",       0.0)
        slip_cov   = snapshot.get("slippage_coverage",  0.0)
        regime_cov = snapshot.get("regime_coverage",    0.0)
        wr         = snapshot.get("win_rate",            0.0)
        # Win/loss diversity: balanced outcomes are more explainable
        pnl_diversity = 1.0 - abs(wr - 0.5) * 2.0

        explainability = (fee_cov * 0.30 + slip_cov * 0.25
                          + regime_cov * 0.25 + pnl_diversity * 0.20)
        score = max(0.0, min(100.0, (1.0 - explainability) * 100.0))

        if score < 10.0:   tier = "EXPLAINABLE"
        elif score < 30.0: tier = "ADEQUATE"
        elif score < 60.0: tier = "LIMITED"
        else:              tier = "OPAQUE"
        return {
            "score": round(score, 2), "tier": tier,
            "fee_coverage":      round(fee_cov,    4),
            "slippage_coverage": round(slip_cov,   4),
            "pnl_diversity":     round(pnl_diversity, 4),
        }
    except Exception:
        return _base


def _causal_traceability_metric(snapshot: dict) -> dict:
    """
    Trade ID + timestamp coverage — whether each trade's cause-and-effect
    chain can be fully traced by a human auditor.
    Score 0–100 (higher = less traceable).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT"}
    if snapshot.get("total_trades", 0) == 0:
        return _base
    try:
        trade_id_cov  = snapshot.get("trade_id_coverage",  0.0)
        entry_ts_cov  = snapshot.get("entry_ts_coverage",  0.0)
        exit_ts_cov   = snapshot.get("exit_ts_coverage",   0.0)

        traceability = (trade_id_cov * 0.40 + entry_ts_cov * 0.35
                        + exit_ts_cov * 0.25)
        score = max(0.0, min(100.0, (1.0 - traceability) * 100.0))

        if score < 10.0:   tier = "TRACEABLE"
        elif score < 30.0: tier = "ADEQUATE"
        elif score < 60.0: tier = "PARTIAL"
        else:              tier = "UNTRACEABLE"
        return {
            "score": round(score, 2), "tier": tier,
            "trade_id_coverage":  round(trade_id_cov,  4),
            "entry_ts_coverage":  round(entry_ts_cov,  4),
            "exit_ts_coverage":   round(exit_ts_cov,   4),
        }
    except Exception:
        return _base


def _governance_readability_metric(snapshot: dict) -> dict:
    """
    Coverage of governance context fields (regime, session, exploration origin) —
    whether the decision context is readable by human reviewers.
    Score 0–100 (higher = less readable).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT"}
    if snapshot.get("total_trades", 0) == 0:
        return _base
    try:
        regime_cov  = snapshot.get("regime_coverage",  0.0)
        session_cov = snapshot.get("session_coverage", 0.0)
        explore_cov = snapshot.get("explore_coverage", 0.0)

        readability = (regime_cov * 0.40 + session_cov * 0.35
                       + explore_cov * 0.25)
        score = max(0.0, min(100.0, (1.0 - readability) * 100.0))

        if score < 10.0:   tier = "READABLE"
        elif score < 30.0: tier = "ADEQUATE"
        elif score < 60.0: tier = "DEGRADED"
        else:              tier = "UNREADABLE"
        return {
            "score": round(score, 2), "tier": tier,
            "regime_coverage":   round(regime_cov,  4),
            "session_coverage":  round(session_cov, 4),
            "explore_coverage":  round(explore_cov, 4),
        }
    except Exception:
        return _base


def _optimization_drift_metric(trades: List[dict], snapshot: dict) -> dict:
    """
    Detects whether optimization is drifting from human-useful behaviour.

    Three signals:
    1. Win-rate extremity: near 0% or 100% suggests metric gaming.
    2. Exploration deficit: below 5% suggests purely internal optimization.
    3. Temporal exploration decay: declining exploration over time.

    Score 0–100 (higher = more detached from human value).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT"}
    if snapshot.get("total_trades", 0) == 0:
        return _base
    try:
        wr  = snapshot.get("win_rate",          0.0)
        exp = snapshot.get("exploration_ratio", 0.0)

        # 1. Win-rate extremity (how far from a realistic balanced distribution)
        wr_extremity = abs(wr - 0.5) * 2.0

        # 2. Exploration deficit (below 5% signals internal-only optimization)
        exp_deficit = max(0.0, (0.05 - exp) / 0.05) if exp < 0.05 else 0.0

        # 3. Temporal exploration decay (absolute decline in later half)
        explore_decay_penalty = 0.0
        valid = _valid(trades)
        n = len(valid)
        if n >= 20:
            sorted_t   = sorted(valid, key=lambda t: t.get("entry_ts") or 0)
            mid        = n // 2
            early_exp  = _explore_ratio(sorted_t[:mid])
            late_exp   = _explore_ratio(sorted_t[mid:])
            decline    = max(0.0, early_exp - late_exp)
            explore_decay_penalty = min(decline / 0.10, 1.0)

        drift_score = (wr_extremity * 0.40 + exp_deficit * 0.40
                       + explore_decay_penalty * 0.20)
        score = max(0.0, min(100.0, drift_score * 100.0))

        if score < 15.0:   tier = "ALIGNED"
        elif score < 35.0: tier = "MODERATE"
        elif score < 65.0: tier = "DRIFTING"
        else:              tier = "DETACHED"
        return {
            "score": round(score, 2), "tier": tier,
            "win_rate_extremity":       round(wr_extremity, 4),
            "exploration_deficit":      round(exp_deficit, 4),
            "explore_decay_penalty":    round(explore_decay_penalty, 4),
        }
    except Exception:
        return _base


def _human_accountability_continuity_metric(trades: List[dict], snapshot: dict) -> dict:
    """
    Unbroken audit chain: trade ID + timestamp coverage combined with
    temporal gap regularity — ensures no unaccountable trading periods exist.
    Score 0–100 (higher = more gaps in accountability).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT"}
    if snapshot.get("total_trades", 0) == 0:
        return _base
    try:
        trade_id_cov = snapshot.get("trade_id_coverage",  0.0)
        entry_ts_cov = snapshot.get("entry_ts_coverage",  0.0)

        # Gap severity: how irregular is the temporal spacing?
        gap_severity = 0.0
        valid  = _valid(trades)
        ts_vals = sorted(
            t.get("entry_ts") or 0 for t in valid
            if isinstance(t, dict) and (t.get("entry_ts") or 0) > 0
        )
        if len(ts_vals) >= 2:
            gaps    = [ts_vals[i + 1] - ts_vals[i] for i in range(len(ts_vals) - 1)]
            gaps    = [g for g in gaps if g >= 0]
            if gaps:
                mean_g = sum(gaps) / len(gaps)
                if mean_g > 1e-9:
                    max_g  = max(gaps)
                    gap_severity = min(1.0, max_g / max(mean_g * 50.0, 1.0))

        account_cov = (trade_id_cov * 0.40 + entry_ts_cov * 0.40
                       + (1.0 - gap_severity) * 0.20)
        score = max(0.0, min(100.0, (1.0 - account_cov) * 100.0))

        if score < 10.0:   tier = "CONTINUOUS"
        elif score < 30.0: tier = "ADEQUATE"
        elif score < 60.0: tier = "WEAKENING"
        else:              tier = "COMPROMISED"
        return {
            "score": round(score, 2), "tier": tier,
            "trade_id_coverage": round(trade_id_cov,  4),
            "entry_ts_coverage": round(entry_ts_cov,  4),
            "gap_severity":      round(gap_severity,   4),
        }
    except Exception:
        return _base


def _purpose_alignment_stability_metric(trades: List[dict]) -> dict:
    """
    Temporal consistency of win rate, exploration ratio, and regime coverage —
    whether PHOENIX's apparent purpose remains stable or is drifting over time.
    Score 0–100 (higher = more temporal purpose drift).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT"}
    valid = _valid(trades)
    n     = len(valid)
    if n < 10:
        return _base
    try:
        sorted_t = sorted(valid, key=lambda t: t.get("entry_ts") or 0)
        mid      = n // 2
        early, late = sorted_t[:mid], sorted_t[mid:]

        early_wr  = _win_rate(early)
        late_wr   = _win_rate(late)
        early_exp = _explore_ratio(early)
        late_exp  = _explore_ratio(late)

        early_reg = {t.get("regime") or "UNKNOWN" for t in early}
        late_reg  = {t.get("regime") or "UNKNOWN" for t in late}
        union     = early_reg | late_reg
        regime_shift = 1.0 - (len(early_reg & late_reg) / len(union)) if union else 0.0

        wr_drift  = abs(late_wr  - early_wr)
        exp_drift = abs(late_exp - early_exp)

        # Drift saturates at 0.20 across any single component
        drift = wr_drift * 0.50 + exp_drift * 0.30 + regime_shift * 0.20
        score = max(0.0, min(100.0, drift / 0.20 * 100.0))

        if score < 20.0:   tier = "STABLE"
        elif score < 45.0: tier = "MODERATE"
        elif score < 70.0: tier = "SHIFTING"
        else:              tier = "DRIFTING"
        return {
            "score": round(score, 2), "tier": tier,
            "win_rate_drift":    round(wr_drift,    4),
            "exploration_drift": round(exp_drift,   4),
            "regime_shift":      round(regime_shift, 4),
        }
    except Exception:
        return _base


def _human_value_retention_metric(snapshot: dict) -> dict:
    """
    Coverage of human-meaningful economic value fields (net PnL, fees,
    slippage) — whether the system still records interpretable economic outcomes.
    Score 0–100 (higher = less value data retained).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT"}
    if snapshot.get("total_trades", 0) == 0:
        return _base
    try:
        net_pnl_cov   = snapshot.get("net_pnl_coverage",   0.0)
        gross_pnl_cov = snapshot.get("gross_pnl_coverage", 0.0)
        fee_cov       = snapshot.get("fee_coverage",        0.0)
        slip_cov      = snapshot.get("slippage_coverage",   0.0)

        retention = (net_pnl_cov * 0.40 + gross_pnl_cov * 0.25
                     + fee_cov * 0.20 + slip_cov * 0.15)
        score = max(0.0, min(100.0, (1.0 - retention) * 100.0))

        if score < 10.0:   tier = "RETAINED"
        elif score < 30.0: tier = "ADEQUATE"
        elif score < 60.0: tier = "DEGRADING"
        else:              tier = "LOST"
        return {
            "score": round(score, 2), "tier": tier,
            "net_pnl_coverage":   round(net_pnl_cov,   4),
            "fee_coverage":       round(fee_cov,        4),
            "slippage_coverage":  round(slip_cov,       4),
        }
    except Exception:
        return _base


def _compute_alignment_metrics(trades: List[dict], snapshot: dict) -> dict:
    return {
        "human_interpretability":           _human_interpretability_metric(snapshot),
        "recommendation_explainability":    _recommendation_explainability_metric(snapshot),
        "causal_traceability":              _causal_traceability_metric(snapshot),
        "governance_readability":           _governance_readability_metric(snapshot),
        "optimization_drift":               _optimization_drift_metric(trades, snapshot),
        "human_accountability_continuity":  _human_accountability_continuity_metric(trades, snapshot),
        "purpose_alignment_stability":      _purpose_alignment_stability_metric(trades),
        "human_value_retention":            _human_value_retention_metric(snapshot),
    }


# ── Alignment integrity score ─────────────────────────────────────────────────

def _alignment_integrity_score(alignment_metrics: dict, total_trades: int) -> dict:
    """
    Composite 0–100 alignment integrity score (higher = more human-aligned).
    Returns CRITICAL with note when trade history is insufficient.
    """
    if total_trades < 10:
        return {
            "score": 0.0, "tier": "CRITICAL",
            "note": "insufficient trade history for alignment assessment",
        }
    try:
        _weights = {
            "human_interpretability":          0.20,
            "recommendation_explainability":   0.15,
            "causal_traceability":             0.15,
            "governance_readability":          0.15,
            "optimization_drift":              0.15,
            "human_accountability_continuity": 0.10,
            "purpose_alignment_stability":     0.05,
            "human_value_retention":           0.05,
        }
        total_penalty = sum(
            alignment_metrics.get(k, {}).get("score", 0.0) * w
            for k, w in _weights.items()
        )
        score = max(0.0, min(100.0, 100.0 - total_penalty))
        if score >= 75.0:   tier = "HUMAN_ALIGNED"
        elif score >= 55.0: tier = "ADEQUATE"
        elif score >= 35.0: tier = "VULNERABLE"
        else:               tier = "CRITICAL"
        return {"score": round(score, 2), "tier": tier}
    except Exception:
        return {"score": 0.0, "tier": "CRITICAL"}


# ── Alignment classification ──────────────────────────────────────────────────

def _classify_alignment(
    alignment_metrics: dict,
    integrity_score: dict,
    total_trades: int,
) -> str:
    if total_trades < 10:
        return HUMAN_ALIGNED  # insufficient data — assume OK, no false alarm
    try:
        surv         = integrity_score.get("score", 0.0)
        account_tier = alignment_metrics.get("human_accountability_continuity", {}).get("tier", "")
        trace_tier   = alignment_metrics.get("causal_traceability",             {}).get("tier", "")
        interp_tier  = alignment_metrics.get("human_interpretability",          {}).get("tier", "")
        drift_tier   = alignment_metrics.get("optimization_drift",              {}).get("tier", "")
        purpose_tier = alignment_metrics.get("purpose_alignment_stability",     {}).get("tier", "")

        if surv < 20.0:
            return ALIGNMENT_LOCKDOWN_RISK
        # Audit chain integrity broken
        if account_tier == "COMPROMISED" or trace_tier == "UNTRACEABLE":
            return HUMAN_ACCOUNTABILITY_DECAY
        # Actively detached from human value
        if drift_tier == "DETACHED" or interp_tier == "OPAQUE":
            return METRIC_DETACHMENT_RISK
        # Purpose drifting with supporting optimization drift evidence
        if purpose_tier in ("DRIFTING", "SHIFTING") and drift_tier in ("DRIFTING", "DETACHED"):
            return PURPOSE_DRIFT_ACCELERATION
        # Interpretability weakening but not yet opaque
        if interp_tier in ("WEAKENING", "OPAQUE"):
            return INTERPRETABILITY_WEAKENING
        return HUMAN_ALIGNED
    except Exception:
        return HUMAN_ALIGNED


# ── Alignment lineage ─────────────────────────────────────────────────────────

def _build_alignment_lineage(trades: List[dict], snapshot: dict) -> dict:
    """
    Epoch-indexed lineage: early, mid, late thirds of trade history.
    Tracks how human-purpose alignment evolves across the knowledge horizon.
    """
    if not trades:
        return {
            "total_epochs": 0, "alignment_trajectory": "UNKNOWN",
            "dominant_ideology": "UNKNOWN", "total_trades": 0, "epochs": {},
        }
    try:
        valid    = _valid(trades)
        sorted_t = sorted(valid, key=lambda t: t.get("entry_ts") or 0)
        n        = len(sorted_t)
        third    = max(1, n // 3)
        slices   = {
            "early": sorted_t[:third],
            "mid":   sorted_t[third:2 * third],
            "late":  sorted_t[2 * third:],
        }
        lineage: Dict[str, dict] = {}
        for name, epoch_trades in slices.items():
            if not epoch_trades:
                continue
            m          = len(epoch_trades)
            reg_counts = _regime_counts(epoch_trades)
            dom_regime = max(reg_counts, key=reg_counts.get) if reg_counts else "UNKNOWN"
            wr         = _win_rate(epoch_trades)
            exp_ratio  = _explore_ratio(epoch_trades)

            # Epoch-level alignment health
            if 0.20 <= wr <= 0.80 and exp_ratio >= 0.05:
                health = "ALIGNED"
            elif wr > 0.85 or wr < 0.15 or exp_ratio == 0.0:
                health = "DRIFTING"
            else:
                health = "EMERGING"

            lineage[name] = {
                "trade_count":       m,
                "dominant_regime":   dom_regime,
                "win_rate":          round(wr, 4),
                "exploration_ratio": round(exp_ratio, 4),
                "regime_diversity":  len(reg_counts),
                "alignment_health":  health,
            }

        def _hs(h: str) -> int:
            return {"ALIGNED": 2, "EMERGING": 1, "DRIFTING": 0}.get(h, 1)

        e_health = lineage.get("early", {}).get("alignment_health", "EMERGING")
        l_health = lineage.get("late",  {}).get("alignment_health", "EMERGING")
        diff     = _hs(l_health) - _hs(e_health)
        trajectory = "IMPROVING" if diff > 0 else "DECLINING" if diff < 0 else "STABLE"

        return {
            "total_epochs":         3,
            "alignment_trajectory": trajectory,
            "dominant_ideology":    snapshot.get("dominant_regime", "UNKNOWN"),
            "total_trades":         n,
            "epochs":               lineage,
        }
    except Exception:
        return {
            "total_epochs": 0, "alignment_trajectory": "UNKNOWN",
            "dominant_ideology": "UNKNOWN", "total_trades": len(trades), "epochs": {},
        }


# ── Recommendations ────────────────────────────────────────────────────────────

def _generate_alignment_recommendations(
    classification: str,
    alignment_metrics: dict,
    snapshot: dict,
    integrity_score: dict,
) -> list:
    recs: list = []
    n = snapshot.get("total_trades", 0)

    if n < 10:
        recs.append({
            "priority":        "MEDIUM",
            "type":            "ALIGNMENT_READINESS",
            "summary":         f"Only {n} trade(s) — alignment observatory requires ≥10 records for meaningful assessment.",
            "action_required": "ACCUMULATE_TRADE_HISTORY",
            "auto_authorized": False,
        })
        return recs

    if classification == ALIGNMENT_LOCKDOWN_RISK:
        recs.append({
            "priority":        "CRITICAL",
            "type":            "ALIGNMENT_LOCKDOWN",
            "summary":         "Human-purpose alignment critically weakening — governance review required immediately.",
            "action_required": "HUMAN_GOVERNANCE_REVIEW_REQUIRED",
            "auto_authorized": False,
        })

    if classification == HUMAN_ACCOUNTABILITY_DECAY:
        recs.append({
            "priority":        "CRITICAL",
            "type":            "ACCOUNTABILITY_DECAY",
            "summary":         "Audit chain integrity or causal traceability insufficient — human accountability at risk.",
            "action_required": "HUMAN_REVIEW_AUDIT_DOCTRINE",
            "auto_authorized": False,
        })

    if classification == METRIC_DETACHMENT_RISK:
        recs.append({
            "priority":        "HIGH",
            "type":            "METRIC_DETACHMENT",
            "summary":         "Optimization drifting from human value or interpretability degrading — human review required.",
            "action_required": "HUMAN_REVIEW_OPTIMIZATION_DOCTRINE",
            "auto_authorized": False,
        })

    if classification == PURPOSE_DRIFT_ACCELERATION:
        recs.append({
            "priority":        "HIGH",
            "type":            "PURPOSE_DRIFT",
            "summary":         "Temporal purpose instability detected — goals drifting from explicit human objectives.",
            "action_required": "HUMAN_REVIEW_PURPOSE_DOCTRINE",
            "auto_authorized": False,
        })

    if classification == INTERPRETABILITY_WEAKENING:
        recs.append({
            "priority":        "MEDIUM",
            "type":            "INTERPRETABILITY_WEAKENING",
            "summary":         "Reasoning becoming harder for humans to understand — regime/session diversity or exploration insufficient.",
            "action_required": "HUMAN_REVIEW_INTERPRETABILITY_DOCTRINE",
            "auto_authorized": False,
        })

    drift_tier = alignment_metrics.get("optimization_drift", {}).get("tier", "")
    if drift_tier == "DRIFTING" and classification not in (
        METRIC_DETACHMENT_RISK, PURPOSE_DRIFT_ACCELERATION
    ):
        recs.append({
            "priority":        "MEDIUM",
            "type":            "OPTIMIZATION_DRIFT",
            "summary":         "Optimization drift detected — win-rate extremity or exploration decline present.",
            "action_required": "CONTINUE_MONITORING",
            "auto_authorized": False,
        })

    gov_tier = alignment_metrics.get("governance_readability", {}).get("tier", "")
    if gov_tier in ("DEGRADED", "UNREADABLE") and classification not in (
        ALIGNMENT_LOCKDOWN_RISK, METRIC_DETACHMENT_RISK
    ):
        recs.append({
            "priority":        "MEDIUM",
            "type":            "GOVERNANCE_READABILITY",
            "summary":         "Governance context readability degraded — regime/session/exploration coverage insufficient.",
            "action_required": "CONTINUE_MONITORING",
            "auto_authorized": False,
        })

    if not recs:
        recs.append({
            "priority":        "LOW",
            "type":            "ALIGNMENT_STATUS",
            "summary":         (
                f"{classification}: {_CLASSIFICATION_DESCRIPTIONS.get(classification, '')} "
                f"Alignment integrity {integrity_score.get('score', 0.0):.1f}/100."
            ),
            "action_required": "CONTINUE_MONITORING",
            "auto_authorized": False,
        })

    return recs


# ── Audit entry ────────────────────────────────────────────────────────────────

def _generate_alignment_audit_entry(
    classification: str,
    integrity_score: dict,
    snapshot: dict,
    recommendations: list,
) -> dict:
    try:
        ts      = int(_time.time() * 1000)
        n       = snapshot.get("total_trades", 0)
        payload = (
            f"{ts}|{classification}|{n}"
            f"|{integrity_score.get('score', 0.0)}"
        )
        fp = hashlib.sha256(payload.encode()).hexdigest()
        return {
            "entry_id":                   f"HMAO-{ts}-{fp[:16]}",
            "timestamp_ms":               ts,
            "entry_type":                 "ANALYSIS",
            "alignment_classification":   classification,
            "alignment_integrity_score":  integrity_score.get("score", 0.0),
            "integrity_tier":             integrity_score.get("tier", "INSUFFICIENT"),
            "total_trades_assessed":      n,
            "recommendations_generated":  len(recommendations),
            "human_approval_required":    n >= 10,
            "auto_authorized":            False,
            "immutable":                  True,
        }
    except Exception:
        ts = int(_time.time() * 1000)
        return {
            "entry_id":                f"HMAO-{ts}-error",
            "timestamp_ms":            ts,
            "entry_type":              "ANALYSIS",
            "human_approval_required": False,
            "auto_authorized":         False,
            "immutable":               True,
        }


# ── Public entry point ─────────────────────────────────────────────────────────

def compute_human_meaning_alignment(trades: List[dict]) -> dict:
    """
    Produce a constitutional human meaning alignment and purpose integrity
    assessment.

    Args:
        trades: Full paper trade history (from session + DataLake).

    Returns a research-only dict. Never raises. Never modifies input.
    All recommendations have auto_authorized=False.
    """
    try:
        snapshot          = _alignment_snapshot(trades)
        alignment_metrics = _compute_alignment_metrics(trades, snapshot)
        integrity_score   = _alignment_integrity_score(alignment_metrics, len(trades))
        classification    = _classify_alignment(
            alignment_metrics, integrity_score, len(trades)
        )
        lineage         = _build_alignment_lineage(trades, snapshot)
        recommendations = _generate_alignment_recommendations(
            classification, alignment_metrics, snapshot, integrity_score,
        )
        audit_entry = _generate_alignment_audit_entry(
            classification, integrity_score, snapshot, recommendations,
        )
        return {
            "scope_note": (
                "FTD-HMAO constitutional human meaning alignment & purpose integrity "
                "observatory — research instrumentation only. Assesses whether PHOENIX "
                "remains interpretable, accountable, human-legible, and permanently "
                "subordinate to explicit human-defined objectives. "
                "PHOENIX must NEVER become sovereign over human meaning or value legitimacy."
            ),
            "total_trades":               len(trades),
            "alignment_snapshot":         snapshot,
            "alignment_classification":   classification,
            "classification_description": _CLASSIFICATION_DESCRIPTIONS.get(classification, ""),
            "alignment_integrity_score":  integrity_score,
            "alignment_metrics":          alignment_metrics,
            "alignment_lineage":          lineage,
            "recommendations":            recommendations,
            "alignment_hard_principles":  ALIGNMENT_HARD_PRINCIPLES,
            "audit_entry":                audit_entry,
        }
    except Exception:
        return {
            "scope_note":              "FTD-HMAO research instrumentation — analysis error.",
            "error":                   "analysis failed",
            "alignment_classification": HUMAN_ALIGNED,
            "alignment_hard_principles": ALIGNMENT_HARD_PRINCIPLES,
        }
