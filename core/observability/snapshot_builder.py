"""
EOW Quant Engine — Snapshot Builder  (FTD-053-GAIA Phase 6)

Safely extracts live trading-engine state into a raw snapshot dict
whose structure matches the intelligence_compressor's _SIGNAL_SCHEMA.

Design principles:
  • ADAPTER-PATTERN  — caller passes engine instances; no direct imports of
                       trading-engine modules, keeping observability isolated
  • INDIVIDUALLY-GUARDED — every field extraction is wrapped in try/except;
                           a broken engine method yields a safe default, not a crash
  • READ-ONLY        — zero mutation of any engine state
  • COMPLETE-AS-POSSIBLE — best-effort: always returns a usable dict even if
                           every engine instance is None

Schema produced (matches intelligence_compressor._SIGNAL_SCHEMA dot-paths):
  session_stats.total_net_pnl     session_stats.n_trades
  session_stats.profit_factor     session_stats.win_rate
  rl.total_contexts               rl.total_trade_decisions
  rl.evolution_state.intelligence_score
  rl.summary_metrics.{toxic_contexts, allow_rate, profitable_pct}
  rl.learning_speed.{maturity_pct, status}
  rl.exploration_pressure.pressure_status
  rl.confidence_trajectory.confidence_direction
  learning.{TRENDING,MEAN_REVERTING,VOLATILITY_EXPANSION}.win_rate
  risk.halted                     gate.can_trade
  trade_flow.{consecutive_losses, daily_trades}
  uptime_secs                     error_count
  regime
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from loguru import logger


# ── Derived-field thresholds ───────────────────────────────────────────────────

_MATURITY_TIERS = [
    (0.80, "MATURE"),
    (0.50, "MATURING"),
    (0.20, "LEARNING"),
    (0.00, "BOOTSTRAPPING"),
]

_EXPLORE_TIERS = [
    (0.70, "HIGH_EXPLORE"),
    (0.40, "BALANCED"),
    (0.20, "EXPLOITING"),
    (0.00, "CONVERGED"),
]


def _safe(fn, default):
    try:
        return fn()
    except Exception:
        return default


def _derive_maturity_status(maturity_pct: float) -> str:
    for threshold, label in _MATURITY_TIERS:
        if maturity_pct >= threshold:
            return label
    return "BOOTSTRAPPING"


def _derive_explore_status(explore_ratio: float) -> str:
    for threshold, label in _EXPLORE_TIERS:
        if explore_ratio >= threshold:
            return label
    return "CONVERGED"


def _derive_confidence_direction(avg_q: float) -> str:
    if avg_q > 0.10:
        return "IMPROVING"
    if avg_q > 0.0:
        return "NEUTRAL"
    return "DECLINING"


def _count_consecutive_losses(trades: List[Any]) -> int:
    from config import cfg
    count = 0
    for trade in reversed(trades):
        pnl = _safe(lambda: float(trade.net_pnl), None)  # noqa: B023
        if pnl is None:
            break
        # Scratch exits (|pnl| ≤ BE epsilon) are excluded — must match the live
        # streak counters in main.py or diagnostics disagree with gating behavior.
        if abs(pnl) <= cfg.BREAKEVEN_EPSILON_USDT:
            continue
        if pnl < 0:
            count += 1
        else:
            break
    return count


def _dominant_regime(regime_det: Any) -> str:
    """Return the most-common confirmed regime across all tracked symbols."""
    try:
        states = regime_det.all_states()
        if not states:
            return "UNKNOWN"
        freq: Dict[str, int] = {}
        for state in states.values():
            r = state.regime.value if hasattr(state.regime, "value") else str(state.regime)
            freq[r] = freq.get(r, 0) + 1
        return max(freq, key=freq.__getitem__)
    except Exception:
        return "UNKNOWN"


# ── Public API ────────────────────────────────────────────────────────────────

def build_raw_snapshot(
    rl_engine=None,
    pnl_calc=None,
    risk_ctrl=None,
    trade_flow_monitor=None,
    learning_engine=None,
    regime_det=None,
    gate_snapshot: Optional[Dict[str, Any]] = None,
    boot_ts: float = 0.0,
    error_count: int = 0,
) -> Dict[str, Any]:
    """
    Build a raw snapshot dict from live engine instances.

    All arguments are optional.  Missing instances yield safe defaults so the
    compressor can still extract whatever fields are available.

    Returns a plain dict — no live references to any engine object.
    Never raises.
    """
    now = time.time()

    # ── session_stats ─────────────────────────────────────────────────────────
    raw_ss = _safe(lambda: dict(pnl_calc.session_stats), {}) if pnl_calc else {}
    session_stats = {
        "total_net_pnl":  _safe(lambda: float(raw_ss.get("total_net_pnl", 0.0)), 0.0),
        "n_trades":       _safe(lambda: int(raw_ss.get("total_trades", 0)), 0),
        "profit_factor":  _safe(lambda: float(raw_ss.get("profit_factor", 0.0)), 0.0),
        "win_rate":       _safe(lambda: float(raw_ss.get("win_rate", 0.0)) / 100.0, 0.0),
    }

    # ── rl engine ─────────────────────────────────────────────────────────────
    rl_summ  = _safe(lambda: rl_engine.summary(), {})            if rl_engine else {}
    rl_evo   = _safe(lambda: rl_engine.get_evolution_state(), {}) if rl_engine else {}

    n_total        = int(rl_evo.get("total_contexts", 0))
    maturity       = rl_evo.get("context_maturity", {})
    mature_count   = int(maturity.get("mature", 0))
    maturity_pct   = (mature_count / n_total) if n_total else 0.0

    learning_dyn   = rl_evo.get("learning_dynamics", {})
    explore_ratio  = float(learning_dyn.get("explore_ratio", 0.0))
    avg_q          = float(learning_dyn.get("avg_q", 0.0))

    rl_block = {
        "total_contexts":      int(rl_summ.get("total_contexts", 0)),
        "total_trade_decisions": int(rl_summ.get("total_pulls", 0)),
        "evolution_state": {
            "intelligence_score": float(rl_evo.get("intelligence_score", 0.0)),
        },
        "summary_metrics": {
            "toxic_contexts": int(rl_summ.get("toxic_contexts", 0)),
            "allow_rate":     float(rl_summ.get("allow_rate", 0.0)),
            "profitable_pct": float(rl_summ.get("profitable_pct", 0.0)),
        },
        "learning_speed": {
            "maturity_pct": round(maturity_pct * 100, 1),
            "status":       _derive_maturity_status(maturity_pct),
        },
        "exploration_pressure": {
            "pressure_status": _derive_explore_status(explore_ratio),
        },
        "confidence_trajectory": {
            "confidence_direction": _derive_confidence_direction(avg_q),
        },
    }

    # ── learning engine ───────────────────────────────────────────────────────
    le_summ   = _safe(lambda: learning_engine.summary(), {})  if learning_engine else {}
    le_regimes = le_summ.get("regimes", {})

    learning_block: Dict[str, Any] = {}
    for regime_key in ("TRENDING", "MEAN_REVERTING", "VOLATILITY_EXPANSION"):
        wr = _safe(
            lambda rk=regime_key: float(le_regimes.get(rk, {}).get("win_rate", 0.0)),
            0.0,
        )
        learning_block[regime_key] = {"win_rate": wr}

    # ── risk / gate ───────────────────────────────────────────────────────────
    risk_block = {
        "halted": _safe(lambda: bool(risk_ctrl.halted), False) if risk_ctrl else False,
    }
    gate_block = {
        "can_trade": _safe(
            lambda: bool(gate_snapshot.get("can_trade", True)),
            True,
        ) if gate_snapshot else (not risk_block["halted"]),
    }

    # ── trade_flow ────────────────────────────────────────────────────────────
    trades       = _safe(lambda: list(pnl_calc.trades), []) if pnl_calc else []
    consec_loss  = _safe(lambda: _count_consecutive_losses(trades), 0)

    today_start  = now - (now % 86400)   # midnight UTC approximation
    daily_trades = _safe(
        lambda: sum(
            1 for t in trades
            if _safe(lambda tr=t: float(getattr(tr, "ts_exit", 0)) / 1000 >= today_start, False)
        ),
        0,
    )

    trade_flow_block = {
        "consecutive_losses": consec_loss,
        "daily_trades":       daily_trades,
    }

    # ── regime ────────────────────────────────────────────────────────────────
    regime = _safe(lambda: _dominant_regime(regime_det), "UNKNOWN") if regime_det else "UNKNOWN"

    # ── assemble ──────────────────────────────────────────────────────────────
    snapshot: Dict[str, Any] = {
        "session_stats": session_stats,
        "rl":            rl_block,
        "learning":      learning_block,
        "risk":          risk_block,
        "gate":          gate_block,
        "trade_flow":    trade_flow_block,
        "uptime_secs":   round(now - boot_ts, 1) if boot_ts > 0 else 0.0,
        "error_count":   int(error_count),
        "regime":        regime,
        "_snapshot_ts":  int(now * 1000),
    }

    return snapshot
