"""
FTD-030B — pattern_engine.py
Builds and manages multi-factor patterns from memory records.

Pattern key: (regime, volatility, instrument, parameter, direction)
Formation gate: samples ≥ 20, confidence ≥ 70, contexts ≥ 3 distinct buckets
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from core.learning_memory.memory_store import MemoryRecord

PATTERN_MIN_SAMPLES    = 20
PATTERN_MIN_CONFIDENCE = 70.0
PATTERN_MIN_CONTEXTS   = 3


@dataclass
class Pattern:
    pattern_id:  str
    regime:      str
    volatility:  str
    instrument:  str
    parameter:   str
    direction:   str

    samples:     int   = 0
    success:     int   = 0
    confidence:  float = 0.0
    contexts:    Set[str] = field(default_factory=set)   # unique context-bucket signatures
    last_seen:   int   = 0    # epoch ms
    age_cycles:  int   = 0    # cycles since first formation

    @property
    def success_rate(self) -> float:
        return self.success / self.samples if self.samples > 0 else 0.0

    @property
    def is_valid(self) -> bool:
        return (
            self.samples     >= PATTERN_MIN_SAMPLES and
            self.confidence  >= PATTERN_MIN_CONFIDENCE and
            len(self.contexts) >= PATTERN_MIN_CONTEXTS
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id":   self.pattern_id,
            "regime":       self.regime,
            "volatility":   self.volatility,
            "instrument":   self.instrument,
            "parameter":    self.parameter,
            "direction":    self.direction,
            "samples":      self.samples,
            "success":      self.success,
            "success_rate": round(self.success_rate, 4),
            "confidence":   round(self.confidence, 2),
            "contexts":     len(self.contexts),
            "last_seen":    self.last_seen,
            "age_cycles":   self.age_cycles,
            "is_valid":     self.is_valid,
        }


class PatternEngine:
    """
    Builds patterns from MemoryRecord observations.
    A pattern is valid once it crosses the formation triple gate.
    """

    def __init__(self):
        self._patterns: Dict[str, Pattern] = {}

    # ── Public API ────────────────────────────────────────────────────────────

    def update(self, record: MemoryRecord, confidence_fn=None) -> Optional[Pattern]:
        """
        Update or create the pattern matching this record.
        Returns the Pattern if it exists (valid or not yet valid).
        """
        key = self._make_key(record)
        pat = self._patterns.get(key)

        if pat is None:
            pat = Pattern(
                pattern_id=key,
                regime=record.context["regime"],
                volatility=record.context["volatility"],
                instrument=record.context["instrument"],
                parameter=record.change["parameter"],
                direction=record.change["direction"],
            )
            self._patterns[key] = pat

        pat.samples  += 1
        pat.last_seen = int(time.time() * 1000)
        pat.age_cycles += 1

        if not record.outcome.get("rollback", False):
            pat.success += 1

        # Track context diversity
        ctx_sig = f"{record.context['regime']}:{record.context['volatility']}"
        pat.contexts.add(ctx_sig)

        # Recompute confidence
        if confidence_fn is not None:
            pat.confidence = confidence_fn(pat)
        else:
            pat.confidence = pat.success_rate * 100.0

        return pat

    def get(self, key: str) -> Optional[Pattern]:
        return self._patterns.get(key)

    def get_for_record(self, record: MemoryRecord) -> Optional[Pattern]:
        return self._patterns.get(self._make_key(record))

    def valid_patterns(self) -> List[Pattern]:
        return [p for p in self._patterns.values() if p.is_valid]

    def all_patterns(self) -> List[Pattern]:
        return list(self._patterns.values())

    def remove(self, pattern_id: str) -> None:
        self._patterns.pop(pattern_id, None)

    def top_by_confidence(self, n: int = 10) -> List[Pattern]:
        valid = self.valid_patterns()
        return sorted(valid, key=lambda p: p.confidence, reverse=True)[:n]

    def bottom_by_confidence(self, n: int = 5) -> List[Pattern]:
        valid = self.valid_patterns()
        return sorted(valid, key=lambda p: p.confidence)[:n]

    def load_from_records(self, records: list, confidence_fn=None) -> None:
        """Rebuild patterns from persisted MemoryRecords (called at startup)."""
        for r in records:
            self.update(r, confidence_fn)

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _make_key(record: MemoryRecord) -> str:
        c = record.context
        ch = record.change
        return (
            f"{c['regime']}:{c['volatility']}:{c['instrument']}"
            f":{ch['parameter']}:{ch['direction']}"
        )

    def summary(self) -> Dict[str, Any]:
        valid = self.valid_patterns()
        return {
            "total_patterns":  len(self._patterns),
            "valid_patterns":  len(valid),
            "top_pattern":     valid[0].to_dict() if valid else None,
            "module": "PATTERN_ENGINE",
            "phase":  "030B",
        }
