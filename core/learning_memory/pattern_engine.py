"""
FTD-030B Part 2 — Pattern Engine

Detects, tracks, and validates multi-factor patterns from memory records.
Pattern key: (regime, volatility, instrument, parameter, direction)
Formation gate: samples ≥ 20, confidence ≥ 70, contexts ≥ 3 distinct buckets
"""
from __future__ import annotations
import time
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple

FORMATION_MIN_SAMPLES    = 20
FORMATION_MIN_CONFIDENCE = 70.0
FORMATION_MIN_CONTEXTS   = 3

PatternKey = Tuple[str, str, str, str, str]


class PatternRecord:
    __slots__ = ("pattern_id", "key", "samples", "success", "confidence",
                 "contexts", "last_seen", "created_at")

    def __init__(self, key: PatternKey):
        self.pattern_id: str   = str(uuid.uuid4())[:12]
        self.key:         PatternKey = key
        self.samples:     int  = 0
        self.success:     int  = 0
        self.confidence:  float = 0.0
        self.contexts:    Set[str] = set()
        self.last_seen:   int  = 0       # cycle counter
        self.created_at:  float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        regime, volatility, instrument, parameter, direction = self.key
        return {
            "pattern_id":  self.pattern_id,
            "key":         {"regime": regime, "volatility": volatility,
                            "instrument": instrument, "parameter": parameter,
                            "direction": direction},
            "samples":     self.samples,
            "success":     self.success,
            "confidence":  round(self.confidence, 2),
            "contexts":    list(self.contexts),
            "last_seen":   self.last_seen,
            "created_at":  self.created_at,
        }

    @property
    def is_formed(self) -> bool:
        return (
            self.samples    >= FORMATION_MIN_SAMPLES
            and self.confidence >= FORMATION_MIN_CONFIDENCE
            and len(self.contexts) >= FORMATION_MIN_CONTEXTS
        )


class PatternEngine:
    """
    Builds and maintains patterns from memory records.
    Only multi-factor patterns (regime + volatility + instrument context) are tracked.
    """

    MODULE = "PATTERN_ENGINE"
    PHASE  = "030B"

    def __init__(self):
        self._patterns:  Dict[PatternKey, PatternRecord] = {}
        self._cycle_seq: int = 0

    # ── Public API ────────────────────────────────────────────────────────────

    def ingest(self, record: Dict[str, Any]) -> Optional[PatternRecord]:
        """
        Feed one memory record into the engine.
        Returns the PatternRecord if a new pattern forms (crossed threshold), else None.
        """
        self._cycle_seq += 1
        key = self._make_key(record)
        if key is None:
            return None

        pat = self._patterns.setdefault(key, PatternRecord(key))
        pat.samples  += 1
        pat.last_seen = self._cycle_seq

        success = not record.get("outcome", {}).get("rollback", True)
        if success:
            pat.success += 1

        context_bucket = self._context_bucket(record)
        if context_bucket:
            pat.contexts.add(context_bucket)

        return pat

    def get_pattern(self, key: PatternKey) -> Optional[PatternRecord]:
        return self._patterns.get(key)

    def formed_patterns(self) -> List[PatternRecord]:
        return [p for p in self._patterns.values() if p.is_formed]

    def all_patterns(self) -> List[PatternRecord]:
        return list(self._patterns.values())

    def make_key_from_context(
        self,
        regime: str,
        volatility: str,
        instrument: str,
        parameter: str,
        direction: str,
    ) -> PatternKey:
        return (
            (regime or "UNKNOWN").upper(),
            (volatility or "MEDIUM").upper(),
            (instrument or "UNKNOWN").upper(),
            parameter,
            (direction or "UP").upper(),
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _make_key(self, record: Dict[str, Any]) -> Optional[PatternKey]:
        ctx = record.get("context", {})
        chg = record.get("change", {})
        regime     = ctx.get("regime", "")
        volatility = ctx.get("volatility", "")
        instrument = ctx.get("instrument", "")
        parameter  = chg.get("parameter", "")
        direction  = chg.get("direction", "")
        if not all([regime, volatility, instrument, parameter, direction]):
            return None
        return (regime.upper(), volatility.upper(), instrument.upper(), parameter, direction.upper())

    @staticmethod
    def _context_bucket(record: Dict[str, Any]) -> str:
        ctx = record.get("context", {})
        return f"{ctx.get('regime','')}/{ctx.get('volatility','')}/{ctx.get('timeframe','')}"
