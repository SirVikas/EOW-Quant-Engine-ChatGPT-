"""
FTD-030B — Pattern Engine
Detects recurring correction patterns using 3-tuple key (Q4-B multi-factor tuple).

Pattern Key: "{instrument}|{parameter}|{direction}"
Context   : distinct "{regime}|{vol_bucket}" pairs observed for this key

Why 3-tuple: regime and vol are tracked as CONTEXT buckets (Q11 anti-overfitting gate).
A 5-tuple key would pin regime+vol into the key, making context_count permanently 1 and
rendering the Q5 contexts≥3 gate impossible. The 3-tuple groups all occurrences of the
same correction type (what changed, on which instrument, in which direction) and validates
that the correction worked across ≥3 distinct market regimes/volatility environments.

Formation Gate (Q5-D ALL of the above):
  - samples ≥ 20
  - confidence ≥ 70
  - contexts (distinct regime × vol_bucket pairs) ≥ 3

Confidence (Q6-D hybrid):
  success_rate × recency(0.95^age_days) × regime_bonus(×1.1 if multi-regime) × 100
"""
from __future__ import annotations
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set

from core.memory.memory_store import MemoryEntry

# Formation gate thresholds (Q5)
MIN_PATTERN_SAMPLES  = 20      # raised from 5 per FTD-030B spec
MIN_CONFIDENCE       = 70.0
MIN_CONTEXTS         = 3       # distinct regime×vol_bucket contexts (anti-overfitting Q11)

# Confidence formula components (Q6-D hybrid)
RECENCY_DECAY        = 0.95    # per-day recency decay
MULTI_REGIME_BONUS   = 1.10   # +10% if pattern spans multiple regimes


@dataclass
class Pattern:
    pattern_id:        str     # "{instrument}|{param}|{direction}"
    regime:            str     # primary (most-recent) regime
    volatility:        str     # primary (most-recent) vol_bucket
    instrument:        str
    parameter:         str
    direction:         str
    sample_count:      int
    success_count:     int
    failure_count:     int
    avg_outcome_score: float
    avg_delta_pct:     float
    confidence:        float   # success_rate × recency × regime_bonus × 100
    validated:         bool    # meets ALL three formation gates
    context_count:     int     # distinct regime×vol_bucket pairs seen
    last_seen_ts:      int     # ms timestamp of most recent sample
    regimes_seen:      List[str] = field(default_factory=list)


class PatternDetector:
    """Groups entries by 3-tuple key and computes pattern stats with context diversity."""

    MIN_SAMPLES          = MIN_PATTERN_SAMPLES
    CONFIDENCE_THRESHOLD = MIN_CONFIDENCE
    MIN_CONTEXTS         = MIN_CONTEXTS

    def detect(self, entries: List[MemoryEntry]) -> Dict[str, Pattern]:
        buckets: Dict[str, List[MemoryEntry]] = defaultdict(list)
        for e in entries:
            key = f"{e.symbol}|{e.parameter}|{e.direction}"
            buckets[key].append(e)

        patterns: Dict[str, Pattern] = {}
        for key, items in buckets.items():
            if not items:
                continue

            parts      = key.split("|", 2)
            instrument = parts[0]
            parameter  = parts[1]
            direction  = parts[2]

            n            = len(items)
            now_ms       = int(time.time() * 1000)
            successes    = sum(1 for e in items if e.outcome_score > 0)
            failures     = sum(1 for e in items if e.outcome_score < 0)
            total_weight = sum(e.decay_weight for e in items) or 1e-9
            avg_outcome  = sum(e.outcome_score * e.decay_weight for e in items) / total_weight
            avg_delta    = sum(e.delta_pct for e in items) / n

            # Distinct context buckets for anti-overfitting gate (Q5/Q11)
            contexts: Set[str] = set()
            for e in items:
                ctx = f"{e.market_regime}|{self._vol_bucket(e.volatility)}"
                contexts.add(ctx)

            # Recency: most recent item age in days
            latest_ts    = max(e.ts for e in items)
            age_days     = (now_ms - latest_ts) / (1000.0 * 86400.0)
            recency      = RECENCY_DECAY ** age_days

            # Primary regime = most recent entry's regime
            most_recent  = max(items, key=lambda e: e.ts)
            primary_regime = most_recent.market_regime
            primary_vol    = self._vol_bucket(most_recent.volatility)

            # Multi-regime bonus (Q6)
            regimes_seen = list({e.market_regime for e in items})
            regime_bonus = MULTI_REGIME_BONUS if len(regimes_seen) > 1 else 1.0

            # Confidence formula (Q6-D): success_rate × recency × regime_bonus × 100
            success_rate = (successes / n) if n else 0.0
            confidence   = min(100.0, success_rate * recency * regime_bonus * 100.0)

            validated = (
                n >= self.MIN_SAMPLES
                and confidence >= self.CONFIDENCE_THRESHOLD
                and len(contexts) >= self.MIN_CONTEXTS
            )

            patterns[key] = Pattern(
                pattern_id=key,
                regime=primary_regime,
                volatility=primary_vol,
                instrument=instrument,
                parameter=parameter,
                direction=direction,
                sample_count=n,
                success_count=successes,
                failure_count=failures,
                avg_outcome_score=round(avg_outcome, 4),
                avg_delta_pct=round(avg_delta, 4),
                confidence=round(confidence, 2),
                validated=validated,
                context_count=len(contexts),
                last_seen_ts=latest_ts,
                regimes_seen=regimes_seen,
            )
        return patterns

    @staticmethod
    def _vol_bucket(volatility: float) -> str:
        """Normalise raw volatility into LOW / MED / HIGH bucket (Q3-A)."""
        if volatility < 0.005:
            return "LOW"
        if volatility < 0.020:
            return "MED"
        return "HIGH"
