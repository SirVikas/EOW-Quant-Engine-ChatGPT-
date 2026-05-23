"""
F.7 Adaptive Equilibrium Orchestrator.

Synthesizes F.1–F.6 into a single equilibrium verdict.
Lineage format: EQ-{ts_ms}-{sha256[:16]}

Tiers:
  BALANCED   ≥ 80  — system is in mathematical equilibrium
  ADAPTING   ≥ 60  — adjusting, within controllable deviation
  STRESSED   ≥ 40  — measurable capital stress, action warranted
  CRITICAL   < 40  — equilibrium broken, capital at structural risk

Pure function — no I/O, no side effects, fail-open, import-safe.
"""
from __future__ import annotations
import hashlib, time
from typing import List

from core.adaptive_equilibrium.kelly_efficiency_engine      import compute_kelly_efficiency
from core.adaptive_equilibrium.drawdown_dynamics_engine     import compute_drawdown_dynamics
from core.adaptive_equilibrium.return_consistency_engine    import compute_return_consistency
from core.adaptive_equilibrium.capital_utilization_engine   import compute_capital_utilization
from core.adaptive_equilibrium.equilibrium_band_engine      import compute_equilibrium_band
from core.adaptive_equilibrium.discipline_cost_engine       import compute_discipline_cost

# Score contributions per sub-engine (total = 100)
_WEIGHTS = {
    "kelly":       20,   # capital sizing efficiency
    "drawdown":    20,   # drawdown control
    "consistency": 20,   # return consistency
    "utilization": 15,   # capital utilization
    "band":        15,   # equilibrium band
    "discipline":  10,   # discipline cost
}

_KELLY_SCORES       = {"OPTIMAL": 20,    "ADEQUATE": 14,    "SUBOPTIMAL": 8,    "NEGLIGENT": 0}
_DRAWDOWN_SCORES    = {"STABLE": 20,     "RECOVERING": 16,  "DETERIORATING": 8, "CRITICAL": 0}
_CONSISTENCY_SCORES = {"CONSISTENT": 20, "ADEQUATE": 14,    "VARIABLE": 8,      "ERRATIC": 0}
_UTIL_SCORES        = {"EFFICIENT": 15,  "ADEQUATE": 10,    "UNDERUTILIZED": 5, "OVEREXTENDED": 2}
_BAND_SCORES        = {"IN_BAND": 15,    "APPROACHING": 10, "OUTSIDE_BAND": 5,  "FAR_OUTSIDE": 0}
_COST_SCORES        = {"COST_MINIMAL": 10, "COST_MODERATE": 7, "COST_SIGNIFICANT": 3, "COST_SEVERE": 0}


def run_adaptive_equilibrium(trades: List[dict]) -> dict:
    ts_ms = int(time.time() * 1000)
    try:
        f1 = compute_kelly_efficiency(trades)
        f2 = compute_drawdown_dynamics(trades)
        f3 = compute_return_consistency(trades)
        f4 = compute_capital_utilization(trades)
        f5 = compute_equilibrium_band(trades)
        f6 = compute_discipline_cost(trades)

        score = (
            _KELLY_SCORES.get(f1.get("state", "NEGLIGENT"), 0) +
            _DRAWDOWN_SCORES.get(f2.get("state", "CRITICAL"), 0) +
            _CONSISTENCY_SCORES.get(f3.get("state", "ERRATIC"), 0) +
            _UTIL_SCORES.get(f4.get("state", "OVEREXTENDED"), 0) +
            _BAND_SCORES.get(f5.get("state", "FAR_OUTSIDE"), 0) +
            _COST_SCORES.get(f6.get("state", "COST_SEVERE"), 0)
        )

        tier = (
            "BALANCED"  if score >= 80 else
            "ADAPTING"  if score >= 60 else
            "STRESSED"  if score >= 40 else
            "CRITICAL"
        )

        payload  = f"EQ|{ts_ms}|{score}|{tier}"
        lineage_id = "EQ-" + str(ts_ms) + "-" + hashlib.sha256(payload.encode()).hexdigest()[:16]

        primary_concern = _primary_concern(f1, f2, f3, f4, f5, f6)

        return {
            "engine":             "F.7_ADAPTIVE_EQUILIBRIUM",
            "lineage_id":         lineage_id,
            "equilibrium_score":  score,
            "equilibrium_tier":   tier,
            "trade_count":        len(trades),
            "sub_engine_states": {
                "f1_kelly":       f1.get("state"),
                "f2_drawdown":    f2.get("state"),
                "f3_consistency": f3.get("state"),
                "f4_utilization": f4.get("state"),
                "f5_band":        f5.get("state"),
                "f6_discipline":  f6.get("state"),
            },
            "sub_engine_scores": {
                "kelly_score":       _KELLY_SCORES.get(f1.get("state", "NEGLIGENT"), 0),
                "drawdown_score":    _DRAWDOWN_SCORES.get(f2.get("state", "CRITICAL"), 0),
                "consistency_score": _CONSISTENCY_SCORES.get(f3.get("state", "ERRATIC"), 0),
                "utilization_score": _UTIL_SCORES.get(f4.get("state", "OVEREXTENDED"), 0),
                "band_score":        _BAND_SCORES.get(f5.get("state", "FAR_OUTSIDE"), 0),
                "discipline_score":  _COST_SCORES.get(f6.get("state", "COST_SEVERE"), 0),
            },
            "primary_concern":    primary_concern,
            "diagnostic_only":    True,
            "auto_authorized":    False,
            "lineage_preserved":  True,
        }
    except Exception as exc:
        ts_ms = int(time.time() * 1000)
        return {
            "engine": "F.7_ADAPTIVE_EQUILIBRIUM", "equilibrium_tier": "CRITICAL",
            "equilibrium_score": 0, "error": str(exc),
            "diagnostic_only": True, "auto_authorized": False, "lineage_preserved": True,
        }


def get_equilibrium_health() -> dict:
    """Lightweight boot-time health check — returns tier without full computation."""
    return {
        "subsystem":  "adaptive_equilibrium",
        "phase":      "F",
        "status":     "operational",
        "engines":    ["F.1", "F.2", "F.3", "F.4", "F.5", "F.6", "F.7"],
        "endpoints":  [
            "/api/equilibrium/kelly",
            "/api/equilibrium/drawdown",
            "/api/equilibrium/consistency",
            "/api/equilibrium/utilization",
            "/api/equilibrium/band",
            "/api/equilibrium/discipline-cost",
            "/api/equilibrium/orchestration",
        ],
    }


def _primary_concern(f1, f2, f3, f4, f5, f6) -> str:
    """Return the sub-engine with the worst contribution."""
    concerns = [
        (_KELLY_SCORES.get(f1.get("state", "NEGLIGENT"), 0),       20, "kelly_efficiency"),
        (_DRAWDOWN_SCORES.get(f2.get("state", "CRITICAL"), 0),     20, "drawdown_dynamics"),
        (_CONSISTENCY_SCORES.get(f3.get("state", "ERRATIC"), 0),   20, "return_consistency"),
        (_UTIL_SCORES.get(f4.get("state", "OVEREXTENDED"), 0),     15, "capital_utilization"),
        (_BAND_SCORES.get(f5.get("state", "FAR_OUTSIDE"), 0),      15, "equilibrium_band"),
        (_COST_SCORES.get(f6.get("state", "COST_SEVERE"), 0),      10, "discipline_cost"),
    ]
    # Worst = largest gap between max possible and actual score
    worst = max(concerns, key=lambda x: x[1] - x[0])
    return worst[2]
