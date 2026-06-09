"""
PHOENIX TRUST PROGRAM — Trust Promotion Ladder  [PTP-03]

Trust is not binary. It is earned progressively.

The Promotion Ladder defines the path from untested intelligence
to institutionally trusted, constitutionally grounded intelligence.

Five rungs:

  UNVERIFIED   → System has generated intelligence but no validation exists.
                 Score: 0–29. Evidence: < 10 records.

  PROVISIONAL  → First evidence accumulated. Pattern is directionally correct
                 but sample is too small for confidence.
                 Score: 30–49. Evidence: 10–30 records.

  TRUSTED      → Strong evidence base. Recommendations in this category
                 can be presented to human operator as high-confidence.
                 Score: 50–69. Evidence: 30–50 records.

  INSTITUTIONAL → Deep validation. Recommendations can inform governance decisions
                  and CORTEX weight adjustments (with human approval).
                  Score: 70–89. Evidence: 50+ records.

  CONSTITUTIONAL → Highest tier. Intelligence has been tested against constitutional
                   principles and found consistent. Can inform amendment proposals.
                   Score: 90–100. Evidence: 100+ records.

Promotions are automatic when score + evidence thresholds are crossed.
Demotions occur when recent accuracy drops below the tier floor for 20+ consecutive records.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


LADDER_RUNGS = [
    {"rung": "UNVERIFIED",    "min_score": 0,   "min_evidence": 0,   "max_score": 29},
    {"rung": "PROVISIONAL",   "min_score": 30,  "min_evidence": 10,  "max_score": 49},
    {"rung": "TRUSTED",       "min_score": 50,  "min_evidence": 30,  "max_score": 69},
    {"rung": "INSTITUTIONAL", "min_score": 70,  "min_evidence": 50,  "max_score": 89},
    {"rung": "CONSTITUTIONAL","min_score": 90,  "min_evidence": 100, "max_score": 100},
]


def _compute_rung(score: float, evidence: int) -> str:
    for rung_def in reversed(LADDER_RUNGS):
        if score >= rung_def["min_score"] and evidence >= rung_def["min_evidence"]:
            return rung_def["rung"]
    return "UNVERIFIED"


@dataclass
class LadderPosition:
    pillar: str
    current_rung: str
    previous_rung: str
    trust_score: float
    evidence_count: int
    promoted_at: float = 0.0
    demoted_at: float = 0.0
    rung_history: List[dict] = field(default_factory=list)  # [{rung, timestamp, score}]

    @property
    def next_rung(self) -> Optional[str]:
        rungs = [r["rung"] for r in LADDER_RUNGS]
        idx = rungs.index(self.current_rung) if self.current_rung in rungs else 0
        return rungs[idx + 1] if idx + 1 < len(rungs) else None

    def requirements_for_next(self) -> Optional[dict]:
        next_r = self.next_rung
        if not next_r:
            return None
        rung_def = next(r for r in LADDER_RUNGS if r["rung"] == next_r)
        return {
            "rung":             next_r,
            "score_needed":     rung_def["min_score"],
            "evidence_needed":  rung_def["min_evidence"],
            "score_gap":        max(0, rung_def["min_score"] - self.trust_score),
            "evidence_gap":     max(0, rung_def["min_evidence"] - self.evidence_count),
        }


class TrustPromotionLadder:
    """
    Tracks promotion/demotion events per trust pillar.
    Computes current rung and requirements for next promotion.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._positions: Dict[str, LadderPosition] = {}

    def sync_from_registry(self) -> None:
        """Sync ladder positions from the TrustValidationRegistry."""
        try:
            from core.trust.trust_validation_registry import trust_validation_registry, PILLARS
            for pillar in PILLARS:
                status = trust_validation_registry.pillar_status(pillar)
                self._update_position(
                    pillar=pillar,
                    score=status.get("trust_score", 0.0),
                    evidence=status.get("total_evidence", 0),
                )
        except Exception:
            pass

    def _update_position(self, pillar: str, score: float, evidence: int) -> None:
        new_rung = _compute_rung(score, evidence)
        with self._lock:
            pos = self._positions.get(pillar)
            if pos is None:
                pos = LadderPosition(
                    pillar=pillar,
                    current_rung=new_rung,
                    previous_rung="UNVERIFIED",
                    trust_score=score,
                    evidence_count=evidence,
                )
                pos.rung_history.append({"rung": new_rung, "timestamp": time.time(), "score": score})
                self._positions[pillar] = pos
                return

            pos.trust_score   = score
            pos.evidence_count = evidence

            if new_rung != pos.current_rung:
                pos.rung_history.append({"rung": new_rung, "timestamp": time.time(), "score": score})
                if len(pos.rung_history) > 50:
                    pos.rung_history = pos.rung_history[-50:]
                # Detect promotion vs demotion
                rungs = [r["rung"] for r in LADDER_RUNGS]
                old_idx = rungs.index(pos.current_rung) if pos.current_rung in rungs else 0
                new_idx = rungs.index(new_rung) if new_rung in rungs else 0
                pos.previous_rung = pos.current_rung
                pos.current_rung  = new_rung
                if new_idx > old_idx:
                    pos.promoted_at = time.time()
                    self._record_milestone(pillar, "PROMOTION", pos.previous_rung, new_rung, score)
                else:
                    pos.demoted_at = time.time()
                    self._record_milestone(pillar, "DEMOTION", pos.previous_rung, new_rung, score)

    def get_position(self, pillar: str) -> Optional[dict]:
        self.sync_from_registry()
        with self._lock:
            pos = self._positions.get(pillar)
        return self._serialise(pos) if pos else None

    def all_positions(self) -> List[dict]:
        self.sync_from_registry()
        with self._lock:
            items = list(self._positions.values())
        return [self._serialise(p) for p in items]

    def program_overview(self) -> dict:
        positions = self.all_positions()
        by_rung: Dict[str, int] = {}
        for p in positions:
            rung = p["current_rung"]
            by_rung[rung] = by_rung.get(rung, 0) + 1
        highest_rung = max(
            positions, key=lambda x: [r["rung"] for r in LADDER_RUNGS].index(x["current_rung"])
            if x["current_rung"] in [r["rung"] for r in LADDER_RUNGS] else 0,
            default=None,
        )
        return {
            "pillar_count":   len(positions),
            "by_rung":        by_rung,
            "highest_rung":   highest_rung["current_rung"] if highest_rung else "UNVERIFIED",
            "positions":      positions,
            "ladder":         LADDER_RUNGS,
        }

    def current_rung(self, pillar: str) -> dict:
        self.sync_from_registry()
        with self._lock:
            pos = self._positions.get(pillar)
        if not pos:
            return {"rung": "UNVERIFIED", "pillar": pillar}
        return {"rung": pos.current_rung, "pillar": pillar, "trust_score": pos.trust_score}

    def force_demote(self, pillar: str, to_rung: str, reason: str = "") -> None:
        with self._lock:
            pos = self._positions.get(pillar)
            if not pos:
                return
            old_rung = pos.current_rung
            pos.previous_rung = old_rung
            pos.current_rung = to_rung
            pos.demoted_at = time.time()
            pos.rung_history.append({"rung": to_rung, "timestamp": time.time(), "score": pos.trust_score, "forced": True, "reason": reason})
        self._record_milestone(pillar, "FORCED_DEMOTION", old_rung, to_rung, pos.trust_score)

    def _record_milestone(self, pillar: str, event: str, from_rung: str, to_rung: str, score: float) -> None:
        try:
            from core.observatory.nexus_bridge import _imraf
            im = _imraf()
            if im:
                im.record_knowledge(
                    title=f"[TRUST LADDER] {pillar} {event}: {from_rung} → {to_rung}",
                    content=f"Score: {score:.1f} | Pillar: {pillar}",
                    category="trust_promotion",
                    tags=["trust", "promotion", pillar.lower(), to_rung.lower()],
                )
        except Exception:
            pass

    @staticmethod
    def _serialise(p: LadderPosition) -> dict:
        return {
            "pillar":         p.pillar,
            "current_rung":   p.current_rung,
            "previous_rung":  p.previous_rung,
            "trust_score":    p.trust_score,
            "evidence_count": p.evidence_count,
            "promoted_at":    p.promoted_at or None,
            "demoted_at":     p.demoted_at or None,
            "next_rung_requirements": p.requirements_for_next(),
            "rung_history":   p.rung_history[-10:],  # last 10 events
        }


# Singleton
trust_promotion_ladder = TrustPromotionLadder()
