"""PCCP — Conflict Resolution Engine: resolves conflicting signals from different layers."""
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional


PRIORITY_HIERARCHY = {
    "SAFETY": 100,
    "RISK_ENGINE": 90,
    "TRUST_ENGINE": 80,
    "CORTEX": 70,
    "AEG": 60,
    "PCAO": 55,
    "OBSERVATORY-X": 50,
    "STRATEGY": 40,
}

GOAL_HIERARCHY = {
    "CAPITAL_PROTECTION": 100,
    "SIGNAL_TRUTH": 90,
    "SYSTEM_STABILITY": 80,
    "PROFITABILITY": 70,
    "GROWTH": 60,
}


@dataclass
class Conflict:
    conflict_id: str
    layer_a: str
    signal_a: str
    layer_b: str
    signal_b: str
    context: str
    resolution: str
    resolution_reason: str
    resolved_at: float
    confidence: float


class ConflictResolver:
    def __init__(self):
        self._lock = threading.RLock()
        self._conflicts: List[Conflict] = []

    def resolve(self, layer_a: str, signal_a: str, layer_b: str, signal_b: str, context: str = "") -> dict:
        with self._lock:
            priority_a = PRIORITY_HIERARCHY.get(layer_a.upper(), 0)
            priority_b = PRIORITY_HIERARCHY.get(layer_b.upper(), 0)

            if priority_a != priority_b:
                winner = layer_a if priority_a > priority_b else layer_b
                winning_signal = signal_a if winner == layer_a else signal_b
                reason = f"Layer priority hierarchy: {layer_a}={priority_a} vs {layer_b}={priority_b}"
                confidence = 0.9
            else:
                # Use goal hierarchy keywords in signals
                def goal_score(signal: str) -> int:
                    s = signal.upper()
                    return max((v for k, v in GOAL_HIERARCHY.items() if k in s), default=0)

                score_a = goal_score(signal_a)
                score_b = goal_score(signal_b)
                if score_a >= score_b:
                    winner = layer_a
                    winning_signal = signal_a
                else:
                    winner = layer_b
                    winning_signal = signal_b
                reason = f"Goal hierarchy keyword match: signal_a_score={score_a} vs signal_b_score={score_b}"
                confidence = 0.6

            conflict_id = str(uuid.uuid4())
            c = Conflict(
                conflict_id=conflict_id,
                layer_a=layer_a,
                signal_a=signal_a,
                layer_b=layer_b,
                signal_b=signal_b,
                context=context,
                resolution=winner,
                resolution_reason=reason,
                resolved_at=time.time(),
                confidence=confidence,
            )
            self._conflicts.append(c)
            if len(self._conflicts) > 500:
                self._conflicts = self._conflicts[-500:]

            return {
                "conflict_id": conflict_id,
                "winner_layer": winner,
                "winning_signal": winning_signal,
                "resolution_reason": reason,
                "confidence": confidence,
            }

    def all_conflicts(self, limit: int = 50) -> List[dict]:
        with self._lock:
            return [asdict(c) for c in self._conflicts[-limit:]]

    def conflict_stats(self) -> dict:
        with self._lock:
            total = len(self._conflicts)
            by_winning = {}
            for c in self._conflicts:
                by_winning[c.resolution] = by_winning.get(c.resolution, 0) + 1
            return {
                "total_conflicts": total,
                "by_winning_layer": by_winning,
                "resolution_rate": 1.0 if total > 0 else 0.0,
            }


conflict_resolver = ConflictResolver()
