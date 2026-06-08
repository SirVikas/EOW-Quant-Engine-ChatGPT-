"""
PHOENIX OBSERVATORY-X — Report Health Monitor  [OX-1C]

Tracks the runtime health of every registered report:
  - last_generated   : epoch timestamp of last successful generation
  - last_status      : "ok" | "failed" | "stale" | "never_run"
  - error_count      : cumulative failure count
  - consecutive_ok   : consecutive successful runs
  - data_completeness: 0–100 score set by report generator (optional)
  - staleness_secs   : how long since last successful generation
  - staleness_verdict: ok | warn | stale | critical

Staleness thresholds (relative to nominal frequency):
  frequency   warn_after   critical_after
  ─────────────────────────────────────────
  realtime    300 s        900 s
  hourly      5400 s       10800 s  (1.5× / 3× interval)
  session     3600 s       7200 s
  daily       129600 s     259200 s (1.5× / 3× interval)
  weekly      907200 s     1814400 s
  on_demand   —            —

Thread-safe: single RLock guards all mutations.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from loguru import logger


# ── Staleness thresholds (seconds) ────────────────────────────────────────────

_STALE_THRESHOLDS: Dict[str, tuple[Optional[int], Optional[int]]] = {
    "realtime":  (300,    900),
    "hourly":    (5400,   10800),
    "session":   (3600,   7200),
    "daily":     (129600, 259200),
    "weekly":    (907200, 1814400),
    "on_demand": (None,   None),
}


# ── Data Model ────────────────────────────────────────────────────────────────

@dataclass
class ReportHealth:
    report_key: str
    frequency: str
    last_generated: float = 0.0      # epoch; 0 = never
    last_status: str = "never_run"   # ok | failed | stale | never_run
    error_count: int = 0
    consecutive_ok: int = 0
    data_completeness: float = 100.0  # 0–100; set by report generator
    last_error_msg: str = ""
    run_count: int = 0


# ── Monitor ───────────────────────────────────────────────────────────────────

class ReportHealthMonitor:
    """
    Central health tracker for all PHOENIX reports.
    Report generators call record_ok() / record_failure() after each run.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: Dict[str, ReportHealth] = {}

    # ── Registration / Seeding ────────────────────────────────────────────────

    def seed(self, report_key: str, frequency: str) -> None:
        """Create a health record if it doesn't exist yet."""
        with self._lock:
            if report_key not in self._records:
                self._records[report_key] = ReportHealth(
                    report_key=report_key,
                    frequency=frequency,
                )

    # ── Event Recording ───────────────────────────────────────────────────────

    def record_ok(
        self,
        report_key: str,
        data_completeness: float = 100.0,
    ) -> None:
        """Call after a report generates successfully."""
        now = time.time()
        with self._lock:
            rec = self._records.get(report_key)
            if not rec:
                rec = ReportHealth(report_key=report_key, frequency="unknown")
                self._records[report_key] = rec
            rec.last_generated = now
            rec.last_status = "ok"
            rec.consecutive_ok += 1
            rec.run_count += 1
            rec.data_completeness = data_completeness
            rec.last_error_msg = ""

    def record_failure(self, report_key: str, error_msg: str = "") -> None:
        """Call when a report fails to generate."""
        with self._lock:
            rec = self._records.get(report_key)
            if not rec:
                rec = ReportHealth(report_key=report_key, frequency="unknown")
                self._records[report_key] = rec
            rec.last_status = "failed"
            rec.error_count += 1
            rec.consecutive_ok = 0
            rec.run_count += 1
            rec.last_error_msg = error_msg[:256] if error_msg else ""
        logger.warning(f"[OBSERVATORY-X Health] Report failed: {report_key} — {error_msg[:120]}")

    # ── Staleness Assessment ──────────────────────────────────────────────────

    def assess(self, report_key: str) -> dict:
        """Return full health assessment for one report."""
        now = time.time()
        with self._lock:
            rec = self._records.get(report_key)
        if not rec:
            return {"report_key": report_key, "verdict": "unknown", "registered": False}

        staleness_secs = (now - rec.last_generated) if rec.last_generated > 0 else None
        warn_thresh, crit_thresh = _STALE_THRESHOLDS.get(rec.frequency, (None, None))

        if rec.last_generated == 0:
            verdict = "never_run"
        elif rec.last_status == "failed":
            verdict = "failed"
        elif staleness_secs is not None and crit_thresh and staleness_secs > crit_thresh:
            verdict = "critical"
        elif staleness_secs is not None and warn_thresh and staleness_secs > warn_thresh:
            verdict = "warn"
        else:
            verdict = "ok"

        return {
            "report_key":        rec.report_key,
            "frequency":         rec.frequency,
            "last_generated":    rec.last_generated,
            "last_status":       rec.last_status,
            "staleness_secs":    staleness_secs,
            "verdict":           verdict,
            "error_count":       rec.error_count,
            "consecutive_ok":    rec.consecutive_ok,
            "data_completeness": rec.data_completeness,
            "last_error_msg":    rec.last_error_msg,
            "run_count":         rec.run_count,
        }

    def assess_all(self) -> List[dict]:
        with self._lock:
            keys = list(self._records.keys())
        return [self.assess(k) for k in keys]

    # ── Summary Dashboard ─────────────────────────────────────────────────────

    def summary(self) -> dict:
        assessments = self.assess_all()
        verdict_counts: Dict[str, int] = {}
        for a in assessments:
            v = a.get("verdict", "unknown")
            verdict_counts[v] = verdict_counts.get(v, 0) + 1

        critical = [a["report_key"] for a in assessments if a.get("verdict") == "critical"]
        failed   = [a["report_key"] for a in assessments if a.get("verdict") == "failed"]
        warn     = [a["report_key"] for a in assessments if a.get("verdict") == "warn"]

        # Overall health score: 100 − penalties
        total = len(assessments) or 1
        penalty = (
            len(critical) * 3
            + len(failed)  * 2
            + len(warn)    * 1
        )
        health_score = max(0, round(100 - (penalty / total) * 10))

        return {
            "total_tracked":   len(assessments),
            "verdict_counts":  verdict_counts,
            "health_score":    health_score,
            "critical_reports": critical,
            "failed_reports":   failed,
            "warn_reports":     warn,
            "assessments":      assessments,
        }


# ── Auto-seed from registry on first import ───────────────────────────────────
# Done lazily to avoid circular imports; called once from Observatory __init__.

def _seed_from_registry() -> None:
    from core.observatory.registry import report_registry
    for defn in report_registry.all():
        report_health_monitor.seed(defn.key, defn.frequency)


# Singleton
report_health_monitor = ReportHealthMonitor()

# Seed immediately (registry is already loaded before this module)
try:
    _seed_from_registry()
except Exception:  # noqa: BLE001
    pass  # registry may not be fully ready; seeding will happen on first assess()
