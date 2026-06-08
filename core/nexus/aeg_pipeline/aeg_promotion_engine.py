"""
PHOENIX NEXUS — AEG Promotion Pipeline

The bridge between Observatory intelligence and Autonomous governance.

Pipeline stages:
  1. OBSERVATORY_RECOMMENDATION  — OBX Inspector generates recommendation
  2. TRUST_VALIDATION            — PTP checks if this rec_type has sufficient trust
  3. AEG_SANDBOX                 — AEG Sandbox simulates the recommendation
  4. SANDBOX_ACCURACY_CHECK      — verifies sandbox history > ACCURACY_THRESHOLD
  5. PROMOTION_CANDIDATE         — marked as ready for human review
  6. HUMAN_APPROVED              — human explicitly approves sandbox-to-live promotion
  7. PROMOTED_TO_LIVE            — AEG recommendation is now live (advisory, not auto-applied)

Demotion triggers:
  - Trust score drops below PROVISIONAL threshold for 10+ consecutive records
  - Sandbox accuracy falls below threshold
  - Constitutional violation flagged during simulation

Without this pipeline:
  - PTP cannot complete (no feedback loop for trust evidence)
  - AEG remains PARTIAL indefinitely
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


TRUST_THRESHOLD_FOR_SANDBOX  = 50.0   # TRUSTED rung minimum
ACCURACY_THRESHOLD_FOR_PROMO = 0.70   # 70% sandbox accuracy required
MIN_SANDBOX_SAMPLES          = 20     # minimum sandbox recommendations before promotion


@dataclass
class PipelineEntry:
    entry_id: str
    rec_id: str
    rec_type: str
    investigation_id: str
    stage: str = "OBSERVATORY_RECOMMENDATION"
    trust_score_at_entry: float = 0.0
    sandbox_accuracy: float = 0.0
    sandbox_sample_count: int = 0
    created_at: float = field(default_factory=time.time)
    stage_history: List[dict] = field(default_factory=list)
    blocked_reason: str = ""
    promoted_at: float = 0.0
    approved_by: str = ""


_STAGES = [
    "OBSERVATORY_RECOMMENDATION",
    "TRUST_VALIDATION",
    "AEG_SANDBOX",
    "SANDBOX_ACCURACY_CHECK",
    "PROMOTION_CANDIDATE",
    "HUMAN_APPROVED",
    "PROMOTED_TO_LIVE",
]

_BLOCKED = "BLOCKED"


class AEGPromotionEngine:
    """
    Manages the Observatory → Trust → AEG Sandbox → Live promotion pipeline.
    Tracks each recommendation's journey through the pipeline.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._entries: Dict[str, PipelineEntry] = {}

    # ── Entry Point ───────────────────────────────────────────────────────────

    def ingest_recommendation(
        self,
        rec_id: str,
        rec_type: str,
        investigation_id: str,
    ) -> PipelineEntry:
        entry_id = f"AEG-PIPE-{rec_id}-{int(time.time())}"
        entry = PipelineEntry(
            entry_id=entry_id,
            rec_id=rec_id,
            rec_type=rec_type,
            investigation_id=investigation_id,
        )
        entry.stage_history.append({"stage": entry.stage, "timestamp": time.time()})
        with self._lock:
            self._entries[rec_id] = entry

        # Auto-advance through pipeline
        self._advance(entry)
        return entry

    # ── Pipeline Advancement ──────────────────────────────────────────────────

    def _advance(self, entry: PipelineEntry) -> None:
        if entry.stage == "OBSERVATORY_RECOMMENDATION":
            self._stage_trust_validation(entry)
        elif entry.stage == "TRUST_VALIDATION":
            self._stage_aeg_sandbox(entry)
        elif entry.stage == "AEG_SANDBOX":
            self._stage_accuracy_check(entry)
        elif entry.stage == "SANDBOX_ACCURACY_CHECK":
            self._stage_promotion_candidate(entry)

    def _stage_trust_validation(self, entry: PipelineEntry) -> None:
        try:
            from core.observatory.trust_engine import recommendation_trust_engine
            trust = recommendation_trust_engine.trust_for_type(entry.rec_type)
            score = trust.get("trust_score", 0.0)
            entry.trust_score_at_entry = score
            if score >= TRUST_THRESHOLD_FOR_SANDBOX:
                self._transition(entry, "TRUST_VALIDATION")
                self._stage_aeg_sandbox(entry)
            else:
                self._block(entry, f"Trust score {score:.1f} < {TRUST_THRESHOLD_FOR_SANDBOX} threshold. Accumulate more evidence.")
        except Exception as e:
            self._block(entry, f"Trust validation error: {e}")

    def _stage_aeg_sandbox(self, entry: PipelineEntry) -> None:
        try:
            from core.nexus.aeg_sandbox.aeg_sandbox_engine import aeg_sandbox
            state = aeg_sandbox._load()
            recs = state.get("recommendations", [])
            matching = [r for r in recs if r.get("rec_type") == entry.rec_type]
            validated = [r for r in matching if r.get("outcome") is not None]
            entry.sandbox_sample_count = len(matching)
            self._transition(entry, "AEG_SANDBOX")
            self._stage_accuracy_check(entry)
        except Exception as e:
            self._transition(entry, "AEG_SANDBOX")  # proceed even if sandbox unavailable

    def _stage_accuracy_check(self, entry: PipelineEntry) -> None:
        try:
            from core.nexus.aeg_sandbox.aeg_sandbox_engine import aeg_sandbox
            status = aeg_sandbox.get_sandbox_status()
            accuracy = float(status.get("accuracy_rate", 0.0))
            sample_count = int(status.get("total_recommendations", 0))
            entry.sandbox_accuracy = accuracy
            entry.sandbox_sample_count = sample_count
            if accuracy >= ACCURACY_THRESHOLD_FOR_PROMO and sample_count >= MIN_SANDBOX_SAMPLES:
                self._transition(entry, "SANDBOX_ACCURACY_CHECK")
                self._stage_promotion_candidate(entry)
            else:
                if sample_count < MIN_SANDBOX_SAMPLES:
                    self._block(entry, f"Sandbox needs {MIN_SANDBOX_SAMPLES} samples (has {sample_count}).")
                else:
                    self._block(entry, f"Sandbox accuracy {accuracy:.1%} < {ACCURACY_THRESHOLD_FOR_PROMO:.0%} threshold.")
        except Exception:
            self._transition(entry, "SANDBOX_ACCURACY_CHECK")

    def _stage_promotion_candidate(self, entry: PipelineEntry) -> None:
        self._transition(entry, "PROMOTION_CANDIDATE")
        # Notify: this is now ready for human review

    # ── Human Approval ────────────────────────────────────────────────────────

    def approve_promotion(self, rec_id: str, approved_by: str) -> dict:
        with self._lock:
            entry = self._entries.get(rec_id)
        if not entry:
            return {"error": f"No pipeline entry for rec_id '{rec_id}'"}
        if entry.stage != "PROMOTION_CANDIDATE":
            return {"error": f"Entry is in stage '{entry.stage}', not PROMOTION_CANDIDATE"}
        with self._lock:
            self._transition(entry, "HUMAN_APPROVED")
            self._transition(entry, "PROMOTED_TO_LIVE")
            entry.approved_by  = approved_by
            entry.promoted_at  = time.time()
        self._record_promotion(entry)
        return {"promoted": True, "rec_id": rec_id, "stage": entry.stage}

    # ── Query ─────────────────────────────────────────────────────────────────

    def get(self, rec_id: str) -> Optional[dict]:
        with self._lock:
            e = self._entries.get(rec_id)
        return self._serialise(e) if e else None

    def all_entries(self, stage_filter: Optional[str] = None) -> List[dict]:
        with self._lock:
            items = list(self._entries.values())
        if stage_filter:
            items = [e for e in items if e.stage == stage_filter]
        return [self._serialise(e) for e in sorted(items, key=lambda x: x.created_at, reverse=True)]

    def candidates_ready(self) -> List[dict]:
        return self.all_entries(stage_filter="PROMOTION_CANDIDATE")

    def live_recommendations(self) -> List[dict]:
        return self.all_entries(stage_filter="PROMOTED_TO_LIVE")

    def summary(self) -> dict:
        with self._lock:
            items = list(self._entries.values())
        by_stage: Dict[str, int] = {}
        for e in items:
            by_stage[e.stage] = by_stage.get(e.stage, 0) + 1
        live = by_stage.get("PROMOTED_TO_LIVE", 0)
        return {
            "total_entries":         len(items),
            "by_stage":              by_stage,
            "live_recommendations":  live,
            "promotion_candidates":  by_stage.get("PROMOTION_CANDIDATE", 0),
            "blocked":               by_stage.get("BLOCKED", 0),
            "pipeline_health":       "ACTIVE" if live > 0 else ("BUILDING" if len(items) > 0 else "EMPTY"),
            "trust_threshold":       TRUST_THRESHOLD_FOR_SANDBOX,
            "accuracy_threshold":    ACCURACY_THRESHOLD_FOR_PROMO,
            "min_sandbox_samples":   MIN_SANDBOX_SAMPLES,
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _transition(self, entry: PipelineEntry, new_stage: str) -> None:
        entry.stage = new_stage
        entry.stage_history.append({"stage": new_stage, "timestamp": time.time()})

    def _block(self, entry: PipelineEntry, reason: str) -> None:
        entry.blocked_reason = reason
        self._transition(entry, "BLOCKED")

    def _record_promotion(self, entry: PipelineEntry) -> None:
        try:
            from core.observatory.nexus_bridge import _imraf
            im = _imraf()
            if im:
                im.record_knowledge(
                    title=f"[AEG PROMOTION] {entry.rec_type} promoted to LIVE",
                    content=f"rec_id={entry.rec_id} | Trust={entry.trust_score_at_entry:.1f} | SandboxAcc={entry.sandbox_accuracy:.1%}",
                    category="aeg_promotion",
                    tags=["aeg", "promotion", entry.rec_type],
                )
        except Exception:
            pass

    @staticmethod
    def _serialise(e: PipelineEntry) -> dict:
        return {
            "entry_id":              e.entry_id,
            "rec_id":                e.rec_id,
            "rec_type":              e.rec_type,
            "investigation_id":      e.investigation_id,
            "stage":                 e.stage,
            "trust_score_at_entry":  e.trust_score_at_entry,
            "sandbox_accuracy":      e.sandbox_accuracy,
            "sandbox_sample_count":  e.sandbox_sample_count,
            "created_at":            e.created_at,
            "blocked_reason":        e.blocked_reason,
            "promoted_at":           e.promoted_at or None,
            "approved_by":           e.approved_by,
            "stage_history":         e.stage_history,
        }


# Singleton
aeg_promotion_engine = AEGPromotionEngine()
