"""
Data gap detector — records and surfaces gaps in market data feeds.
"""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class DataGap:
    gap_id: str
    feed_name: str
    symbol: str
    gap_type: str   # MISSING_CANDLE / FEED_DELAY / STALE_DATA
    gap_start: str
    gap_end: Optional[str]
    severity: str   # HIGH / MEDIUM / LOW
    detected_at: str
    resolved: bool = False


class DataGapDetector:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._gaps: List[DataGap] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"DGP-{self._counter:03d}"

    def record_gap(
        self,
        feed_name: str,
        symbol: str,
        gap_type: str,
        severity: str,
        gap_start: Optional[str] = None,
        gap_end: Optional[str] = None,
    ) -> DataGap:
        now = datetime.utcnow().isoformat()
        with self._lock:
            gap = DataGap(
                gap_id=self._next_id(),
                feed_name=feed_name,
                symbol=symbol,
                gap_type=gap_type,
                gap_start=gap_start or now,
                gap_end=gap_end,
                severity=severity,
                detected_at=now,
            )
            self._gaps.append(gap)
            return gap

    def active_gaps(self) -> List[DataGap]:
        with self._lock:
            return [g for g in self._gaps if not g.resolved]

    def gap_summary(self) -> dict:
        with self._lock:
            active = [g for g in self._gaps if not g.resolved]
            return {
                "total_gaps": len(self._gaps),
                "active_gaps": len(active),
                "by_severity": {
                    "HIGH": sum(1 for g in active if g.severity == "HIGH"),
                    "MEDIUM": sum(1 for g in active if g.severity == "MEDIUM"),
                    "LOW": sum(1 for g in active if g.severity == "LOW"),
                },
                "by_type": {
                    "MISSING_CANDLE": sum(1 for g in active if g.gap_type == "MISSING_CANDLE"),
                    "FEED_DELAY": sum(1 for g in active if g.gap_type == "FEED_DELAY"),
                    "STALE_DATA": sum(1 for g in active if g.gap_type == "STALE_DATA"),
                },
            }


data_gap_detector = DataGapDetector()
