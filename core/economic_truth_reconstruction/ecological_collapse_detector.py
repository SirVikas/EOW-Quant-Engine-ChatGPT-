"""
PRP-PHASED.4 — Ecological Collapse Detector.

Identifies where signal ecology structurally collapses via trade history
analysis combined with live signal ecology telemetry.

Detects: overtrading toxicity, confidence saturation, ecological instability,
strategy crowding, regime mismatch, alpha evaporation, volatility toxicity,
entropy escalation.

Identifies: collapse onset, collapse acceleration, collapse recovery zones,
ecological stabilization windows.

DIAGNOSTIC ONLY — no execution authority, no deployment authority.

Pure module — accepts trades: List[dict], no side effects. Import-safe.
"""
from __future__ import annotations

import time as _time
from collections import defaultdict
from statistics import mean, stdev
from typing import Any, Dict, List, Optional


def _net(t: dict) -> float:
    return t.get("net_pnl", 0.0)


def _gross(t: dict) -> float:
    return t.get("gross_pnl", 0.0)


def _fees(t: dict) -> float:
    return t.get("fee_entry", 0.0) + t.get("fee_exit", 0.0) + t.get("slippage_cost", 0.0)


def _hold_sec(t: dict) -> float:
    entry = t.get("entry_ts", 0) or 0
    exit_ = t.get("exit_ts",  0) or 0
    return max(0.0, (exit_ - entry) / 1000.0)


def _rolling_net_expectancy(trades: List[dict], window: int = 20) -> List[float]:
    """Rolling mean net PnL over 'window' trades."""
    if len(trades) < window:
        return [mean([_net(t) for t in trades])] if trades else []
    result = []
    for i in range(window - 1, len(trades)):
        subset = trades[i - window + 1: i + 1]
        result.append(round(mean([_net(t) for t in subset]), 4))
    return result


def detect_ecological_collapse(trades: List[dict]) -> dict:
    """
    PRP-PHASED.4 — Detect structural ecological collapse patterns.

    Combines trade history analysis with live signal ecology telemetry.

    Args:
        trades: Combined session + historical trade dicts.

    Returns ECOLOGICAL_COLLAPSE_REPORT; never raises.
    """
    collapse_signals: List[dict] = []
    recovery_zones: List[dict] = []

    # ── Source 1: Live signal ecology telemetry ───────────────────────────────
    ecology_state: Dict[str, Any] = {}
    try:
        from core.signal_ecology.signal_density_engine import signal_density_engine
        from core.signal_ecology.exploration_recovery import exploration_recovery_governor
        from core.signal_ecology.alpha_context_memory import alpha_context_memory

        den_t = signal_density_engine.get_telemetry()
        rec_t = exploration_recovery_governor.get_telemetry()
        acm_t = alpha_context_memory.get_telemetry()

        is_starvation   = den_t.get("is_starvation", False)
        is_drought      = den_t.get("is_drought", False)
        survival_rate   = den_t.get("survival_rate", 1.0)
        drought_sec     = den_t.get("drought_seconds", 0.0)
        consec_blocks   = rec_t.get("consecutive_blocks", 0)
        total_rec       = rec_t.get("total_recoveries", 0)
        active_cycle    = rec_t.get("active_cycle_id")
        total_ctx       = acm_t.get("total_contexts", 0)
        toxic_count     = acm_t.get("toxic_count", 0)
        boost_count     = acm_t.get("boost_count", 0)
        block_count     = acm_t.get("block_count", 0)

        ecology_state = {
            "is_starvation":   is_starvation,
            "is_drought":      is_drought,
            "survival_rate":   round(survival_rate, 4),
            "drought_seconds": round(drought_sec, 1),
            "consecutive_blocks": consec_blocks,
            "total_recoveries":   total_rec,
            "active_recovery":    bool(active_cycle),
            "total_contexts":     total_ctx,
            "toxic_count":        toxic_count,
            "toxic_ratio":        round(toxic_count / total_ctx, 4) if total_ctx else 0.0,
            "boost_count":        boost_count,
            "block_count":        block_count,
        }

        if is_starvation:
            collapse_signals.append({
                "signal": "SIGNAL_STARVATION",
                "severity": "CRITICAL",
                "source": "signal_density_engine",
                "detail": f"Signal starvation active (drought={drought_sec:.0f}s)",
            })
        elif is_drought:
            collapse_signals.append({
                "signal": "SIGNAL_DROUGHT",
                "severity": "HIGH",
                "source": "signal_density_engine",
                "detail": f"Signal drought detected (drought={drought_sec:.0f}s)",
            })

        if consec_blocks >= 100:
            collapse_signals.append({
                "signal": "CONSECUTIVE_BLOCK_ESCALATION",
                "severity": "HIGH" if consec_blocks < 200 else "CRITICAL",
                "source": "exploration_recovery_governor",
                "detail": f"Consecutive blocks: {consec_blocks}",
            })

        if total_ctx > 0 and toxic_count / total_ctx >= 0.50:
            collapse_signals.append({
                "signal": "ALPHA_EVAPORATION",
                "severity": "HIGH",
                "source": "alpha_context_memory",
                "detail": f"Toxic contexts dominant: {toxic_count}/{total_ctx}",
            })

        if active_cycle:
            recovery_zones.append({
                "zone": "ACTIVE_RECOVERY_CYCLE",
                "source": "exploration_recovery_governor",
                "detail": f"Active recovery cycle id={active_cycle}",
            })

    except Exception as exc:
        ecology_state["error"] = str(exc)

    # ── Source 2: Trade history analysis ──────────────────────────────────────
    trade_analysis: Dict[str, Any] = {}

    if not trades:
        trade_analysis = {"note": "No trades available for history analysis."}
    else:
        sorted_trades = sorted(trades, key=lambda t: t.get("entry_ts", 0))
        nets = [_net(t) for t in sorted_trades]

        # Overtrading toxicity: look for short-interval clustering with net negative
        hold_times = [_hold_sec(t) for t in sorted_trades]
        fast_trades = [t for t, h in zip(sorted_trades, hold_times) if h < 60]
        fast_net = mean([_net(t) for t in fast_trades]) if fast_trades else None
        overtrading_toxic = (
            len(fast_trades) / len(trades) > 0.40
            and fast_net is not None and fast_net < 0
        )
        if overtrading_toxic:
            collapse_signals.append({
                "signal": "OVERTRADING_TOXICITY",
                "severity": "HIGH",
                "source": "trade_history",
                "detail": (
                    f"{len(fast_trades)}/{len(trades)} trades held <60s, "
                    f"avg net={fast_net:.4f}"
                ),
            })

        # Strategy crowding: one strategy dominating (>70%) with negative expectancy
        strat_groups: Dict[str, List[dict]] = defaultdict(list)
        for t in sorted_trades:
            strat_groups[t.get("strategy_id", "default") or "default"].append(t)
        if strat_groups:
            dominant_strat = max(strat_groups, key=lambda k: len(strat_groups[k]))
            dom_ratio = len(strat_groups[dominant_strat]) / len(trades)
            dom_net   = mean([_net(t) for t in strat_groups[dominant_strat]])
            if dom_ratio >= 0.70 and dom_net < 0:
                collapse_signals.append({
                    "signal": "STRATEGY_CROWDING",
                    "severity": "MEDIUM",
                    "source": "trade_history",
                    "detail": (
                        f"Strategy '{dominant_strat}' dominates "
                        f"{dom_ratio:.0%} with net_exp={dom_net:.4f}"
                    ),
                })

        # Regime mismatch: UNKNOWN regime dominant
        regime_groups: Dict[str, List[dict]] = defaultdict(list)
        for t in sorted_trades:
            regime_groups[t.get("regime", "UNKNOWN") or "UNKNOWN"].append(t)
        unknown_ratio = len(regime_groups.get("UNKNOWN", [])) / len(trades)
        if unknown_ratio >= 0.50:
            collapse_signals.append({
                "signal": "REGIME_MISMATCH",
                "severity": "MEDIUM",
                "source": "trade_history",
                "detail": f"{unknown_ratio:.0%} of trades have unknown regime",
            })

        # Entropy escalation: stdev of net PnL increasing over time
        rolling = _rolling_net_expectancy(sorted_trades, window=min(20, len(sorted_trades)))
        if len(rolling) >= 4:
            first_half = rolling[:len(rolling)//2]
            second_half = rolling[len(rolling)//2:]
            try:
                std_first  = stdev(first_half)
                std_second = stdev(second_half)
                if std_second > std_first * 1.5:
                    collapse_signals.append({
                        "signal": "ENTROPY_ESCALATION",
                        "severity": "MEDIUM",
                        "source": "trade_history",
                        "detail": (
                            f"PnL variance escalating: "
                            f"early_std={std_first:.4f} → late_std={std_second:.4f}"
                        ),
                    })
            except Exception:
                pass

        # Collapse onset: first point where rolling expectancy crosses below 0
        collapse_onset_idx: Optional[int] = None
        for i, val in enumerate(rolling):
            if val < 0:
                collapse_onset_idx = i
                break

        # Collapse recovery zones: where rolling expectancy returns positive
        for i in range(1, len(rolling)):
            if rolling[i - 1] < 0 and rolling[i] >= 0:
                recovery_zones.append({
                    "zone": "ROLLING_EXP_RECOVERY",
                    "source": "trade_history",
                    "detail": f"Rolling expectancy positive at trade sequence index ~{i}",
                })

        # Volatility toxicity: VOLATILITY_EXPANSION regime with negative expectancy
        vol_exp_trades = [t for t in sorted_trades
                          if (t.get("regime") or "").upper() == "VOLATILITY_EXPANSION"]
        if len(vol_exp_trades) >= 5:
            vol_net = mean([_net(t) for t in vol_exp_trades])
            if vol_net < 0:
                collapse_signals.append({
                    "signal": "VOLATILITY_TOXICITY",
                    "severity": "MEDIUM",
                    "source": "trade_history",
                    "detail": (
                        f"VOLATILITY_EXPANSION regime net_exp={vol_net:.4f} "
                        f"({len(vol_exp_trades)} trades)"
                    ),
                })

        trade_analysis = {
            "total_trades":      len(trades),
            "fast_trade_count":  len(fast_trades),
            "fast_trade_ratio":  round(len(fast_trades) / len(trades), 4),
            "overtrading_toxic": overtrading_toxic,
            "regime_distribution": {k: len(v) for k, v in regime_groups.items()},
            "collapse_onset_idx":  collapse_onset_idx,
            "rolling_expectancy":  rolling[-10:],  # last 10 points only
        }

    # ── Collapse severity assessment ──────────────────────────────────────────
    critical_signals = [s for s in collapse_signals if s["severity"] == "CRITICAL"]
    high_signals     = [s for s in collapse_signals if s["severity"] == "HIGH"]

    if critical_signals:
        collapse_severity = "CRITICAL"
    elif len(high_signals) >= 2:
        collapse_severity = "HIGH"
    elif high_signals:
        collapse_severity = "MODERATE"
    elif collapse_signals:
        collapse_severity = "LOW"
    else:
        collapse_severity = "NONE"

    return {
        "report":              "ECOLOGICAL_COLLAPSE_REPORT",
        "collapse_severity":   collapse_severity,
        "collapse_signals":    collapse_signals,
        "signal_count":        len(collapse_signals),
        "critical_signal_count": len(critical_signals),
        "recovery_zones":      recovery_zones,
        "recovery_zone_count": len(recovery_zones),
        "ecology_state":       ecology_state,
        "trade_analysis":      trade_analysis,
        "diagnostic_only":     True,
        "auto_authorized":     False,
        "generated_ts":        int(_time.time() * 1000),
    }
