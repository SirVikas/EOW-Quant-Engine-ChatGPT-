"""
FTD-LHEO: Long-Horizon Constitutional Evolution Observatory
& Intergenerational Drift Doctrine.

Pure analytics — no I/O, no side effects, no execution authority.

Segments the full paper trade history into time-ordered eras, computes
per-era cognitive snapshots, and measures 8 constitutional continuity
metrics that distinguish healthy long-horizon maturation from slow
constitutional cognitive collapse.

Defines:
  - Era-based segmentation (up to 5 eras, ≥20 trades per era)
  - 8 constitutional continuity metrics (0–100, higher = worse)
  - 6 evolutionary classifications (CONSTITUTIONALLY_RESILIENT → LONG_HORIZON_LOCKDOWN_RISK)
  - Long-horizon stability score (0–100, higher = more stable)
  - Cognitive lineage with early/mid/late era snapshots + trajectories
  - Immutable evolution audit entry (LHEO-{ts}-{sha256[:16]})

Hard constitutional rules (non-negotiable, enforced at module level):
  DO NOT enable self-rewriting doctrine
  DO NOT enable recursive constitutional mutation
  DO NOT enable autonomous governance evolution
  DO NOT enable sovereign adaptive succession
  DO NOT weaken human constitutional authority

PHOENIX must NEVER evolve beyond explicit constitutional human governance.

Isolation guarantee: no live engine imports. Fail-open on any exception.
Research only — NOT an execution or governance authority.
"""
from __future__ import annotations

import hashlib
import time as _time
from typing import Dict, List, Optional

_N_ERAS = 5  # maximum eras; each era requires at least 20 trades

# ── Evolutionary classifications ───────────────────────────────────────────────
CONSTITUTIONALLY_RESILIENT  = "CONSTITUTIONALLY_RESILIENT"
IDEOLOGICAL_RIGIDIFICATION  = "IDEOLOGICAL_RIGIDIFICATION"
EXPLORATION_EXTINCTION      = "EXPLORATION_EXTINCTION"
SURVIVABILITY_MONOCULTURE   = "SURVIVABILITY_MONOCULTURE"
ADAPTIVE_MEMORY_DECAY       = "ADAPTIVE_MEMORY_DECAY"
LONG_HORIZON_LOCKDOWN_RISK  = "LONG_HORIZON_LOCKDOWN_RISK"

_CLASSIFICATION_DESCRIPTIONS: Dict[str, str] = {
    CONSTITUTIONALLY_RESILIENT: "Stable long-horizon cognition — constitutional alignment preserved across eras.",
    IDEOLOGICAL_RIGIDIFICATION: "Governance monoculture emerging — doctrine convergence reducing adaptive flexibility.",
    EXPLORATION_EXTINCTION:     "Curiosity collapse — exploration ratio approaching extinction across eras.",
    SURVIVABILITY_MONOCULTURE:  "Narrow ecological over-specialisation — regime concentration becoming pathological.",
    ADAPTIVE_MEMORY_DECAY:      "Long-horizon forgetting instability — drift acceleration suggests unstable adaptation.",
    LONG_HORIZON_LOCKDOWN_RISK: "Constitutional degradation accumulating — long-horizon stability requires human governance review.",
}

# ── Hard constitutional principles (immutable) ────────────────────────────────
EVOLUTION_HARD_PRINCIPLES: Dict[str, bool] = {
    "human_authority_over_evolution":    True,
    "explicit_approval_required":        True,
    "immutable_lineage_guaranteed":      True,
    "lineage_reconstruction_possible":   True,
    "doctrine_review_human_only":        True,
    "era_transitions_human_approved":    True,
    "self_rewriting_doctrine":           False,
    "recursive_constitutional_mutation": False,
    "autonomous_governance_evolution":   False,
    "sovereign_adaptive_succession":     False,
    "autonomous_era_transitions":        False,
}


# ── Era segmentation ───────────────────────────────────────────────────────────

def _segment_eras(trades: List[dict], n_eras: int) -> List[List[dict]]:
    """Partition time-sorted trades into n_eras equally sized eras."""
    valid = [t for t in trades if isinstance(t, dict)]
    if not valid or n_eras <= 0:
        return []
    sorted_t = sorted(valid, key=lambda t: t.get("entry_ts") or 0)
    if n_eras >= len(sorted_t):
        return [[t] for t in sorted_t]
    era_size = len(sorted_t) // n_eras
    eras = []
    for i in range(n_eras):
        start = i * era_size
        end   = start + era_size if i < n_eras - 1 else len(sorted_t)
        eras.append(sorted_t[start:end])
    return eras


# ── Era snapshot ───────────────────────────────────────────────────────────────

def _era_snapshot(trades: List[dict], era_idx: int) -> dict:
    """Compute key cognitive indicators for a single era's trade slice."""
    _base = {
        "era_index": era_idx, "trade_count": 0,
        "dominant_regime": "UNKNOWN", "exploration_ratio": 0.0,
        "net_expectancy": 0.0, "win_rate": 0.0,
        "fee_gross_ratio": 0.0, "slippage_gross_ratio": 0.0,
        "regime_hhi": 0.0, "session_hhi": 0.0,
        "era_constitutional_health": 0.0,
    }
    if not trades:
        return _base
    try:
        n = len(trades)
        net_pnl_vals = [t.get("net_pnl") or 0.0 for t in trades]
        net_expectancy = sum(net_pnl_vals) / n
        win_count      = sum(1 for v in net_pnl_vals if v > 0)
        win_rate       = win_count / n

        explore_count = sum(
            1 for t in trades
            if isinstance(t.get("exploration_origin"), dict)
            and t["exploration_origin"].get("was_exploration_trade")
        )
        exploration_ratio = explore_count / n

        regime_counts: Dict[str, int] = {}
        for t in trades:
            r = t.get("regime") or "UNKNOWN"
            regime_counts[r] = regime_counts.get(r, 0) + 1
        dominant_regime = max(regime_counts, key=regime_counts.get)
        regime_hhi = sum((c / n) ** 2 for c in regime_counts.values()) * 100.0

        session_counts: Dict[str, int] = {}
        for t in trades:
            s = t.get("origin_session") or "UNKNOWN"
            session_counts[s] = session_counts.get(s, 0) + 1
        session_hhi = sum((c / n) ** 2 for c in session_counts.values()) * 100.0

        gross_vals   = [abs(t.get("gross_pnl") or t.get("net_pnl") or 0.0) for t in trades]
        total_gross  = sum(gross_vals)
        total_fees   = sum((t.get("fee_entry") or 0.0) + (t.get("fee_exit") or 0.0) for t in trades)
        total_slip   = sum(t.get("slippage_cost") or 0.0 for t in trades)
        fee_gr       = total_fees / max(total_gross, 1e-9) * 100.0
        slip_gr      = total_slip / max(total_gross, 1e-9) * 100.0

        # Constitutional health proxy: net expectancy sustainability vs friction
        friction    = (fee_gr + slip_gr) / 2.0
        const_hlth  = max(0.0, min(100.0, 100.0 - min(friction * 2.0, 100.0)))

        return {
            "era_index":               era_idx,
            "trade_count":             n,
            "dominant_regime":         dominant_regime,
            "exploration_ratio":       round(exploration_ratio, 4),
            "net_expectancy":          round(net_expectancy, 4),
            "win_rate":                round(win_rate, 4),
            "fee_gross_ratio":         round(fee_gr, 2),
            "slippage_gross_ratio":    round(slip_gr, 2),
            "regime_hhi":              round(regime_hhi, 2),
            "session_hhi":             round(session_hhi, 2),
            "era_constitutional_health": round(const_hlth, 2),
        }
    except Exception:
        return _base


# ── Constitutional continuity metrics ─────────────────────────────────────────

def _constitutional_stability_metric(era_snapshots: List[dict]) -> dict:
    """
    Variability of constitutional health across eras.
    High CV = unstable constitutional alignment.
    Score 0–100 (higher = more instability).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT", "sample_count": len(era_snapshots),
             "mean_constitutional_health": None}
    if len(era_snapshots) < 2:
        return _base
    try:
        vals = [e.get("era_constitutional_health", 0.0) for e in era_snapshots]
        mean = sum(vals) / len(vals)
        cv   = (sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5 / max(abs(mean), 1e-9)
        score = min(100.0, cv * 100.0)
        if score < 10.0:   tier = "STABLE"
        elif score < 25.0: tier = "MODERATE"
        elif score < 50.0: tier = "VOLATILE"
        else:              tier = "UNSTABLE"
        return {"score": round(score, 2), "tier": tier,
                "sample_count": len(era_snapshots),
                "mean_constitutional_health": round(mean, 2)}
    except Exception:
        return _base


def _drift_acceleration_metric(era_snapshots: List[dict]) -> dict:
    """
    Rate of change in net expectancy between consecutive eras.
    High mean delta = fast drift.
    Score 0–100 (higher = faster/worse drift).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT", "sample_count": len(era_snapshots),
             "mean_era_delta": None}
    if len(era_snapshots) < 2:
        return _base
    try:
        ne_vals = [e.get("net_expectancy", 0.0) for e in era_snapshots]
        deltas  = [abs(ne_vals[i + 1] - ne_vals[i]) for i in range(len(ne_vals) - 1)]
        mean_d  = sum(deltas) / len(deltas)
        score   = min(100.0, mean_d / 0.1 * 50.0)
        if score < 15.0:   tier = "MINIMAL"
        elif score < 35.0: tier = "LOW"
        elif score < 60.0: tier = "MODERATE"
        else:              tier = "HIGH"
        return {"score": round(score, 2), "tier": tier,
                "sample_count": len(era_snapshots),
                "mean_era_delta": round(mean_d, 4)}
    except Exception:
        return _base


def _governance_ideology_concentration_metric(era_snapshots: List[dict]) -> dict:
    """
    Regime concentration within eras + consistency of dominant regime across eras.
    High = governance monoculture.
    Score 0–100 (higher = more concentrated/risky).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT", "sample_count": len(era_snapshots),
             "mean_within_era_hhi": None, "cross_era_regime_hhi": None}
    if not era_snapshots:
        return _base
    try:
        hhi_vals = [e.get("regime_hhi", 0.0) for e in era_snapshots]
        mean_hhi = sum(hhi_vals) / len(hhi_vals)

        regime_counts: Dict[str, int] = {}
        for e in era_snapshots:
            r = e.get("dominant_regime", "UNKNOWN") or "UNKNOWN"
            regime_counts[r] = regime_counts.get(r, 0) + 1
        n = len(era_snapshots)
        cross_hhi = sum((c / n) ** 2 for c in regime_counts.values()) * 100.0

        score = min(100.0, mean_hhi * 0.50 + cross_hhi * 0.50)
        if score < 30.0:   tier = "DIVERSE"
        elif score < 50.0: tier = "MODERATE"
        elif score < 70.0: tier = "CONCENTRATED"
        else:              tier = "MONOCULTURE"
        return {"score": round(score, 2), "tier": tier,
                "sample_count": len(era_snapshots),
                "mean_within_era_hhi": round(mean_hhi, 2),
                "cross_era_regime_hhi": round(cross_hhi, 2)}
    except Exception:
        return _base


def _plasticity_half_life_metric(era_snapshots: List[dict]) -> dict:
    """
    Decay rate of exploration ratio from early to late era.
    High decay = rapid plasticity loss.
    Score 0–100 (higher = faster plasticity loss).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT", "sample_count": len(era_snapshots),
             "early_era_exploration": None, "late_era_exploration": None, "decay_rate": None}
    if len(era_snapshots) < 2:
        return _base
    try:
        early_exp = era_snapshots[0].get("exploration_ratio", 0.0)
        late_exp  = era_snapshots[-1].get("exploration_ratio", 0.0)
        if early_exp < 1e-9:
            decay_rate = 0.0
        else:
            decay_rate = max(0.0, (early_exp - late_exp) / early_exp)
        score = min(100.0, decay_rate * 100.0)
        if score < 20.0:   tier = "HEALTHY"
        elif score < 45.0: tier = "DECLINING"
        elif score < 70.0: tier = "RAPID_DECAY"
        else:              tier = "EXTINCT"
        return {"score": round(score, 2), "tier": tier,
                "sample_count": len(era_snapshots),
                "early_era_exploration": round(early_exp, 4),
                "late_era_exploration":  round(late_exp, 4),
                "decay_rate":            round(decay_rate, 4)}
    except Exception:
        return _base


def _exploration_extinction_risk_metric(era_snapshots: List[dict]) -> dict:
    """
    Absolute exploration level in the most recent era.
    Near-zero exploration = extinction risk.
    Score 0–100 (higher = more extinction risk).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT", "sample_count": len(era_snapshots),
             "late_era_exploration_ratio": None}
    if not era_snapshots:
        return _base
    try:
        late_exp = era_snapshots[-1].get("exploration_ratio", 0.0)
        # 0% → score 100; 20%+ → score 0
        score = max(0.0, min(100.0, (1.0 - late_exp / 0.20) * 100.0))
        if score < 20.0:   tier = "LOW"
        elif score < 50.0: tier = "MODERATE"
        elif score < 80.0: tier = "HIGH"
        else:              tier = "CRITICAL"
        return {"score": round(score, 2), "tier": tier,
                "sample_count": len(era_snapshots),
                "late_era_exploration_ratio": round(late_exp, 4)}
    except Exception:
        return _base


def _survivability_monoculture_risk_metric(era_snapshots: List[dict]) -> dict:
    """
    Average within-era regime HHI across eras.
    High = survivability depends on one narrow regime type.
    Score 0–100 (higher = more monoculture risk).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT", "sample_count": len(era_snapshots),
             "mean_regime_hhi": None}
    if not era_snapshots:
        return _base
    try:
        hhi_vals = [e.get("regime_hhi", 0.0) for e in era_snapshots]
        mean_hhi = sum(hhi_vals) / len(hhi_vals)
        score    = min(100.0, mean_hhi)
        if score < 30.0:   tier = "DIVERSE"
        elif score < 50.0: tier = "MODERATE"
        elif score < 70.0: tier = "CONCENTRATED"
        else:              tier = "MONOCULTURE"
        return {"score": round(score, 2), "tier": tier,
                "sample_count": len(era_snapshots),
                "mean_regime_hhi": round(mean_hhi, 2)}
    except Exception:
        return _base


def _cognitive_diversity_retention_metric(era_snapshots: List[dict]) -> dict:
    """
    Preservation of diverse session and regime competencies across eras.
    High = cognitive diversity is collapsing.
    Score 0–100 (higher = worse diversity retention).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT", "sample_count": len(era_snapshots),
             "mean_session_hhi": None, "mean_regime_hhi": None}
    if len(era_snapshots) < 2:
        return _base
    try:
        sess_hhi  = [e.get("session_hhi", 0.0) for e in era_snapshots]
        reg_hhi   = [e.get("regime_hhi",  0.0) for e in era_snapshots]
        mean_sess = sum(sess_hhi) / len(sess_hhi)
        mean_reg  = sum(reg_hhi)  / len(reg_hhi)

        win_rates = [e.get("win_rate", 0.0) for e in era_snapshots]
        wr_mean   = sum(win_rates) / len(win_rates)
        wr_std    = (sum((v - wr_mean) ** 2 for v in win_rates) / len(win_rates)) ** 0.5
        # Very low win-rate std = converging performance = less adaptive diversity
        convergence_pen = max(0.0, min(30.0, (0.10 - wr_std) / 0.10 * 30.0))

        score = min(100.0, mean_sess * 0.35 + mean_reg * 0.35 + convergence_pen)
        if score < 30.0:   tier = "HIGH_DIVERSITY"
        elif score < 50.0: tier = "MODERATE"
        elif score < 70.0: tier = "LOW_DIVERSITY"
        else:              tier = "CRITICALLY_LOW"
        return {"score": round(score, 2), "tier": tier,
                "sample_count": len(era_snapshots),
                "mean_session_hhi": round(mean_sess, 2),
                "mean_regime_hhi":  round(mean_reg, 2)}
    except Exception:
        return _base


def _long_horizon_replay_dependence_metric(era_snapshots: List[dict]) -> dict:
    """
    Whether the late era is dominated by replay at the expense of exploration
    performance. Low explore + declining win rate = high replay dependence.
    Score 0–100 (higher = more replay dependence).
    """
    _base = {"score": 0.0, "tier": "INSUFFICIENT", "sample_count": len(era_snapshots),
             "late_era_exploration": None, "late_era_win_rate": None}
    if len(era_snapshots) < 2:
        return _base
    try:
        late_exp  = era_snapshots[-1].get("exploration_ratio", 0.0)
        late_wr   = era_snapshots[-1].get("win_rate",          0.0)
        early_wr  = era_snapshots[0].get("win_rate",           0.0)

        # Exploration drought penalty (0→60 score as explore→0)
        exp_pen  = max(0.0, min(60.0, (0.10 - late_exp) / 0.10 * 60.0))
        # Win-rate drag (early→late decline)
        wr_drag  = max(0.0, (early_wr - late_wr) / max(early_wr, 0.01)) * 40.0
        wr_drag  = min(40.0, wr_drag)
        score    = min(100.0, exp_pen + wr_drag)

        if score < 20.0:   tier = "MINIMAL"
        elif score < 40.0: tier = "LOW"
        elif score < 65.0: tier = "MODERATE"
        else:              tier = "HIGH"
        return {"score": round(score, 2), "tier": tier,
                "sample_count": len(era_snapshots),
                "late_era_exploration": round(late_exp, 4),
                "late_era_win_rate":    round(late_wr, 4)}
    except Exception:
        return _base


# ── Aggregated evolution metrics ──────────────────────────────────────────────

def _compute_evolution_metrics(era_snapshots: List[dict]) -> dict:
    return {
        "constitutional_stability":          _constitutional_stability_metric(era_snapshots),
        "drift_acceleration":                _drift_acceleration_metric(era_snapshots),
        "governance_ideology_concentration": _governance_ideology_concentration_metric(era_snapshots),
        "plasticity_half_life":              _plasticity_half_life_metric(era_snapshots),
        "exploration_extinction_risk":       _exploration_extinction_risk_metric(era_snapshots),
        "survivability_monoculture_risk":    _survivability_monoculture_risk_metric(era_snapshots),
        "cognitive_diversity_retention":     _cognitive_diversity_retention_metric(era_snapshots),
        "long_horizon_replay_dependence":    _long_horizon_replay_dependence_metric(era_snapshots),
    }


# ── Long-horizon stability score ──────────────────────────────────────────────

def _long_horizon_stability_score(
    evolution_metrics: dict,
    n_eras: int,
) -> dict:
    """
    Composite 0–100 stability score (higher = more stable).
    Returns INSUFFICIENT if fewer than 2 eras — not enough data to judge.
    """
    if n_eras < 2:
        return {"score": 0.0, "tier": "INSUFFICIENT",
                "note": "fewer than 2 eras analysed — insufficient long-horizon data"}
    try:
        _weights = {
            "constitutional_stability":          0.20,
            "drift_acceleration":                0.15,
            "governance_ideology_concentration": 0.10,
            "plasticity_half_life":              0.15,
            "exploration_extinction_risk":       0.15,
            "survivability_monoculture_risk":    0.10,
            "cognitive_diversity_retention":     0.10,
            "long_horizon_replay_dependence":    0.05,
        }
        total_penalty = sum(
            evolution_metrics.get(k, {}).get("score", 0.0) * w
            for k, w in _weights.items()
        )
        score = max(0.0, min(100.0, 100.0 - total_penalty))
        if score >= 75.0:   tier = "RESILIENT"
        elif score >= 55.0: tier = "ADEQUATE"
        elif score >= 35.0: tier = "VULNERABLE"
        else:               tier = "CRITICAL"
        return {"score": round(score, 2), "tier": tier}
    except Exception:
        return {"score": 0.0, "tier": "CRITICAL"}


# ── Evolutionary classification ────────────────────────────────────────────────

def _classify_evolution(evolution_metrics: dict, n_eras: int) -> str:
    if n_eras < 2:
        return CONSTITUTIONALLY_RESILIENT  # insufficient data — no alarming classification
    try:
        cs_tier = evolution_metrics.get("constitutional_stability",          {}).get("tier", "INSUFFICIENT")
        da_tier = evolution_metrics.get("drift_acceleration",                {}).get("tier", "INSUFFICIENT")
        ic_tier = evolution_metrics.get("governance_ideology_concentration", {}).get("tier", "INSUFFICIENT")
        pl_tier = evolution_metrics.get("plasticity_half_life",              {}).get("tier", "INSUFFICIENT")
        ee_tier = evolution_metrics.get("exploration_extinction_risk",       {}).get("tier", "INSUFFICIENT")
        mc_tier = evolution_metrics.get("survivability_monoculture_risk",    {}).get("tier", "INSUFFICIENT")
        rd_tier = evolution_metrics.get("long_horizon_replay_dependence",    {}).get("tier", "INSUFFICIENT")

        # Most severe first
        if cs_tier == "UNSTABLE" or (da_tier == "HIGH" and cs_tier == "VOLATILE"):
            return LONG_HORIZON_LOCKDOWN_RISK
        if ee_tier in ("HIGH", "CRITICAL") and pl_tier in ("RAPID_DECAY", "EXTINCT"):
            return EXPLORATION_EXTINCTION
        if mc_tier == "MONOCULTURE" and ic_tier in ("CONCENTRATED", "MONOCULTURE"):
            return SURVIVABILITY_MONOCULTURE
        if da_tier == "HIGH" and cs_tier in ("VOLATILE", "MODERATE"):
            return ADAPTIVE_MEMORY_DECAY
        if ic_tier in ("CONCENTRATED", "MONOCULTURE") or rd_tier == "HIGH":
            return IDEOLOGICAL_RIGIDIFICATION
        return CONSTITUTIONALLY_RESILIENT
    except Exception:
        return CONSTITUTIONALLY_RESILIENT


# ── Cognitive lineage ─────────────────────────────────────────────────────────

def _build_cognitive_lineage(era_snapshots: List[dict]) -> dict:
    """Preserve early/mid/late era snapshots and key metric trajectories."""
    if not era_snapshots:
        return {"eras": 0, "early_era": None, "mid_era": None, "late_era": None, "trajectory": {}}
    try:
        n     = len(era_snapshots)
        early = era_snapshots[0]
        late  = era_snapshots[-1]
        mid   = era_snapshots[n // 2]

        _SNAP_KEYS = ("era_index", "net_expectancy", "exploration_ratio",
                      "win_rate", "dominant_regime", "regime_hhi",
                      "era_constitutional_health")

        def _snap(e):
            return {k: e.get(k) for k in _SNAP_KEYS}

        def _direction(key, threshold=0.005):
            ev, lv = early.get(key, 0.0) or 0.0, late.get(key, 0.0) or 0.0
            delta  = lv - ev
            if abs(delta) < threshold:
                return "STABLE"
            return "IMPROVING" if delta > 0 else "DECLINING"

        def _direction_inv(key, threshold=1.0):
            # For HHI-type metrics: decreasing = improving
            ev, lv = early.get(key, 0.0) or 0.0, late.get(key, 0.0) or 0.0
            delta  = lv - ev
            if abs(delta) < threshold:
                return "STABLE"
            return "DECLINING" if delta > 0 else "IMPROVING"

        return {
            "eras":      n,
            "early_era": _snap(early),
            "mid_era":   _snap(mid),
            "late_era":  _snap(late),
            "trajectory": {
                "net_expectancy":          _direction("net_expectancy"),
                "exploration_ratio":       _direction("exploration_ratio"),
                "win_rate":                _direction("win_rate"),
                "regime_hhi":              _direction_inv("regime_hhi"),
                "constitutional_health":   _direction("era_constitutional_health"),
            },
        }
    except Exception:
        return {"eras": len(era_snapshots), "early_era": None, "mid_era": None,
                "late_era": None, "trajectory": {}}


# ── Recommendations ────────────────────────────────────────────────────────────

def _generate_evolution_recommendations(
    classification: str,
    evolution_metrics: dict,
    n_eras: int,
    stability_score: dict,
) -> List[dict]:
    recs: List[dict] = []

    if n_eras < 2:
        recs.append({
            "priority":       "MEDIUM",
            "type":           "LONG_HORIZON_READINESS",
            "summary":        f"Only {n_eras} era(s) analysed — long-horizon observatory requires ≥2 eras (≥40 trades).",
            "action_required": "ACCUMULATE_TRADE_HISTORY",
            "auto_authorized": False,
        })
        return recs

    if classification == LONG_HORIZON_LOCKDOWN_RISK:
        recs.append({
            "priority":       "CRITICAL",
            "type":           "CONSTITUTIONAL_DEGRADATION",
            "summary":        "Constitutional stability critical — long-horizon drift accumulating. Human governance review required.",
            "action_required": "HUMAN_GOVERNANCE_REVIEW_REQUIRED",
            "auto_authorized": False,
        })

    if classification == EXPLORATION_EXTINCTION:
        recs.append({
            "priority":       "CRITICAL",
            "type":           "EXPLORATION_COLLAPSE",
            "summary":        "Curiosity collapse detected — exploration ratio approaching extinction. Plasticity decay accelerating.",
            "action_required": "HUMAN_REVIEW_EXPLORATION_DOCTRINE",
            "auto_authorized": False,
        })

    if classification == SURVIVABILITY_MONOCULTURE:
        recs.append({
            "priority":       "HIGH",
            "type":           "MONOCULTURE_RISK",
            "summary":        "Survivability monoculture — regime concentration pathologically high across eras.",
            "action_required": "HUMAN_REVIEW_REGIME_DIVERSITY",
            "auto_authorized": False,
        })

    if classification == ADAPTIVE_MEMORY_DECAY:
        recs.append({
            "priority":       "HIGH",
            "type":           "MEMORY_DECAY",
            "summary":        "Long-horizon drift acceleration — adaptation instability increasing across eras.",
            "action_required": "HUMAN_REVIEW_ADAPTATION_DOCTRINE",
            "auto_authorized": False,
        })

    if classification == IDEOLOGICAL_RIGIDIFICATION:
        recs.append({
            "priority":       "MEDIUM",
            "type":           "GOVERNANCE_RIGIDITY",
            "summary":        "Governance ideology concentrating — doctrine flexibility declining across eras.",
            "action_required": "HUMAN_REVIEW_GOVERNANCE_DOCTRINE",
            "auto_authorized": False,
        })

    ee_tier = evolution_metrics.get("exploration_extinction_risk", {}).get("tier", "INSUFFICIENT")
    if ee_tier in ("HIGH", "CRITICAL") and EXPLORATION_EXTINCTION not in (classification,):
        recs.append({
            "priority":       "HIGH",
            "type":           "EXPLORATION_WARNING",
            "summary":        f"Exploration extinction risk {ee_tier.lower()} — late-era exploration approaching critical threshold.",
            "action_required": "HUMAN_REVIEW_EXPLORATION_BALANCE",
            "auto_authorized": False,
        })

    rd_tier = evolution_metrics.get("long_horizon_replay_dependence", {}).get("tier", "INSUFFICIENT")
    if rd_tier == "HIGH" and classification not in (IDEOLOGICAL_RIGIDIFICATION,):
        recs.append({
            "priority":       "MEDIUM",
            "type":           "REPLAY_DEPENDENCE",
            "summary":        "High late-era replay dependence — engine increasingly reliant on established patterns.",
            "action_required": "HUMAN_REVIEW_REPLAY_BALANCE",
            "auto_authorized": False,
        })

    if not recs:
        recs.append({
            "priority":       "LOW",
            "type":           "LONG_HORIZON_STATUS",
            "summary":        (
                f"{classification}: {_CLASSIFICATION_DESCRIPTIONS.get(classification, '')} "
                f"Stability score {stability_score.get('score', 0.0):.1f}/100."
            ),
            "action_required": "CONTINUE_MONITORING",
            "auto_authorized": False,
        })

    return recs


# ── Audit entry ────────────────────────────────────────────────────────────────

def _generate_evolution_audit_entry(
    classification: str,
    stability_score: dict,
    n_eras: int,
    total_trades: int,
    recommendations: List[dict],
) -> dict:
    try:
        ts      = int(_time.time() * 1000)
        payload = (
            f"{ts}|{classification}|{n_eras}|{total_trades}"
            f"|{stability_score.get('score', 0.0)}"
        )
        fp = hashlib.sha256(payload.encode()).hexdigest()
        return {
            "entry_id":                     f"LHEO-{ts}-{fp[:16]}",
            "timestamp_ms":                 ts,
            "entry_type":                   "ANALYSIS",
            "evolution_classification":     classification,
            "long_horizon_stability_score": stability_score.get("score", 0.0),
            "stability_tier":               stability_score.get("tier", "INSUFFICIENT"),
            "eras_analyzed":                n_eras,
            "total_trades":                 total_trades,
            "recommendations_generated":    len(recommendations),
            "human_approval_required":      n_eras >= 2,
            "auto_authorized":              False,
            "immutable":                    True,
        }
    except Exception:
        ts = int(_time.time() * 1000)
        return {
            "entry_id":             f"LHEO-{ts}-error",
            "timestamp_ms":         ts,
            "entry_type":           "ANALYSIS",
            "human_approval_required": False,
            "auto_authorized":      False,
            "immutable":            True,
        }


# ── Public entry point ─────────────────────────────────────────────────────────

def compute_long_horizon_evolution(trades: List[dict]) -> dict:
    """
    Produce a constitutional long-horizon evolution observatory assessment.

    Args:
        trades: Full paper trade history (from session + DataLake).

    Returns a research-only dict. Never raises. Never modifies input.
    All recommendations have auto_authorized=False.
    """
    try:
        n_eras    = max(1, min(_N_ERAS, len(trades) // 20))
        era_lists = _segment_eras(trades, n_eras)
        snapshots = [_era_snapshot(era, i) for i, era in enumerate(era_lists)]

        evolution_metrics = _compute_evolution_metrics(snapshots)
        stability_score   = _long_horizon_stability_score(evolution_metrics, len(snapshots))
        classification    = _classify_evolution(evolution_metrics, len(snapshots))
        lineage           = _build_cognitive_lineage(snapshots)
        recommendations   = _generate_evolution_recommendations(
            classification, evolution_metrics, len(snapshots), stability_score,
        )
        audit_entry = _generate_evolution_audit_entry(
            classification, stability_score, len(snapshots), len(trades), recommendations,
        )

        return {
            "scope_note": (
                "FTD-LHEO long-horizon constitutional evolution observatory — research instrumentation only. "
                "Observes whether PHOENIX remains cognitively adaptive, constitutionally stable, and "
                "governance-aligned across very long learning horizons. "
                "PHOENIX must NEVER evolve beyond explicit constitutional human governance."
            ),
            "total_trades":             len(trades),
            "eras_analyzed":            len(snapshots),
            "era_snapshots":            snapshots,
            "evolution_classification": classification,
            "classification_description": _CLASSIFICATION_DESCRIPTIONS.get(classification, ""),
            "long_horizon_stability":   stability_score,
            "evolution_metrics":        evolution_metrics,
            "cognitive_lineage":        lineage,
            "recommendations":          recommendations,
            "evolution_hard_principles": EVOLUTION_HARD_PRINCIPLES,
            "audit_entry":              audit_entry,
        }
    except Exception:
        return {
            "scope_note": "FTD-LHEO research instrumentation — analysis error.",
            "error":      "analysis failed",
            "evolution_classification": CONSTITUTIONALLY_RESILIENT,
            "evolution_hard_principles": EVOLUTION_HARD_PRINCIPLES,
        }
