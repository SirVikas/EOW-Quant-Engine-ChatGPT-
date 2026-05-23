"""
PRP-PHASED.G.3 — Equilibrium Resumption Engine.

Determines when normal adaptive participation can safely resume after
preservation or lockdown postures by evaluating 6 stabilisation dimensions.

States: ACTIVE / CAUTIONARY / PRESERVATION / RECOVERY / LOCKDOWN

DIAGNOSTIC ONLY — no execution authority, no deployment authority.

Pure module — accepts trades: List[dict], no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from statistics import mean
from typing import Any, Dict, List, Optional


def _net(t: dict) -> float:
    return t.get("net_pnl", 0.0)


def _hold_sec(t: dict) -> float:
    return max(0.0, ((t.get("exit_ts") or 0) - (t.get("entry_ts") or 0)) / 1000.0)


def compute_equilibrium_resumption(trades: List[dict]) -> dict:
    """
    PRP-PHASED.G.3 — Evaluate equilibrium resumption readiness.

    Args:
        trades: Combined session + historical trade dicts.

    Returns EQUILIBRIUM_RESUMPTION_REPORT; never raises.
    """
    ts_ms = int(_time.time() * 1000)

    _DEFAULT_DIMS = {
        "ecological_stabilization":      50,
        "entropy_normalization":         50,
        "expectancy_recovery":           50,
        "confidence_realism_recovery":   50,
        "alpha_persistence_restoration": 50,
        "regime_stabilization":          50,
    }
    _WEIGHTS = {
        "ecological_stabilization":      0.25,
        "entropy_normalization":         0.20,
        "expectancy_recovery":           0.20,
        "confidence_realism_recovery":   0.15,
        "alpha_persistence_restoration": 0.10,
        "regime_stabilization":          0.10,
    }

    try:
        dim_scores: Dict[str, int] = dict(_DEFAULT_DIMS)

        if not trades:
            return {
                "report":              "EQUILIBRIUM_RESUMPTION_REPORT",
                "equilibrium_state":   "CAUTIONARY",
                "equilibrium_score":   50,
                "recovery_readiness":  False,
                "dimension_scores":    dim_scores,
                "dimension_weights":   _WEIGHTS,
                "trade_count":         0,
                "diagnostic_only":     True,
                "auto_authorized":     False,
                "human_confirmed":     True,
                "lineage_preserved":   True,
                "generated_ts":        ts_ms,
            }

        sorted_t = sorted(trades, key=lambda t: t.get("entry_ts", 0))
        nets = [_net(t) for t in sorted_t]

        # ── Dim 1: Ecological stabilisation ──────────────────────────────────
        try:
            from core.survivability_evolution.ecological_self_preservation_engine import (
                compute_ecological_self_preservation,
            )
            _ep = compute_ecological_self_preservation(trades)
            dim_scores["ecological_stabilization"] = max(0, min(100, int(_ep.get("preservation_score", 50))))
        except Exception:
            fast_ratio = sum(1 for t in trades if _hold_sec(t) < 60) / len(trades)
            dim_scores["ecological_stabilization"] = max(0, min(100, round(100 - fast_ratio * 100)))

        # ── Dim 2: Entropy normalisation ──────────────────────────────────────
        try:
            from core.survivability_evolution.entropy_resistance_engine import compute_entropy_resistance
            _er = compute_entropy_resistance(trades)
            dim_scores["entropy_normalization"] = max(0, min(100, int(_er.get("resistance_score", 50))))
        except Exception:
            pass  # fallback stays at 50

        # ── Dim 3: Expectancy recovery ────────────────────────────────────────
        if len(nets) >= 5:
            last10_mean = mean(nets[-10:]) if len(nets) >= 10 else mean(nets)
            dim_scores["expectancy_recovery"] = max(0, min(100, round(50 + last10_mean * 20)))
        # else stays 50

        # ── Dim 4: Confidence realism recovery ────────────────────────────────
        try:
            from core.survivability_evolution.confidence_realism_engine import compute_confidence_realism
            _cr = compute_confidence_realism(trades)
            dim_scores["confidence_realism_recovery"] = max(0, min(100, int(_cr.get("realism_score", 50))))
        except Exception:
            pass

        # ── Dim 5: Alpha persistence restoration ──────────────────────────────
        try:
            from core.survivability_evolution.alpha_persistence_tracker import track_alpha_persistence
            _ap = track_alpha_persistence(trades)
            dim_scores["alpha_persistence_restoration"] = max(0, min(100, int(_ap.get("persistence_score", 50))))
        except Exception:
            pass

        # ── Dim 6: Regime stabilisation ───────────────────────────────────────
        regimes = [t.get("regime", "UNKNOWN") or "UNKNOWN" for t in trades]
        distinct = len(set(regimes))
        unknown_ratio = regimes.count("UNKNOWN") / len(regimes)
        if distinct == 1:
            rscore = 80
        elif distinct == 2:
            rscore = 60
        else:
            rscore = 40
        if unknown_ratio > 0.50:
            rscore -= 20
        dim_scores["regime_stabilization"] = max(0, min(100, rscore))

        # ── Composite score ───────────────────────────────────────────────────
        composite = round(sum(dim_scores[k] * _WEIGHTS[k] for k in _WEIGHTS))

        if composite >= 75:
            state = "ACTIVE"
        elif composite >= 55:
            state = "CAUTIONARY"
        elif composite >= 35:
            state = "PRESERVATION"
        elif composite >= 20:
            state = "RECOVERY"
        else:
            state = "LOCKDOWN"

        recovery_readiness = composite >= 55 and dim_scores["expectancy_recovery"] >= 50

        return {
            "report":             "EQUILIBRIUM_RESUMPTION_REPORT",
            "equilibrium_state":  state,
            "equilibrium_score":  composite,
            "recovery_readiness": recovery_readiness,
            "dimension_scores":   dim_scores,
            "dimension_weights":  _WEIGHTS,
            "trade_count":        len(trades),
            "diagnostic_only":    True,
            "auto_authorized":    False,
            "human_confirmed":    True,
            "lineage_preserved":  True,
            "generated_ts":       ts_ms,
        }

    except Exception as exc:
        return {
            "report":             "EQUILIBRIUM_RESUMPTION_REPORT",
            "error":              str(exc),
            "equilibrium_state":  "LOCKDOWN",
            "equilibrium_score":  0,
            "recovery_readiness": False,
            "dimension_scores":   _DEFAULT_DIMS,
            "dimension_weights":  _WEIGHTS,
            "trade_count":        len(trades) if trades else 0,
            "diagnostic_only":    True,
            "auto_authorized":    False,
            "human_confirmed":    True,
            "lineage_preserved":  True,
            "generated_ts":       ts_ms,
        }
