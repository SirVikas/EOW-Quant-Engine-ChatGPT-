"""GAP-03: Alpha Attribution Engine — master alpha attribution aggregator."""
from __future__ import annotations

import time
from typing import Dict, Any

from loguru import logger


class AlphaAttributionEngine:
    """Master alpha attribution. Aggregates profit mapping, edge contributions, and decomposition."""

    def attribution_report(self) -> Dict[str, Any]:
        from core.alpha_attribution.profit_source_mapper import profit_source_mapper
        from core.alpha_attribution.edge_contribution_tracker import edge_contribution_tracker
        from core.alpha_attribution.performance_decomposition import performance_decomposition

        avg_attr = profit_source_mapper.avg_attribution()
        top_edges = edge_contribution_tracker.top_contributing_edges(n=3)
        decomp = performance_decomposition.decompose("latest")

        periods_tracked = avg_attr.get("periods_tracked", 0)
        most_valuable = top_edges[0]["edge_name"] if top_edges else "none"
        unexplained = decomp["unexplained_pct"]

        if periods_tracked >= 10 and unexplained < 20:
            confidence = "HIGH"
        elif periods_tracked >= 3:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        return {
            "latest_decomposition": decomp,
            "top_alpha_sources": avg_attr,
            "most_valuable_edge": most_valuable,
            "attribution_confidence": confidence,
            "periods_tracked": periods_tracked,
            "ts": int(time.time() * 1000),
        }

    def one_liner(self) -> str:
        report = self.attribution_report()
        return (
            f"AlphaAttribution: top_edge={report['most_valuable_edge']} | "
            f"confidence={report['attribution_confidence']} | "
            f"periods={report['periods_tracked']}"
        )


alpha_attribution_engine = AlphaAttributionEngine()
