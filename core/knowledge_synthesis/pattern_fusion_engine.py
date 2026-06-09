"""Pattern Fusion Engine — fuses patterns from multiple domains into synthesized insights."""
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List


@dataclass
class FusedPattern:
    fusion_id: str
    pattern_ids: List[str]
    synthesis_result: str
    strength: float  # 0-1
    fused_at: str


class PatternFusionEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._patterns: List[FusedPattern] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"FUS-{self._counter:03d}"

    def fuse(self, pattern_ids: List[str], synthesis_result: str, strength: float = 0.5) -> dict:
        with self._lock:
            fp = FusedPattern(
                fusion_id=self._next_id(),
                pattern_ids=list(pattern_ids),
                synthesis_result=synthesis_result,
                strength=max(0.0, min(1.0, strength)),
                fused_at=datetime.now(timezone.utc).isoformat(),
            )
            self._patterns.append(fp)
            return asdict(fp)

    def all_fused_patterns(self, limit: int = 50) -> List[dict]:
        with self._lock:
            return [asdict(p) for p in self._patterns[-limit:]]

    def strong_patterns(self, threshold: float = 0.7) -> List[dict]:
        with self._lock:
            return [asdict(p) for p in self._patterns if p.strength >= threshold]

    def fusion_stats(self) -> dict:
        with self._lock:
            total = len(self._patterns)
            if total == 0:
                return {"total_fusions": 0, "avg_strength": 0.0, "strong_count": 0}
            avg_strength = sum(p.strength for p in self._patterns) / total
            strong = sum(1 for p in self._patterns if p.strength >= 0.7)
            return {"total_fusions": total, "avg_strength": avg_strength, "strong_count": strong}


pattern_fusion_engine = PatternFusionEngine()
