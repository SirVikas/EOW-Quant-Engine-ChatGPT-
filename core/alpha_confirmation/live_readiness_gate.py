"""
I.6 Live Readiness Gate.

Constitutional hard gate — synthesizes I.1–I.5 into a binary readiness verdict.

Rules:
  - BLOCKED if ANY engine is in a critical fail state
  - CONDITIONAL if all pass but at least one is not at highest confidence
  - READY_FOR_CONSIDERATION if all engines at highest tier

CRITICAL: even READY_FOR_CONSIDERATION does NOT authorize live trading.
It means the evidence base is sufficient for a human to begin due diligence.
live_deployment_authorized is ALWAYS False — this flag cannot be overridden.

Pure function — no I/O, no side effects, fail-open, import-safe.
"""
from __future__ import annotations
import hashlib, time
from typing import List

# States that block live consideration entirely
_BLOCKING_STATES = {
    "I.1_STATISTICAL_SIGNIFICANCE": {"NO_EDGE"},
    "I.2_OOS_VALIDATION":           {"OOS_FAILURE"},
    "I.3_FEE_SURVIVAL":             {"FEE_DESTROYED"},
    "I.4_REGIME_ROBUSTNESS":        {"FRAGILE"},
    "I.5_DRAWDOWN_TOLERANCE":       {"DISQUALIFYING"},
}

# States at highest confidence per engine
_HIGHEST_STATES = {
    "I.1_STATISTICAL_SIGNIFICANCE": "PROVEN",
    "I.2_OOS_VALIDATION":           "OOS_CONSISTENT",
    "I.3_FEE_SURVIVAL":             "FEE_CERTIFIED",
    "I.4_REGIME_ROBUSTNESS":        "ROBUST",
    "I.5_DRAWDOWN_TOLERANCE":       "DEPLOYMENT_READY",
}


def compute_live_readiness(sub_results: List[dict]) -> dict:
    ts_ms = int(time.time() * 1000)
    try:
        blocks      = []
        all_highest = True
        gate_checks = {}

        for result in sub_results:
            engine = result.get("engine", "UNKNOWN")
            state  = result.get("state", "")
            blocking = _BLOCKING_STATES.get(engine, set())
            highest  = _HIGHEST_STATES.get(engine, "")

            is_blocked = state in blocking
            is_highest = state == highest

            if is_blocked:
                blocks.append(f"{engine}: {state}")
            if not is_highest:
                all_highest = False

            gate_checks[engine] = {
                "state": state, "blocked": is_blocked, "at_highest": is_highest,
            }

        if blocks:
            gate_status = "BLOCKED"
        elif all_highest:
            gate_status = "READY_FOR_CONSIDERATION"
        else:
            # Check if any are in intermediate states (not blocked, not highest)
            any_inadequate = any(
                not v["blocked"] and not v["at_highest"]
                for v in gate_checks.values()
            )
            gate_status = "CONDITIONAL" if any_inadequate else "READY_FOR_CONSIDERATION"

        blocking_reasons = blocks if blocks else []

        # Insufficient data check
        any_insufficient = any(
            r.get("insufficient_data") or r.get("min_required") for r in sub_results
        )
        if any_insufficient and gate_status != "BLOCKED":
            gate_status = "INSUFFICIENT_DATA"

        payload    = f"I6|{ts_ms}|{gate_status}|{len(blocks)}"
        lineage_id = "ALPHA-I6-" + hashlib.sha256(payload.encode()).hexdigest()[:12]

        return {
            "engine":                    "I.6_LIVE_READINESS_GATE",
            "lineage_id":                lineage_id,
            "gate_status":               gate_status,
            "blocking_reasons":          blocking_reasons,
            "gate_checks":               gate_checks,
            "all_engines_at_highest":    all_highest,
            # Constitutional invariant — cannot be overridden at any tier
            "live_deployment_authorized":False,
            "human_confirmation_required":True,
            "diagnostic_only":           True,
            "auto_authorized":           False,
            "lineage_preserved":         True,
        }
    except Exception as exc:
        return {
            "engine": "I.6_LIVE_READINESS_GATE", "gate_status": "BLOCKED",
            "error": str(exc), "live_deployment_authorized": False,
            "human_confirmation_required": True, "diagnostic_only": True,
            "auto_authorized": False, "lineage_preserved": True,
        }
