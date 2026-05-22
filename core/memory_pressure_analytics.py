"""
FTD-ONTOLOGY-DRIFT: Memory Pressure & Ontology Drift Dynamics.

Pure analytics — no I/O, no side effects, no execution authority.

Measures how PHOENIX's memory systems evolve under long-horizon learning
pressure. Compares belief states across five subsystems:
  RL Q-memory × PatternEngine WR-memory × NegativeMemory rollback-memory
  × signal ecology WR-memory × AlphaContextMemory amplification-memory

State dict is collected by the live endpoint and passed here — this module
has no live engine imports and cannot mutate any engine state.

Hard non-mutation rule: DO NOT alter memory weights, forgetting rates, RL
equations, NegativeMemory thresholds, or exploration behavior.
All outputs are research overlays — not execution authorities.
"""
from __future__ import annotations

import math
from collections import defaultdict
from statistics import mean
from typing import Dict, List, Optional

# ── Research category labels ──────────────────────────────────────────────────
HEALTHY_PLASTICITY      = "HEALTHY_PLASTICITY"
PREMATURE_FOSSILIZATION = "PREMATURE_FOSSILIZATION"
ONTOLOGY_FRAGMENTATION  = "ONTOLOGY_FRAGMENTATION"
ADAPTIVE_CONVERGENCE    = "ADAPTIVE_CONVERGENCE"
MEMORY_SATURATION       = "MEMORY_SATURATION"
ECOLOGICAL_AMNESIA      = "ECOLOGICAL_AMNESIA"

# ── Drift thresholds ──────────────────────────────────────────────────────────
DRIFT_HIGH     = 60   # score >= this → HIGH_DRIFT
DRIFT_MODERATE = 35   # score >= this → MODERATE_DRIFT
DRIFT_LOW      = 15   # score >= this → LOW_DRIFT

# ── Plasticity / fossilization thresholds ────────────────────────────────────
Q_ENTROPY_HIGH        = 2.0    # bits — healthy Q diversity
Q_ENTROPY_LOW         = 1.5    # bits — stagnation signal
NEGMEM_DENSITY_SAFE   = 30.0   # % — density at or below this = healthy
NEGMEM_DENSITY_RISK   = 50.0   # % — density above this = fossilization risk
AVG_VELOCITY_ACTIVE   = 0.005  # healthy learning velocity
AVG_VELOCITY_STAGNANT = 0.0025 # stagnation velocity
EXPLORE_RATE_MIN      = 0.10   # explore ratio below this = drying up
EXPLORE_RATE_MAX      = 0.45   # explore ratio above this = runaway


# ── Helpers ───────────────────────────────────────────────────────────────────

def _drift_tier(score: float) -> str:
    if score >= DRIFT_HIGH:     return "HIGH_DRIFT"
    if score >= DRIFT_MODERATE: return "MODERATE_DRIFT"
    if score >= DRIFT_LOW:      return "LOW_DRIFT"
    return "ALIGNED"


def _q_entropy(q_values: List[float]) -> float:
    """Shannon entropy of Q-values discretized into 10 equal-width bins."""
    if len(q_values) < 2:
        return 0.0
    lo, hi = min(q_values), max(q_values)
    if hi == lo:
        return 0.0
    n_bins = 10
    width  = (hi - lo) / n_bins
    counts = [0] * n_bins
    for q in q_values:
        idx = min(int((q - lo) / width), n_bins - 1)
        counts[idx] += 1
    total   = len(q_values)
    entropy = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            entropy -= p * math.log2(p)
    return round(entropy, 4)


# ── Plasticity & Fossilization ────────────────────────────────────────────────

def _plasticity_score(
    q_entropy:      float,
    negmem_density: float,
    avg_q_velocity: float,
    explore_rate:   float,
) -> dict:
    """
    0-100 composite: how well PHOENIX can still update its beliefs.
    Four contributing factors worth 25 points each.
    """
    score = 0
    if q_entropy >= Q_ENTROPY_HIGH:                          score += 25
    if negmem_density <= NEGMEM_DENSITY_SAFE:                score += 25
    if avg_q_velocity >= AVG_VELOCITY_ACTIVE:                score += 25
    if EXPLORE_RATE_MIN <= explore_rate <= EXPLORE_RATE_MAX: score += 25

    if score >= 75:   tier = "HIGH"
    elif score >= 50: tier = "MODERATE"
    elif score >= 25: tier = "LOW"
    else:             tier = "CRITICAL"

    return {
        "score": score,
        "tier":  tier,
        "components": {
            "q_entropy_contribution":  25 if q_entropy >= Q_ENTROPY_HIGH else 0,
            "negmem_headroom":         25 if negmem_density <= NEGMEM_DENSITY_SAFE else 0,
            "q_velocity_contribution": 25 if avg_q_velocity >= AVG_VELOCITY_ACTIVE else 0,
            "explore_balance":         25 if EXPLORE_RATE_MIN <= explore_rate <= EXPLORE_RATE_MAX else 0,
        },
    }


def _fossilization_risk(
    negmem_density: float,
    q_entropy:      float,
    avg_q_velocity: float,
    explore_rate:   float,
) -> dict:
    """
    0-100 composite: how close PHOENIX is to learning rigidity.
    Four contributing risk factors.
    """
    score = 0
    if negmem_density > NEGMEM_DENSITY_RISK:     score += 30
    if q_entropy < Q_ENTROPY_LOW:                score += 25
    if avg_q_velocity < AVG_VELOCITY_STAGNANT:   score += 25
    if explore_rate < EXPLORE_RATE_MIN:          score += 20

    if score >= 60:   tier = "HIGH"
    elif score >= 35: tier = "MEDIUM"
    elif score >= 15: tier = "LOW"
    else:             tier = "MINIMAL"

    return {
        "score": score,
        "tier":  tier,
        "components": {
            "negmem_overload":       30 if negmem_density > NEGMEM_DENSITY_RISK else 0,
            "q_entropy_stagnation":  25 if q_entropy < Q_ENTROPY_LOW else 0,
            "q_velocity_stagnation": 25 if avg_q_velocity < AVG_VELOCITY_STAGNANT else 0,
            "exploration_drying":    20 if explore_rate < EXPLORE_RATE_MIN else 0,
        },
    }


# ── Drift pair computations ───────────────────────────────────────────────────

def _drift_rl_negmem(rl: dict, negmem: dict) -> dict:
    """
    RL ↔ NegMem drift: optimism vs pessimism discordance.

    RL failure rate (1 - profitable_pct) vs NegMem permanent density.
    High drift = RL believes it's succeeding while NegMem has accumulated
    many permanent bans (or vice versa).

    Key-level comparison is not possible because RL uses 3-component context
    keys (regime|hour|strategy) while NegMem uses 5-component PatternKeys
    (regime|volatility|instrument|parameter|direction). Aggregate-level only.
    """
    rl_profitable   = float(rl.get("profitable_pct", 0.0) or 0.0)
    rl_failure_rate = max(0.0, 1.0 - rl_profitable)

    nm_count        = negmem.get("count", {}) or {}
    nm_total        = max(nm_count.get("total", 0), 1)
    nm_permanent    = nm_count.get("permanent", 0)
    negmem_perm_density = nm_permanent / nm_total

    disagreement = abs(rl_failure_rate - negmem_perm_density)
    drift_score  = round(min(100.0, disagreement * 100), 1)

    return {
        "drift_score":              drift_score,
        "tier":                     _drift_tier(drift_score),
        "rl_failure_rate_pct":      round(rl_failure_rate * 100, 1),
        "negmem_perm_density_pct":  round(negmem_perm_density * 100, 1),
        "interpretation": (
            "RL optimism and NegMem pessimism are aligned"
            if drift_score < DRIFT_MODERATE
            else "RL/NegMem belief gap — contexts blocked by NegMem may conflict with RL confidence"
        ),
    }


def _drift_rl_pattern(rl: dict, patterns: dict) -> dict:
    """
    RL ↔ PatternEngine drift: Q-learning success belief vs WR-memory success belief.

    Compares RL's profitable_pct to mean success rate of formed patterns.
    """
    rl_profitable = float(rl.get("profitable_pct", 0.0) or 0.0)

    formed = patterns.get("formed_pattern_dicts", []) or []
    if not formed:
        return {
            "drift_score": 0.0,
            "tier":        "ALIGNED",
            "note":        "No formed patterns — comparison unavailable",
        }

    pattern_success_ratios = []
    for p in formed:
        samples = p.get("samples", 0) or 0
        success = p.get("success", 0) or 0
        if samples > 0:
            pattern_success_ratios.append(success / samples)

    if not pattern_success_ratios:
        return {"drift_score": 0.0, "tier": "ALIGNED", "note": "No valid pattern samples"}

    pattern_success_ratio = mean(pattern_success_ratios)
    disagreement  = abs(rl_profitable - pattern_success_ratio)
    drift_score   = round(min(100.0, disagreement * 100), 1)

    return {
        "drift_score":              drift_score,
        "tier":                     _drift_tier(drift_score),
        "rl_profitable_pct":        round(rl_profitable * 100, 1),
        "pattern_mean_success_pct": round(pattern_success_ratio * 100, 1),
        "formed_patterns_used":     len(pattern_success_ratios),
    }


def _drift_rl_ecology(rl: dict, ecology: dict, regime_avg_q: dict) -> dict:
    """
    RL ↔ Ecology drift: per-regime polarity agreement.

    For each regime present in both systems:
      Ecology bullish → weight >= 1.0
      RL bullish      → regime average Q > 0
    Conflict = polarity disagreement between the two systems.
    """
    regimes_eco = (ecology.get("regimes", {}) or {})
    if not regimes_eco or not regime_avg_q:
        return {
            "drift_score": 0.0,
            "tier":        "ALIGNED",
            "note":        "Insufficient regime data for RL/Ecology comparison",
        }

    shared = set(regimes_eco.keys()) & set(regime_avg_q.keys())
    if not shared:
        return {
            "drift_score": 0.0,
            "tier":        "ALIGNED",
            "note":        "No shared regimes between RL table and Ecology",
        }

    conflicts:  List[str] = []
    agreements: List[str] = []
    for regime in sorted(shared):
        eco_data    = regimes_eco[regime] or {}
        eco_bullish = (eco_data.get("weight", 1.0) or 1.0) >= 1.0
        rl_bullish  = (regime_avg_q.get(regime, 0.0) or 0.0) > 0.0
        if eco_bullish != rl_bullish:
            conflicts.append(regime)
        else:
            agreements.append(regime)

    drift_score = round(len(conflicts) / len(shared) * 100, 1)

    return {
        "drift_score":       drift_score,
        "tier":              _drift_tier(drift_score),
        "shared_regimes":    len(shared),
        "conflict_regimes":  conflicts,
        "agreement_regimes": agreements,
    }


def _drift_pattern_negmem(patterns: dict, negmem: dict) -> dict:
    """
    Pattern ↔ NegMem drift: per-regime success belief vs rollback belief.

    Groups formed patterns by regime (from key.regime) and NegMem entries
    by first component of key_str. For shared regimes compares:
      pattern success rate  vs  (1 - negmem permanent fraction)
    These should be close if both memory systems agree on what works.
    """
    formed  = patterns.get("formed_pattern_dicts", []) or []
    entries = negmem.get("entries", []) or []

    if not formed or not entries:
        return {
            "drift_score": 0.0,
            "tier":        "ALIGNED",
            "note":        "Insufficient data for Pattern/NegMem comparison",
        }

    # Pattern success rates by regime
    pat_by_regime: Dict[str, List[float]] = defaultdict(list)
    for p in formed:
        regime  = ((p.get("key") or {}).get("regime") or "UNKNOWN")
        samples = p.get("samples", 0) or 0
        success = p.get("success", 0) or 0
        if samples > 0:
            pat_by_regime[regime].append(success / samples)

    # NegMem permanent fraction by regime (first component of key_str)
    nm_by_regime: Dict[str, dict] = defaultdict(lambda: {"total": 0, "permanent": 0})
    for e in entries:
        key_str = e.get("key_str", "") or ""
        regime  = key_str.split("|")[0] if "|" in key_str else "UNKNOWN"
        nm_by_regime[regime]["total"]     += 1
        nm_by_regime[regime]["permanent"] += int(bool(e.get("permanent", False)))

    shared = set(pat_by_regime.keys()) & set(nm_by_regime.keys())
    if not shared:
        return {
            "drift_score": 0.0,
            "tier":        "ALIGNED",
            "note":        "No shared regimes between Pattern and NegMem namespaces",
        }

    disagreements: List[float] = []
    per_regime: dict = {}
    for regime in sorted(shared):
        pat_success  = mean(pat_by_regime[regime])
        nm_data      = nm_by_regime[regime]
        nm_perm_frac = nm_data["permanent"] / max(nm_data["total"], 1)
        complement   = 1.0 - nm_perm_frac
        disagreement = abs(pat_success - complement)
        disagreements.append(disagreement)
        per_regime[regime] = {
            "pattern_success_pct":  round(pat_success * 100, 1),
            "negmem_perm_frac_pct": round(nm_perm_frac * 100, 1),
            "disagreement_pct":     round(disagreement * 100, 1),
        }

    drift_score = round(mean(disagreements) * 100, 1)

    return {
        "drift_score":    drift_score,
        "tier":           _drift_tier(drift_score),
        "shared_regimes": len(shared),
        "per_regime":     per_regime,
    }


def _drift_alpha_context_rl(alpha_context: dict, rl: dict) -> dict:
    """
    AlphaContext ↔ RL drift: signal amplification belief vs Q-learning belief.

    Compares AlphaContextMemory's profitable fraction to RL's profitable_pct.
    Both measure "what fraction of known contexts are good" — divergence
    suggests the two filters are targeting different region of context space.
    """
    total_ac  = max(alpha_context.get("total_contexts", 0) or 0, 1)
    ac_profit = alpha_context.get("profitable_count", 0) or 0
    ac_pct    = ac_profit / total_ac

    rl_pct      = float(rl.get("profitable_pct", 0.0) or 0.0)
    drift_score = round(min(100.0, abs(ac_pct - rl_pct) * 100), 1)

    return {
        "drift_score":       drift_score,
        "tier":              _drift_tier(drift_score),
        "alpha_context_pct": round(ac_pct * 100, 1),
        "rl_profitable_pct": round(rl_pct * 100, 1),
        "total_ac_contexts": total_ac,
    }


# ── Cognitive state classification ────────────────────────────────────────────

def _classify_cognitive_state(
    negmem_density:        float,
    pattern_formation_rate: float,
    max_drift:             float,
    avg_drift:             float,
    fossilization_score:   int,
    plasticity_score:      int,
    negmem_total:          int,
    rl_total_contexts:     int,
    explore_rate:          float,
    avg_q_velocity:        float,
) -> str:
    """
    Classify the cognitive state into one of 6 research categories.

    Priority order (most severe first):
      MEMORY_SATURATION → ONTOLOGY_FRAGMENTATION → PREMATURE_FOSSILIZATION →
      ECOLOGICAL_AMNESIA → ADAPTIVE_CONVERGENCE → HEALTHY_PLASTICITY

    Research label only — not an execution authority.
    """
    if negmem_density > 60.0 and pattern_formation_rate > 60.0:
        return MEMORY_SATURATION

    if max_drift >= 70.0 or avg_drift >= 50.0:
        return ONTOLOGY_FRAGMENTATION

    if fossilization_score >= 60 and plasticity_score <= 25:
        return PREMATURE_FOSSILIZATION

    if (negmem_total == 0
            and rl_total_contexts > 30
            and explore_rate > 0.4):
        return ECOLOGICAL_AMNESIA

    q_improving    = avg_q_velocity >= AVG_VELOCITY_ACTIVE
    er_not_runaway = explore_rate <= EXPLORE_RATE_MAX
    if (q_improving and er_not_runaway and max_drift < 40.0 and plasticity_score >= 50):
        return ADAPTIVE_CONVERGENCE

    return HEALTHY_PLASTICITY


# ── Main entry point ──────────────────────────────────────────────────────────

def compute_memory_pressure_dynamics(state: dict) -> dict:
    """
    Full memory-pressure and ontology-drift cartography.

    Accepts a pre-collected state dict assembled by the endpoint from live
    engine objects. Never raises — fail-open contract.

    State dict keys:
      rl            → {profitable_pct (0-1), total_contexts, q_values,
                        q_velocities, toxic_count, explore_ratio, regime_avg_q}
      negmem        → {count: {permanent, temporary, total}, entries: list}
      patterns      → {total_patterns, formed_patterns, formed_pattern_dicts}
      ecology       → {regimes: {regime: {n_trades, win_rate, weight}}}
      alpha_context → {profitable_count, toxic_count, total_contexts}

    Returns structured dict covering:
      memory_pressure  — negmem density, Q entropy, plasticity, fossilization
      ontology_drift   — five pairwise drift scores
      drift_heatmap    — sorted by drift_score descending
      cognitive_state  — 6-category classification
      summary_stats    — avg/max/min drift across all pairs
    """
    SCOPE = (
        "FTD-ONTOLOGY-DRIFT: Research instrumentation only — non-governing. "
        "Measures memory pressure and ontology drift across RL × Pattern × NegMem × "
        "Ecology × AlphaContext. "
        "DO NOT alter memory weights, forgetting rates, RL equations, NegMem thresholds, "
        "or exploration behavior based on these metrics alone. "
        "Not an execution authority. All decisions at developer discretion."
    )

    try:
        rl            = state.get("rl",            {}) or {}
        negmem        = state.get("negmem",         {}) or {}
        patterns      = state.get("patterns",       {}) or {}
        ecology       = state.get("ecology",         {}) or {}
        alpha_context = state.get("alpha_context",  {}) or {}
        regime_avg_q  = rl.get("regime_avg_q",      {}) or {}

        # ── Raw scalars ────────────────────────────────────────────────────────
        q_values       = rl.get("q_values",     []) or []
        q_velocities   = rl.get("q_velocities", []) or []
        rl_total       = max(rl.get("total_contexts", 0) or 0, 0)
        rl_toxic       = rl.get("toxic_count",   0) or 0
        explore_rate   = float(rl.get("explore_ratio", 0.0) or 0.0)
        rl_profitable  = float(rl.get("profitable_pct", 0.0) or 0.0)

        nm_count       = negmem.get("count", {}) or {}
        nm_total       = max(nm_count.get("total", 0) or 0, 0)
        nm_permanent   = nm_count.get("permanent", 0) or 0
        negmem_density = (nm_permanent / nm_total * 100) if nm_total > 0 else 0.0

        pat_total      = max(patterns.get("total_patterns", 0) or 0, 0)
        pat_formed     = patterns.get("formed_patterns", 0) or 0
        pat_form_rate  = (pat_formed / pat_total * 100) if pat_total > 0 else 0.0

        q_entropy_val  = _q_entropy(q_values)
        avg_q_velocity = (mean(q_velocities) if q_velocities else 0.0)

        cognitive_compression = (nm_total / max(rl_total, 1) * 100) if rl_total > 0 else 0.0

        # ── Plasticity & Fossilization ─────────────────────────────────────────
        plasticity    = _plasticity_score(q_entropy_val, negmem_density, avg_q_velocity, explore_rate)
        fossilization = _fossilization_risk(negmem_density, q_entropy_val, avg_q_velocity, explore_rate)

        memory_pressure = {
            "negmem_permanent_count":      nm_permanent,
            "negmem_total_count":          nm_total,
            "negmem_density_pct":          round(negmem_density, 1),
            "pattern_total":               pat_total,
            "pattern_formed":              pat_formed,
            "pattern_formation_rate_pct":  round(pat_form_rate, 1),
            "q_entropy_bits":              q_entropy_val,
            "q_values_sampled":            len(q_values),
            "avg_q_velocity":              round(avg_q_velocity, 6),
            "rl_total_contexts":           rl_total,
            "rl_toxic_count":              rl_toxic,
            "exploration_rate_pct":        round(explore_rate * 100, 1),
            "cognitive_compression_ratio": round(cognitive_compression, 1),
            "plasticity":                  plasticity,
            "fossilization_risk":          fossilization,
        }

        # ── Drift pairs ────────────────────────────────────────────────────────
        pair_rl_negmem  = _drift_rl_negmem(rl, negmem)
        pair_rl_pattern = _drift_rl_pattern(rl, patterns)
        pair_rl_ecology = _drift_rl_ecology(rl, ecology, regime_avg_q)
        pair_pat_negmem = _drift_pattern_negmem(patterns, negmem)
        pair_ac_rl      = _drift_alpha_context_rl(alpha_context, rl)

        ontology_drift = {
            "RL_vs_NegMem":       pair_rl_negmem,
            "RL_vs_Pattern":      pair_rl_pattern,
            "RL_vs_Ecology":      pair_rl_ecology,
            "Pattern_vs_NegMem":  pair_pat_negmem,
            "AlphaContext_vs_RL": pair_ac_rl,
        }

        # ── Drift heatmap ──────────────────────────────────────────────────────
        heatmap = sorted(
            [
                {
                    "pair":       name,
                    "drift_score": m.get("drift_score", 0.0),
                    "tier":        m.get("tier", "ALIGNED"),
                }
                for name, m in ontology_drift.items()
                if "drift_score" in m
            ],
            key=lambda x: x["drift_score"],
            reverse=True,
        )

        # ── Summary stats ──────────────────────────────────────────────────────
        drift_scores = [h["drift_score"] for h in heatmap]
        summary_stats = {
            "total_pairs": len(drift_scores),
            "avg_drift":   round(mean(drift_scores), 1) if drift_scores else 0.0,
            "max_drift":   max(drift_scores) if drift_scores else 0.0,
            "min_drift":   min(drift_scores) if drift_scores else 0.0,
        }

        # ── Classification ─────────────────────────────────────────────────────
        cognitive_state = _classify_cognitive_state(
            negmem_density         = negmem_density,
            pattern_formation_rate = pat_form_rate,
            max_drift              = summary_stats["max_drift"],
            avg_drift              = summary_stats["avg_drift"],
            fossilization_score    = fossilization["score"],
            plasticity_score       = plasticity["score"],
            negmem_total           = nm_total,
            rl_total_contexts      = rl_total,
            explore_rate           = explore_rate,
            avg_q_velocity         = avg_q_velocity,
        )

        return {
            "scope_note":      SCOPE,
            "cognitive_state": cognitive_state,
            "memory_pressure": memory_pressure,
            "ontology_drift":  ontology_drift,
            "drift_heatmap":   heatmap,
            "summary_stats":   summary_stats,
        }

    except Exception as exc:
        return {
            "scope_note": SCOPE,
            "error":      str(exc),
        }
