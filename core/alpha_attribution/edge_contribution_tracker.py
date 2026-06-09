"""GAP-03: Edge Contribution Tracker — tracks each strategy edge's P&L contribution."""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Dict, Any, List

from loguru import logger


@dataclass
class EdgeContrib:
    contrib_id: str
    edge_name: str
    edge_type: str
    period: str
    pnl_contribution: float
    trade_count: int
    win_rate_pct: float
    recorded_at: int


class EdgeContributionTracker:
    """Tracks each strategy edge's P&L contribution. Thread-safe."""

    def __init__(self):
        self._lock = threading.RLock()
        self._records: List[EdgeContrib] = []
        self._counter = 0
        logger.info("[GAP-03] EdgeContributionTracker initialized")

    def _next_id(self) -> str:
        self._counter += 1
        return f"ECT-{self._counter:03d}"

    def record(
        self,
        edge_name: str,
        edge_type: str,
        period: str,
        pnl_contribution: float,
        trade_count: int,
        win_rate_pct: float,
    ) -> str:
        with self._lock:
            cid = self._next_id()
            self._records.append(EdgeContrib(
                contrib_id=cid,
                edge_name=edge_name,
                edge_type=edge_type,
                period=period,
                pnl_contribution=pnl_contribution,
                trade_count=trade_count,
                win_rate_pct=win_rate_pct,
                recorded_at=int(time.time() * 1000),
            ))
            return cid

    def by_edge(self, edge_name: str) -> List[Dict[str, Any]]:
        with self._lock:
            return [vars(r) for r in self._records if r.edge_name == edge_name]

    def top_contributing_edges(self, n: int = 5) -> List[Dict[str, Any]]:
        with self._lock:
            # Aggregate by edge_name
            edge_totals: Dict[str, float] = {}
            for r in self._records:
                edge_totals[r.edge_name] = edge_totals.get(r.edge_name, 0.0) + r.pnl_contribution
            sorted_edges = sorted(edge_totals.items(), key=lambda x: x[1], reverse=True)
            return [{"edge_name": e, "total_pnl_contribution": round(v, 4)} for e, v in sorted_edges[:n]]


edge_contribution_tracker = EdgeContributionTracker()
