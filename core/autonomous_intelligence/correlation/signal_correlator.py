"""FTD-AIL-001: Signal Correlator — cross-signal correlation across report families."""
from __future__ import annotations
from typing import Any


def correlate(snapshots: dict[str, Any]) -> list[dict]:
    """Return list of correlated signal dicts from multiple report sources."""
    correlations = []

    genome  = snapshots.get("Genome Exposure Audit", {})
    perf    = snapshots.get("Performance Status", {})
    promo   = snapshots.get("Promotion Watch", {})

    exec_rate = genome.get("execution_rate", 1.0)
    win_rate  = perf.get("win_rate", 1.0)
    promoted  = promo.get("total_promoted", -1)
    cycles    = promo.get("total_cycles", 0)

    if exec_rate < 0.1 and win_rate < 0.5:
        correlations.append({
            "type": "GENOME_EXECUTION_WIN_RATE_COLLAPSE",
            "sources": ["Genome Exposure Audit", "Performance Status"],
            "exec_rate": exec_rate,
            "win_rate": win_rate,
            "severity": "HIGH",
        })

    if promoted == 0 and cycles > 100:
        correlations.append({
            "type": "ZERO_PROMOTIONS_HIGH_CYCLES",
            "sources": ["Promotion Watch"],
            "total_promoted": promoted,
            "total_cycles": cycles,
            "severity": "MEDIUM",
        })

    return correlations
