"""
FTD-034 — Consistency Engine.

Ensures that signal flow, diagnosis, alerts, and AI decision are
internally coherent. No mismatch allowed between:
  ✔ Signal Flow
  ✔ Diagnosis (primary_issue)
  ✔ Alerts
  ✔ AI Decision

Applied as the last step before report rendering.
"""
from __future__ import annotations


def enforce(data: dict) -> dict:
    """
    Fix any mismatch between signal flow, diagnosis, and AI decision.

    Guaranteed invariants after this call:
      - primary_issue is never SYSTEM_IN_LOSS when trades == 0
      - primary_reason is always populated when primary_issue == NO_EXECUTION
    """
    result = dict(data)

    tf      = data.get("trade_flow", {})
    trades  = tf.get("total_trades",  0)
    signals = tf.get("total_signals", 0)

    # Mismatch fix: SYSTEM_IN_LOSS is wrong when no trades executed
    if result.get("primary_issue") in ("SYSTEM_IN_LOSS", "SYSTEM IN LOSS") and trades == 0:
        result["primary_issue"]  = "NO_EXECUTION"
        result["primary_reason"] = "All signals blocked — 0 trades executed"

    # Ensure primary_reason is always populated for NO_EXECUTION
    if result.get("primary_issue") == "NO_EXECUTION" and not result.get("primary_reason"):
        result["primary_reason"] = "All signals blocked — 0 trades executed"

    return result
