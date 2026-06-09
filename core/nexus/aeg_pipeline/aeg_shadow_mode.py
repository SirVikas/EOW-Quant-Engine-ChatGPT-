"""
PHOENIX AEG — Shadow Mode Engine  [GAP-R4 / GAP-C]

AEG Shadow Mode is the final validation stage before full autonomy.

In shadow mode:
  - AEG generates recommendations as normal
  - Recommendations are NOT applied to live trading
  - Outcomes are tracked as if they had been applied
  - Human decisions are tracked in parallel
  - After N recommendations, compare: AEG vs Human performance

This answers: "Would AEG have done better than the human operator?"

Shadow mode lifecycle:
  INACTIVE → ACTIVE → EVALUATION → GRADUATED (ready for live) / FAILED

Graduation requires:
  - MIN_SHADOW_SAMPLES shadow recommendations
  - Shadow accuracy >= GRADUATION_ACCURACY_THRESHOLD
  - Shadow net PnL >= human net PnL (AEG must not underperform)
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


MIN_SHADOW_SAMPLES              = 30
GRADUATION_ACCURACY_THRESHOLD   = 0.72
SHADOW_OUTPERFORMANCE_THRESHOLD = 0.0    # shadow PnL >= human PnL


@dataclass
class ShadowRecommendation:
    shadow_id: str
    rec_type: str
    claimed_outcome: str
    actual_outcome: str = ""
    shadow_correct: Optional[bool] = None
    shadow_pnl: float = 0.0
    human_decision: str = ""    # "APPLIED" / "REJECTED" / "MODIFIED"
    human_pnl: float = 0.0
    generated_at: float = field(default_factory=time.time)
    resolved_at: float = 0.0


@dataclass
class ShadowSession:
    session_id: str
    rec_type: str
    status: str = "ACTIVE"    # ACTIVE / EVALUATION / GRADUATED / FAILED / PAUSED
    started_at: float = field(default_factory=time.time)
    ended_at: float = 0.0
    graduation_reason: str = ""


class AEGShadowMode:
    """
    Tracks AEG shadow recommendations and compares against human decisions.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._sessions: Dict[str, ShadowSession] = {}
        self._recs: List[ShadowRecommendation] = []

    # ── Session Management ────────────────────────────────────────────────────

    def start_shadow(self, rec_type: str) -> ShadowSession:
        session_id = f"SHADOW-{rec_type[:6]}-{int(time.time()*1000)}"
        session = ShadowSession(session_id=session_id, rec_type=rec_type)
        with self._lock:
            self._sessions[session_id] = session
        return session

    def pause_shadow(self, session_id: str) -> dict:
        with self._lock:
            s = self._sessions.get(session_id)
        if not s:
            return {"error": f"Session '{session_id}' not found"}
        s.status = "PAUSED"
        return {"paused": True, "session_id": session_id}

    # ── Shadow Recommendations ────────────────────────────────────────────────

    def record_shadow_rec(
        self,
        rec_type: str,
        claimed_outcome: str,
        human_decision: str = "REJECTED",
    ) -> ShadowRecommendation:
        sr = ShadowRecommendation(
            shadow_id=f"SHD-{rec_type[:4]}-{int(time.time()*1000)}",
            rec_type=rec_type,
            claimed_outcome=claimed_outcome,
            human_decision=human_decision,
        )
        with self._lock:
            self._recs.append(sr)
            if len(self._recs) > 10_000:
                self._recs = self._recs[-10_000:]
        return sr

    def resolve_shadow(
        self,
        shadow_id: str,
        actual_outcome: str,
        shadow_correct: bool,
        shadow_pnl: float,
        human_pnl: float = 0.0,
    ) -> Optional[dict]:
        with self._lock:
            sr = next((r for r in self._recs if r.shadow_id == shadow_id), None)
        if not sr:
            return {"error": f"Shadow rec '{shadow_id}' not found"}
        sr.actual_outcome   = actual_outcome
        sr.shadow_correct   = shadow_correct
        sr.shadow_pnl       = shadow_pnl
        sr.human_pnl        = human_pnl
        sr.resolved_at      = time.time()
        return {"resolved": True, "shadow_id": shadow_id, "shadow_correct": shadow_correct}

    # ── Analysis ──────────────────────────────────────────────────────────────

    def performance_comparison(self, rec_type: str) -> dict:
        with self._lock:
            recs = [r for r in self._recs if r.rec_type == rec_type and r.shadow_correct is not None]
        if not recs:
            return {"rec_type": rec_type, "note": "No resolved shadow recommendations yet"}

        shadow_correct = sum(1 for r in recs if r.shadow_correct)
        shadow_pnl     = sum(r.shadow_pnl for r in recs)
        human_pnl      = sum(r.human_pnl for r in recs)
        shadow_acc     = round(shadow_correct / len(recs), 3)
        outperforms    = shadow_pnl >= human_pnl

        return {
            "rec_type":          rec_type,
            "shadow_samples":    len(recs),
            "shadow_accuracy":   shadow_acc,
            "shadow_net_pnl":    round(shadow_pnl, 4),
            "human_net_pnl":     round(human_pnl, 4),
            "aeg_outperforms":   outperforms,
            "pnl_delta":         round(shadow_pnl - human_pnl, 4),
            "graduation_eligible": (
                len(recs) >= MIN_SHADOW_SAMPLES and
                shadow_acc >= GRADUATION_ACCURACY_THRESHOLD and
                outperforms
            ),
        }

    def evaluate_for_graduation(self, rec_type: str) -> dict:
        comp = self.performance_comparison(rec_type)
        eligible = comp.get("graduation_eligible", False)
        reasons = []
        if comp.get("shadow_samples", 0) < MIN_SHADOW_SAMPLES:
            reasons.append(f"Need {MIN_SHADOW_SAMPLES} samples (have {comp.get('shadow_samples', 0)})")
        if (comp.get("shadow_accuracy") or 0) < GRADUATION_ACCURACY_THRESHOLD:
            reasons.append(f"Accuracy {comp.get('shadow_accuracy', 0):.1%} < {GRADUATION_ACCURACY_THRESHOLD:.0%}")
        if not comp.get("aeg_outperforms"):
            reasons.append("AEG PnL does not exceed human PnL")
        if eligible:
            # Update session status
            with self._lock:
                for s in self._sessions.values():
                    if s.rec_type == rec_type and s.status == "ACTIVE":
                        s.status = "GRADUATED"
                        s.ended_at = time.time()
                        s.graduation_reason = "All graduation criteria met"
        return {
            "rec_type":  rec_type,
            "eligible":  eligible,
            "reasons":   reasons if not eligible else ["All graduation criteria met"],
            "verdict":   "GRADUATED" if eligible else "NOT_READY",
            **comp,
        }

    def all_sessions(self) -> List[dict]:
        with self._lock:
            items = list(self._sessions.values())
        return [
            {
                "session_id":       s.session_id,
                "rec_type":         s.rec_type,
                "status":           s.status,
                "started_at":       s.started_at,
                "ended_at":         s.ended_at or None,
                "graduation_reason": s.graduation_reason,
            }
            for s in sorted(items, key=lambda x: x.started_at, reverse=True)
        ]

    def summary(self) -> dict:
        with self._lock:
            total_recs = len(self._recs)
            resolved = sum(1 for r in self._recs if r.shadow_correct is not None)
            sessions = list(self._sessions.values())
        return {
            "total_shadow_recs":    total_recs,
            "resolved":             resolved,
            "active_sessions":      sum(1 for s in sessions if s.status == "ACTIVE"),
            "graduated_sessions":   sum(1 for s in sessions if s.status == "GRADUATED"),
            "min_samples_required": MIN_SHADOW_SAMPLES,
            "graduation_threshold": GRADUATION_ACCURACY_THRESHOLD,
        }


# Singleton
aeg_shadow_mode = AEGShadowMode()
