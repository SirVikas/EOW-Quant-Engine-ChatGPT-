"""FTD-AIL-001: Trend Engine — metric trending over time."""
from __future__ import annotations


def compute_trend(history: list[float]) -> str:
    """Returns 'RISING', 'FALLING', or 'STABLE' given a list of values (oldest first)."""
    if len(history) < 3:
        return "STABLE"
    first_half = history[:len(history) // 2]
    second_half = history[len(history) // 2:]
    avg_first  = sum(first_half) / len(first_half)
    avg_second = sum(second_half) / len(second_half)
    delta = avg_second - avg_first
    if abs(avg_first) < 1e-9:
        return "STABLE"
    pct_change = delta / abs(avg_first)
    if pct_change > 0.05:
        return "RISING"
    if pct_change < -0.05:
        return "FALLING"
    return "STABLE"
