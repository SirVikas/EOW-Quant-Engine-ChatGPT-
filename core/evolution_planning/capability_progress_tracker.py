"""Capability Progress Tracker — monitors maturity of PHOENIX capabilities over time."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class CapabilityProgress:
    cap_id: str
    capability_name: str
    current_maturity_pct: float  # 0-100
    target_maturity_pct: float
    progress_delta_last_period: float
    trend: str  # ADVANCING/STALLED/REGRESSING
    last_updated: str


class CapabilityProgressTracker:
    def __init__(self):
        self._lock = threading.RLock()
        self._capabilities: dict[str, CapabilityProgress] = {}

    def record_progress(self, capability_name: str, current_maturity_pct: float,
                        target_maturity_pct: float = 100) -> dict:
        with self._lock:
            existing = self._capabilities.get(capability_name)
            delta = 0.0
            trend = "STALLED"
            if existing:
                delta = current_maturity_pct - existing.current_maturity_pct
                if delta > 0:
                    trend = "ADVANCING"
                elif delta < 0:
                    trend = "REGRESSING"
            else:
                trend = "ADVANCING" if current_maturity_pct > 0 else "STALLED"

            cap = CapabilityProgress(
                cap_id=capability_name,
                capability_name=capability_name,
                current_maturity_pct=current_maturity_pct,
                target_maturity_pct=target_maturity_pct,
                progress_delta_last_period=delta,
                trend=trend,
                last_updated=datetime.now(timezone.utc).isoformat(),
            )
            self._capabilities[capability_name] = cap
            return asdict(cap)

    def lagging_capabilities(self, threshold: float = 60) -> List[dict]:
        with self._lock:
            return [asdict(c) for c in self._capabilities.values()
                    if c.current_maturity_pct < threshold]

    def all_capabilities(self) -> List[dict]:
        with self._lock:
            return [asdict(c) for c in self._capabilities.values()]

    def progress_summary(self) -> dict:
        with self._lock:
            total = len(self._capabilities)
            if total == 0:
                return {"total": 0, "on_track": 0, "lagging": 0, "avg_maturity_pct": 0}
            on_track = sum(1 for c in self._capabilities.values()
                           if c.current_maturity_pct >= 60)
            lagging = total - on_track
            avg = sum(c.current_maturity_pct for c in self._capabilities.values()) / total
            return {
                "total": total,
                "on_track": on_track,
                "lagging": lagging,
                "avg_maturity_pct": avg,
            }


capability_progress_tracker = CapabilityProgressTracker()
