"""
PHOENIX AEG — Sandbox Statistics & Recommendation Leaderboard  [AEG-GAP-01/02/03/04]

AEG-GAP-01: Per rec_type sandbox statistics (accuracy, win-rate, sample count)
AEG-GAP-02: Recommendation Leaderboard — ranked by sandbox performance
AEG-GAP-03: Promotion Evidence Package — full evidence bundle for a rec_type
AEG-GAP-04: Automatic demotion with rollback — live recs that degrade get demoted
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


DEMOTION_ACCURACY_FLOOR     = 0.55    # if live rec accuracy drops below, trigger auto-demotion
DEMOTION_MIN_LIVE_SAMPLES   = 10      # minimum live samples before auto-demotion is considered
DEMOTION_LOOKBACK_DAYS      = 14      # window for measuring live accuracy degradation


@dataclass
class SandboxStatRecord:
    rec_type: str
    total: int = 0
    correct: int = 0
    samples_with_outcome: int = 0
    last_updated: float = field(default_factory=time.time)

    @property
    def accuracy(self) -> Optional[float]:
        if self.samples_with_outcome == 0:
            return None
        return round(self.correct / self.samples_with_outcome, 3)

    @property
    def win_rate(self) -> Optional[float]:
        if self.total == 0:
            return None
        return round(self.correct / self.total, 3)


@dataclass
class LivePerformanceRecord:
    rec_type: str
    rec_id: str
    outcome_correct: bool
    recorded_at: float = field(default_factory=time.time)


class AEGSandboxStats:
    """
    AEG-GAP-01: Per rec_type sandbox statistics.
    AEG-GAP-02: Leaderboard.
    AEG-GAP-03: Evidence packages.
    AEG-GAP-04: Auto-demotion tracking.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._stats: Dict[str, SandboxStatRecord] = {}
        self._live_outcomes: List[LivePerformanceRecord] = []
        self._demotion_log: List[dict] = []

    # ── AEG-GAP-01: Ingest ────────────────────────────────────────────────────

    def record_sandbox_outcome(self, rec_type: str, correct: bool) -> None:
        with self._lock:
            s = self._stats.setdefault(rec_type, SandboxStatRecord(rec_type=rec_type))
            s.total += 1
            s.samples_with_outcome += 1
            if correct:
                s.correct += 1
            s.last_updated = time.time()

    def record_sandbox_generated(self, rec_type: str) -> None:
        with self._lock:
            s = self._stats.setdefault(rec_type, SandboxStatRecord(rec_type=rec_type))
            s.total += 1
            s.last_updated = time.time()

    def stats_for(self, rec_type: str) -> dict:
        with self._lock:
            s = self._stats.get(rec_type)
        if not s:
            return {"rec_type": rec_type, "total": 0, "accuracy": None, "note": "No data"}
        return {
            "rec_type":             s.rec_type,
            "total":                s.total,
            "samples_with_outcome": s.samples_with_outcome,
            "correct":              s.correct,
            "accuracy":             s.accuracy,
            "win_rate":             s.win_rate,
            "last_updated":         s.last_updated,
        }

    def all_stats(self) -> List[dict]:
        with self._lock:
            items = list(self._stats.values())
        return [self.stats_for(s.rec_type) for s in items]

    # ── AEG-GAP-02: Leaderboard ───────────────────────────────────────────────

    def leaderboard(self, min_samples: int = 5, limit: int = 20) -> List[dict]:
        with self._lock:
            items = list(self._stats.values())
        ranked = [
            s for s in items
            if s.samples_with_outcome >= min_samples and s.accuracy is not None
        ]
        ranked.sort(key=lambda x: (x.accuracy or 0), reverse=True)
        out = []
        for rank, s in enumerate(ranked[:limit], start=1):
            d = self.stats_for(s.rec_type)
            d["rank"] = rank
            out.append(d)
        return out

    # ── AEG-GAP-03: Evidence Package ──────────────────────────────────────────

    def evidence_package(self, rec_type: str) -> dict:
        sandbox = self.stats_for(rec_type)
        live_recent = self._recent_live_outcomes(rec_type, days=DEMOTION_LOOKBACK_DAYS)

        pipeline_entry = None
        try:
            from core.nexus.aeg_pipeline.aeg_promotion_engine import aeg_promotion_engine
            entries = aeg_promotion_engine.all_entries()
            for e in entries:
                if e["rec_type"] == rec_type:
                    pipeline_entry = e
                    break
        except Exception:
            pass

        trust_status = None
        try:
            from core.observatory.trust_engine import recommendation_trust_engine
            trust_status = recommendation_trust_engine.trust_for_type(rec_type)
        except Exception:
            pass

        return {
            "rec_type":          rec_type,
            "generated_at":      time.time(),
            "sandbox_stats":     sandbox,
            "live_recent_count": len(live_recent),
            "live_recent_accuracy": (
                round(sum(1 for r in live_recent if r.outcome_correct) / len(live_recent), 3)
                if live_recent else None
            ),
            "pipeline_entry":    pipeline_entry,
            "trust_status":      trust_status,
            "promotion_eligible": (
                sandbox.get("accuracy") is not None and
                sandbox.get("accuracy", 0) >= 0.70 and
                sandbox.get("samples_with_outcome", 0) >= 20
            ),
        }

    # ── AEG-GAP-04: Auto-Demotion ─────────────────────────────────────────────

    def record_live_outcome(self, rec_type: str, rec_id: str, correct: bool) -> Optional[dict]:
        rec = LivePerformanceRecord(rec_type=rec_type, rec_id=rec_id, outcome_correct=correct)
        with self._lock:
            self._live_outcomes.append(rec)
            if len(self._live_outcomes) > 5000:
                self._live_outcomes = self._live_outcomes[-5000:]

        return self._check_auto_demotion(rec_type)

    def _recent_live_outcomes(self, rec_type: str, days: int = DEMOTION_LOOKBACK_DAYS) -> List[LivePerformanceRecord]:
        cutoff = time.time() - days * 86400
        with self._lock:
            return [r for r in self._live_outcomes if r.rec_type == rec_type and r.recorded_at >= cutoff]

    def _check_auto_demotion(self, rec_type: str) -> Optional[dict]:
        recent = self._recent_live_outcomes(rec_type)
        if len(recent) < DEMOTION_MIN_LIVE_SAMPLES:
            return None
        accuracy = sum(1 for r in recent if r.outcome_correct) / len(recent)
        if accuracy < DEMOTION_ACCURACY_FLOOR:
            return self._trigger_auto_demotion(rec_type, accuracy, len(recent))
        return None

    def _trigger_auto_demotion(self, rec_type: str, live_accuracy: float, sample_count: int) -> dict:
        event = {
            "rec_type":       rec_type,
            "live_accuracy":  round(live_accuracy, 3),
            "sample_count":   sample_count,
            "threshold":      DEMOTION_ACCURACY_FLOOR,
            "triggered_at":   time.time(),
            "action":         "DEMOTED_TO_SANDBOX",
        }
        with self._lock:
            self._demotion_log.append(event)

        # Mark the pipeline entry as demoted
        try:
            from core.nexus.aeg_pipeline.aeg_promotion_engine import aeg_promotion_engine
            entries = aeg_promotion_engine.all_entries(stage_filter="PROMOTED_TO_LIVE")
            for e in entries:
                if e["rec_type"] == rec_type:
                    aeg_promotion_engine._entries[e["rec_id"]]._transition(
                        aeg_promotion_engine._entries[e["rec_id"]], "AEG_SANDBOX"
                    )
        except Exception:
            pass

        return event

    def demotion_log(self) -> List[dict]:
        with self._lock:
            return list(self._demotion_log)

    def rollback_demotion(self, rec_type: str, approved_by: str) -> dict:
        try:
            from core.nexus.aeg_pipeline.aeg_promotion_engine import aeg_promotion_engine
            # Re-promote the most recent matching entry that's in AEG_SANDBOX after demotion
            entries = aeg_promotion_engine.all_entries()
            for e in entries:
                if e["rec_type"] == rec_type and e["stage"] == "AEG_SANDBOX":
                    result = aeg_promotion_engine.approve_promotion(e["rec_id"], approved_by=approved_by)
                    return {"rolled_back": True, "rec_type": rec_type, **result}
            return {"error": f"No demoted sandbox entry found for rec_type '{rec_type}'"}
        except Exception as ex:
            return {"error": str(ex)}

    def oversight_summary(self) -> dict:
        with self._lock:
            total_demotions = len(self._demotion_log)
        try:
            from core.nexus.aeg_pipeline.aeg_promotion_engine import aeg_promotion_engine
            pipe_summary = aeg_promotion_engine.summary()
        except Exception:
            pipe_summary = {}

        return {
            "auto_demotions":          total_demotions,
            "demotion_accuracy_floor": DEMOTION_ACCURACY_FLOOR,
            "demotion_min_samples":    DEMOTION_MIN_LIVE_SAMPLES,
            "demotion_lookback_days":  DEMOTION_LOOKBACK_DAYS,
            "pipeline":                pipe_summary,
            "leaderboard_top5":        self.leaderboard(limit=5),
        }


# Singleton
aeg_sandbox_stats = AEGSandboxStats()
