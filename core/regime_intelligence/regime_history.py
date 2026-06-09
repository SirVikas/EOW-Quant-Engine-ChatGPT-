"""Regime History — records the history of market regimes."""
import threading
import time
from dataclasses import dataclass


@dataclass
class RegimeRecord:
    record_id: str
    regime: str
    started_at: float
    ended_at: float  # 0.0 = still open
    duration_days: float
    characteristics: dict
    transition_trigger: str


class RegimeHistory:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: list[RegimeRecord] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"RGH-{self._counter:03d}"

    def record_regime(self, regime: str, characteristics: dict = None,
                      transition_trigger: str = "") -> str:
        with self._lock:
            now = time.time()
            # Close previous open regime
            for r in self._records:
                if r.ended_at == 0.0:
                    r.ended_at = now
                    r.duration_days = (now - r.started_at) / 86400

            rid = self._next_id()
            self._records.append(RegimeRecord(
                record_id=rid,
                regime=regime,
                started_at=now,
                ended_at=0.0,
                duration_days=0.0,
                characteristics=characteristics or {},
                transition_trigger=transition_trigger,
            ))
            return rid

    def current_regime(self) -> dict:
        with self._lock:
            for r in reversed(self._records):
                if r.ended_at == 0.0:
                    return vars(r)
            return {}

    def all_regimes(self, limit: int = 50) -> list:
        with self._lock:
            return [vars(r) for r in self._records[-limit:]]

    def regime_stats(self) -> dict:
        with self._lock:
            items = self._records[:]
            total = len(items)
            durations = [r.duration_days for r in items if r.ended_at != 0.0]
            avg_dur = sum(durations) / len(durations) if durations else 0.0
            longest = max(durations) if durations else 0.0
            by_type: dict = {}
            for r in items:
                by_type[r.regime] = by_type.get(r.regime, 0) + 1
            return {
                "total_regimes": total,
                "avg_duration_days": avg_dur,
                "longest_regime": longest,
                "by_regime_type": by_type,
                "current": self.current_regime(),
            }


regime_history = RegimeHistory()
