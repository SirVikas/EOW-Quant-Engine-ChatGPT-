"""
PRP-002 Analytics — Exploration Recovery Reports

Generates exploration collapse and recovery cycle forensic reports from:
  - ExplorationRecoveryGovernor (starvation / curiosity / forced recovery)
  - SignalDensityEngine (drought / starvation detection)

Reports produced:
  03_exploration_collapse_monitor
  08_exploration_recovery_cycles

Pure module — no I/O, no side effects. Fail-open on any engine error.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List


def _recovery():
    from core.signal_ecology.exploration_recovery import exploration_recovery_governor
    return exploration_recovery_governor

def _density():
    from core.signal_ecology.signal_density_engine import signal_density_engine
    return signal_density_engine


# ── Individual report generators ──────────────────────────────────────────────

def report_03_exploration_collapse_monitor() -> Dict[str, Any]:
    """
    Exploration collapse monitor: detects current and recent collapse states
    — drought, starvation, rejection-loop, consecutive-block escalation.
    """
    try:
        rec_t = _recovery().get_telemetry()
        den_t = _density().get_telemetry()

        consec_blocks  = rec_t.get("consecutive_blocks", 0)
        drought_sec    = rec_t.get("drought_seconds", 0.0)
        active_cycle   = rec_t.get("active_cycle_id")
        total_rec      = rec_t.get("total_recoveries", 0)
        cooldown_left  = rec_t.get("cooldown_remaining", 0.0)
        is_drought     = den_t.get("is_drought", False)
        is_starvation  = den_t.get("is_starvation", False)
        survival_rate  = den_t.get("survival_rate", 0.0)

        # Collapse severity
        if is_starvation and drought_sec >= 900:
            severity = "CRITICAL"
        elif is_starvation or (drought_sec >= 600):
            severity = "SEVERE"
        elif is_drought or consec_blocks >= 50:
            severity = "MODERATE"
        elif consec_blocks >= 20:
            severity = "MILD"
        else:
            severity = "NONE"

        recent_decisions = rec_t.get("recent_decisions", [])[-15:]
        recovery_active  = rec_t.get("active_cycle_id") is not None

        return {
            "report":              "03_exploration_collapse_monitor",
            "prp":                 "002",
            "collapse_severity":   severity,
            "is_drought":          is_drought,
            "is_starvation":       is_starvation,
            "drought_seconds":     round(drought_sec, 1),
            "consecutive_blocks":  consec_blocks,
            "survival_rate":       survival_rate,
            "recovery_active":     recovery_active,
            "active_cycle_id":     active_cycle,
            "total_recoveries":    total_rec,
            "cooldown_remaining":  round(cooldown_left, 1),
            "recent_decisions":    recent_decisions,
            "generated_ts":        int(time.time() * 1000),
        }
    except Exception as exc:
        return {"report": "03_exploration_collapse_monitor", "prp": "002", "error": str(exc),
                "generated_ts": int(time.time() * 1000)}


def report_08_exploration_recovery_cycles() -> Dict[str, Any]:
    """
    Exploration recovery cycle audit: full history of curiosity and forced
    recovery cycles, with mode distribution and effectiveness assessment.
    """
    try:
        rec_t = _recovery().get_telemetry()

        cycle_log       = rec_t.get("recent_cycles", [])
        decision_log    = rec_t.get("recent_decisions", [])
        total_rec       = rec_t.get("total_recoveries", 0)
        active_cycle    = rec_t.get("active_cycle_id")
        cycle_trades    = rec_t.get("cycle_trade_count", 0)

        # Mode distribution across recent decisions
        modes: Dict[str, int] = {}
        for d in decision_log:
            m = d.get("mode", "NONE")
            modes[m] = modes.get(m, 0) + 1

        # Classify cycles by mode
        curiosity_count = sum(
            1 for e in cycle_log
            if e.get("mode") == "CURIOSITY" and e.get("event") != "CLOSED"
        )
        forced_count = sum(
            1 for e in cycle_log
            if e.get("mode") == "FORCED" and e.get("event") != "CLOSED"
        )
        closed_count = sum(
            1 for e in cycle_log if e.get("event") == "CLOSED"
        )

        # Effectiveness: what fraction of cycles closed with SIGNAL_RECOVERED
        recovered_closes = sum(
            1 for e in cycle_log
            if e.get("event") == "CLOSED" and e.get("reason") == "SIGNAL_RECOVERED"
        )
        recovery_effectiveness = (
            round(recovered_closes / closed_count, 3) if closed_count > 0 else None
        )

        avg_trades_per_cycle = (
            round(cycle_trades / max(1, total_rec - (1 if active_cycle else 0)), 2)
            if total_rec > 0 else 0.0
        )

        return {
            "report":                  "08_exploration_recovery_cycles",
            "prp":                     "002",
            "total_recoveries":        total_rec,
            "active_cycle_id":         active_cycle,
            "trades_in_active_cycle":  cycle_trades,
            "curiosity_activations":   curiosity_count,
            "forced_activations":      forced_count,
            "cycles_closed":           closed_count,
            "recovery_effectiveness":  recovery_effectiveness,
            "avg_trades_per_cycle":    avg_trades_per_cycle,
            "mode_distribution":       modes,
            "cycle_log":               cycle_log[-20:],
            "generated_ts":            int(time.time() * 1000),
        }
    except Exception as exc:
        return {"report": "08_exploration_recovery_cycles", "prp": "002", "error": str(exc),
                "generated_ts": int(time.time() * 1000)}


# ── Bundle API ────────────────────────────────────────────────────────────────

def generate_all_reports() -> Dict[str, Any]:
    """Generate all exploration-side PRP-002 forensic reports as a bundle."""
    return {
        "prp":          "002",
        "module":       "exploration_reports",
        "generated_ts": int(time.time() * 1000),
        "reports": {
            "03_exploration_collapse_monitor": report_03_exploration_collapse_monitor(),
            "08_exploration_recovery_cycles":  report_08_exploration_recovery_cycles(),
        },
    }
