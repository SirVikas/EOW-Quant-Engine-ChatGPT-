"""GAP-03: Performance Decomposition — decomposes overall performance into components."""
from __future__ import annotations

import time
from typing import Dict, Any, List

from loguru import logger


class PerformanceDecomposition:
    """Decomposes overall performance into components using lazy-loaded sub-engines."""

    def decompose(self, period: str) -> Dict[str, Any]:
        from core.alpha_attribution.profit_source_mapper import profit_source_mapper
        from core.alpha_attribution.edge_contribution_tracker import edge_contribution_tracker

        avg_attr = profit_source_mapper.avg_attribution()
        top_edges = edge_contribution_tracker.top_contributing_edges(n=5)

        # Determine dominant alpha source
        source_map = {
            "signal": avg_attr.get("signal", 0.0),
            "risk": avg_attr.get("risk", 0.0),
            "sizing": avg_attr.get("sizing", 0.0),
            "regime": avg_attr.get("regime", 0.0),
        }
        dominant = max(source_map, key=lambda k: source_map[k]) if source_map else "unknown"
        total_explained = sum(source_map.values())
        unexplained_pct = max(0.0, round(100.0 - total_explained, 2))

        components = [
            {"source": k, "contribution_pct": round(v, 2)} for k, v in source_map.items()
        ]

        return {
            "period": period,
            "components": components,
            "dominant_alpha_source": dominant,
            "unexplained_pct": unexplained_pct,
            "top_edges": top_edges,
            "ts": int(time.time() * 1000),
        }

    def full_decomposition_history(self) -> List[Dict[str, Any]]:
        from core.alpha_attribution.profit_source_mapper import profit_source_mapper
        return profit_source_mapper.attribution_history()


performance_decomposition = PerformanceDecomposition()
