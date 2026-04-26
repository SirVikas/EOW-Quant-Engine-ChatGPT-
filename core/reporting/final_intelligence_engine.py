"""
FTD-034 — Final Intelligence Engine.

Applies NO_EXECUTION override, root-cause priority resolution, and
gate-trace injection as the final step in the reporting pipeline.

Pipeline position:
    raw
    → truth_engine.process()
    → intelligence_layer.enrich()
    → final_intelligence_engine.apply()   ← this module
    → consistency_engine.enforce()
    → generate_report()
"""
from __future__ import annotations

_PRIORITY = [
    "NO_EXECUTION",
    "NEGATIVE_NET_EDGE",
    "GATE_BLOCK",
    "RISK_BLOCK",
    "STRATEGY_WEAKNESS",
]


def _resolve_priority(data: dict) -> str:
    current = str(data.get("primary_issue", ""))
    for p in _PRIORITY:
        if p in current.upper():
            return p
    return current or "UNKNOWN"


def apply(data: dict) -> dict:
    """
    FTD-034 final intelligence pass.

    Rules (applied in order):
      1. NO_EXECUTION override — when signals > 0 and trades == 0, force
         primary_issue to NO_EXECUTION regardless of what earlier layers set.
      2. Priority resolution — primary_issue must match canonical priority order.
      3. Gate trace injection — surface dominant_block info in alerts_enriched.
    """
    result = dict(data)

    tf      = data.get("trade_flow", {})
    signals = tf.get("total_signals", 0)
    trades  = tf.get("total_trades",  0)

    # Rule 1 — NO_EXECUTION override (mandatory)
    if signals > 0 and trades == 0:
        result["primary_issue"]  = "NO_EXECUTION"
        result["primary_reason"] = "All signals blocked — 0 trades executed"
        result["severity"]       = "CRITICAL"

    # Rule 2 — single primary based on priority
    result["primary_issue"] = _resolve_priority(result)

    # Rule 3 — gate trace injection into alerts_enriched
    gate       = data.get("gate", {})
    gate_trace = data.get("gate_trace", {})
    existing   = data.get("alerts_enriched", {})

    result["alerts_enriched"] = {
        "can_trade": gate_trace.get(
            "can_trade", gate.get("can_trade", existing.get("can_trade", False))
        ),
        "reason": gate_trace.get(
            "reason", gate.get("reason", existing.get("reason", "UNKNOWN"))
        ),
        "dominant_block": gate_trace.get(
            "top_3_failures", existing.get("dominant_block", [])
        ),
    }

    return result
