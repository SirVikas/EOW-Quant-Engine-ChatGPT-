"""GAP-07: Performance Ranker — ranks PHOENIX performance vs benchmarks."""
from __future__ import annotations

import time
from typing import Dict, Any, List

from loguru import logger


class PerformanceRanker:
    """Ranks PHOENIX performance vs benchmarks using lazy-loaded peer comparison data."""

    def rank(self) -> List[Dict[str, Any]]:
        from core.benchmarking.peer_comparison_tracker import peer_comparison_tracker
        records = peer_comparison_tracker.all_records()
        sorted_records = sorted(records, key=lambda r: r.outperformance_pct, reverse=True)
        return [
            {
                "benchmark_name": r.benchmark_name,
                "phoenix_sharpe": r.phoenix_sharpe,
                "benchmark_sharpe": r.benchmark_sharpe,
                "phoenix_vs_benchmark": r.outperformance_pct,
                "period": r.period,
            }
            for r in sorted_records
        ]

    def percentile_rank(self) -> float:
        from core.benchmarking.peer_comparison_tracker import peer_comparison_tracker
        records = peer_comparison_tracker.all_records()
        if not records:
            return 50.0
        outperforming = sum(1 for r in records if r.outperformance_pct > 0)
        return round(outperforming / len(records) * 100, 2)


performance_ranker = PerformanceRanker()
