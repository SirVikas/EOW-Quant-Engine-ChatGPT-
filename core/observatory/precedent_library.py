"""
PHOENIX OBSERVATORY-X — Precedent Library  [OX-GAP-04]

Before each investigation, the system must ask: "Have we seen this before?"

The Precedent Library is the Observatory-native case registry.
Unlike IMRAF (general institutional memory), this library is specifically
structured for investigation-level lookup: given a trigger type, actor, or
defect pattern, find similar past cases and their outcomes.

Each precedent contains:
  - What the investigation found
  - What was recommended
  - What actually happened (the measured outcome)
  - Whether the case is binding (must not contradict) or advisory

Binding precedents are created when an investigation + outcome cycle is complete
and the finding has been verified.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Precedent:
    case_id: str
    title: str
    investigation_id: str
    trigger_type: str           # LOSS_INVESTIGATION | ANOMALY | STALE_REPORT | CUSTOM
    primary_dimension: str      # actor | session | defect_type | regime | strategy
    primary_value: str          # the specific value (e.g. module name, time window)
    finding_summary: str        # one-sentence finding
    recommendation_applied: str # what was done
    outcome: str                # improved | no_change | worsened | unknown
    outcome_detail: str         # quantitative detail (e.g. "+4.2% WR, -1.3 PF")
    is_binding: bool            # if True, future investigations cannot contradict casually
    binding_verdict: str        # the standing institutional verdict
    created_at: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)


class PrecedentLibrary:
    """
    Observatory-native case registry.
    Provides "seen before?" lookup for investigations.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._cases: Dict[str, Precedent] = {}
        self._bootstrap_founding_precedents()

    # ── Recording ─────────────────────────────────────────────────────────────

    def record(
        self,
        case_id: str,
        title: str,
        investigation_id: str,
        trigger_type: str,
        primary_dimension: str,
        primary_value: str,
        finding_summary: str,
        recommendation_applied: str,
        outcome: str,
        outcome_detail: str,
        is_binding: bool = False,
        binding_verdict: str = "",
        tags: Optional[List[str]] = None,
    ) -> Precedent:
        p = Precedent(
            case_id=case_id,
            title=title,
            investigation_id=investigation_id,
            trigger_type=trigger_type,
            primary_dimension=primary_dimension,
            primary_value=primary_value,
            finding_summary=finding_summary,
            recommendation_applied=recommendation_applied,
            outcome=outcome,
            outcome_detail=outcome_detail,
            is_binding=is_binding,
            binding_verdict=binding_verdict,
            tags=tags or [],
        )
        with self._lock:
            self._cases[case_id] = p
        self._record_imraf(p)
        return p

    # ── Lookup ────────────────────────────────────────────────────────────────

    def seen_before(
        self,
        dimension: Optional[str] = None,
        value: Optional[str] = None,
        trigger_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[dict]:
        """Find precedents matching any of the given criteria."""
        with self._lock:
            cases = list(self._cases.values())

        matches = []
        for p in cases:
            match = False
            if dimension and value and p.primary_dimension == dimension and p.primary_value == value:
                match = True
            if trigger_type and p.trigger_type == trigger_type:
                match = True
            if tags and any(t in p.tags for t in tags):
                match = True
            if match:
                matches.append(p)

        matches.sort(key=lambda x: x.created_at, reverse=True)
        return [self._serialise(p) for p in matches]

    def binding_precedents(self) -> List[dict]:
        with self._lock:
            items = [p for p in self._cases.values() if p.is_binding]
        return [self._serialise(p) for p in items]

    def get(self, case_id: str) -> Optional[dict]:
        with self._lock:
            p = self._cases.get(case_id)
        return self._serialise(p) if p else None

    def all_cases(self) -> List[dict]:
        with self._lock:
            items = sorted(self._cases.values(), key=lambda x: x.created_at, reverse=True)
        return [self._serialise(p) for p in items]

    def summary(self) -> dict:
        with self._lock:
            total = len(self._cases)
            binding = sum(1 for p in self._cases.values() if p.is_binding)
            outcomes: Dict[str, int] = {}
            for p in self._cases.values():
                outcomes[p.outcome] = outcomes.get(p.outcome, 0) + 1
        return {
            "total_cases":    total,
            "binding_cases":  binding,
            "advisory_cases": total - binding,
            "by_outcome":     outcomes,
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _bootstrap_founding_precedents(self) -> None:
        # ATR Root Cause Investigation — founding binding precedent
        self.record(
            case_id="CASE-001",
            title="ATR Not Root Cause of Losses",
            investigation_id="FOUNDING-001",
            trigger_type="CUSTOM",
            primary_dimension="actor",
            primary_value="atr_calculator",
            finding_summary="ATR values were accurate; losses caused by market regime mismatch, not ATR errors.",
            recommendation_applied="Regime filter tightened; ATR parameters unchanged.",
            outcome="improved",
            outcome_detail="Loss rate reduced post regime-filter tightening. ATR exonerated.",
            is_binding=True,
            binding_verdict=(
                "ATR is not the root cause of losses. Investigations implicating ATR must "
                "first rule out regime mismatch before proceeding."
            ),
            tags=["atr", "regime", "root_cause", "founding"],
        )

    def _record_imraf(self, p: Precedent) -> None:
        try:
            from core.observatory.nexus_bridge import _imraf
            im = _imraf()
            if im:
                im.record_knowledge(
                    title=f"[PRECEDENT] {p.case_id}: {p.title}",
                    content=f"Finding: {p.finding_summary} | Outcome: {p.outcome} | Binding: {p.is_binding}",
                    category="observatory_precedent",
                    tags=["precedent", p.trigger_type, p.primary_dimension] + p.tags,
                )
        except Exception:
            pass

    @staticmethod
    def _serialise(p: Precedent) -> dict:
        return {
            "case_id":                 p.case_id,
            "title":                   p.title,
            "investigation_id":        p.investigation_id,
            "trigger_type":            p.trigger_type,
            "primary_dimension":       p.primary_dimension,
            "primary_value":           p.primary_value,
            "finding_summary":         p.finding_summary,
            "recommendation_applied":  p.recommendation_applied,
            "outcome":                 p.outcome,
            "outcome_detail":          p.outcome_detail,
            "is_binding":              p.is_binding,
            "binding_verdict":         p.binding_verdict,
            "created_at":              p.created_at,
            "tags":                    p.tags,
        }


# Singleton
precedent_library = PrecedentLibrary()
