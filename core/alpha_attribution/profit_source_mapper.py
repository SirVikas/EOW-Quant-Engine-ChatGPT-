"""GAP-03: Profit Source Mapper — maps profit to its generating components."""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Dict, Any, List

from loguru import logger


@dataclass
class ProfitMap:
    map_id: str
    period: str
    total_pnl: float
    signal_contribution_pct: float
    risk_contribution_pct: float
    sizing_contribution_pct: float
    regime_contribution_pct: float
    other_pct: float
    recorded_at: int


class ProfitSourceMapper:
    """Maps profit to its generating components. Thread-safe."""

    def __init__(self):
        self._lock = threading.RLock()
        self._maps: List[ProfitMap] = []
        self._counter = 0
        logger.info("[GAP-03] ProfitSourceMapper initialized")

    def _next_id(self) -> str:
        self._counter += 1
        return f"PSM-{self._counter:03d}"

    def record(
        self,
        period: str,
        total_pnl: float,
        signal_pct: float,
        risk_pct: float,
        sizing_pct: float,
        regime_pct: float,
    ) -> str:
        with self._lock:
            other = max(0.0, 100.0 - signal_pct - risk_pct - sizing_pct - regime_pct)
            mid = self._next_id()
            self._maps.append(ProfitMap(
                map_id=mid,
                period=period,
                total_pnl=total_pnl,
                signal_contribution_pct=signal_pct,
                risk_contribution_pct=risk_pct,
                sizing_contribution_pct=sizing_pct,
                regime_contribution_pct=regime_pct,
                other_pct=other,
                recorded_at=int(time.time() * 1000),
            ))
            return mid

    def attribution_history(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [vars(m) for m in self._maps]

    def avg_attribution(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._maps)
            if total == 0:
                return {"signal": 0.0, "risk": 0.0, "sizing": 0.0, "regime": 0.0, "other": 0.0}
            return {
                "signal": round(sum(m.signal_contribution_pct for m in self._maps) / total, 2),
                "risk": round(sum(m.risk_contribution_pct for m in self._maps) / total, 2),
                "sizing": round(sum(m.sizing_contribution_pct for m in self._maps) / total, 2),
                "regime": round(sum(m.regime_contribution_pct for m in self._maps) / total, 2),
                "other": round(sum(m.other_pct for m in self._maps) / total, 2),
                "periods_tracked": total,
                "ts": int(time.time() * 1000),
            }


profit_source_mapper = ProfitSourceMapper()
