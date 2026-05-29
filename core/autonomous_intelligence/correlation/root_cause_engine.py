"""FTD-AIL-001: Root Cause Engine — cross-report pattern detection."""
from __future__ import annotations
from typing import Any


def detect_patterns(snapshots: dict[str, Any]) -> list[dict]:
    """Detect cross-report correlations and return list of pattern dicts."""
    patterns = []

    perf = snapshots.get("Performance Status", {})
    obs  = snapshots.get("Observability", {})
    rec  = snapshots.get("Recovery Cycle Audit", {})

    avg_win  = perf.get("avg_win_run", 0)
    avg_loss = perf.get("avg_loss_run", 0)
    anomalies = obs.get("anomaly_count", 0)

    # Micro-profit compression pattern
    if avg_win > 0 and avg_loss > avg_win * 3 and anomalies > 0:
        patterns.append({
            "pattern": "MICRO_PROFIT_COMPRESSION",
            "sources": ["Performance Status", "Observability"],
            "description": f"avg_win_run={avg_win:.3f}, avg_loss_run={avg_loss:.3f}, anomalies={anomalies}",
            "severity": "HIGH",
        })

    # Recovery loop risk
    consecutive = rec.get("consecutive_blocks", 0)
    if consecutive and consecutive > 30 and avg_loss > avg_win * 2:
        patterns.append({
            "pattern": "RECOVERY_LOOP_RISK",
            "sources": ["Recovery Cycle Audit", "Performance Status"],
            "description": f"consecutive_blocks={consecutive}, loss/win ratio={avg_loss/avg_win:.1f}",
            "severity": "HIGH",
        })

    return patterns
