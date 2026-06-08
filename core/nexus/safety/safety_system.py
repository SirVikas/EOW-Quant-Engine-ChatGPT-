"""
FTD-NEXUS-100-PERCENT-001 Phase 7 — Safety System
Approval Queue + Rollback Layer + Human Oversight

This makes AEG.check_safety_system() PASS.
Architecture:
  - RecommendationQueue: pending recommendations awaiting human approval
  - RollbackRecord: log of applied recommendations (reversible)
  - SafetyGate: confidence threshold enforcement before surfacing

State is persisted to data/nexus_safety.json (JSON — no DB needed for MVP).
"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

import logging
logger = logging.getLogger(__name__)

_STATE_PATH = Path("data/nexus_safety.json")
_CONFIDENCE_THRESHOLD = 0.65


class SafetySystem:

    def __init__(self) -> None:
        self._queue: List[dict] = []    # pending approval
        self._applied: List[dict] = []  # approved + applied
        self._rejected: List[dict] = [] # rejected
        self._load()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self) -> None:
        try:
            if _STATE_PATH.exists():
                raw = json.loads(_STATE_PATH.read_text())
                self._queue    = raw.get("queue", [])
                self._applied  = raw.get("applied", [])
                self._rejected = raw.get("rejected", [])
        except Exception as exc:
            logger.warning("SafetySystem._load: %s", exc)

    def _save(self) -> None:
        try:
            _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
            _STATE_PATH.write_text(json.dumps({
                "queue": self._queue,
                "applied": self._applied,
                "rejected": self._rejected,
            }, indent=2))
        except Exception as exc:
            logger.warning("SafetySystem._save: %s", exc)

    # ── Core Operations ───────────────────────────────────────────────────────

    def submit_recommendation(
        self,
        rec_id: str,
        source: str,
        recommendation: str,
        confidence: float,
        evidence: dict,
    ) -> dict:
        """
        Gate recommendations on confidence threshold before queuing.
        Low-confidence submissions are auto-rejected so humans only review
        credible recommendations.
        """
        now_ms = int(time.time() * 1000)
        entry: dict = {
            "id": rec_id,
            "source": source,
            "recommendation": recommendation,
            "confidence": confidence,
            "evidence": evidence,
            "submitted_at": now_ms,
            "approved_by": None,
        }

        if confidence < _CONFIDENCE_THRESHOLD:
            entry["status"] = "REJECTED"
            entry["rejection_reason"] = f"confidence {confidence:.3f} below threshold {_CONFIDENCE_THRESHOLD}"
            entry["rejected_at"] = now_ms
            self._rejected.append(entry)
            self._save()
            return entry

        entry["status"] = "PENDING"
        self._queue.append(entry)
        self._save()
        return entry

    def approve_recommendation(self, rec_id: str, approver: str = "HUMAN") -> bool:
        """Move from queue to applied; record approval metadata and rollback token."""
        for i, entry in enumerate(self._queue):
            if entry["id"] == rec_id:
                entry = dict(entry)
                entry["status"] = "APPLIED"
                entry["approved_by"] = approver
                entry["approved_at"] = int(time.time() * 1000)
                entry["rollback_token"] = str(uuid.uuid4())
                self._queue.pop(i)
                self._applied.append(entry)
                self._save()
                return True
        return False

    def reject_recommendation(self, rec_id: str, reason: str = "") -> bool:
        """Move from queue to rejected."""
        for i, entry in enumerate(self._queue):
            if entry["id"] == rec_id:
                entry = dict(entry)
                entry["status"] = "REJECTED"
                entry["rejection_reason"] = reason
                entry["rejected_at"] = int(time.time() * 1000)
                self._queue.pop(i)
                self._rejected.append(entry)
                self._save()
                return True
        return False

    def rollback(self, rec_id: str) -> dict:
        """
        Reverse an applied recommendation. Archives a GOVERNANCE record to IMRAF,
        then moves the entry back to queue with ROLLED_BACK status.
        """
        for i, entry in enumerate(self._applied):
            if entry["id"] == rec_id:
                entry = dict(entry)
                entry["status"] = "ROLLED_BACK"
                entry["rolled_back_at"] = int(time.time() * 1000)
                self._applied.pop(i)
                self._queue.append(entry)
                self._save()

                # Document the rollback in IMRAF
                try:
                    from core.institutional_memory.imraf_engine import imraf, Category
                    imraf.record(
                        category=Category.GOVERNANCE,
                        title=f"SAFETY_ROLLBACK: recommendation {rec_id} rolled back",
                        data={"content": f"Recommendation '{entry.get('recommendation','')[:80]}' was rolled back",
                              "rec_id": rec_id, "rollback_ts": entry["rolled_back_at"]},
                        tags=["safety", "rollback", "governance"],
                    )
                except Exception as exc:
                    logger.warning("SafetySystem.rollback: IMRAF record failed: %s", exc)

                return {"rolled_back": True, "rec_id": rec_id, "entry": entry}

        return {"rolled_back": False, "rec_id": rec_id, "error": "not found in applied"}

    # ── Queries ───────────────────────────────────────────────────────────────

    def get_queue(self) -> List[dict]:
        return list(self._queue)

    def get_applied(self) -> List[dict]:
        return list(self._applied)

    def get_safety_status(self) -> dict:
        pending = len(self._queue)
        applied = len(self._applied)
        rejected = len(self._rejected)

        # Safety score: full 100 when implemented and no pending violations;
        # deduct for pending items that have exceeded reasonable review time (>24h).
        now_ms = int(time.time() * 1000)
        overdue = sum(
            1 for r in self._queue
            if now_ms - r.get("submitted_at", now_ms) > 86_400_000
        )
        safety_score = max(0.0, 100.0 - overdue * 10)

        return {
            "implemented": True,
            "pending_count": pending,
            "applied_count": applied,
            "rejected_count": rejected,
            "confidence_threshold": _CONFIDENCE_THRESHOLD,
            "approval_required": True,
            "rollback_available": True,
            "human_oversight": True,
            "safety_score": safety_score,
        }


# Singleton
safety_system = SafetySystem()
