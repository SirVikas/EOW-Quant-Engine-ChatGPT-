"""
PHOENIX TRUST PROGRAM — Trust Decay Engine  [PTP-GAP-03 / PTP-GAP-04]

PTP-GAP-03: Trust Decay
  - Trust that is not reinforced with new evidence becomes stale.
  - After DECAY_STALE_DAYS with no new validations, a pillar's effective
    score is reduced by DECAY_RATE_PER_DAY per additional day.
  - Decay is advisory: the raw stored score is unchanged, but
    decay_adjusted_score() returns the degraded value.

PTP-GAP-04: Trust Revocation
  - A TRUSTED (or higher) entity that accumulates REVOCATION_FAIL_THRESHOLD
    consecutive failures within REVOCATION_WINDOW_DAYS has its rung
    forcibly demoted by one level.
  - Revocation events are recorded in the revocation log.
  - Re-earning trust requires starting a new evidence run from the demoted rung.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


DECAY_STALE_DAYS        = 14          # days before staleness begins
DECAY_RATE_PER_DAY      = 0.5         # score points lost per day after stale window
DECAY_FLOOR             = 5.0         # score never decays below this floor

REVOCATION_FAIL_THRESHOLD = 10        # consecutive failures to trigger revocation
REVOCATION_WINDOW_DAYS    = 30        # failures must fall within this window

_RUNG_ORDER = [
    "UNVERIFIED",
    "PROVISIONAL",
    "TRUSTED",
    "INSTITUTIONAL",
    "CONSTITUTIONAL",
]


@dataclass
class DecayStatus:
    pillar: str
    raw_score: float
    last_evidence_ts: float
    days_since_evidence: float
    decay_applied: float
    adjusted_score: float
    is_stale: bool
    decay_note: str


@dataclass
class RevocationEvent:
    event_id: str
    pillar: str
    entity_id: str
    previous_rung: str
    demoted_to_rung: str
    consecutive_failures: int
    reason: str
    revoked_at: float = field(default_factory=time.time)
    reinstated_at: float = 0.0
    reinstated: bool = False


class TrustDecayEngine:
    """
    PTP-GAP-03: Computes effective (decay-adjusted) trust scores when evidence is stale.
    PTP-GAP-04: Tracks consecutive failures and issues revocations when threshold is hit.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._last_evidence_ts: Dict[str, float] = {}      # pillar → timestamp
        self._consecutive_fails: Dict[str, List[float]] = {}  # pillar → list of fail timestamps
        self._revocations: List[RevocationEvent] = []

    # ── PTP-GAP-03: Decay ──────────────────────────────────────────────────────

    def notify_new_evidence(self, pillar: str) -> None:
        with self._lock:
            self._last_evidence_ts[pillar] = time.time()

    def decay_status(self, pillar: str, raw_score: float) -> DecayStatus:
        now = time.time()
        with self._lock:
            last_ts = self._last_evidence_ts.get(pillar, 0.0)

        if last_ts == 0.0:
            return DecayStatus(
                pillar=pillar,
                raw_score=raw_score,
                last_evidence_ts=0.0,
                days_since_evidence=0.0,
                decay_applied=0.0,
                adjusted_score=raw_score,
                is_stale=False,
                decay_note="No evidence recorded yet — no decay applicable",
            )

        days_elapsed = (now - last_ts) / 86400.0
        stale_days = max(0.0, days_elapsed - DECAY_STALE_DAYS)
        decay = min(raw_score - DECAY_FLOOR, stale_days * DECAY_RATE_PER_DAY)
        decay = max(0.0, decay)
        adjusted = raw_score - decay
        is_stale = days_elapsed > DECAY_STALE_DAYS

        note = (
            f"Decayed {decay:.2f} pts ({stale_days:.1f} days past stale window)"
            if is_stale else
            f"Fresh — {DECAY_STALE_DAYS - days_elapsed:.1f} days until stale"
        )

        return DecayStatus(
            pillar=pillar,
            raw_score=raw_score,
            last_evidence_ts=last_ts,
            days_since_evidence=days_elapsed,
            decay_applied=decay,
            adjusted_score=round(adjusted, 2),
            is_stale=is_stale,
            decay_note=note,
        )

    def all_decay_statuses(self) -> List[dict]:
        try:
            from core.trust.trust_validation_registry import PILLARS, trust_registry
        except Exception:
            return []
        out = []
        for p in PILLARS:
            status = trust_registry.pillar_status(p)
            raw_score = status.get("score", 0.0)
            ds = self.decay_status(p, raw_score)
            out.append({
                "pillar":              ds.pillar,
                "raw_score":           ds.raw_score,
                "adjusted_score":      ds.adjusted_score,
                "decay_applied":       ds.decay_applied,
                "days_since_evidence": round(ds.days_since_evidence, 1),
                "is_stale":            ds.is_stale,
                "decay_note":          ds.decay_note,
                "last_evidence_ts":    ds.last_evidence_ts,
            })
        return out

    # ── PTP-GAP-04: Revocation ─────────────────────────────────────────────────

    def record_outcome(self, pillar: str, entity_id: str, correct: bool) -> Optional[RevocationEvent]:
        now = time.time()
        key = f"{pillar}::{entity_id}"
        cutoff = now - REVOCATION_WINDOW_DAYS * 86400

        with self._lock:
            if correct:
                # Success resets the consecutive-failure streak
                self._consecutive_fails[key] = []
                return None

            bucket = self._consecutive_fails.get(key, [])
            bucket = [ts for ts in bucket if ts >= cutoff]  # prune old failures
            bucket.append(now)
            self._consecutive_fails[key] = bucket

            if len(bucket) >= REVOCATION_FAIL_THRESHOLD:
                return self._issue_revocation(pillar, entity_id, len(bucket))

        return None

    def _issue_revocation(self, pillar: str, entity_id: str, fail_count: int) -> Optional[RevocationEvent]:
        try:
            from core.trust.trust_promotion_ladder import trust_promotion_ladder
        except Exception:
            return None

        current = trust_promotion_ladder.current_rung(pillar)
        rung_name = current.get("rung", "UNVERIFIED")
        if rung_name == "UNVERIFIED":
            return None  # can't demote further

        idx = _RUNG_ORDER.index(rung_name) if rung_name in _RUNG_ORDER else 0
        demoted_to = _RUNG_ORDER[max(0, idx - 1)]

        ev = RevocationEvent(
            event_id=f"REV-{pillar[:4]}-{int(time.time()*1000)}",
            pillar=pillar,
            entity_id=entity_id,
            previous_rung=rung_name,
            demoted_to_rung=demoted_to,
            consecutive_failures=fail_count,
            reason=f"{fail_count} consecutive failures in {REVOCATION_WINDOW_DAYS}-day window",
        )
        self._revocations.append(ev)

        # Apply demotion
        try:
            trust_promotion_ladder.force_demote(pillar, demoted_to, reason=ev.reason)
        except Exception:
            pass

        # Reset failure bucket to prevent immediate re-revocation
        key = f"{pillar}::{entity_id}"
        self._consecutive_fails[key] = []

        return ev

    def reinstate(self, event_id: str) -> dict:
        with self._lock:
            ev = next((e for e in self._revocations if e.event_id == event_id), None)
        if not ev:
            return {"error": f"Revocation event '{event_id}' not found"}
        if ev.reinstated:
            return {"error": "Already reinstated"}
        try:
            from core.trust.trust_promotion_ladder import trust_promotion_ladder
            trust_promotion_ladder.force_demote(ev.pillar, ev.previous_rung, reason=f"Reinstatement of {event_id}")
            ev.reinstated = True
            ev.reinstated_at = time.time()
            return {"reinstated": True, "event_id": event_id, "restored_rung": ev.previous_rung}
        except Exception as e:
            return {"error": str(e)}

    # ── Query ──────────────────────────────────────────────────────────────────

    def revocation_log(self, pillar: Optional[str] = None) -> List[dict]:
        with self._lock:
            items = list(self._revocations)
        if pillar:
            items = [e for e in items if e.pillar == pillar]
        return [self._ser(e) for e in sorted(items, key=lambda x: x.revoked_at, reverse=True)]

    def summary(self) -> dict:
        with self._lock:
            total = len(self._revocations)
            active = sum(1 for e in self._revocations if not e.reinstated)
        return {
            "total_revocations":  total,
            "active_revocations": active,
            "reinstated":         total - active,
            "stale_threshold_days": DECAY_STALE_DAYS,
            "decay_rate_per_day": DECAY_RATE_PER_DAY,
            "decay_floor":        DECAY_FLOOR,
            "revocation_fail_threshold": REVOCATION_FAIL_THRESHOLD,
            "revocation_window_days":    REVOCATION_WINDOW_DAYS,
        }

    @staticmethod
    def _ser(e: RevocationEvent) -> dict:
        return {
            "event_id":             e.event_id,
            "pillar":               e.pillar,
            "entity_id":            e.entity_id,
            "previous_rung":        e.previous_rung,
            "demoted_to_rung":      e.demoted_to_rung,
            "consecutive_failures": e.consecutive_failures,
            "reason":               e.reason,
            "revoked_at":           e.revoked_at,
            "reinstated":           e.reinstated,
            "reinstated_at":        e.reinstated_at or None,
        }


# Singleton
trust_decay_engine = TrustDecayEngine()
