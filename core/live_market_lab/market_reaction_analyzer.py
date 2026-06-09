"""GAP-02: Market Reaction Analyzer — analyzes how the market reacts to events/signals."""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Dict, Any, List

from loguru import logger


@dataclass
class ReactionRecord:
    reaction_id: str
    event_type: str
    signal_name: str
    immediate_reaction_pct: float
    sustained_reaction_pct: float
    reaction_duration_bars: int
    analyzed_at: int


class MarketReactionAnalyzer:
    """Analyzes how the market reacts to events/signals. Thread-safe."""

    def __init__(self):
        self._lock = threading.RLock()
        self._records: Dict[str, ReactionRecord] = {}
        self._counter = 0
        logger.info("[GAP-02] MarketReactionAnalyzer initialized")

    def _next_id(self) -> str:
        self._counter += 1
        return f"MRA-{self._counter:03d}"

    def record(
        self,
        event_type: str,
        signal_name: str,
        immediate_reaction_pct: float,
        sustained_reaction_pct: float,
        reaction_duration_bars: int,
    ) -> str:
        with self._lock:
            rid = self._next_id()
            self._records[rid] = ReactionRecord(
                reaction_id=rid,
                event_type=event_type,
                signal_name=signal_name,
                immediate_reaction_pct=immediate_reaction_pct,
                sustained_reaction_pct=sustained_reaction_pct,
                reaction_duration_bars=reaction_duration_bars,
                analyzed_at=int(time.time() * 1000),
            )
            return rid

    def by_event_type(self, event_type: str) -> List[Dict[str, Any]]:
        with self._lock:
            return [vars(r) for r in self._records.values() if r.event_type == event_type]

    def reaction_report(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._records)
            if total == 0:
                return {"total_reactions": 0, "avg_immediate_pct": 0.0, "avg_sustained_pct": 0.0, "ts": int(time.time() * 1000)}
            avg_imm = sum(r.immediate_reaction_pct for r in self._records.values()) / total
            avg_sus = sum(r.sustained_reaction_pct for r in self._records.values()) / total
            event_types = list({r.event_type for r in self._records.values()})
            return {
                "total_reactions": total,
                "avg_immediate_pct": round(avg_imm, 4),
                "avg_sustained_pct": round(avg_sus, 4),
                "event_types_tracked": event_types,
                "ts": int(time.time() * 1000),
            }


market_reaction_analyzer = MarketReactionAnalyzer()
