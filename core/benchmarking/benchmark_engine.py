"""GAP-07: Benchmark Engine — master benchmarking aggregator."""
from __future__ import annotations

import time
from typing import Dict, Any

from loguru import logger


class BenchmarkEngine:
    """Master benchmarking. Aggregates peer comparisons, rankings, and improvement gaps."""

    def benchmark_report(self) -> Dict[str, Any]:
        from core.benchmarking.peer_comparison_tracker import peer_comparison_tracker
        from core.benchmarking.performance_ranker import performance_ranker
        from core.benchmarking.improvement_gap_detector import improvement_gap_detector

        outperforming = peer_comparison_tracker.outperforming_benchmarks()
        underperforming = peer_comparison_tracker.underperforming_benchmarks()
        percentile = performance_ranker.percentile_rank()
        gap_report = improvement_gap_detector.gap_report()
        large_gaps = improvement_gap_detector.large_opportunities()

        return {
            "benchmarks_tracked": len(outperforming) + len(underperforming),
            "outperforming_count": len(outperforming),
            "underperforming_count": len(underperforming),
            "percentile_rank": percentile,
            "largest_improvement_gaps": large_gaps[:3],
            "gap_summary": gap_report,
            "ts": int(time.time() * 1000),
        }

    def one_liner(self) -> str:
        report = self.benchmark_report()
        return (
            f"Benchmarking: {report['outperforming_count']}/{report['benchmarks_tracked']} outperforming | "
            f"percentile={report['percentile_rank']} | "
            f"large_gaps={report['gap_summary']['large_opportunities']}"
        )


benchmark_engine = BenchmarkEngine()
