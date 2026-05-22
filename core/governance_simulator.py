"""
FTD-GAGS: Guarded Adaptive Governance Simulator & Policy Arbitration Engine.

Pure analytics — no I/O, no side effects, no execution authority.

Extends the counterfactual lab to simulate compound policy stacks (sequential
composition of multiple interventions), then arbitrates across 6 governance
profiles to identify which compound best serves each profile's objectives.

Hard non-mutation rule:
  DO NOT enable live adaptive governance, autonomous execution control,
  or self-modifying production policies based on these outputs.
  Not an execution authority. All decisions at developer discretion.

Isolation guarantee: this module imports only from core.counterfactual_lab
and the standard library. Zero live engine imports.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from core.counterfactual_lab import (
    INTERVENTION_PROFILES,
    MIN_REPLAY_TRADES,
    _compute_trade_metrics,
)

# ── Governance outcome labels ─────────────────────────────────────────────────
GOVERNANCE_STABLE          = "GOVERNANCE_STABLE"          # baseline maintained, no disruption
ECONOMIC_AUTHORITARIANISM  = "ECONOMIC_AUTHORITARIANISM"  # NE up but opportunity access suppressed
PLASTICITY_OVEREXPANSION   = "PLASTICITY_OVEREXPANSION"   # exploration increased but economics degraded
ONTOLOGY_FRAGMENTATION     = "ONTOLOGY_FRAGMENTATION"     # explore/exploit drift materially worsened
ECOLOGICAL_COLLAPSE        = "ECOLOGICAL_COLLAPSE"        # survivability forced up via trade starvation
BALANCED_ADAPTATION        = "BALANCED_ADAPTATION"        # broad improvement across ≥3 objectives

# ── Governance thresholds ─────────────────────────────────────────────────────
COLLAPSE_OPP_THRESHOLD     = -50.0   # % opp drop that triggers collapse classifications
ONTOLOGY_FRAG_DRIFT_DELTA  = 10.0   # drift increase (abs) → ONTOLOGY_FRAGMENTATION
BALANCED_MIN_IMPROVED      = 3      # objectives that must improve for BALANCED_ADAPTATION

# ── Compound policy stacks (6) ─────────────────────────────────────────────────
COMPOUND_PROFILES: Dict[str, List[str]] = {
    "SOFT_NEGMEM_TF5": [
        "NEGMEM_SOFT_DECAY",
        "TF5_SURVIVABILITY_FILTER",
    ],
    "NY_TF5_PROJECTION": [
        "NY_ONLY_SURVIVABILITY",
        "TF5_SURVIVABILITY_FILTER",
    ],
    "DEFENSIVE_SESSIONS": [
        "SESSION_SUPPRESSION_ASIA",
        "ECOLOGY_STRICTER",
    ],
    "EXPLORE_REGIME_RESET": [
        "RULE4_HIGH_EXPLORE",
        "RL_RESET_MEAN_REVERTING",
    ],
    "FULL_QUALITY_FILTER": [
        "ECOLOGY_STRICTER",
        "NEGMEM_SOFT_DECAY",
        "SESSION_SUPPRESSION_ASIA",
    ],
    "ONTOLOGY_RL_TF5": [
        "ONTOLOGY_WEIGHTING_RL_DOMINANT",
        "TF5_SURVIVABILITY_FILTER",
    ],
}

# ── Governance profiles (6) ────────────────────────────────────────────────────

GOVERNANCE_PROFILES: Dict[str, dict] = {
    "ECONOMIC_MAXIMALIST": {
        "description": (
            "Prioritises net expectancy and survivability above all else. "
            "Accepts reduced opportunity density if economics improve. "
            "Research label: how would a pure-profit governance framework "
            "rank compound policies?"
        ),
        "weights": {
            "net_expectancy":    0.60,
            "survivability":     0.25,
            "opportunity_density": 0.10,
            "plasticity":        0.05,
            "ontology_coherence": 0.0,
            "fee_efficiency":    0.0,
        },
    },
    "PLASTICITY_PRESERVER": {
        "description": (
            "Prioritises cognitive plasticity and opportunity breadth. "
            "Values exploration diversity over short-term expectancy gains. "
            "Research label: how would an anti-fossilization framework "
            "rank compound policies?"
        ),
        "weights": {
            "net_expectancy":    0.20,
            "survivability":     0.0,
            "opportunity_density": 0.30,
            "plasticity":        0.50,
            "ontology_coherence": 0.0,
            "fee_efficiency":    0.0,
        },
    },
    "SURVIVABILITY_DEFENSIVE": {
        "description": (
            "Prioritises raw survivability score and fee efficiency. "
            "Accepts some expectancy sacrifice to avoid drawdown exposure. "
            "Research label: how would a capital-preservation framework "
            "rank compound policies?"
        ),
        "weights": {
            "net_expectancy":    0.30,
            "survivability":     0.50,
            "opportunity_density": 0.0,
            "plasticity":        0.0,
            "ontology_coherence": 0.0,
            "fee_efficiency":    0.20,
        },
    },
    "ECOLOGY_BALANCED": {
        "description": (
            "Prioritises opportunity density and ecological breadth. "
            "Balances expectancy with plasticity. Resists session suppression. "
            "Research label: how would a regime-diversity framework "
            "rank compound policies?"
        ),
        "weights": {
            "net_expectancy":    0.30,
            "survivability":     0.0,
            "opportunity_density": 0.40,
            "plasticity":        0.30,
            "ontology_coherence": 0.0,
            "fee_efficiency":    0.0,
        },
    },
    "ONTOLOGY_HARMONIZER": {
        "description": (
            "Prioritises ontology coherence — keeping explore/exploit beliefs "
            "aligned. Values plasticity over expectancy. "
            "Research label: how would an anti-drift framework "
            "rank compound policies?"
        ),
        "weights": {
            "net_expectancy":    0.20,
            "survivability":     0.0,
            "opportunity_density": 0.0,
            "plasticity":        0.30,
            "ontology_coherence": 0.50,
            "fee_efficiency":    0.0,
        },
    },
    "ADAPTIVE_GENERALIST": {
        "description": (
            "Balances all six governance objectives with equal-ish weighting. "
            "Seeks broad improvement without dominating any single dimension. "
            "Research label: how would a multi-objective generalist framework "
            "rank compound policies?"
        ),
        "weights": {
            "net_expectancy":    0.20,
            "survivability":     0.20,
            "opportunity_density": 0.20,
            "plasticity":        0.20,
            "ontology_coherence": 0.10,
            "fee_efficiency":    0.10,
        },
    },
}


# ── Compound stack application ─────────────────────────────────────────────────

def _apply_compound(trades: List[dict], intervention_names: List[str]) -> List[dict]:
    """
    Apply a sequence of intervention functions to the trade list.
    Each step's output becomes the next step's input.
    Input list is never mutated.
    """
    result = list(trades)
    for name in intervention_names:
        fn = INTERVENTION_PROFILES[name]["fn"]
        result = fn(result)
    return result


# ── Weighted governance score ──────────────────────────────────────────────────

def _weighted_governance_score(
    candidate_metrics: dict,
    baseline_metrics:  dict,
    baseline_count:    int,
    weights:           dict,
) -> float:
    """
    Score a compound's metrics against a governance profile's objective weights.

    Each dimension delta is normalised to [-1, +1]:
      net_expectancy     : delta / max(|baseline|, 0.001), clipped
      survivability      : delta / 100
      plasticity         : delta / 3.32  (log2(10) ≈ max Shannon entropy, 10 bins)
      opportunity_density: (candidate_count − baseline_count) / baseline_count
      ontology_coherence : −(drift_cand − drift_base) / 100  (lower drift = better)
      fee_efficiency     : −(fee_cand − fee_base) / 50       (lower fee drag = better)

    Final score: 50 + weighted_sum × 50, clamped to [0, 100].
    """
    def _clip(v: float) -> float:
        return max(-1.0, min(1.0, v))

    ne_base = float(baseline_metrics.get("net_expectancy")  or 0.0)
    ne_cand = float(candidate_metrics.get("net_expectancy") or 0.0)
    ne_norm = _clip((ne_cand - ne_base) / max(abs(ne_base), 0.001))

    surv_base = float(baseline_metrics.get("survivability_score")  or 0.0)
    surv_cand = float(candidate_metrics.get("survivability_score") or 0.0)
    surv_norm = _clip((surv_cand - surv_base) / 100.0)

    pl_base = float(baseline_metrics.get("plasticity_proxy")  or 0.0)
    pl_cand = float(candidate_metrics.get("plasticity_proxy") or 0.0)
    pl_norm = _clip((pl_cand - pl_base) / 3.32)

    i_count = int(candidate_metrics.get("trade_count") or 0)
    opp_norm = _clip((i_count - baseline_count) / max(baseline_count, 1))

    drift_base = float(baseline_metrics.get("ontology_drift_proxy")  or 0.0)
    drift_cand = float(candidate_metrics.get("ontology_drift_proxy") or 0.0)
    oc_norm = _clip(-(drift_cand - drift_base) / 100.0)

    fee_base = float(baseline_metrics.get("fee_drag_mean_pct")  or 0.0)
    fee_cand = float(candidate_metrics.get("fee_drag_mean_pct") or 0.0)
    fe_norm = _clip(-(fee_cand - fee_base) / 50.0)

    normed = {
        "net_expectancy":    ne_norm,
        "survivability":     surv_norm,
        "plasticity":        pl_norm,
        "opportunity_density": opp_norm,
        "ontology_coherence": oc_norm,
        "fee_efficiency":    fe_norm,
    }

    weighted_sum = sum(weights.get(k, 0.0) * v for k, v in normed.items())
    raw = 50.0 + weighted_sum * 50.0
    return round(max(0.0, min(100.0, raw)), 2)


# ── Regime specialization risk ────────────────────────────────────────────────

def _regime_specialization_risk(trades: List[dict]) -> dict:
    """
    Herfindahl-Hirschman Index × 100 as a concentration score.

    HHI = Σ (share_i)² where share_i = count_i / total.
    Multiplied by 100 to give a 0–100 score.
    Tiers: HIGH (≥70), MODERATE (≥40), LOW (≥20), MINIMAL.
    """
    if not trades:
        return {"score": 0.0, "tier": "MINIMAL", "regime_counts": {}}

    total = len(trades)
    counts: Dict[str, int] = {}
    for t in trades:
        regime = t.get("regime") or "UNKNOWN"
        counts[regime] = counts.get(regime, 0) + 1

    hhi   = sum((c / total) ** 2 for c in counts.values())
    score = round(hhi * 100, 1)

    if   score >= 70: tier = "HIGH"
    elif score >= 40: tier = "MODERATE"
    elif score >= 20: tier = "LOW"
    else:             tier = "MINIMAL"

    return {"score": score, "tier": tier, "regime_counts": counts}


# ── Overfitting risk ──────────────────────────────────────────────────────────

def _overfitting_risk(baseline_metrics: dict, best_metrics: dict) -> dict:
    """
    Proxy: survivability improvement paired with deep opportunity density loss
    indicates the compound may be cherry-picking by filtering most trades away.

    HIGH   : opp drop > 40% and survivability improved > 5 pts
    MODERATE: opp drop > 20% and survivability improved > 2 pts
    LOW    : otherwise
    """
    b_count = int(baseline_metrics.get("trade_count") or 0)
    i_count = int(best_metrics.get("trade_count")    or 0)
    opp_pct = (i_count - b_count) / max(b_count, 1) * 100

    surv_base = float(baseline_metrics.get("survivability_score") or 0.0)
    surv_best = float(best_metrics.get("survivability_score")     or 0.0)
    surv_delta = surv_best - surv_base

    if opp_pct < -40 and surv_delta > 5:
        tier  = "HIGH"
        score = min(100.0, abs(opp_pct) + surv_delta)
    elif opp_pct < -20 and surv_delta > 2:
        tier  = "MODERATE"
        score = min(100.0, abs(opp_pct) * 0.5 + surv_delta)
    else:
        tier  = "LOW"
        score = max(0.0, abs(opp_pct) * 0.1)

    return {"score": round(score, 1), "tier": tier}


# ── Governance outcome classification ─────────────────────────────────────────

def _classify_governance(
    best_metrics:    dict,
    baseline_metrics: dict,
    baseline_count:  int,
) -> str:
    """
    Classify the governance outcome for a profile's best compound.

    Priority (checked in sequence):
      ECOLOGICAL_COLLAPSE      — survivability up but opp density ≤ −50%
      ECONOMIC_AUTHORITARIANISM — NE up but opp density ≤ −50%
      ONTOLOGY_FRAGMENTATION   — ontology drift worsened by > 10 pts
      PLASTICITY_OVEREXPANSION  — plasticity up but NE degraded
      BALANCED_ADAPTATION      — ≥3 objectives improved, no collapse condition
      GOVERNANCE_STABLE        — default (baseline held, no clear winner)

    Research label only — not an execution authority.
    """
    i_count = int(best_metrics.get("trade_count") or 0)
    opp_pct = (i_count - baseline_count) / max(baseline_count, 1) * 100

    ne_base  = float(baseline_metrics.get("net_expectancy")       or 0.0)
    ne_best  = float(best_metrics.get("net_expectancy")           or 0.0)
    ne_up    = ne_best > ne_base

    surv_base = float(baseline_metrics.get("survivability_score") or 0.0)
    surv_best = float(best_metrics.get("survivability_score")     or 0.0)
    surv_up   = surv_best > surv_base

    drift_base = float(baseline_metrics.get("ontology_drift_proxy") or 0.0)
    drift_best = float(best_metrics.get("ontology_drift_proxy")     or 0.0)

    pl_base = float(baseline_metrics.get("plasticity_proxy") or 0.0)
    pl_best = float(best_metrics.get("plasticity_proxy")     or 0.0)
    pl_up   = pl_best > pl_base

    fee_base = float(baseline_metrics.get("fee_drag_mean_pct") or 0.0)
    fee_best = float(best_metrics.get("fee_drag_mean_pct")     or 0.0)

    if surv_up and opp_pct < COLLAPSE_OPP_THRESHOLD:
        return ECOLOGICAL_COLLAPSE

    if ne_up and opp_pct < COLLAPSE_OPP_THRESHOLD:
        return ECONOMIC_AUTHORITARIANISM

    if (drift_best - drift_base) > ONTOLOGY_FRAG_DRIFT_DELTA:
        return ONTOLOGY_FRAGMENTATION

    if pl_up and ne_best < ne_base:
        return PLASTICITY_OVEREXPANSION

    improved = sum([
        ne_up,
        surv_up,
        pl_up,
        opp_pct > 0,
        (drift_best - drift_base) < 0,
        fee_best < fee_base,
    ])
    if improved >= BALANCED_MIN_IMPROVED:
        return BALANCED_ADAPTATION

    return GOVERNANCE_STABLE


# ── Conflict detection ─────────────────────────────────────────────────────────

def _detect_conflicts(governance_results: dict) -> dict:
    """
    Detect policy arbitration conflicts between competing governance profiles.

    Three monitored conflict axes:
      ECONOMIC_MAXIMALIST  vs PLASTICITY_PRESERVER  → EXPECTANCY_VS_PLASTICITY
      ECOLOGY_BALANCED     vs SURVIVABILITY_DEFENSIVE → OPPORTUNITY_VS_SURVIVABILITY
      ONTOLOGY_HARMONIZER  vs ADAPTIVE_GENERALIST   → ONTOLOGY_VS_BALANCE
    """
    conflicts = []

    em_best = governance_results.get("ECONOMIC_MAXIMALIST",   {}).get("best_compound")
    pp_best = governance_results.get("PLASTICITY_PRESERVER",  {}).get("best_compound")
    if em_best and pp_best and em_best != pp_best:
        conflicts.append({
            "profiles":      ["ECONOMIC_MAXIMALIST", "PLASTICITY_PRESERVER"],
            "conflict_type": "EXPECTANCY_VS_PLASTICITY",
            "choices":       {"ECONOMIC_MAXIMALIST": em_best, "PLASTICITY_PRESERVER": pp_best},
        })

    eb_best = governance_results.get("ECOLOGY_BALANCED",        {}).get("best_compound")
    sd_best = governance_results.get("SURVIVABILITY_DEFENSIVE", {}).get("best_compound")
    if eb_best and sd_best and eb_best != sd_best:
        conflicts.append({
            "profiles":      ["ECOLOGY_BALANCED", "SURVIVABILITY_DEFENSIVE"],
            "conflict_type": "OPPORTUNITY_VS_SURVIVABILITY",
            "choices":       {"ECOLOGY_BALANCED": eb_best, "SURVIVABILITY_DEFENSIVE": sd_best},
        })

    oh_best = governance_results.get("ONTOLOGY_HARMONIZER",   {}).get("best_compound")
    ag_best = governance_results.get("ADAPTIVE_GENERALIST",   {}).get("best_compound")
    if oh_best and ag_best and oh_best != ag_best:
        conflicts.append({
            "profiles":      ["ONTOLOGY_HARMONIZER", "ADAPTIVE_GENERALIST"],
            "conflict_type": "ONTOLOGY_VS_BALANCE",
            "choices":       {"ONTOLOGY_HARMONIZER": oh_best, "ADAPTIVE_GENERALIST": ag_best},
        })

    return {
        "conflict_count":       len(conflicts),
        "conflicts":            conflicts,
        "consensus_reachable":  len(conflicts) == 0,
    }


# ── Consensus compound ────────────────────────────────────────────────────────

def _consensus_compound(governance_results: dict) -> Optional[str]:
    """
    Return the compound selected as best by the plurality of governance profiles.
    Returns None if two or more compounds tie for first place.
    """
    votes: Dict[str, int] = {}
    for result in governance_results.values():
        best = result.get("best_compound")
        if best:
            votes[best] = votes.get(best, 0) + 1

    if not votes:
        return None

    max_votes = max(votes.values())
    winners   = [k for k, v in votes.items() if v == max_votes]
    return winners[0] if len(winners) == 1 else None


# ── Main entry point ──────────────────────────────────────────────────────────

def compute_adaptive_governance(trades: List[dict]) -> dict:
    """
    Simulate all 6 compound policy stacks against all 6 governance profiles.

    For each compound stack:
      1. Apply constituent interventions sequentially (deterministic, no mutation)
      2. Compute sandbox economics via compute_economic_ground_truth

    For each governance profile:
      1. Score every compound with the profile's objective weights
      2. Select the highest-scoring compound as that profile's recommendation
      3. Classify the governance outcome for that recommendation

    Cross-cutting analytics:
      - Conflict detection between competing profiles
      - Regime specialization risk (HHI)
      - Overfitting risk (survivability improvement via trade starvation)
      - Consensus compound (plurality vote across all profiles)

    Isolation guarantee: no live engine state read or written.
    Never raises — fail-open contract.
    """
    SCOPE = (
        "FTD-GAGS: Guarded Adaptive Governance Simulator & Policy Arbitration Engine. "
        "Research instrumentation only — non-governing. "
        "Simulates compound policy stacks (sequential intervention composition) and "
        "arbitrates across 6 governance profiles to identify multi-objective tradeoffs. "
        "No production state is read or written. No execution behavior is altered. "
        "DO NOT enable live adaptive governance, autonomous execution control, or "
        "self-modifying production policies based on these outputs. "
        "Not an execution authority. All decisions at developer discretion."
    )

    try:
        if not trades or not isinstance(trades, list):
            return {
                "scope_note":   SCOPE,
                "total_trades": 0,
                "note":         "No trades provided for governance simulation.",
            }

        baseline_count   = len(trades)
        baseline_metrics = _compute_trade_metrics(trades)

        if "note" in baseline_metrics or "error" in baseline_metrics:
            return {
                "scope_note":   SCOPE,
                "total_trades": baseline_count,
                "note": (
                    f"Insufficient baseline trades (< {MIN_REPLAY_TRADES}). "
                    "Governance simulation requires more historical data."
                ),
            }

        # ── Apply each compound stack ─────────────────────────────────────────
        compound_stacks: Dict[str, dict] = {}
        for name, i_names in COMPOUND_PROFILES.items():
            try:
                replay  = _apply_compound(trades, i_names)
                metrics = _compute_trade_metrics(replay)
                compound_stacks[name] = {
                    "interventions": i_names,
                    "trade_count":   len(replay),
                    "metrics":       metrics,
                }
            except Exception as exc:
                compound_stacks[name] = {
                    "interventions": i_names,
                    "trade_count":   0,
                    "metrics":       {"trade_count": 0, "error": str(exc)},
                    "error":         str(exc),
                }

        # ── Score each compound against each governance profile ───────────────
        governance_profiles: Dict[str, dict] = {}
        for gp_name, gp in GOVERNANCE_PROFILES.items():
            compound_scores: Dict[str, float] = {}
            for c_name, c_data in compound_stacks.items():
                c_metrics = c_data.get("metrics", {})
                if "note" in c_metrics or "error" in c_metrics:
                    compound_scores[c_name] = 0.0
                else:
                    compound_scores[c_name] = _weighted_governance_score(
                        c_metrics, baseline_metrics, baseline_count, gp["weights"]
                    )

            best_compound = (
                max(compound_scores, key=lambda k: compound_scores[k])
                if compound_scores else None
            )
            best_metrics = (
                compound_stacks.get(best_compound, {}).get("metrics", {})
                if best_compound else {}
            )
            govclass = (
                _classify_governance(best_metrics, baseline_metrics, baseline_count)
                if best_metrics and "note" not in best_metrics and "error" not in best_metrics
                else GOVERNANCE_STABLE
            )

            governance_profiles[gp_name] = {
                "description":             gp["description"],
                "weights":                 gp["weights"],
                "compound_scores":         compound_scores,
                "best_compound":           best_compound,
                "best_score":              compound_scores.get(best_compound, 0.0) if best_compound else 0.0,
                "governance_classification": govclass,
            }

        # ── Cross-cutting analytics ───────────────────────────────────────────
        conflict_analysis      = _detect_conflicts(governance_profiles)
        regime_risk            = _regime_specialization_risk(trades)
        consensus              = _consensus_compound(governance_profiles)

        em_best = governance_profiles.get("ECONOMIC_MAXIMALIST", {}).get("best_compound")
        em_metrics = compound_stacks.get(em_best, {}).get("metrics", {}) if em_best else {}
        overfit_risk = (
            _overfitting_risk(baseline_metrics, em_metrics)
            if em_metrics and "note" not in em_metrics and "error" not in em_metrics
            else {"score": 0.0, "tier": "LOW"}
        )

        classifications = {
            gp: r.get("governance_classification", GOVERNANCE_STABLE)
            for gp, r in governance_profiles.items()
        }

        return {
            "scope_note":                    SCOPE,
            "total_trades":                  baseline_count,
            "baseline":                      baseline_metrics,
            "compound_stacks":               compound_stacks,
            "governance_profiles":           governance_profiles,
            "governance_classifications":    classifications,
            "conflict_analysis":             conflict_analysis,
            "regime_specialization_risk":    regime_risk,
            "overfitting_risk":              overfit_risk,
            "consensus_compound":            consensus,
        }

    except Exception as exc:
        return {
            "scope_note": SCOPE,
            "error":      str(exc),
        }
