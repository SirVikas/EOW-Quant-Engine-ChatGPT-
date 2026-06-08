"""
Evidence Accumulation Tracker.

Tracks live evidence accumulation progress toward AEG activation threshold
(60 days). Derives boot_ts from oldest IMRAF record so the clock starts
the moment NEXUS first ran — not from when this module was introduced.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List

import logging
logger = logging.getLogger(__name__)

_DATA_FILE = Path(__file__).parent.parent.parent.parent.parent / "data" / "nexus_evidence_tracker.json"
_MS_PER_DAY = 86_400_000
_TARGET_DAYS = 60
_MILESTONES = [
    (7,  "First Week"),
    (14, "Two Weeks"),
    (30, "One Month"),
    (45, "Six Weeks"),
    (60, "AEG Activation Threshold"),
]
# Rolling window for evidence_velocity (days)
_VELOCITY_WINDOW_DAYS = 7


class EvidenceAccumulationTracker:
    """
    Tracks days of live evidence, confidence trajectory, and projected AEG activation date.
    Persists state to data/nexus_evidence_tracker.json.
    """

    def __init__(self, data_file: Path = _DATA_FILE) -> None:
        self._data_file = data_file
        self._data_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _load(self) -> dict:
        if self._data_file.exists():
            try:
                return json.loads(self._data_file.read_text())
            except Exception:
                pass
        return {}

    def _save(self, state: dict) -> None:
        self._data_file.write_text(json.dumps(state, indent=2))

    def _resolve_boot_ts_ms(self) -> int:
        """Use oldest IMRAF record ts as the canonical evidence start time.
        Falls back to current time when IMRAF is empty or unavailable.
        """
        try:
            from core.institutional_memory.imraf_engine import imraf
            with imraf._lock:
                row = imraf._conn.execute(
                    "SELECT MIN(ts) as min_ts FROM imraf_records"
                ).fetchone()
            if row and row[0]:
                return int(row[0])
        except Exception:
            pass
        return int(time.time() * 1000)

    def _evidence_velocity(self) -> float:
        """7-day rolling average of new IMRAF records per day."""
        try:
            from core.institutional_memory.imraf_engine import imraf
            cutoff_ms = int(time.time() * 1000) - _VELOCITY_WINDOW_DAYS * _MS_PER_DAY
            with imraf._lock:
                row = imraf._conn.execute(
                    "SELECT COUNT(*) as cnt FROM imraf_records WHERE ts >= ?",
                    (cutoff_ms,),
                ).fetchone()
            count = row[0] if row else 0
            return round(count / _VELOCITY_WINDOW_DAYS, 4)
        except Exception:
            return 0.0

    # ── Public API ────────────────────────────────────────────────────────────

    def get_progress(self) -> dict:
        """Return full accumulation progress report."""
        with self._lock:
            boot_ts_ms = self._resolve_boot_ts_ms()
            now_ms = int(time.time() * 1000)
            elapsed_ms = max(0, now_ms - boot_ts_ms)
            live_days = elapsed_ms / _MS_PER_DAY
            progress_pct = min(live_days / _TARGET_DAYS * 100, 100.0)
            projected_activation_ms = boot_ts_ms + _TARGET_DAYS * _MS_PER_DAY
            projected_activation_date = _ms_to_iso(projected_activation_ms)
            velocity = self._evidence_velocity()
            milestones = self.get_milestone_status()

            return {
                "boot_ts": boot_ts_ms,
                "boot_date": _ms_to_iso(boot_ts_ms),
                "live_days": round(live_days, 2),
                "target_days": _TARGET_DAYS,
                "progress_pct": round(progress_pct, 2),
                "milestones": milestones,
                "projected_activation_date": projected_activation_date,
                "evidence_velocity": velocity,
                "threshold_met": self.is_threshold_met(),
                "aeg_readiness": "THRESHOLD_MET" if self.is_threshold_met() else "ACCUMULATING",
            }

    def get_milestone_status(self) -> List[dict]:
        """Return list of milestone dicts with {days, label, status, date}."""
        boot_ts_ms = self._resolve_boot_ts_ms()
        now_ms = int(time.time() * 1000)
        elapsed_ms = max(0, now_ms - boot_ts_ms)
        live_days = elapsed_ms / _MS_PER_DAY

        result = []
        for days, label in _MILESTONES:
            milestone_date = _ms_to_iso(boot_ts_ms + days * _MS_PER_DAY)
            status = "REACHED" if live_days >= days else "PENDING"
            result.append({
                "days": days,
                "label": label,
                "status": status,
                "date": milestone_date,
            })
        return result

    def is_threshold_met(self) -> bool:
        """True if 60+ days of evidence accumulated."""
        boot_ts_ms = self._resolve_boot_ts_ms()
        now_ms = int(time.time() * 1000)
        elapsed_ms = max(0, now_ms - boot_ts_ms)
        return elapsed_ms >= _TARGET_DAYS * _MS_PER_DAY


def _ms_to_iso(ms: int) -> str:
    import datetime
    return datetime.datetime.utcfromtimestamp(ms / 1000).strftime("%Y-%m-%dT%H:%M:%SZ")


evidence_tracker = EvidenceAccumulationTracker()
