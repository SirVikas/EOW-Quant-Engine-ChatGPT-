"""
FTD-REGIME-SURVIV: Adaptive Economic Regime Mapping & Survivability Cartography.

Pure analytics — no I/O, no side effects, no execution authority.

Maps economic survivability across the multidimensional state-space of:
  regime × timeframe × session × exploration state × ontology alignment

Shadow TF projections reuse core.timeframe_economics.project_trade_to_tf.

Ontology state is derived from exploration_origin.was_exploration_trade as
the best available proxy: exploit trades follow the main RL path (ALIGNED),
exploration trades override it (EXPLORATION_OVERRIDE). Direct NegativeMemory
conflict data is not embedded in TradeRecord — cross-reference with the
exploration-diagnostics endpoint for that level of detail.

All classification results are research overlays only — not execution authorities.
"""
from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Callable, Dict, List, Optional, Set

from core.economic_truth import compute_economic_ground_truth
from core.timeframe_economics import project_trade_to_tf, TF_MULTIPLIERS

# ── Research category labels ──────────────────────────────────────────────────
ALPHA_DESERT          = "ALPHA_DESERT"           # no cell scores >= threshold
MICROSTRUCTURE_TRAP   = "MICROSTRUCTURE_TRAP"    # fails at 1m, survives at higher TF
SESSION_ALPHA_POCKET  = "SESSION_ALPHA_POCKET"   # localized to specific session
REGIME_ALPHA_CLUSTER  = "REGIME_ALPHA_CLUSTER"   # localized to specific regime
EXPLORATION_DEPENDENT = "EXPLORATION_DEPENDENT"  # exploration trades outperform exploit
STABLE_ALPHA_REGION   = "STABLE_ALPHA_REGION"    # broad survivability across dimensions

# ── Diagnostic thresholds ─────────────────────────────────────────────────────
MIN_CELL_TRADES      = 3     # minimum trades for a meaningful cell
SURVIVABILITY_THRESH = 50    # score >= this = survivable cell
TF_IMPROVEMENT_THRESH = 35   # shadow TF score >= this = meaningful improvement


# ── Dimension extractors ──────────────────────────────────────────────────────

def _get_regime(trade: dict) -> str:
    return trade.get("regime", "UNKNOWN") or "UNKNOWN"


def _get_explore_type(trade: dict) -> str:
    eo = trade.get("exploration_origin") or {}
    return eo.get("explore_type", "UNKNOWN") if isinstance(eo, dict) else "UNKNOWN"


def _get_ontology_state(trade: dict) -> str:
    """
    Proxy for ontology alignment derived from exploration provenance.

    ALIGNED             = trade followed RL's main execution path (was_exploration_trade=False).
    EXPLORATION_OVERRIDE = trade overrode normal flow (RULE1_UCB or RULE4_MIN_EXPLORE);
                          these are the trades most likely to conflict with NegativeMemory.
    UNKNOWN             = no exploration_origin data (legacy DataLake records).
    """
    eo = trade.get("exploration_origin") or {}
    if not isinstance(eo, dict):
        return "UNKNOWN"
    was_explore = eo.get("was_exploration_trade")
    if was_explore is None:
        return "UNKNOWN"
    return "EXPLORATION_OVERRIDE" if was_explore else "ALIGNED"


# ── Cell analytics ────────────────────────────────────────────────────────────

def _cell_metrics(subset: List[dict], multiplier: int = 1) -> dict:
    """
    Compute survivability metrics for a trade subset at a given TF multiplier.

    Returns a note dict (with trade_count) when subset is below MIN_CELL_TRADES.
    Fail-open: any computation error returns a partial dict.
    """
    count = len(subset)
    if count < MIN_CELL_TRADES:
        return {
            "trade_count": count,
            "note":        f"Insufficient data (< {MIN_CELL_TRADES} trades)",
        }

    projected = (
        [project_trade_to_tf(t, multiplier) for t in subset]
        if multiplier != 1
        else subset
    )

    try:
        full = compute_economic_ground_truth(projected)
    except Exception as exc:
        return {"trade_count": count, "error": str(exc)}

    geo  = full.get("payoff_geometry",       {})
    surv = full.get("survivability_score",   {})
    fdd  = full.get("fee_drag_distribution", {})

    cb_count = sum(1 for t in subset if t.get("crossed_session_boundary", False))

    return {
        "trade_count":             count,
        "net_expectancy":          full.get("net_expectancy"),
        "fee_drag_mean_pct":       fdd.get("mean"),
        "survivability_score":     surv.get("score"),
        "survivability_tier":      surv.get("tier"),
        "win_rate_pct":            geo.get("fee_adjusted_win_rate_pct"),
        "payoff_asymmetry":        geo.get("payoff_asymmetry_ratio"),
        "cross_boundary_rate_pct": round(cb_count / count * 100, 1),
        "is_shadow":               multiplier != 1,
        "shadow_multiplier":       multiplier,
    }


# ── 2D matrix builders ────────────────────────────────────────────────────────

def _matrix_1d(
    trades: List[dict],
    key_fn: Callable[[dict], str],
    multiplier: int = 1,
) -> dict:
    """Group trades by key_fn; return {key: cell_metrics}."""
    groups: Dict[str, List[dict]] = defaultdict(list)
    for t in trades:
        groups[key_fn(t)].append(t)
    return {k: _cell_metrics(v, multiplier) for k, v in sorted(groups.items())}


def _regime_tf_matrix(trades: List[dict]) -> dict:
    """
    For each regime: cell metrics at 1m (actual) and 5m/15m (shadow).
    Primary matrix for "does alpha survive regime × TF interaction?"
    """
    groups: Dict[str, List[dict]] = defaultdict(list)
    for t in trades:
        groups[_get_regime(t)].append(t)

    result: dict = {}
    for regime, subset in sorted(groups.items()):
        result[regime] = {
            tf: _cell_metrics(subset, mult)
            for tf, mult in TF_MULTIPLIERS.items()
        }
    return result


def _regime_session_matrix(trades: List[dict]) -> dict:
    """For each regime × session: actual 1m cell metrics."""
    groups: Dict[str, Dict[str, List[dict]]] = defaultdict(lambda: defaultdict(list))
    for t in trades:
        groups[_get_regime(t)][t.get("origin_session", "UNKNOWN") or "UNKNOWN"].append(t)

    return {
        regime: {sess: _cell_metrics(subset) for sess, subset in sorted(sessions.items())}
        for regime, sessions in sorted(groups.items())
    }


def _ontology_regime_matrix(trades: List[dict]) -> dict:
    """
    For each ontology state × regime: 1m cell metrics.
    Shows whether ALIGNED vs EXPLORATION_OVERRIDE trades perform differently per regime.
    """
    groups: Dict[str, Dict[str, List[dict]]] = defaultdict(lambda: defaultdict(list))
    for t in trades:
        groups[_get_ontology_state(t)][_get_regime(t)].append(t)

    return {
        state: {regime: _cell_metrics(subset) for regime, subset in sorted(regimes.items())}
        for state, regimes in sorted(groups.items())
    }


# ── Heatmap engine ────────────────────────────────────────────────────────────

def _heatmap_entries(trades: List[dict]) -> List[dict]:
    """
    Generate (session, TF, regime) → survivability_score entries.

    Groups trades by (session, regime) first, then projects to each TF.
    Only cells with >= MIN_CELL_TRADES trades are included.
    Sorted by score descending.
    """
    base_groups: Dict[tuple, List[dict]] = defaultdict(list)
    for t in trades:
        regime  = _get_regime(t)
        session = t.get("origin_session", "UNKNOWN") or "UNKNOWN"
        base_groups[(session, regime)].append(t)

    entries: List[dict] = []
    for (session, regime), subset in base_groups.items():
        if len(subset) < MIN_CELL_TRADES:
            continue
        for tf_label, mult in TF_MULTIPLIERS.items():
            m = _cell_metrics(subset, mult)
            if "note" in m or "error" in m:
                continue
            score = m.get("survivability_score")
            if score is None:
                continue
            entries.append({
                "region":            f"{session} + {tf_label} + {regime}",
                "session":           session,
                "timeframe":         tf_label,
                "regime":            regime,
                "score":             score,
                "tier":              m.get("survivability_tier"),
                "net_expectancy":    m.get("net_expectancy"),
                "fee_drag_mean_pct": m.get("fee_drag_mean_pct"),
                "win_rate_pct":      m.get("win_rate_pct"),
                "payoff_asymmetry":  m.get("payoff_asymmetry"),
                "trade_count":       len(subset),
                "is_shadow":         mult != 1,
            })

    return sorted(entries, key=lambda x: x["score"], reverse=True)


# ── Regime-transition survivability ──────────────────────────────────────────

def _regime_transition_survivability(trades: List[dict]) -> dict:
    """
    Identify trades immediately following a regime change and compare their
    economics to stable-regime trades.

    Transition proxy: a trade's regime differs from the previous trade's regime
    in chronological order. Requires min MIN_CELL_TRADES in each group.
    """
    sorted_trades = sorted(trades, key=lambda t: t.get("entry_ts", 0))

    transition_trades: List[dict] = []
    stable_trades:     List[dict] = []
    prev_regime: Optional[str] = None

    for t in sorted_trades:
        regime = _get_regime(t)
        if (prev_regime is not None
                and prev_regime != "UNKNOWN"
                and regime != "UNKNOWN"
                and regime != prev_regime):
            transition_trades.append(t)
        else:
            stable_trades.append(t)
        prev_regime = regime

    result: dict = {
        "transition_trade_count": len(transition_trades),
        "stable_trade_count":     len(stable_trades),
    }
    if len(transition_trades) >= MIN_CELL_TRADES:
        result["transition_metrics"] = _cell_metrics(transition_trades)
    else:
        result["transition_note"] = (
            f"Insufficient regime-transition trades (< {MIN_CELL_TRADES}). "
            "Regime transitions may be rare or regime field unpopulated."
        )
    if len(stable_trades) >= MIN_CELL_TRADES:
        result["stable_metrics"] = _cell_metrics(stable_trades)

    return result


# ── Cartography classification ────────────────────────────────────────────────

def classify_cartography(heatmap: List[dict], explore_matrix: dict) -> str:
    """
    Classify the overall alpha landscape into one of 6 research categories.

    Priority (best → worst):
      STABLE_ALPHA_REGION   broad survivability (≥5 cells, ≥2 sessions, ≥2 regimes)
      MICROSTRUCTURE_TRAP   1m fails, higher TF survives
      REGIME_ALPHA_CLUSTER  only one regime survives (others present but not survivable)
      SESSION_ALPHA_POCKET  only one session survives (others present but not survivable)
      EXPLORATION_DEPENDENT exploration expectancy positive, exploit not survivable
      ALPHA_DESERT          no survivable cell at any dimension

    Research category only — not an execution authority.
    """
    survivable = [h for h in heatmap if (h.get("score") or 0) >= SURVIVABILITY_THRESH]

    all_regimes  = {h["regime"]  for h in heatmap}
    all_sessions = {h["session"] for h in heatmap}

    if not survivable:
        any_tf_improvement = any(
            (h.get("score") or 0) >= TF_IMPROVEMENT_THRESH
            and h.get("timeframe") in ("5m", "15m")
            for h in heatmap
        )
        return MICROSTRUCTURE_TRAP if any_tf_improvement else ALPHA_DESERT

    # 1m survivable locations
    survivable_1m_pairs = {
        (h["session"], h["regime"])
        for h in survivable if h.get("timeframe") == "1m"
    }
    survivable_higher_pairs = {
        (h["session"], h["regime"])
        for h in survivable if h.get("timeframe") in ("5m", "15m")
    }

    if not survivable_1m_pairs and survivable_higher_pairs:
        return MICROSTRUCTURE_TRAP

    survivable_sessions = {h["session"] for h in survivable if h.get("timeframe") == "1m"}
    survivable_regimes  = {h["regime"]  for h in survivable if h.get("timeframe") == "1m"}

    # Broad survivability check
    broad = (
        len(survivable) >= 5
        and len(survivable_sessions) >= 2
        and len(survivable_regimes)  >= 2
    )
    if broad:
        return STABLE_ALPHA_REGION

    # Regime localization
    if survivable_regimes and len(survivable_regimes) == 1 and len(all_regimes) > 1:
        return REGIME_ALPHA_CLUSTER

    # Session localization
    if survivable_sessions and len(survivable_sessions) == 1 and len(all_sessions) > 1:
        return SESSION_ALPHA_POCKET

    # Exploration dependence
    exploit_score = (explore_matrix.get("EXPLOIT", {}).get("survivability_score") or 0)
    r4_score      = (explore_matrix.get("RULE4_MIN_EXPLORE", {}).get("survivability_score") or 0)
    r1_score      = (explore_matrix.get("RULE1_UCB", {}).get("survivability_score") or 0)
    best_explore  = max(r4_score, r1_score)
    if best_explore >= SURVIVABILITY_THRESH and exploit_score < SURVIVABILITY_THRESH:
        return EXPLORATION_DEPENDENT

    # Survivable cells exist — default to session pocket (most common narrow case)
    return SESSION_ALPHA_POCKET


# ── Main entry point ──────────────────────────────────────────────────────────

def compute_regime_survivability_cartography(trades: List[dict]) -> dict:
    """
    Full economic regime survivability cartography for a portfolio of closed trades.

    Generates multidimensional survivability maps across:
      regime × timeframe (with shadow TF projections)
      regime × session
      exploration state (RULE1_UCB / RULE4_MIN_EXPLORE / EXPLOIT)
      ontology state (ALIGNED / EXPLORATION_OVERRIDE)
      regime × session × TF heatmap

    Returns structured cartography dict. Never raises.
    """
    SCOPE = (
        "FTD-REGIME-SURVIV: Research instrumentation only — non-governing. "
        "Maps economic survivability across regime × session × timeframe × exploration state. "
        "Shadow 5m/15m projections assume proportional gross PnL scaling with constant fees. "
        "Ontology state derived from exploration_origin as proxy for NegMem alignment. "
        "Not an execution authority. All decisions at developer discretion."
    )

    try:
        if not trades:
            return {"scope_note": SCOPE, "total_trades": 0, "note": "No trades recorded yet."}

        # 1. Per-regime economics at 1m (actual)
        regime_matrix = _matrix_1d(trades, _get_regime)

        # 2. Regime × TF (1m actual + 5m/15m shadow)
        regime_tf_matrix = _regime_tf_matrix(trades)

        # 3. Regime × Session (1m actual)
        regime_session_matrix = _regime_session_matrix(trades)

        # 4. Exploration dependence (per explore_type at 1m)
        exploration_matrix = _matrix_1d(trades, _get_explore_type)

        # 5. Ontology alignment × regime
        ontology_regime_matrix = _ontology_regime_matrix(trades)

        # 6. NY session — per regime at all TFs
        ny_trades = [t for t in trades if t.get("origin_session", "") == "NY"]
        ny_regime_matrix = (
            _regime_tf_matrix(ny_trades) if ny_trades else {"note": "No NY trades"}
        )

        # 7. Rule4 per-regime analysis
        rule4_trades = [t for t in trades if _get_explore_type(t) == "RULE4_MIN_EXPLORE"]
        rule4_regime_matrix = (
            _matrix_1d(rule4_trades, _get_regime)
            if rule4_trades else {"note": "No Rule4 trades"}
        )

        # 8. Heatmap (session × TF × regime)
        heatmap = _heatmap_entries(trades)

        # 9. Regime-transition survivability
        regime_transition = _regime_transition_survivability(trades)

        # 10. Cartography category
        category = classify_cartography(heatmap, exploration_matrix)

        # 11. Alpha regions (top and bottom)
        alpha_persistence_regions = heatmap[:10]
        alpha_desert_regions      = sorted(heatmap, key=lambda x: x["score"])[:5]

        return {
            "scope_note":               SCOPE,
            "total_trades":             len(trades),
            "cartography_category":     category,
            "regime_matrix":            regime_matrix,
            "regime_tf_matrix":         regime_tf_matrix,
            "regime_session_matrix":    regime_session_matrix,
            "exploration_dependence":   exploration_matrix,
            "ontology_regime_matrix":   ontology_regime_matrix,
            "ny_regime_analysis":       ny_regime_matrix,
            "rule4_regime_analysis":    rule4_regime_matrix,
            "survivability_heatmap":    heatmap,
            "alpha_persistence_regions": alpha_persistence_regions,
            "alpha_desert_regions":     alpha_desert_regions,
            "regime_transition_survivability": regime_transition,
        }

    except Exception as exc:
        return {
            "scope_note":   SCOPE,
            "total_trades": len(trades) if isinstance(trades, list) else 0,
            "error":        str(exc),
        }
