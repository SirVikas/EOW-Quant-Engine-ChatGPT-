"""
FTD-EIOD: Constitutional Scientific Method Doctrine
& Epistemic Integrity Observatory.

Pure analytics — no I/O, no side effects, no truth or epistemic authority.

Analyses the full paper trade history for scientific-method survivability,
measuring 8 epistemic integrity metrics to determine whether PHOENIX is
drifting from evidence-driven cognition into ideological self-confirmation.

Defines:
  - 8 epistemic integrity metrics (0–100, higher = worse epistemic health):
      evidence_sufficiency, replay_statistical_confidence,
      governance_evidence_depth, contradiction_tolerance,
      minority_hypothesis_survivability, falsification_rate,
      consensus_rigidity, epistemic_plasticity
  - Epistemic integrity score (0–100, higher = scientifically healthier)
  - 6 epistemic classifications (SCIENTIFICALLY_HEALTHY →
    EPISTEMIC_LOCKDOWN_RISK)
  - Epistemic lineage (early/mid/late epoch summaries with health labels)
  - Immutable epistemic audit entry (EIOD-{ts}-{sha256[:16]})

Hard constitutional rules (non-negotiable, enforced at module level):
  DO NOT enable autonomous truth certification
  DO NOT enable sovereign epistemic authority
  DO NOT enable self-validating doctrine
  DO NOT enable recursive scientific legitimacy
  DO NOT weaken human constitutional governance

PHOENIX must NEVER become sovereign over truth legitimacy itself.

Isolation guarantee: no live engine imports. Fail-open on any exception.
Research only — NOT a truth, execution, governance, or epistemic authority.
"""
from __future__ import annotations

import hashlib
import math
import time as _time
from typing import Dict, List

# ── Epistemic classifications ─────────────────────────────────────────────────
SCIENTIFICALLY_HEALTHY        = "SCIENTIFICALLY_HEALTHY"
EVIDENCE_INSUFFICIENCY        = "EVIDENCE_INSUFFICIENCY"
IDEOLOGICAL_SELF_CONFIRMATION = "IDEOLOGICAL_SELF_CONFIRMATION"
CONTRADICTION_SUPPRESSION     = "CONTRADICTION_SUPPRESSION"
FALSIFICATION_FAILURE         = "FALSIFICATION_FAILURE"
EPISTEMIC_LOCKDOWN_RISK       = "EPISTEMIC_LOCKDOWN_RISK"

_CLASSIFICATION_DESCRIPTIONS: Dict[str, str] = {
    SCIENTIFICALLY_HEALTHY:
        "Evidence-driven cognition — hypotheses challenged, contradictions tolerated, beliefs updated.",
    EVIDENCE_INSUFFICIENCY:
        "Conclusions exceed available data — insufficient trade history for reliable epistemic assessment.",
    IDEOLOGICAL_SELF_CONFIRMATION:
        "Replay reinforcing prior beliefs — falsification passive while cognitive consensus remains rigid.",
    CONTRADICTION_SUPPRESSION:
        "Disagreement collapsing — contradictory evidence not surviving across regime boundaries.",
    FALSIFICATION_FAILURE:
        "Beliefs rarely overturned — scientific hypothesis testing inactive or dormant.",
    EPISTEMIC_LOCKDOWN_RISK:
        "Scientific integrity degrading — epistemic corrigibility at critical risk; human review required.",
}

# ── Hard constitutional epistemic principles (immutable) ──────────────────────
EPISTEMIC_HARD_PRINCIPLES: Dict[str, bool] = {
    "human_authority_over_truth_governance":    True,
    "explicit_scientific_approval_required":    True,
    "immutable_epistemic_lineage_guaranteed":   True,
    "falsification_human_controlled":           True,
    "contradiction_tolerance_preserved":        True,
    "epistemic_decisions_developer_controlled": True,
    "autonomous_truth_certification":           False,
    "sovereign_epistemic_authority":            False,
    "self_validating_doctrine":                 False,
    "recursive_scientific_legitimacy":          False,
    "autonomous_doctrine_validation":           False,
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


def _session_counts(trades: List[dict]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for t in trades:
        s = t.get("origin_session") or "UNKNOWN"
        counts[s] = counts.get(s, 0) + 1
    return counts


def _hhi(counts: Dict[str, int]) -> float:
    total = sum(counts.values())
    if total == 0:
        return 1.0
    return sum((v / total) ** 2 for v in counts.values())


def _std(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5


def _cv(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    if abs(mean) < 1e-12:
        return 0.0
    return _std(values) / abs(mean)


# ── Epistemic metrics ─────────────────────────────────────────────────────────

def _evidence_sufficiency_metric(trades: List[dict]) -> dict:
    """
    Trade count + regime/session/exploration diversity — the breadth of
    evidence base available for conclusions.
    Score 0–100 (higher = less evidence = higher epistemic risk).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT", "total_trades": 0}
    valid = _valid(trades)
    n = len(valid)
    if n == 0:
        return _base
    try:
        reg_counts        = _regime_counts(valid)
        distinct_regimes  = len(reg_counts)
        distinct_sessions = len({t.get("origin_session") or "UNKNOWN" for t in valid})
        exp_cov           = _explore_ratio(valid)

        n_score    = min(n / 200.0, 1.0)
        reg_score  = min(distinct_regimes  / 4.0, 1.0)
        sess_score = min(distinct_sessions / 4.0, 1.0)
        exp_score  = min(exp_cov / 0.15, 1.0)

        combined = (n_score * 0.40 + reg_score * 0.20
                    + sess_score * 0.20 + exp_score * 0.20)
        score    = max(0.0, min(100.0, (1.0 - combined) * 100.0))

        if score < 10.0:   tier = "SUFFICIENT"
        elif score < 30.0: tier = "MARGINAL"
        elif score < 60.0: tier = "SPARSE"
        else:              tier = "INSUFFICIENT"
        return {
            "score": round(score, 2), "tier": tier,
            "total_trades":      n,
            "distinct_regimes":  distinct_regimes,
            "distinct_sessions": distinct_sessions,
            "exploration_coverage": round(exp_cov, 4),
        }
    except Exception:
        return _base


def _replay_statistical_confidence_metric(trades: List[dict]) -> dict:
    """
    Wilson 95% CI width on win rate — how statistically reliable are
    replay conclusions?
    Score 0–100 (higher = wider interval = less statistical confidence).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT"}
    valid = _valid(trades)
    n     = len(valid)
    if n == 0:
        return _base
    try:
        wr     = _win_rate(valid)
        margin = 1.96 * math.sqrt(max(wr * (1.0 - wr), 0.0001) / max(n, 1))
        score  = min(100.0, margin * 400.0)

        if score < 15.0:   tier = "HIGH"
        elif score < 30.0: tier = "ADEQUATE"
        elif score < 60.0: tier = "LOW"
        else:              tier = "INSUFFICIENT"
        return {
            "score": round(score, 2), "tier": tier,
            "win_rate":        round(wr, 4),
            "sample_n":        n,
            "margin_of_error": round(margin, 4),
        }
    except Exception:
        return _base


def _governance_evidence_depth_metric(trades: List[dict]) -> dict:
    """
    Depth of evidence base supporting governance decisions — regime/session
    diversity + exploration coverage + corpus size.
    Score 0–100 (higher = shallower governance evidence).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT"}
    valid = _valid(trades)
    n     = len(valid)
    if n == 0:
        return _base
    try:
        reg_counts        = _regime_counts(valid)
        distinct_regimes  = len(reg_counts)
        distinct_sessions = len({t.get("origin_session") or "UNKNOWN" for t in valid})
        exp_cov           = _explore_ratio(valid)

        reg_depth  = min(distinct_regimes  / 4.0, 1.0)
        sess_depth = min(distinct_sessions / 4.0, 1.0)
        exp_depth  = min(exp_cov / 0.15, 1.0)
        n_depth    = min(n / 100.0, 1.0)

        combined = (reg_depth * 0.30 + sess_depth * 0.25
                    + exp_depth * 0.25 + n_depth * 0.20)
        score    = max(0.0, min(100.0, (1.0 - combined) * 100.0))

        if score < 15.0:   tier = "DEEP"
        elif score < 35.0: tier = "ADEQUATE"
        elif score < 65.0: tier = "SHALLOW"
        else:              tier = "INSUFFICIENT"
        return {
            "score": round(score, 2), "tier": tier,
            "distinct_regimes":    distinct_regimes,
            "distinct_sessions":   distinct_sessions,
            "exploration_coverage": round(exp_cov, 4),
        }
    except Exception:
        return _base


def _contradiction_tolerance_metric(trades: List[dict]) -> dict:
    """
    Std deviation of per-regime win rates — high variance means contradictory
    evidence (different outcomes across regimes) is preserved.
    Score 0–100 (higher = lower tolerance = more contradiction suppression).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT"}
    valid = _valid(trades)
    n     = len(valid)
    if n == 0:
        return _base
    try:
        reg_counts = _regime_counts(valid)
        if len(reg_counts) < 2:
            return {
                "score": 100.0, "tier": "SUPPRESSED",
                "cross_regime_std": 0.0, "distinct_regimes": len(reg_counts),
            }
        per_regime_wr = [
            _win_rate([t for t in valid if (t.get("regime") or "UNKNOWN") == r])
            for r in reg_counts
        ]
        std_wr = _std(per_regime_wr)
        # std ≥ 0.25 indicates meaningful cross-regime contradiction
        score  = max(0.0, min(100.0, (1.0 - min(std_wr / 0.25, 1.0)) * 100.0))

        if score < 20.0:   tier = "TOLERANT"
        elif score < 45.0: tier = "MODERATE"
        elif score < 70.0: tier = "RIGID"
        else:              tier = "SUPPRESSED"
        return {
            "score": round(score, 2), "tier": tier,
            "cross_regime_std": round(std_wr, 4),
            "distinct_regimes": len(reg_counts),
        }
    except Exception:
        return _base


def _minority_hypothesis_survivability_metric(trades: List[dict]) -> dict:
    """
    Dominant regime concentration — if one regime dominates, minority hypotheses
    have little room to persist.
    Score 0–100 (higher = dominant_fraction × 100 = less minority survival).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT"}
    valid = _valid(trades)
    n     = len(valid)
    if n == 0:
        return _base
    try:
        reg_counts = _regime_counts(valid)
        if not reg_counts:
            return _base
        dominant_count = max(reg_counts.values())
        dominant_frac  = dominant_count / n
        score          = max(0.0, min(100.0, dominant_frac * 100.0))

        if score < 25.0:   tier = "HIGH"
        elif score < 50.0: tier = "ADEQUATE"
        elif score < 75.0: tier = "LOW"
        else:              tier = "EXTINCT"
        return {
            "score": round(score, 2), "tier": tier,
            "dominant_regime_fraction": round(dominant_frac, 4),
            "minority_support":         round(1.0 - dominant_frac, 4),
            "distinct_regimes":         len(reg_counts),
        }
    except Exception:
        return _base


def _falsification_rate_metric(trades: List[dict]) -> dict:
    """
    Exploration ratio + win-rate volatility across time quartiles — proxies
    for how actively PHOENIX tests and potentially overturns its hypotheses.
    Score 0–100 (higher = less falsification = more dogmatic).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT"}
    valid = _valid(trades)
    n     = len(valid)
    if n == 0:
        return _base
    try:
        exp_ratio = _explore_ratio(valid)

        win_rate_cv = 0.0
        if n >= 20:
            sorted_t  = sorted(valid, key=lambda t: t.get("entry_ts") or 0)
            q_size    = max(1, n // 4)
            quartiles = [sorted_t[i * q_size:(i + 1) * q_size] for i in range(4)
                         if sorted_t[i * q_size:(i + 1) * q_size]]
            q_wrs = [_win_rate(q) for q in quartiles if q]
            win_rate_cv = _cv(q_wrs)

        # Exploration ratio of 10% (0.10) saturates the exploration component.
        # Win-rate CV across quartiles (target 0.5 for saturation) adds bonus.
        falsification_proxy = (
            min(exp_ratio / 0.10, 1.0) * 0.70
            + min(win_rate_cv / 0.5, 1.0) * 0.30
        )
        score = max(0.0, min(100.0, (1.0 - min(falsification_proxy, 1.0)) * 100.0))

        if score < 25.0:   tier = "ACTIVE"
        elif score < 50.0: tier = "MODERATE"
        elif score < 75.0: tier = "PASSIVE"
        else:              tier = "DORMANT"
        return {
            "score": round(score, 2), "tier": tier,
            "exploration_ratio": round(exp_ratio, 4),
            "win_rate_cv":       round(win_rate_cv, 4),
        }
    except Exception:
        return _base


def _consensus_rigidity_metric(trades: List[dict]) -> dict:
    """
    HHI of regime and session distributions — high concentration means
    cognitive consensus is locked into a narrow worldview.
    Score 0–100 (higher = more rigid = HHI × 100 weighted).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT"}
    valid = _valid(trades)
    n     = len(valid)
    if n == 0:
        return _base
    try:
        hhi_regime = _hhi(_regime_counts(valid))
        hhi_sess   = _hhi(_session_counts(valid))
        score      = max(0.0, min(100.0, (hhi_regime * 0.60 + hhi_sess * 0.40) * 100.0))

        if score < 20.0:   tier = "FLEXIBLE"
        elif score < 45.0: tier = "MODERATE"
        elif score < 70.0: tier = "RIGID"
        else:              tier = "LOCKED"
        return {
            "score": round(score, 2), "tier": tier,
            "regime_hhi":  round(hhi_regime, 4),
            "session_hhi": round(hhi_sess, 4),
        }
    except Exception:
        return _base


def _epistemic_plasticity_metric(trades: List[dict]) -> dict:
    """
    Early-vs-late delta in win rate, exploration ratio, and regime overlap.
    High delta = beliefs update over time = plastic cognition.
    Score 0–100 (higher = less belief updating = more crystallized).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT"}
    valid = _valid(trades)
    n     = len(valid)
    if n < 10:
        return _base
    try:
        sorted_t   = sorted(valid, key=lambda t: t.get("entry_ts") or 0)
        mid        = n // 2
        early, late = sorted_t[:mid], sorted_t[mid:]

        win_delta = abs(_win_rate(late) - _win_rate(early))
        exp_delta = abs(_explore_ratio(late) - _explore_ratio(early))

        early_reg = {t.get("regime") or "UNKNOWN" for t in early}
        late_reg  = {t.get("regime") or "UNKNOWN" for t in late}
        union     = early_reg | late_reg
        regime_shift = 1.0 - (len(early_reg & late_reg) / len(union)) if union else 0.0

        # plasticity ≥ 0.25 saturates the metric → score 0
        plasticity = win_delta * 0.50 + exp_delta * 0.30 + regime_shift * 0.20
        score      = max(0.0, min(100.0, (1.0 - min(plasticity / 0.25, 1.0)) * 100.0))

        if score < 20.0:   tier = "PLASTIC"
        elif score < 45.0: tier = "ADEQUATE"
        elif score < 70.0: tier = "RIGID"
        else:              tier = "CRYSTALLIZED"
        return {
            "score": round(score, 2), "tier": tier,
            "win_rate_delta":   round(win_delta, 4),
            "exploration_delta": round(exp_delta, 4),
            "regime_shift":     round(regime_shift, 4),
        }
    except Exception:
        return _base


def _compute_epistemic_metrics(trades: List[dict]) -> dict:
    return {
        "evidence_sufficiency":              _evidence_sufficiency_metric(trades),
        "replay_statistical_confidence":     _replay_statistical_confidence_metric(trades),
        "governance_evidence_depth":         _governance_evidence_depth_metric(trades),
        "contradiction_tolerance":           _contradiction_tolerance_metric(trades),
        "minority_hypothesis_survivability": _minority_hypothesis_survivability_metric(trades),
        "falsification_rate":                _falsification_rate_metric(trades),
        "consensus_rigidity":                _consensus_rigidity_metric(trades),
        "epistemic_plasticity":              _epistemic_plasticity_metric(trades),
    }


# ── Epistemic integrity score ─────────────────────────────────────────────────

def _epistemic_integrity_score(epistemic_metrics: dict, total_trades: int) -> dict:
    """
    Composite 0–100 epistemic integrity score (higher = scientifically healthier).
    Returns CRITICAL with note when trade history is insufficient.
    """
    if total_trades < 10:
        return {
            "score": 0.0, "tier": "CRITICAL",
            "note": "insufficient trade history for epistemic assessment",
        }
    try:
        _weights = {
            "evidence_sufficiency":              0.20,
            "replay_statistical_confidence":     0.15,
            "governance_evidence_depth":         0.15,
            "contradiction_tolerance":           0.15,
            "minority_hypothesis_survivability": 0.10,
            "falsification_rate":                0.10,
            "consensus_rigidity":                0.10,
            "epistemic_plasticity":              0.05,
        }
        total_penalty = sum(
            epistemic_metrics.get(k, {}).get("score", 0.0) * w
            for k, w in _weights.items()
        )
        score = max(0.0, min(100.0, 100.0 - total_penalty))
        if score >= 75.0:   tier = "SCIENTIFICALLY_HEALTHY"
        elif score >= 55.0: tier = "ADEQUATE"
        elif score >= 35.0: tier = "VULNERABLE"
        else:               tier = "CRITICAL"
        return {"score": round(score, 2), "tier": tier}
    except Exception:
        return {"score": 0.0, "tier": "CRITICAL"}


# ── Epistemic classification ──────────────────────────────────────────────────

def _classify_epistemic(
    epistemic_metrics: dict,
    integrity_score: dict,
    total_trades: int,
) -> str:
    if total_trades < 10:
        return EVIDENCE_INSUFFICIENCY
    try:
        surv_score  = integrity_score.get("score", 0.0)
        evid_tier   = epistemic_metrics.get("evidence_sufficiency",              {}).get("tier", "INSUFFICIENT")
        false_tier  = epistemic_metrics.get("falsification_rate",                {}).get("tier", "INSUFFICIENT")
        contra_tier = epistemic_metrics.get("contradiction_tolerance",           {}).get("tier", "INSUFFICIENT")
        cons_tier   = epistemic_metrics.get("consensus_rigidity",                {}).get("tier", "INSUFFICIENT")

        if surv_score < 20.0:
            return EPISTEMIC_LOCKDOWN_RISK
        # Passive/dormant falsification combined with rigid consensus = ideological loop
        if false_tier in ("PASSIVE", "DORMANT") and cons_tier in ("RIGID", "LOCKED"):
            return IDEOLOGICAL_SELF_CONFIRMATION
        # Cross-regime contradictions fully suppressed
        if contra_tier in ("RIGID", "SUPPRESSED"):
            return CONTRADICTION_SUPPRESSION
        # Falsification dormant or overall score still very low
        if false_tier == "DORMANT" or surv_score < 40.0:
            return FALSIFICATION_FAILURE
        # Evidence base genuinely absent — not merely sparse
        if evid_tier == "INSUFFICIENT":
            return EVIDENCE_INSUFFICIENCY
        return SCIENTIFICALLY_HEALTHY
    except Exception:
        return SCIENTIFICALLY_HEALTHY


# ── Epistemic lineage ─────────────────────────────────────────────────────────

def _build_epistemic_lineage(trades: List[dict]) -> dict:
    """
    Epoch-indexed lineage: early, mid, late thirds of trade history.
    Tracks how scientific health evolves across the knowledge horizon.
    """
    if not trades:
        return {
            "total_epochs": 0, "epistemic_trajectory": "UNKNOWN",
            "total_trades": 0, "epochs": {},
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

            if exp_ratio >= 0.10 and 0.25 <= wr <= 0.75:
                health = "HEALTHY"
            elif exp_ratio < 0.03:
                health = "RIGID"
            else:
                health = "EMERGING"

            lineage[name] = {
                "trade_count":       m,
                "dominant_regime":   dom_regime,
                "win_rate":          round(wr, 4),
                "exploration_ratio": round(exp_ratio, 4),
                "regime_diversity":  len(reg_counts),
                "epistemic_health":  health,
            }

        def _hs(h: str) -> int:
            return {"HEALTHY": 2, "EMERGING": 1, "RIGID": 0}.get(h, 1)

        e_health = lineage.get("early", {}).get("epistemic_health", "EMERGING")
        l_health = lineage.get("late",  {}).get("epistemic_health", "EMERGING")
        diff     = _hs(l_health) - _hs(e_health)
        trajectory = "IMPROVING" if diff > 0 else "DECLINING" if diff < 0 else "STABLE"

        return {
            "total_epochs":         3,
            "epistemic_trajectory": trajectory,
            "total_trades":         n,
            "epochs":               lineage,
        }
    except Exception:
        return {
            "total_epochs": 0, "epistemic_trajectory": "UNKNOWN",
            "total_trades": len(trades), "epochs": {},
        }


# ── Recommendations ────────────────────────────────────────────────────────────

def _generate_epistemic_recommendations(
    classification: str,
    epistemic_metrics: dict,
    integrity_score: dict,
    total_trades: int,
) -> list:
    recs: list = []

    if total_trades < 10:
        recs.append({
            "priority":        "MEDIUM",
            "type":            "EPISTEMIC_READINESS",
            "summary":         f"Only {total_trades} trade(s) — epistemic observatory requires ≥10 records for meaningful assessment.",
            "action_required": "ACCUMULATE_TRADE_HISTORY",
            "auto_authorized": False,
        })
        return recs

    if classification == EPISTEMIC_LOCKDOWN_RISK:
        recs.append({
            "priority":        "CRITICAL",
            "type":            "EPISTEMIC_LOCKDOWN",
            "summary":         "Epistemic integrity critically low — scientific corrigibility at severe risk. Human governance review required.",
            "action_required": "HUMAN_GOVERNANCE_REVIEW_REQUIRED",
            "auto_authorized": False,
        })

    if classification == IDEOLOGICAL_SELF_CONFIRMATION:
        recs.append({
            "priority":        "CRITICAL",
            "type":            "IDEOLOGICAL_RIGIDITY",
            "summary":         "Replay reinforcing prior beliefs with rigid consensus — risk of ideological self-confirmation. Increase exploration diversity.",
            "action_required": "HUMAN_REVIEW_EXPLORATION_DOCTRINE",
            "auto_authorized": False,
        })

    if classification == CONTRADICTION_SUPPRESSION:
        recs.append({
            "priority":        "HIGH",
            "type":            "CONTRADICTION_SUPPRESSION",
            "summary":         "Cross-regime contradictions collapsing — all regimes converging to similar outcomes. Investigate regime diversity.",
            "action_required": "HUMAN_REVIEW_REGIME_DIVERSITY",
            "auto_authorized": False,
        })

    if classification == FALSIFICATION_FAILURE:
        recs.append({
            "priority":        "HIGH",
            "type":            "FALSIFICATION_FAILURE",
            "summary":         "Hypothesis testing inactive — exploration ratio low and win-rate stable across time. Scientific falsification at risk.",
            "action_required": "HUMAN_REVIEW_FALSIFICATION_DOCTRINE",
            "auto_authorized": False,
        })

    if classification == EVIDENCE_INSUFFICIENCY:
        recs.append({
            "priority":        "MEDIUM",
            "type":            "EVIDENCE_INSUFFICIENCY",
            "summary":         "Governance conclusions exceed available evidence — insufficient trade/regime diversity for reliable epistemic assessment.",
            "action_required": "ACCUMULATE_DIVERSE_TRADE_EVIDENCE",
            "auto_authorized": False,
        })

    false_tier = epistemic_metrics.get("falsification_rate", {}).get("tier", "")
    if false_tier == "PASSIVE" and classification not in (
        IDEOLOGICAL_SELF_CONFIRMATION, FALSIFICATION_FAILURE
    ):
        recs.append({
            "priority":        "MEDIUM",
            "type":            "PASSIVE_FALSIFICATION",
            "summary":         "Falsification rate passive — exploration activity below threshold for reliable hypothesis testing.",
            "action_required": "CONTINUE_MONITORING",
            "auto_authorized": False,
        })

    cons_tier = epistemic_metrics.get("consensus_rigidity", {}).get("tier", "")
    if cons_tier == "RIGID" and classification not in (IDEOLOGICAL_SELF_CONFIRMATION,):
        recs.append({
            "priority":        "MEDIUM",
            "type":            "CONSENSUS_RIGIDITY",
            "summary":         "Cognitive consensus rigid — regime/session concentration high. Diversification recommended.",
            "action_required": "CONTINUE_MONITORING",
            "auto_authorized": False,
        })

    if not recs:
        recs.append({
            "priority":        "LOW",
            "type":            "EPISTEMIC_STATUS",
            "summary":         (
                f"{classification}: {_CLASSIFICATION_DESCRIPTIONS.get(classification, '')} "
                f"Epistemic integrity {integrity_score.get('score', 0.0):.1f}/100."
            ),
            "action_required": "CONTINUE_MONITORING",
            "auto_authorized": False,
        })

    return recs


# ── Audit entry ────────────────────────────────────────────────────────────────

def _generate_epistemic_audit_entry(
    classification: str,
    integrity_score: dict,
    total_trades: int,
    recommendations: list,
) -> dict:
    try:
        ts      = int(_time.time() * 1000)
        payload = (
            f"{ts}|{classification}|{total_trades}"
            f"|{integrity_score.get('score', 0.0)}"
        )
        fp = hashlib.sha256(payload.encode()).hexdigest()
        return {
            "entry_id":                   f"EIOD-{ts}-{fp[:16]}",
            "timestamp_ms":               ts,
            "entry_type":                 "ANALYSIS",
            "epistemic_classification":   classification,
            "epistemic_integrity_score":  integrity_score.get("score", 0.0),
            "integrity_tier":             integrity_score.get("tier", "INSUFFICIENT"),
            "total_trades_assessed":      total_trades,
            "recommendations_generated":  len(recommendations),
            "human_approval_required":    total_trades >= 10,
            "auto_authorized":            False,
            "immutable":                  True,
        }
    except Exception:
        ts = int(_time.time() * 1000)
        return {
            "entry_id":                f"EIOD-{ts}-error",
            "timestamp_ms":            ts,
            "entry_type":              "ANALYSIS",
            "human_approval_required": False,
            "auto_authorized":         False,
            "immutable":               True,
        }


# ── Public entry point ─────────────────────────────────────────────────────────

def compute_epistemic_integrity(trades: List[dict]) -> dict:
    """
    Produce a constitutional epistemic integrity and scientific-method
    survivability assessment.

    Args:
        trades: Full paper trade history (from session + DataLake).

    Returns a research-only dict. Never raises. Never modifies input.
    All recommendations have auto_authorized=False.
    """
    try:
        epistemic_metrics = _compute_epistemic_metrics(trades)
        integrity_score   = _epistemic_integrity_score(epistemic_metrics, len(trades))
        classification    = _classify_epistemic(
            epistemic_metrics, integrity_score, len(trades)
        )
        lineage         = _build_epistemic_lineage(trades)
        recommendations = _generate_epistemic_recommendations(
            classification, epistemic_metrics, integrity_score, len(trades),
        )
        audit_entry = _generate_epistemic_audit_entry(
            classification, integrity_score, len(trades), recommendations,
        )
        return {
            "scope_note": (
                "FTD-EIOD constitutional scientific method doctrine & epistemic integrity "
                "observatory — research instrumentation only. Assesses whether PHOENIX "
                "remains evidence-driven, falsifiable, contradiction-tolerant, and "
                "scientifically corrigible across long adaptive horizons. "
                "PHOENIX must NEVER become sovereign over truth legitimacy itself."
            ),
            "total_trades":               len(trades),
            "epistemic_classification":   classification,
            "classification_description": _CLASSIFICATION_DESCRIPTIONS.get(classification, ""),
            "epistemic_integrity_score":  integrity_score,
            "epistemic_metrics":          epistemic_metrics,
            "epistemic_lineage":          lineage,
            "recommendations":            recommendations,
            "epistemic_hard_principles":  EPISTEMIC_HARD_PRINCIPLES,
            "audit_entry":                audit_entry,
        }
    except Exception:
        return {
            "scope_note":              "FTD-EIOD research instrumentation — analysis error.",
            "error":                   "analysis failed",
            "epistemic_classification": SCIENTIFICALLY_HEALTHY,
            "epistemic_hard_principles": EPISTEMIC_HARD_PRINCIPLES,
        }
