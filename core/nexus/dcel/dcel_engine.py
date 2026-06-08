"""
PHOENIX NEXUS — Decision Capture Expansion Layer (DCEL)
FTD-NEXUS-ACCELERATION-001 Phase-A

Provides named archive functions that record trading-engine decisions into IMRAF.
All functions are fire-and-forget; exceptions are suppressed by callers.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

# Throttle state — only DCEL module uses this; no external write access needed.
_last_rl_archive_ts: float = 0.0

# DCEL hooks capture live runtime events — all records originate here.
_DCEL_SOURCE = "core/nexus/dcel/dcel_engine.py"


def _imraf():
    """Lazy import to prevent circular imports at module load time."""
    from core.institutional_memory.imraf_engine import imraf, Category, Provenance
    return imraf, Category, Provenance


def _dcel_prov(Provenance):
    """Build a standard DCEL provenance object."""
    return Provenance(
        source_file=_DCEL_SOURCE,
        extraction_method="dcel_hook",
        confidence=0.9,  # live runtime capture is high confidence
    )


# ── Archive functions ─────────────────────────────────────────────────────────

def archive_genome_decision(
    strategy_type: str,
    decision: str,
    genome_id: str,
    train_pf: float,
    oos_pf: float,
    avg_r: float,
    win_rate: float,
    cost_drag: float,
    trades: int,
    reason: str,
    dna_keys: List[str],
) -> None:
    im, Category, Provenance = _imraf()
    im.record(
        category=Category.EVOLUTION,
        subcategory=decision,
        title=f"Genome {decision}: {strategy_type} [{genome_id}]",
        data={
            "strategy_type": strategy_type,
            "decision": decision,
            "genome_id": genome_id,
            "train_pf": round(train_pf, 4),
            "oos_pf": round(oos_pf, 4),
            "avg_r": round(avg_r, 4),
            "win_rate": round(win_rate, 4),
            "cost_drag_pct": round(cost_drag, 4),
            "trades": trades,
            "reason": reason,
            "dna_keys": dna_keys,
        },
        tags=["genome", "evolution", decision.lower(), strategy_type.lower()],
        provenance=_dcel_prov(Provenance),
    )


def archive_rsi_adaptation(
    regime: str,
    action: str,
    old_bands: Dict[str, Any],
    new_bands: Dict[str, Any],
    survival_rate: float,
) -> None:
    im, Category, Provenance = _imraf()
    im.record(
        category=Category.EVOLUTION,
        subcategory=f"RSI_{regime}_{action}",
        title=f"RSI Governor adapt: {regime} → {action}",
        data={
            "regime": regime,
            "action": action,
            "old_bands": old_bands,
            "new_bands": new_bands,
            "survival_rate": round(survival_rate, 4),
        },
        tags=["rsi", "adaptation", regime.lower(), action.lower()],
        provenance=_dcel_prov(Provenance),
    )


def archive_lcc_event(
    event_type: str,
    consecutive_losses: int,
    pause_minutes: float = 0,
    symbol: str = "",
) -> None:
    im, Category, Provenance = _imraf()
    im.record(
        category=Category.OPERATIONAL,
        subcategory=f"LCC_{event_type}",
        title=f"LCC {event_type}: {consecutive_losses} consecutive losses",
        data={
            "event_type": event_type,
            "consecutive_losses": consecutive_losses,
            "pause_minutes": pause_minutes,
            "symbol": symbol,
        },
        tags=["lcc", "loss_cluster", event_type.lower()],
        provenance=_dcel_prov(Provenance),
    )


def archive_safe_mode_event(
    action: str,
    reason: str,
    duration_min: float = 0.0,
    score: float = 0.0,
) -> None:
    im, Category, Provenance = _imraf()
    im.record(
        category=Category.OPERATIONAL,
        subcategory=f"SAFE_MODE_{action}",
        title=f"Safe Mode {action}: {reason[:80]}",
        data={
            "action": action,
            "reason": reason,
            "duration_min": duration_min,
            "score": score,
        },
        tags=["safe_mode", action.lower()],
        provenance=_dcel_prov(Provenance),
    )


def archive_scorer_decision(
    symbol: str,
    regime: str,
    score: float,
    threshold: float,
    passed: bool,
    factors: Dict[str, Any],
    strategy: str,
) -> None:
    # Only archive failures or near-misses (within 10 points of threshold)
    near_miss = abs(score - threshold) <= 10
    if passed and not near_miss:
        return

    im, Category, Provenance = _imraf()
    subcategory = "SCORE_PASS" if passed else "SCORE_FAIL"
    label = "NEAR_MISS" if (passed and near_miss) else subcategory
    im.record(
        category=Category.DECISION,
        subcategory=subcategory,
        title=f"Scorer {label}: {symbol} {strategy} score={score:.1f} threshold={threshold:.1f}",
        data={
            "symbol": symbol,
            "regime": regime,
            "score": score,
            "threshold": threshold,
            "passed": passed,
            "near_miss": near_miss,
            "strategy": strategy,
            "factors": factors,
        },
        tags=["scorer", label.lower(), symbol, strategy.lower()],
        provenance=_dcel_prov(Provenance),
    )


def archive_rl_summary(
    total_contexts: int,
    total_pulls: int,
    avg_q: float,
    toxic_count: int,
    eco_toxic_count: int,
    convergence_state: str,
    intelligence_score: float,
) -> None:
    global _last_rl_archive_ts
    now = time.time()
    # Throttle: at most once per 60 seconds
    if now - _last_rl_archive_ts < 60.0:
        return
    _last_rl_archive_ts = now

    im, Category, Provenance = _imraf()
    im.record(
        category=Category.EVOLUTION,
        subcategory="RL_SUMMARY",
        title=f"RL Summary: convergence={convergence_state} intelligence={intelligence_score:.2f}",
        data={
            "total_contexts": total_contexts,
            "total_pulls": total_pulls,
            "avg_q": round(avg_q, 4),
            "toxic_count": toxic_count,
            "eco_toxic_count": eco_toxic_count,
            "convergence_state": convergence_state,
            "intelligence_score": round(intelligence_score, 4),
        },
        tags=["rl", "summary", convergence_state.lower()],
        provenance=_dcel_prov(Provenance),
    )


def archive_regime_transition(
    symbol: str,
    old_regime: str,
    new_regime: str,
    trigger: str,
    session: str,
) -> None:
    im, Category, Provenance = _imraf()
    im.record(
        category=Category.REGIME,
        subcategory=f"{old_regime}→{new_regime}",
        title=f"Regime transition: {symbol} {old_regime}→{new_regime}",
        data={
            "symbol": symbol,
            "old_regime": old_regime,
            "new_regime": new_regime,
            "trigger": trigger,
            "session": session,
        },
        tags=["regime", "transition", symbol, old_regime.lower(), new_regime.lower()],
        provenance=_dcel_prov(Provenance),
    )


def archive_risk_state_change(
    event: str,
    daily_used_pct: float,
    daily_cap_pct: float,
    drawdown_pct: float,
    safe_mode: bool,
    reason: str = "",
) -> None:
    im, Category, Provenance = _imraf()
    im.record(
        category=Category.OPERATIONAL,
        subcategory=event,
        title=f"Risk state: {event} | used={daily_used_pct:.1f}% dd={drawdown_pct:.1f}%",
        data={
            "event": event,
            "daily_used_pct": round(daily_used_pct, 2),
            "daily_cap_pct": round(daily_cap_pct, 2),
            "drawdown_pct": round(drawdown_pct, 2),
            "safe_mode": safe_mode,
            "reason": reason,
        },
        tags=["risk", "state_change", event.lower()],
        provenance=_dcel_prov(Provenance),
    )


# ── Coverage stats ────────────────────────────────────────────────────────────

_DCEL_TARGET = 800  # 500 OPERATIONAL + 200 EVOLUTION + 100 REGIME


def get_coverage_stats() -> Dict[str, Any]:
    """
    Returns per-category DCEL record counts and an estimated coverage percentage
    against the 800-record target (500 OPERATIONAL + 200 EVOLUTION + 100 REGIME).
    """
    im, Category, _ = _imraf()
    stats = im.get_stats()
    by_cat = stats.get("by_category", {})

    operational = by_cat.get("OPERATIONAL", 0)
    evolution   = by_cat.get("EVOLUTION", 0)
    regime      = by_cat.get("REGIME", 0)
    decision    = by_cat.get("DECISION", 0)

    dcel_total = operational + evolution + regime + decision
    coverage_pct = round(min(dcel_total / _DCEL_TARGET * 100, 100.0), 2)

    return {
        "operational": operational,
        "evolution": evolution,
        "regime": regime,
        "decision": decision,
        "dcel_total": dcel_total,
        "target": _DCEL_TARGET,
        "coverage_pct": coverage_pct,
    }
