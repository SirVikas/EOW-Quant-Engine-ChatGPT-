"""
Signal decay tracker — monitors erosion of signal predictive power over time.
"""
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class SignalDecay:
    decay_id: str
    signal_name: str
    initial_hit_rate_pct: float
    current_hit_rate_pct: float
    decay_rate_pct_per_month: float
    status: str   # STABLE / DECAYING / DEPLETED
    measured_at: str


class SignalDecayTracker:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: List[SignalDecay] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"SDT-{self._counter:03d}"

    def record(
        self,
        signal_name: str,
        initial_hit_rate_pct: float,
        current_hit_rate_pct: float,
    ) -> SignalDecay:
        decay_rate = round(initial_hit_rate_pct - current_hit_rate_pct, 2)
        if current_hit_rate_pct < 30:
            status = "DEPLETED"
        elif decay_rate > 10:
            status = "DECAYING"
        else:
            status = "STABLE"
        with self._lock:
            rec = SignalDecay(
                decay_id=self._next_id(),
                signal_name=signal_name,
                initial_hit_rate_pct=initial_hit_rate_pct,
                current_hit_rate_pct=current_hit_rate_pct,
                decay_rate_pct_per_month=decay_rate,
                status=status,
                measured_at=datetime.utcnow().isoformat(),
            )
            self._records.append(rec)
            return rec

    def decaying_signals(self) -> List[SignalDecay]:
        with self._lock:
            return [r for r in self._records if r.status in ("DECAYING", "DEPLETED")]

    def decay_report(self) -> dict:
        with self._lock:
            return {
                "total_signals_tracked": len(self._records),
                "stable": sum(1 for r in self._records if r.status == "STABLE"),
                "decaying": sum(1 for r in self._records if r.status == "DECAYING"),
                "depleted": sum(1 for r in self._records if r.status == "DEPLETED"),
                "signals": [
                    {
                        "signal_name": r.signal_name,
                        "initial_hit_rate_pct": r.initial_hit_rate_pct,
                        "current_hit_rate_pct": r.current_hit_rate_pct,
                        "status": r.status,
                    }
                    for r in self._records
                ],
            }


signal_decay_tracker = SignalDecayTracker()
