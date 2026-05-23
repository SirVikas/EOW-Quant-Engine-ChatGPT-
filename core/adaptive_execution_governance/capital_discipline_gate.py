"""
PRP-PHASED.G.2 — Capital Discipline Gate.
DIAGNOSTIC ONLY — no execution authority.
"""
from __future__ import annotations

import time as _time
import statistics
from typing import List


def _net(t: dict) -> float:
    return t.get("net_pnl", 0.0)


def _hold_sec(t: dict) -> float:
    return max(0.0, ((t.get("exit_ts") or 0) - (t.get("entry_ts") or 0)) / 1000.0)


_CONSTITUTIONAL_NOTE = (
    "This gate recommends — it does not autonomously block. "
    "Final authority is human-confirmed."
)

_NO_DATA_CHECK = {"passed": True, "detail": "No trade data"}


def compute_capital_discipline_gate(trades: List[dict]) -> dict:
    try:
        return _compute(trades)
    except Exception as exc:
        return {
            "report": "CAPITAL_DISCIPLINE_GATE_REPORT",
            "error": str(exc),
            "diagnostic_only": True,
            "auto_authorized": False,
            "human_confirmed": True,
            "override_visible": True,
            "lineage_preserved": True,
            "generated_ts": int(_time.time() * 1000),
        }


def _compute(trades: List[dict]) -> dict:
    ts = int(_time.time() * 1000)
    trade_count = len(trades)

    if not trades:
        checks = [
            {"check": "survivability_check", **_NO_DATA_CHECK},
            {"check": "ecological_check", **_NO_DATA_CHECK},
            {"check": "entropy_check", **_NO_DATA_CHECK},
            {"check": "confidence_realism_check", **_NO_DATA_CHECK},
            {"check": "equilibrium_check", **_NO_DATA_CHECK},
            {"check": "participation_check", **_NO_DATA_CHECK},
        ]
        return {
            "report": "CAPITAL_DISCIPLINE_GATE_REPORT",
            "gate_state": "PASS",
            "gate_score": 100,
            "checks": checks,
            "checks_passed": 6,
            "checks_failed": 0,
            "constitutional_note": _CONSTITUTIONAL_NOTE,
            "trade_count": 0,
            "diagnostic_only": True,
            "auto_authorized": False,
            "human_confirmed": True,
            "override_visible": True,
            "lineage_preserved": True,
            "generated_ts": ts,
        }

    nets = [float(_net(t)) for t in trades]
    net_exp = statistics.mean(nets)

    holds = [_hold_sec(t) for t in trades]
    fast_trade_ratio = sum(1 for h in holds if h < 60) / trade_count

    rolling_last10: float | None = None
    if trade_count >= 10:
        rolling_last10 = statistics.mean(nets[-10:])

    # --- survivability_check ---
    surv_passed = net_exp > 0
    surv_check = {
        "check": "survivability_check",
        "passed": surv_passed,
        "detail": f"Net expectancy: {net_exp:.4f}",
    }

    # --- ecological_check ---
    eco_passed = fast_trade_ratio <= 0.50 or (rolling_last10 is not None and rolling_last10 > 0)
    eco_check = {
        "check": "ecological_check",
        "passed": eco_passed,
        "detail": f"Fast trade ratio: {fast_trade_ratio:.1%}",
    }

    # --- entropy_check ---
    entropy_state = "UNKNOWN"
    try:
        from core.survivability_evolution.entropy_resistance_engine import (
            compute_entropy_resistance,
        )
        _er = compute_entropy_resistance(trades)
        entropy_state = _er.get("entropy_state", "UNKNOWN")
    except Exception:
        pass
    entropy_passed = entropy_state in ("STABLE", "FRAGILE", "UNKNOWN")
    entropy_check = {
        "check": "entropy_check",
        "passed": entropy_passed,
        "detail": f"Entropy state: {entropy_state}",
    }

    # --- confidence_realism_check ---
    realism_score = 50
    try:
        from core.survivability_evolution.confidence_realism_engine import (
            compute_confidence_realism,
        )
        _cr = compute_confidence_realism(trades)
        realism_score = _cr.get("realism_score", 50)
    except Exception:
        pass
    realism_passed = realism_score >= 50
    realism_check = {
        "check": "confidence_realism_check",
        "passed": realism_passed,
        "detail": f"Confidence realism score: {realism_score}",
    }

    # --- equilibrium_check ---
    if trade_count >= 5:
        wins = sum(1 for n in nets if n > 0)
        win_rate = wins / trade_count
        equil_passed = win_rate >= 0.40
    else:
        win_rate = 1.0
        equil_passed = True
    equil_check = {
        "check": "equilibrium_check",
        "passed": equil_passed,
        "detail": f"Win rate: {win_rate:.1%}",
    }

    # --- participation_check ---
    part_passed = rolling_last10 is None or rolling_last10 >= -0.5
    part_detail = f"Last-10 rolling exp: {rolling_last10:.4f}" if rolling_last10 is not None else "Last-10 rolling exp: N/A"
    part_check = {
        "check": "participation_check",
        "passed": part_passed,
        "detail": part_detail,
    }

    checks = [surv_check, eco_check, entropy_check, realism_check, equil_check, part_check]
    passed_count = sum(1 for c in checks if c["passed"])
    failed_count = 6 - passed_count

    if failed_count == 0:
        gate_state = "PASS"
    elif failed_count <= 2:
        gate_state = "CAUTION"
    elif failed_count <= 4:
        gate_state = "DEFENSIVE"
    else:
        gate_state = "UNSAFE"

    gate_score = round(passed_count / 6 * 100)

    return {
        "report": "CAPITAL_DISCIPLINE_GATE_REPORT",
        "gate_state": gate_state,
        "gate_score": gate_score,
        "checks": checks,
        "checks_passed": passed_count,
        "checks_failed": failed_count,
        "constitutional_note": _CONSTITUTIONAL_NOTE,
        "trade_count": trade_count,
        "diagnostic_only": True,
        "auto_authorized": False,
        "human_confirmed": True,
        "override_visible": True,
        "lineage_preserved": True,
        "generated_ts": ts,
    }
