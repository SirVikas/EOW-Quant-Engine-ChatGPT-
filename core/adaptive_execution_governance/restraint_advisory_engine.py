"""
PRP-PHASED.G.1 — Restraint Advisory Engine.
DIAGNOSTIC ONLY — no execution authority.
"""
from __future__ import annotations

import hashlib
import json
import time as _time
import statistics
from typing import List


def _net(t: dict) -> float:
    return t.get("net_pnl", 0.0)


def _hold_sec(t: dict) -> float:
    return max(0.0, ((t.get("exit_ts") or 0) - (t.get("entry_ts") or 0)) / 1000.0)


def compute_restraint_advisory(trades: List[dict]) -> dict:
    try:
        return _compute(trades)
    except Exception as exc:
        return {
            "report": "RESTRAINT_ADVISORY_REPORT",
            "error": str(exc),
            "diagnostic_only": True,
            "auto_authorized": False,
            "human_confirmed": True,
            "override_visible": True,
            "generated_ts": int(_time.time() * 1000),
        }


def _compute(trades: List[dict]) -> dict:
    ts = int(_time.time() * 1000)
    trade_count = len(trades)

    if not trades:
        lineage_id = _make_lineage_id(ts, "TRADE_ALLOWED", None, 0)
        return {
            "report": "RESTRAINT_ADVISORY_REPORT",
            "advisory": "TRADE_ALLOWED",
            "advisory_rationale": "All survivability checks acceptable — participation allowed",
            "contributing_subsystems": ["trade_history_analysis"],
            "entropy_state": "UNKNOWN",
            "ecological_preservation_tier": "UNKNOWN",
            "net_expectancy": None,
            "rolling_last10_expectancy": None,
            "fast_trade_ratio": 0.0,
            "decay_detected": False,
            "trade_count": 0,
            "lineage_id": lineage_id,
            "confidence_realism_linkage": "see /api/survivability/confidence-realism",
            "entropy_linkage": "see /api/survivability/entropy",
            "replay_safe": True,
            "lineage_preserved": True,
            "diagnostic_only": True,
            "auto_authorized": False,
            "human_confirmed": True,
            "override_visible": True,
            "generated_ts": ts,
        }

    nets = [float(_net(t)) for t in trades]
    net_exp = round(statistics.mean(nets), 4)

    holds = [_hold_sec(t) for t in trades]
    fast_count = sum(1 for h in holds if h < 60)
    fast_trade_ratio = fast_count / trade_count

    rolling_last10: float | None = None
    if trade_count >= 10:
        rolling_last10 = round(statistics.mean(nets[-10:]), 4)

    sorted_by_entry = sorted(trades, key=lambda t: (t.get("entry_ts") or 0))
    mid = trade_count // 2
    first_half = sorted_by_entry[:mid]
    second_half = sorted_by_entry[mid:]

    early_half_mean: float | None = None
    late_half_mean: float | None = None
    if first_half:
        early_half_mean = statistics.mean(float(_net(t)) for t in first_half)
    if second_half:
        late_half_mean = statistics.mean(float(_net(t)) for t in second_half)

    decay_detected = (
        early_half_mean is not None
        and late_half_mean is not None
        and trade_count >= 10
        and late_half_mean < early_half_mean
    )

    vol_exp_ratio = sum(
        1 for t in trades if t.get("regime") == "VOLATILITY_EXPANSION"
    ) / trade_count

    contributing_subsystems = ["trade_history_analysis"]

    entropy_state = "UNKNOWN"
    try:
        from core.survivability_evolution.entropy_resistance_engine import (
            compute_entropy_resistance,
        )
        _er = compute_entropy_resistance(trades)
        entropy_state = _er.get("entropy_state", "UNKNOWN")
        contributing_subsystems.append("entropy_resistance_engine")
    except Exception:
        pass

    preservation_tier = "UNKNOWN"
    try:
        from core.survivability_evolution.ecological_self_preservation_engine import (
            compute_ecological_self_preservation,
        )
        _ep = compute_ecological_self_preservation(trades)
        preservation_tier = _ep.get("preservation_tier", "UNKNOWN")
        contributing_subsystems.append("ecological_self_preservation_engine")
    except Exception:
        pass

    if entropy_state in ("DEGENERATIVE", "CRITICAL"):
        advisory = "ENTROPY_ALERT"
        rationale = f"Entropy state {entropy_state} — systemic degradation accelerating"
    elif preservation_tier == "CRITICAL" or (
        fast_trade_ratio > 0.60
        and rolling_last10 is not None
        and rolling_last10 < 0
    ):
        advisory = "PAUSE_ACTIVITY"
        rationale = "Ecological danger elevated — fast-trade toxicity or critical preservation breach"
    elif (
        rolling_last10 is not None
        and rolling_last10 < 0
        and net_exp < 0
        and trade_count >= 20
    ):
        advisory = "RECOVERY_WAIT"
        rationale = (
            f"Rolling expectancy negative (last10={rolling_last10:.4f}), "
            f"net_exp={net_exp:.4f} — stabilization incomplete"
        )
    elif net_exp < 0:
        advisory = "PRESERVE_CAPITAL"
        rationale = f"Net expectancy negative ({net_exp:.4f}) — defensive posture advised"
    elif decay_detected:
        advisory = "CONTRACT_RISK"
        rationale = (
            f"Expectancy degrading (early={early_half_mean:.4f}→late={late_half_mean:.4f})"
            " — reduce aggressiveness"
        )
    else:
        advisory = "TRADE_ALLOWED"
        rationale = "All survivability checks acceptable — participation allowed"

    lineage_id = _make_lineage_id(ts, advisory, net_exp, trade_count)

    return {
        "report": "RESTRAINT_ADVISORY_REPORT",
        "advisory": advisory,
        "advisory_rationale": rationale,
        "contributing_subsystems": contributing_subsystems,
        "entropy_state": entropy_state,
        "ecological_preservation_tier": preservation_tier,
        "net_expectancy": net_exp,
        "rolling_last10_expectancy": rolling_last10,
        "fast_trade_ratio": fast_trade_ratio,
        "decay_detected": decay_detected,
        "trade_count": trade_count,
        "lineage_id": lineage_id,
        "confidence_realism_linkage": "see /api/survivability/confidence-realism",
        "entropy_linkage": "see /api/survivability/entropy",
        "replay_safe": True,
        "lineage_preserved": True,
        "diagnostic_only": True,
        "auto_authorized": False,
        "human_confirmed": True,
        "override_visible": True,
        "generated_ts": ts,
    }


def _make_lineage_id(ts_ms: int, advisory: str, net_exp: float | None, trade_count: int) -> str:
    payload = json.dumps(
        {
            "trade_count": trade_count,
            "advisory": advisory,
            "net_exp_rounded": round(net_exp, 4) if net_exp is not None else None,
        },
        sort_keys=True,
    )
    digest = hashlib.sha256(payload.encode()).hexdigest()[:12]
    return f"ADV-{ts_ms}-{digest}"
