"""GAP-01: Alpha Source Tracker — tracks identified alpha sources."""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from loguru import logger


@dataclass
class AlphaSource:
    source_id: str
    source_name: str
    source_type: str  # SIGNAL/RISK_MGMT/POSITION_SIZING/REGIME_DETECTION/TIMING
    contribution_pct: float
    evidence_count: int
    confidence: str  # HIGH/MEDIUM/LOW/UNVERIFIED
    last_updated: int


class AlphaSourceTracker:
    """Tracks identified alpha sources. Thread-safe."""

    VALID_TYPES = {"SIGNAL", "RISK_MGMT", "POSITION_SIZING", "REGIME_DETECTION", "TIMING"}
    VALID_CONF = {"HIGH", "MEDIUM", "LOW", "UNVERIFIED"}

    def __init__(self):
        self._lock = threading.RLock()
        self._sources: Dict[str, AlphaSource] = {}
        self._counter = 0
        logger.info("[GAP-01] AlphaSourceTracker initialized")

    def _next_id(self) -> str:
        self._counter += 1
        return f"ALF-{self._counter:03d}"

    def record(
        self,
        source_name: str,
        source_type: str,
        contribution_pct: float,
        evidence_count: int,
        confidence: str,
    ) -> str:
        with self._lock:
            sid = self._next_id()
            self._sources[sid] = AlphaSource(
                source_id=sid,
                source_name=source_name,
                source_type=source_type if source_type in self.VALID_TYPES else "SIGNAL",
                contribution_pct=contribution_pct,
                evidence_count=evidence_count,
                confidence=confidence if confidence in self.VALID_CONF else "UNVERIFIED",
                last_updated=int(time.time() * 1000),
            )
            return sid

    def by_type(self) -> Dict[str, List[Dict[str, Any]]]:
        with self._lock:
            result: Dict[str, List[Dict[str, Any]]] = {}
            for s in self._sources.values():
                result.setdefault(s.source_type, []).append(vars(s))
            return result

    def top_sources(self, n: int = 5) -> List[Dict[str, Any]]:
        with self._lock:
            sorted_sources = sorted(
                self._sources.values(), key=lambda x: x.contribution_pct, reverse=True
            )
            return [vars(s) for s in sorted_sources[:n]]

    def alpha_source_summary(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._sources)
            verified = sum(1 for s in self._sources.values() if s.confidence in {"HIGH", "MEDIUM"})
            total_contribution = sum(s.contribution_pct for s in self._sources.values())
            return {
                "total_sources": total,
                "verified_sources": verified,
                "unverified_sources": total - verified,
                "total_contribution_pct": round(total_contribution, 2),
                "by_type_counts": {t: len(lst) for t, lst in self.by_type().items()},
                "ts": int(time.time() * 1000),
            }


alpha_source_tracker = AlphaSourceTracker()
