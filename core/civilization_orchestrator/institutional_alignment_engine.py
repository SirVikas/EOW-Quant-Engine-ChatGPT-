"""Institutional Alignment Engine — tracks alignment between institutional layers."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Dict, Optional


@dataclass
class LayerAlignment:
    layer_name: str
    alignment_score: float  # 0-100
    last_assessed: str
    status: str  # ALIGNED / MISALIGNED / UNKNOWN


_DEFAULT_LAYERS = [
    "Intelligence",
    "Governance",
    "Research",
    "Evolution",
    "Forecasting",
    "AgentEcosystem",
]


class InstitutionalAlignmentEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._layers: Dict[str, LayerAlignment] = {}
        now = datetime.now(timezone.utc).isoformat()
        for name in _DEFAULT_LAYERS:
            self._layers[name] = LayerAlignment(
                layer_name=name,
                alignment_score=85.0,
                last_assessed=now,
                status="ALIGNED",
            )

    def assess_alignment(self, layer_name: str, score: float) -> dict:
        with self._lock:
            now = datetime.now(timezone.utc).isoformat()
            status = "ALIGNED" if score >= 70 else "MISALIGNED"
            if layer_name not in self._layers:
                self._layers[layer_name] = LayerAlignment(
                    layer_name=layer_name,
                    alignment_score=score,
                    last_assessed=now,
                    status=status,
                )
            else:
                layer = self._layers[layer_name]
                layer.alignment_score = score
                layer.last_assessed = now
                layer.status = status
            return asdict(self._layers[layer_name])

    def misaligned_layers(self) -> List[dict]:
        with self._lock:
            return [asdict(l) for l in self._layers.values() if l.status == "MISALIGNED"]

    def alignment_summary(self) -> dict:
        with self._lock:
            layers = list(self._layers.values())
            aligned = sum(1 for l in layers if l.status == "ALIGNED")
            misaligned = sum(1 for l in layers if l.status == "MISALIGNED")
            avg_score = sum(l.alignment_score for l in layers) / len(layers) if layers else 0
            return {
                "total_layers": len(layers),
                "aligned": aligned,
                "misaligned": misaligned,
                "average_alignment_score": round(avg_score, 2),
                "overall_status": "ALIGNED" if misaligned == 0 else "PARTIALLY_MISALIGNED",
                "layers": [asdict(l) for l in layers],
            }


institutional_alignment_engine = InstitutionalAlignmentEngine()
