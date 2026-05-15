"""
FTD-057-PHOENIX Phase 2 — Signal Density Engine

Tracks signals/hr, blocked/reason, survival rates, and starvation detection.
Provides the forensic telemetry backbone for all other signal ecology modules.

Starvation thresholds:
  - DROUGHT:     0 signals passed in last DROUGHT_WINDOW_SEC seconds
  - STARVATION:  survival rate < STARVATION_SR_THRESH over last N evaluations
  - AUTO_RECOVER: triggers ExplorationRecovery when drought exceeds DROUGHT_AUTO_SEC
"""
from __future__ import annotations

import time
import threading
from collections import deque, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from loguru import logger


# ── Thresholds ─────────────────────────────────────────────────────────────────
DROUGHT_WINDOW_SEC   = 300     # 5 minutes without a passing signal = drought
DROUGHT_AUTO_SEC     = 600     # 10 minutes = trigger auto-recovery
STARVATION_SR_THRESH = 0.05    # survival rate below 5% = starvation
STARVATION_WINDOW    = 200     # rolling evaluation window for starvation check
DENSITY_WINDOW_SEC   = 3600    # 1 hour window for signals/hr calculation


@dataclass
class DensitySnapshot:
    ts:              int
    signals_per_hr:  float
    survival_rate:   float
    blocked_count:   int
    passed_count:    int
    is_drought:      bool
    is_starvation:   bool
    top_block_reason: str
    regime_breakdown: Dict[str, Any]


class SignalDensityEngine:
    """
    Real-time signal flow health monitor.
    Thread-safe — uses RLock.
    """

    def __init__(self):
        self._lock = threading.RLock()

        # Rolling logs
        self._events: deque = deque()              # (ts, passed, reason, regime, symbol)
        self._pass_ts: deque = deque()             # timestamps of passing signals

        # Starvation window (fixed size, 1 = passed, 0 = blocked)
        self._survival_window: deque = deque(maxlen=STARVATION_WINDOW)

        # Reason counters
        self._block_reasons: Dict[str, int] = defaultdict(int)

        # Per-regime tracking
        self._regime_evaluated: Dict[str, int] = defaultdict(int)
        self._regime_passed:    Dict[str, int] = defaultdict(int)

        # Drought state
        self._last_pass_ts: float = time.time()   # seeded so no false drought at start
        self._drought_notified: bool = False
        self._auto_recover_triggered: bool = False
        self._auto_recover_count: int = 0

        # Session totals
        self._total_evaluated: int = 0
        self._total_passed:    int = 0

        # Snapshot history
        self._snapshots: deque = deque(maxlen=200)

    # ── Core recording API ─────────────────────────────────────────────────────

    def record_evaluated(
        self,
        passed: bool,
        reason: str = "",
        regime: str = "UNKNOWN",
        symbol: str = "",
        strategy: str = "",
    ) -> None:
        """
        Called for every signal evaluation (pass or block).
        """
        with self._lock:
            now = time.time()
            ts  = int(now * 1000)

            self._events.append((ts, passed, reason, regime, symbol))
            self._survival_window.append(1 if passed else 0)

            self._total_evaluated += 1
            self._regime_evaluated[regime] += 1

            if passed:
                self._total_passed += 1
                self._regime_passed[regime] += 1
                self._pass_ts.append(now)
                self._last_pass_ts = now
                self._drought_notified = False
                self._auto_recover_triggered = False
            else:
                if reason:
                    self._block_reasons[reason[:80]] += 1

            # Prune old pass timestamps outside density window
            cutoff = now - DENSITY_WINDOW_SEC
            while self._pass_ts and self._pass_ts[0] < cutoff:
                self._pass_ts.popleft()

            # Prune events older than 2 hours
            cutoff2 = ts - 7_200_000
            while self._events and self._events[0][0] < cutoff2:
                self._events.popleft()

    def record_block(self, reason: str, regime: str = "UNKNOWN", symbol: str = "") -> None:
        """Convenience wrapper for a blocked evaluation."""
        self.record_evaluated(False, reason=reason, regime=regime, symbol=symbol)

    def record_pass(self, regime: str = "UNKNOWN", symbol: str = "") -> None:
        """Convenience wrapper for a passing evaluation."""
        self.record_evaluated(True, regime=regime, symbol=symbol)

    # ── State queries ──────────────────────────────────────────────────────────

    def survival_rate(self) -> float:
        with self._lock:
            if not self._survival_window:
                return 0.0
            return sum(self._survival_window) / len(self._survival_window)

    def signals_per_hour(self) -> float:
        with self._lock:
            return float(len(self._pass_ts))

    def is_drought(self) -> bool:
        with self._lock:
            return (time.time() - self._last_pass_ts) >= DROUGHT_WINDOW_SEC

    def is_starvation(self) -> bool:
        with self._lock:
            if len(self._survival_window) < 20:
                return False
            return self.survival_rate() < STARVATION_SR_THRESH

    def should_auto_recover(self) -> bool:
        """Returns True if drought has lasted long enough to trigger auto-recovery."""
        with self._lock:
            elapsed = time.time() - self._last_pass_ts
            if elapsed >= DROUGHT_AUTO_SEC and not self._auto_recover_triggered:
                return True
            return False

    def mark_auto_recover_triggered(self) -> None:
        with self._lock:
            self._auto_recover_triggered = True
            self._auto_recover_count += 1
            logger.warning(
                f"[FTD-057][DENSITY] Auto-recovery triggered "
                f"(drought={time.time()-self._last_pass_ts:.0f}s, "
                f"total_recoveries={self._auto_recover_count})"
            )

    # ── Snapshot / telemetry ───────────────────────────────────────────────────

    def snapshot(self) -> DensitySnapshot:
        with self._lock:
            sr   = self.survival_rate()
            sph  = self.signals_per_hour()
            drg  = self.is_drought()
            starv = self.is_starvation()

            # Top block reason by count
            if self._block_reasons:
                top_reason = max(self._block_reasons, key=self._block_reasons.get)
            else:
                top_reason = ""

            regime_breakdown = {}
            all_regimes = set(self._regime_evaluated) | set(self._regime_passed)
            for r in all_regimes:
                ev = self._regime_evaluated.get(r, 0)
                pa = self._regime_passed.get(r, 0)
                regime_breakdown[r] = {
                    "evaluated": ev,
                    "passed":    pa,
                    "survival":  round(pa / ev, 4) if ev > 0 else 0.0,
                }

            snap = DensitySnapshot(
                ts=int(time.time() * 1000),
                signals_per_hr=round(sph, 2),
                survival_rate=round(sr, 4),
                blocked_count=self._total_evaluated - self._total_passed,
                passed_count=self._total_passed,
                is_drought=drg,
                is_starvation=starv,
                top_block_reason=top_reason,
                regime_breakdown=regime_breakdown,
            )
            self._snapshots.append({
                "ts": snap.ts,
                "survival_rate": snap.survival_rate,
                "signals_per_hr": snap.signals_per_hr,
                "is_drought": drg,
                "is_starvation": starv,
            })

            if drg and not self._drought_notified:
                self._drought_notified = True
                logger.warning(
                    f"[FTD-057][DENSITY] DROUGHT detected: "
                    f"{time.time()-self._last_pass_ts:.0f}s without signal, "
                    f"survival_rate={sr:.3f}"
                )
            return snap

    def get_telemetry(self) -> Dict[str, Any]:
        with self._lock:
            snap = self.snapshot()
            top_reasons = sorted(
                self._block_reasons.items(), key=lambda x: x[1], reverse=True
            )[:10]
            return {
                "module":              "SignalDensityEngine",
                "ftd":                 "057",
                "total_evaluated":     self._total_evaluated,
                "total_passed":        self._total_passed,
                "total_blocked":       self._total_evaluated - self._total_passed,
                "signals_per_hr":      snap.signals_per_hr,
                "survival_rate":       snap.survival_rate,
                "is_drought":          snap.is_drought,
                "is_starvation":       snap.is_starvation,
                "drought_seconds":     round(time.time() - self._last_pass_ts, 1),
                "auto_recover_count":  self._auto_recover_count,
                "top_block_reasons":   [{"reason": r, "count": c} for r, c in top_reasons],
                "regime_breakdown":    snap.regime_breakdown,
                "recent_snapshots":    list(self._snapshots)[-20:],
                "ts":                  snap.ts,
            }

    def block_reason_matrix(self) -> List[Dict[str, Any]]:
        """Sorted list of block reasons with counts and percentages."""
        with self._lock:
            total = self._total_evaluated - self._total_passed
            if total == 0:
                return []
            return [
                {
                    "reason":  r,
                    "count":   c,
                    "pct":     round(c / total * 100, 1),
                }
                for r, c in sorted(self._block_reasons.items(),
                                   key=lambda x: x[1], reverse=True)
            ]


# ── Singleton ──────────────────────────────────────────────────────────────────
signal_density_engine = SignalDensityEngine()
