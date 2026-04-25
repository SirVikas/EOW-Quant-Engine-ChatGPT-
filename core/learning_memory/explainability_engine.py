"""
FTD-030B — explainability_engine.py
Generates a mandatory audit record for every memory-influenced correction.

Every time memory is applied, this engine produces an ExplainCard that is:
  - Logged to the correction audit trail (extending FTD-029 AuditLogger)
  - Included in the dashboard last-memory-used card
  - Written to the memory report
"""
from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.learning_memory.pattern_engine import Pattern


@dataclass
class ExplainCard:
    pattern_id:      str
    confidence:      float
    success_rate:    float
    applied_weight:  float
    context_match:   float    # 0.0–1.0: how well the current context matches the pattern
    memory_suggest:  float    # raw memory-suggested value
    live_suggest:    float    # raw live-planner-suggested value
    final_value:     float    # blended final value applied
    parameter:       str
    ts:              int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ExplainabilityEngine:
    """
    Produces ExplainCards for every memory-influenced correction.
    Maintains a short history for dashboard display.
    """

    def __init__(self, history_size: int = 20):
        self._history: list[ExplainCard] = []
        self._history_size = history_size

    # ── Public API ────────────────────────────────────────────────────────────

    def build(
        self,
        pattern:         "Pattern",
        memory_suggest:  float,
        live_suggest:    float,
        final_value:     float,
        applied_weight:  float,
        context_match:   float = 1.0,
    ) -> ExplainCard:
        """Create and record an ExplainCard for the applied memory influence."""
        card = ExplainCard(
            pattern_id=pattern.pattern_id,
            confidence=round(pattern.confidence, 2),
            success_rate=round(pattern.success_rate, 4),
            applied_weight=round(applied_weight, 3),
            context_match=round(context_match, 3),
            memory_suggest=round(memory_suggest, 6),
            live_suggest=round(live_suggest, 6),
            final_value=round(final_value, 6),
            parameter=pattern.parameter,
            ts=int(time.time() * 1000),
        )
        self._history.append(card)
        if len(self._history) > self._history_size:
            self._history = self._history[-self._history_size:]
        return card

    def last(self) -> Optional[ExplainCard]:
        return self._history[-1] if self._history else None

    def recent(self, n: int = 10) -> list[Dict[str, Any]]:
        return [c.to_dict() for c in self._history[-n:]]

    def summary(self) -> Dict[str, Any]:
        last = self.last()
        return {
            "last_card":    last.to_dict() if last else None,
            "history_count": len(self._history),
            "module": "EXPLAINABILITY_ENGINE",
            "phase":  "030B",
        }
