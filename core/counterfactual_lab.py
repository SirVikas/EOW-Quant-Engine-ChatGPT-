"""
FTD-CIL: Protected Counterfactual Intervention Laboratory & Adaptive Replay Sandbox.

Pure analytics — no I/O, no side effects, no execution authority.

Simulates hypothetical adaptive interventions against historical trade streams
in a fully isolated sandbox. Each intervention is a deterministic, read-only
policy applied to the caller-supplied trade list — no production state is
ever read or written.

Hard non-mutation rule:
  DO NOT enable self-modifying production logic, automatic adaptive routing,
  or autonomous intervention based on these outputs.
  Not an execution authority. All decisions at developer discretion.

Isolation guarantee: this module contains zero live engine imports. All
operations are pure transformations on the caller-supplied trade list.
"""
from __future__ import annotations

from statistics import mean
from typing import Callable, Dict, List, Optional

from core.economic_truth import compute_economic_ground_truth
from core.timeframe_economics import project_trade_to_tf
from core.memory_pressure_analytics import _q_entropy

# ── Research category labels ──────────────────────────────────────────────────
BENEFICIAL_ADAPTATION  = "BENEFICIAL_ADAPTATION"   # genuine survivability improvement
COSMETIC_STABILITY     = "COSMETIC_STABILITY"       # metrics cleaner, economics unchanged
OPPORTUNITY_COLLAPSE   = "OPPORTUNITY_COLLAPSE"     # fewer trades, no real edge
FRAGILE_OPTIMIZATION   = "FRAGILE_OPTIMIZATION"     # local gains only
ONTOLOGY_STABILIZATION = "ONTOLOGY_STABILIZATION"   # drift materially reduced
COGNITIVE_OVERFITTING  = "COGNITIVE_OVERFITTING"    # replay policy harms plasticity
INSUFFICIENT_DATA      = "INSUFFICIENT_DATA"        # not enough trades for replay

# ── Classification thresholds ─────────────────────────────────────────────────
MIN_REPLAY_TRADES        = 5
OPP_COLLAPSE_THRESHOLD   = -40.0   # % trade count reduction → OPPORTUNITY_COLLAPSE
BENEFICIAL_NE_DELTA      = 0.0001  # min net expectancy improvement for BENEFICIAL
OPP_DENSITY_WARN         = -20.0   # % — if opp drops more than this, can't be BENEFICIAL
ONTOLOGY_STAB_THRESHOLD  = -15.0   # drift reduction ≥ this → ONTOLOGY_STABILIZATION
PLASTICITY_DROP_THRESHOLD = -20.0  # plasticity drop ≤ this → COGNITIVE_OVERFITTING


# ── Trade field helpers ───────────────────────────────────────────────────────

def _is_exploration(trade: dict) -> bool:
    eo = trade.get("exploration_origin") or {}
    return bool(eo.get("was_exploration_trade") if isinstance(eo, dict) else False)


def _compute_implied_fee(trade: dict) -> float:
    """
    Total fee from explicit fee fields; falls back to gross-net difference for
    legacy DataLake records that predate the fee decomposition.
    """
    fee_entry = float(trade.get("fee_entry",     0.0) or 0.0)
    fee_exit  = float(trade.get("fee_exit",      0.0) or 0.0)
    slippage  = float(trade.get("slippage_cost", 0.0) or 0.0)
    borrow    = float(trade.get("borrow_cost",   0.0) or 0.0)
    total     = fee_entry + fee_exit + slippage + borrow
    if total > 0.0:
        return total
    gross = float(trade.get("gross_pnl") or 0.0)
    net   = float(trade.get("net_pnl")   or 0.0)
    return max(0.0, gross - net)


def _gross_fee_rate(trade: dict) -> float:
    """Return fee-to-|gross| ratio. Returns 0.0 when gross is zero."""
    gross = abs(float(trade.get("gross_pnl") or 0.0))
    if gross == 0.0:
        return 0.0
    return _compute_implied_fee(trade) / gross


# ── Intervention filter / transform functions ─────────────────────────────────

def _apply_negmem_soft_decay(trades: List[dict]) -> List[dict]:
    """
    Simulate softer NegMem: keep profitable exploit trades + all exploration trades.
    Proxy: faster NegMem learning blocks unprofitable exploit patterns before they run.
    """
    return [
        t for t in trades
        if _is_exploration(t) or (t.get("net_pnl") or 0.0) > 0
    ]


def _apply_rule4_high_explore(trades: List[dict]) -> List[dict]:
    """
    Simulate higher Rule4 floor: replay exploration-flagged trades only.
    Proxy: near-maximum exploration rate engaged throughout the period.
    """
    return [t for t in trades if _is_exploration(t)]


def _apply_ny_only(trades: List[dict]) -> List[dict]:
    """
    Simulate NY-only session routing: replay NY session trades exclusively.
    """
    return [t for t in trades if (t.get("origin_session") or "") == "NY"]


def _apply_tf5_projection(trades: List[dict]) -> List[dict]:
    """
    Simulate 5m timeframe economics: project all trades to 5m shadow PnL.
    Fees held constant; gross PnL scaled ×5. No trade count change.
    """
    return [project_trade_to_tf(t, 5) for t in trades]


def _apply_rl_reset_mean_reverting(trades: List[dict]) -> List[dict]:
    """
    Simulate RL context reset for MEAN_REVERTING regime: exclude those trades.
    Proxy: Q-table cleared for that regime → no routing into mean-reverting setups.
    """
    return [t for t in trades if (t.get("regime") or "") != "MEAN_REVERTING"]


def _apply_session_suppression_asia(trades: List[dict]) -> List[dict]:
    """
    Simulate ASIA session suppression: exclude ASIA session trades.
    """
    return [t for t in trades if (t.get("origin_session") or "") != "ASIA"]


def _apply_ontology_weighting_rl_dominant(trades: List[dict]) -> List[dict]:
    """
    Simulate RL-dominant ontology weighting: replay exploit trades only.
    Proxy: RL context decisions fully override exploration at all times.
    """
    return [t for t in trades if not _is_exploration(t)]


def _apply_ecology_stricter(trades: List[dict]) -> List[dict]:
    """
    Simulate stricter ecology survivability threshold: keep only trades where
    implied fees are ≤50% of gross. Proxy: tighter signal-quality filter.
    """
    return [t for t in trades if _gross_fee_rate(t) <= 0.5]


# ── Intervention profile registry ─────────────────────────────────────────────

INTERVENTION_PROFILES: Dict[str, dict] = {
    "NEGMEM_SOFT_DECAY": {
        "description": (
            "Simulate softer NegMem decay: keep profitable exploit + all exploration trades. "
            "Proxy: NegMem learned faster and blocked unprofitable exploit patterns."
        ),
        "fn": _apply_negmem_soft_decay,
    },
    "RULE4_HIGH_EXPLORE": {
        "description": (
            "Simulate stronger Rule4 floor: replay exploration-flagged trades only. "
            "Proxy: near-maximum exploration rate engaged."
        ),
        "fn": _apply_rule4_high_explore,
    },
    "NY_ONLY_SURVIVABILITY": {
        "description": (
            "Simulate NY-only session routing: replay NY session trades only. "
            "Proxy: all non-NY session routing suppressed."
        ),
        "fn": _apply_ny_only,
    },
    "TF5_SURVIVABILITY_FILTER": {
        "description": (
            "Simulate 5m timeframe economics: project all trades to 5m shadow PnL. "
            "Proxy: PHOENIX operating at 5m rather than 1m granularity. "
            "Fees held constant; gross PnL scaled ×5."
        ),
        "fn": _apply_tf5_projection,
    },
    "RL_RESET_MEAN_REVERTING": {
        "description": (
            "Simulate RL context reset for MEAN_REVERTING regime: exclude those trades. "
            "Proxy: Q-table cleared for mean-reverting context."
        ),
        "fn": _apply_rl_reset_mean_reverting,
    },
    "SESSION_SUPPRESSION_ASIA": {
        "description": (
            "Simulate ASIA session suppression: exclude ASIA session trades. "
            "Proxy: ASIA routing disabled."
        ),
        "fn": _apply_session_suppression_asia,
    },
    "ONTOLOGY_WEIGHTING_RL_DOMINANT": {
        "description": (
            "Simulate RL-dominant ontology weighting: replay exploit trades only. "
            "Proxy: RL context decisions override exploration at all times."
        ),
        "fn": _apply_ontology_weighting_rl_dominant,
    },
    "ECOLOGY_STRICTER": {
        "description": (
            "Simulate stricter ecology survivability threshold: keep only trades where "
            "implied fees ≤50% of gross. Proxy: tighter signal-quality filter."
        ),
        "fn": _apply_ecology_stricter,
    },
}


# ── Proxy metrics ─────────────────────────────────────────────────────────────

def _plasticity_proxy(trades: List[dict]) -> float:
    """
    Shannon entropy of the gross PnL distribution — proxy for belief diversity.
    Higher = more varied outcomes = less converged learning (more plastic).
    """
    vals = [float(t.get("gross_pnl") or 0.0) for t in trades]
    return _q_entropy(vals)


def _ontology_drift_proxy(trades: List[dict]) -> float:
    """
    Absolute divergence between explore and exploit win-rates (0–100 scale).
    Measures whether the two execution paths hold different beliefs about success.
    """
    explore = [t for t in trades if     _is_exploration(t)]
    exploit = [t for t in trades if not _is_exploration(t)]

    def _wr(subset: List[dict]) -> float:
        if not subset:
            return 0.5
        return sum(1 for t in subset if (t.get("net_pnl") or 0.0) > 0) / len(subset)

    return round(abs(_wr(explore) - _wr(exploit)) * 100, 1)


def _exploration_dependence(trades: List[dict]) -> float:
    """Fraction of trades that are exploration-flagged (0–100 scale)."""
    if not trades:
        return 0.0
    return round(sum(1 for t in trades if _is_exploration(t)) / len(trades) * 100, 1)


# ── Trade metric computation ──────────────────────────────────────────────────

def _compute_trade_metrics(trades: List[dict]) -> dict:
    """
    Compute full sandbox economics for a trade subset.
    Returns a note dict (with trade_count) when below MIN_REPLAY_TRADES.
    Fail-open: computation errors return a partial dict.
    """
    count = len(trades)
    if count < MIN_REPLAY_TRADES:
        return {
            "trade_count": count,
            "note":        f"Insufficient replay trades (< {MIN_REPLAY_TRADES})",
        }

    try:
        eco = compute_economic_ground_truth(trades)
    except Exception as exc:
        return {"trade_count": count, "error": str(exc)}

    geo  = eco.get("payoff_geometry",       {}) or {}
    surv = eco.get("survivability_score",   {}) or {}
    fdd  = eco.get("fee_drag_distribution", {}) or {}

    return {
        "trade_count":               count,
        "net_expectancy":            eco.get("net_expectancy"),
        "survivability_score":       surv.get("score"),
        "survivability_tier":        surv.get("tier"),
        "fee_drag_mean_pct":         fdd.get("mean"),
        "win_rate_pct":              geo.get("fee_adjusted_win_rate_pct"),
        "payoff_asymmetry":          geo.get("payoff_asymmetry_ratio"),
        "plasticity_proxy":          _plasticity_proxy(trades),
        "ontology_drift_proxy":      _ontology_drift_proxy(trades),
        "exploration_dependence_pct": _exploration_dependence(trades),
    }


# ── Delta computation ─────────────────────────────────────────────────────────

def _safe_delta(a, b) -> Optional[float]:
    """Return a - b if both numeric, else None."""
    if a is None or b is None:
        return None
    try:
        return round(float(a) - float(b), 6)
    except (TypeError, ValueError):
        return None


def _compute_deltas(baseline: dict, intervention: dict, baseline_count: int) -> dict:
    """
    Compute per-metric deltas: intervention value − baseline value.
    opportunity_density_delta_pct is expressed relative to baseline_count.
    """
    i_count   = intervention.get("trade_count", 0)
    opp_delta = round((i_count - baseline_count) / max(baseline_count, 1) * 100, 1)

    return {
        "net_expectancy_delta":           _safe_delta(intervention.get("net_expectancy"),
                                                      baseline.get("net_expectancy")),
        "survivability_delta":            _safe_delta(intervention.get("survivability_score"),
                                                      baseline.get("survivability_score")),
        "fee_drag_delta":                 _safe_delta(intervention.get("fee_drag_mean_pct"),
                                                      baseline.get("fee_drag_mean_pct")),
        "win_rate_delta":                 _safe_delta(intervention.get("win_rate_pct"),
                                                      baseline.get("win_rate_pct")),
        "plasticity_delta":               _safe_delta(intervention.get("plasticity_proxy"),
                                                      baseline.get("plasticity_proxy")),
        "ontology_drift_delta":           _safe_delta(intervention.get("ontology_drift_proxy"),
                                                      baseline.get("ontology_drift_proxy")),
        "exploration_dependence_delta":   _safe_delta(intervention.get("exploration_dependence_pct"),
                                                      baseline.get("exploration_dependence_pct")),
        "opportunity_density_delta_pct":  opp_delta,
    }


# ── Replay confidence ─────────────────────────────────────────────────────────

def _replay_confidence(original_count: int, intervention_count: int) -> dict:
    """
    Statistical confidence tier based on what fraction of original trades remain.
    """
    if original_count == 0:
        return {"score": 0.0, "tier": "INSUFFICIENT"}
    ratio = intervention_count / original_count * 100
    if ratio >= 80:   tier = "HIGH"
    elif ratio >= 50: tier = "MODERATE"
    elif ratio >= 25: tier = "LOW"
    else:             tier = "INSUFFICIENT"
    return {"score": round(ratio, 1), "tier": tier}


# ── Classification ────────────────────────────────────────────────────────────

def _classify_intervention(
    deltas:  dict,
    i_count: int,
    b_count: int,
) -> str:
    """
    Classify the replay outcome into one of 7 research categories.

    Priority order (checked in sequence):
      INSUFFICIENT_DATA   → too few replay trades
      OPPORTUNITY_COLLAPSE → trade count dropped >40%
      COGNITIVE_OVERFITTING → plasticity proxy degraded significantly
      BENEFICIAL_ADAPTATION → genuine NE + survivability improvement, low opp cost
      ONTOLOGY_STABILIZATION → drift proxy materially reduced
      COSMETIC_STABILITY   → metrics flat or slightly better but NE unchanged
      FRAGILE_OPTIMIZATION → partial improvement (NE or survivability only)
      (default COSMETIC_STABILITY)

    Research label only — not an execution authority.
    """
    if i_count < MIN_REPLAY_TRADES:
        return INSUFFICIENT_DATA

    opp_delta   = deltas.get("opportunity_density_delta_pct") or 0.0
    ne_delta    = deltas.get("net_expectancy_delta")
    surv_delta  = deltas.get("survivability_delta")
    plast_delta = deltas.get("plasticity_delta")
    drift_delta = deltas.get("ontology_drift_delta")

    if opp_delta < OPP_COLLAPSE_THRESHOLD:
        return OPPORTUNITY_COLLAPSE

    if plast_delta is not None and plast_delta < PLASTICITY_DROP_THRESHOLD:
        return COGNITIVE_OVERFITTING

    if (ne_delta   is not None and ne_delta > BENEFICIAL_NE_DELTA
            and surv_delta is not None and surv_delta > 0
            and opp_delta  > OPP_DENSITY_WARN):
        return BENEFICIAL_ADAPTATION

    if drift_delta is not None and drift_delta < ONTOLOGY_STAB_THRESHOLD:
        return ONTOLOGY_STABILIZATION

    if (ne_delta is not None and abs(ne_delta) < BENEFICIAL_NE_DELTA
            and ((surv_delta is not None and surv_delta >= 0)
                 or (deltas.get("fee_drag_delta") or 0.0) < 0)):
        return COSMETIC_STABILITY

    if (ne_delta is not None and ne_delta > 0) or (surv_delta is not None and surv_delta > 0):
        return FRAGILE_OPTIMIZATION

    return COSMETIC_STABILITY


# ── Ranking ───────────────────────────────────────────────────────────────────

def _rank_interventions(interventions: dict) -> List[dict]:
    """
    Sort interventions by net_expectancy_delta descending.
    Interventions with no valid NE delta (INSUFFICIENT_DATA) sort last.
    """
    ranked = []
    for name, data in interventions.items():
        deltas = data.get("deltas", {})
        ne_d   = deltas.get("net_expectancy_delta")
        ranked.append({
            "intervention":                name,
            "net_expectancy_delta":        ne_d,
            "classification":              data.get("classification", ""),
            "opportunity_density_delta_pct": deltas.get("opportunity_density_delta_pct"),
            "survivability_delta":         deltas.get("survivability_delta"),
        })
    ranked.sort(
        key=lambda x: (x["net_expectancy_delta"] is not None, x["net_expectancy_delta"] or -999),
        reverse=True,
    )
    return ranked


# ── Main entry point ──────────────────────────────────────────────────────────

def compute_counterfactual_interventions(trades: List[dict]) -> dict:
    """
    Run all intervention profiles against the historical trade stream.

    For each profile:
      1. Apply the filter/transform (deterministic, never mutates input)
      2. Compute sandbox economics via compute_economic_ground_truth
      3. Compute deltas vs baseline
      4. Classify the outcome into one of 7 research categories
      5. Score replay confidence based on trade retention

    Returns structured dict with baseline, per-intervention results,
    ranking, and aggregate detection flags.

    Isolation guarantee: no live engine state read or written.
    Never raises — fail-open contract.
    """
    SCOPE = (
        "FTD-CIL: Protected Counterfactual Intervention Laboratory. "
        "Research instrumentation only — non-governing. "
        "All interventions are sandbox replay policies on historical DataLake records. "
        "No production state is read or written. No execution behavior is altered. "
        "DO NOT enable self-modifying production logic or autonomous intervention based on "
        "these outputs. Not an execution authority. All decisions at developer discretion."
    )

    try:
        if not trades or not isinstance(trades, list):
            return {
                "scope_note":   SCOPE,
                "total_trades": 0,
                "note":         "No trades provided for replay analysis.",
            }

        baseline_count   = len(trades)
        baseline_metrics = _compute_trade_metrics(trades)

        if "note" in baseline_metrics or "error" in baseline_metrics:
            return {
                "scope_note":   SCOPE,
                "total_trades": baseline_count,
                "note": f"Insufficient baseline trades (< {MIN_REPLAY_TRADES}). "
                        "Replay analysis requires more historical data.",
            }

        results: Dict[str, dict] = {}
        for name, profile in INTERVENTION_PROFILES.items():
            try:
                fn: Callable  = profile["fn"]
                replay        = fn(trades)           # never mutates input
                replay_m      = _compute_trade_metrics(replay)
                replay_count  = replay_m.get("trade_count", 0)

                if "note" in replay_m or "error" in replay_m:
                    deltas = {
                        k: None for k in (
                            "net_expectancy_delta", "survivability_delta",
                            "fee_drag_delta", "win_rate_delta", "plasticity_delta",
                            "ontology_drift_delta", "exploration_dependence_delta",
                        )
                    }
                    deltas["opportunity_density_delta_pct"] = round(
                        (replay_count - baseline_count) / max(baseline_count, 1) * 100, 1
                    )
                else:
                    deltas = _compute_deltas(baseline_metrics, replay_m, baseline_count)

                classification = _classify_intervention(deltas, replay_count, baseline_count)
                confidence     = _replay_confidence(baseline_count, replay_count)

                results[name] = {
                    "description":       profile["description"],
                    "trade_count":       replay_count,
                    "replay_confidence": confidence,
                    "metrics":           replay_m,
                    "deltas":            deltas,
                    "classification":    classification,
                }
            except Exception as exc:
                results[name] = {
                    "description":    profile["description"],
                    "trade_count":    0,
                    "classification": INSUFFICIENT_DATA,
                    "error":          str(exc),
                    "deltas":         {},
                }

        ranking   = _rank_interventions(results)
        top_entry = ranking[0] if ranking else {}
        top_classification = results.get(
            top_entry.get("intervention", ""), {}
        ).get("classification", "")
        top_intervention = (
            top_entry.get("intervention")
            if top_classification not in (INSUFFICIENT_DATA, OPPORTUNITY_COLLAPSE)
            else None
        )

        beneficial_any      = any(r.get("classification") == BENEFICIAL_ADAPTATION  for r in results.values())
        opp_collapse_any    = any(r.get("classification") == OPPORTUNITY_COLLAPSE   for r in results.values())
        ontology_stab_any   = any(r.get("classification") == ONTOLOGY_STABILIZATION for r in results.values())
        cog_overfit_any     = any(r.get("classification") == COGNITIVE_OVERFITTING  for r in results.values())

        return {
            "scope_note":                        SCOPE,
            "total_trades":                      baseline_count,
            "baseline":                          baseline_metrics,
            "interventions":                     results,
            "intervention_ranking":              ranking,
            "top_intervention":                  top_intervention,
            "beneficial_adaptation_detected":    beneficial_any,
            "opportunity_collapse_detected":     opp_collapse_any,
            "ontology_stabilization_detected":   ontology_stab_any,
            "cognitive_overfitting_detected":    cog_overfit_any,
        }

    except Exception as exc:
        return {
            "scope_note": SCOPE,
            "error":      str(exc),
        }
