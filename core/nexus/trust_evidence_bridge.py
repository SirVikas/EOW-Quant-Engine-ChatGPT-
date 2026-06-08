"""
PHOENIX NEXUS — Trust Evidence Integration Bridge  [NEXUS-TRUST-EVIDENCE-01]

Connects the Trust Program (PTP) to NEXUS institutional memory.

Responsibilities:
  - When a new validation event is recorded in PTP, mirror it to IMRAF
  - When a pillar is promoted/demoted, record the milestone in IMRAF
  - When accuracy ledger passes a threshold, record the insight
  - When trust decay becomes critical, flag it in IMRAF
  - Provides a unified trust evidence snapshot for NEXUS queries

This is the feedback loop that closes the triangle:
  Observatory → PTP → NEXUS → Observatory
"""
from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional


class TrustEvidenceBridge:
    """
    Mirrors PTP events into NEXUS institutional memory and provides
    a cross-layer trust evidence summary.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._mirrored_events: List[dict] = []

    # ── Mirroring ─────────────────────────────────────────────────────────────

    def mirror_validation(
        self,
        pillar: str,
        entity_id: str,
        correct: bool,
        evidence_detail: str = "",
    ) -> None:
        self._mirror(
            category="trust_validation",
            title=f"[TRUST] {pillar} validation — {'CORRECT' if correct else 'INCORRECT'} | {entity_id}",
            content=f"Pillar: {pillar} | Entity: {entity_id} | Correct: {correct} | Detail: {evidence_detail}",
            tags=["trust", pillar.lower(), "validation", "correct" if correct else "incorrect"],
        )

    def mirror_promotion(self, pillar: str, from_rung: str, to_rung: str, score: float) -> None:
        direction = "PROMOTED" if to_rung > from_rung else "DEMOTED"
        self._mirror(
            category="trust_promotion",
            title=f"[TRUST LADDER] {pillar} {direction}: {from_rung} → {to_rung}",
            content=f"Pillar: {pillar} | Score: {score:.1f} | {from_rung} → {to_rung}",
            tags=["trust", "promotion", pillar.lower(), to_rung.lower()],
        )

    def mirror_revocation(self, pillar: str, entity_id: str, consecutive_fails: int, demoted_to: str) -> None:
        self._mirror(
            category="trust_revocation",
            title=f"[TRUST REVOCATION] {pillar} revoked — {consecutive_fails} consecutive failures",
            content=f"Pillar: {pillar} | Entity: {entity_id} | Consecutive failures: {consecutive_fails} | Demoted to: {demoted_to}",
            tags=["trust", "revocation", pillar.lower(), "critical"],
        )

    def mirror_decay_alert(self, pillar: str, raw_score: float, adjusted_score: float, days_stale: float) -> None:
        self._mirror(
            category="trust_decay",
            title=f"[TRUST DECAY] {pillar} score degraded — {days_stale:.1f} days stale",
            content=f"Pillar: {pillar} | Raw: {raw_score:.1f} → Adjusted: {adjusted_score:.1f} | Stale: {days_stale:.1f} days",
            tags=["trust", "decay", pillar.lower(), "stale"],
        )

    def mirror_aeg_promotion(self, rec_type: str, rec_id: str, trust_score: float, sandbox_accuracy: float) -> None:
        self._mirror(
            category="aeg_promotion",
            title=f"[AEG] {rec_type} promoted to LIVE",
            content=f"rec_type: {rec_type} | rec_id: {rec_id} | Trust: {trust_score:.1f} | Sandbox accuracy: {sandbox_accuracy:.1%}",
            tags=["aeg", "promotion", rec_type.lower()],
        )

    def mirror_aeg_demotion(self, rec_type: str, live_accuracy: float) -> None:
        self._mirror(
            category="aeg_demotion",
            title=f"[AEG] {rec_type} auto-demoted — live accuracy {live_accuracy:.1%}",
            content=f"rec_type: {rec_type} | Live accuracy fell below threshold: {live_accuracy:.1%}",
            tags=["aeg", "demotion", rec_type.lower(), "degraded"],
        )

    # ── Unified Snapshot ──────────────────────────────────────────────────────

    def trust_evidence_snapshot(self) -> dict:
        snapshot: Dict[str, Any] = {
            "generated_at": time.time(),
            "ptp_health":   None,
            "decay_status": None,
            "ladder":       None,
            "aeg_pipeline": None,
            "revocations":  None,
        }

        try:
            from core.trust.trust_validation_registry import trust_validation_registry
            snapshot["ptp_health"] = trust_validation_registry.overall_trust_health()
        except Exception:
            pass

        try:
            from core.trust.trust_decay_engine import trust_decay_engine
            snapshot["decay_status"] = trust_decay_engine.all_decay_statuses()
            snapshot["revocations"] = trust_decay_engine.revocation_log()
        except Exception:
            pass

        try:
            from core.trust.trust_promotion_ladder import trust_promotion_ladder
            snapshot["ladder"] = trust_promotion_ladder.program_overview()
        except Exception:
            pass

        try:
            from core.nexus.aeg_pipeline.aeg_promotion_engine import aeg_promotion_engine
            snapshot["aeg_pipeline"] = aeg_promotion_engine.summary()
        except Exception:
            pass

        return snapshot

    # ── Internal ──────────────────────────────────────────────────────────────

    def _mirror(self, category: str, title: str, content: str, tags: List[str]) -> None:
        event = {
            "category":    category,
            "title":       title,
            "content":     content,
            "tags":        tags,
            "mirrored_at": time.time(),
        }
        with self._lock:
            self._mirrored_events.append(event)
            if len(self._mirrored_events) > 2000:
                self._mirrored_events = self._mirrored_events[-2000:]

        try:
            from core.observatory.nexus_bridge import _imraf
            im = _imraf()
            if im:
                im.record_knowledge(title=title, content=content, category=category, tags=tags)
        except Exception:
            pass

    def recent_mirrors(self, limit: int = 50) -> List[dict]:
        with self._lock:
            items = list(self._mirrored_events)
        return sorted(items, key=lambda x: x["mirrored_at"], reverse=True)[:limit]


# Singleton
trust_evidence_bridge = TrustEvidenceBridge()
