"""Resource Demand Predictor — predicts future resource demand."""
import threading
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DemandPrediction:
    pred_id: str
    resource_type: str
    horizon_days: int
    predicted_demand_units: float
    confidence_pct: float
    predicted_at: datetime


class ResourceDemandPredictor:
    def __init__(self):
        self._lock = threading.RLock()
        self._predictions: dict[str, DemandPrediction] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"RDP-{self._counter:03d}"

    def predict(self, resource_type: str, horizon_days: int,
                predicted_demand_units: float, confidence_pct: float) -> DemandPrediction:
        with self._lock:
            p = DemandPrediction(
                pred_id=self._next_id(),
                resource_type=resource_type,
                horizon_days=horizon_days,
                predicted_demand_units=predicted_demand_units,
                confidence_pct=max(0.0, min(100.0, confidence_pct)),
                predicted_at=datetime.utcnow(),
            )
            self._predictions[p.pred_id] = p
            return p

    def predictions_for(self, resource_type: str) -> list[dict]:
        with self._lock:
            return [
                {"pred_id": p.pred_id, "horizon_days": p.horizon_days,
                 "predicted_demand_units": p.predicted_demand_units,
                 "confidence_pct": p.confidence_pct,
                 "predicted_at": p.predicted_at.isoformat()}
                for p in self._predictions.values() if p.resource_type == resource_type
            ]

    def upcoming_demand(self) -> list[dict]:
        with self._lock:
            # Latest prediction per resource type
            latest: dict[str, DemandPrediction] = {}
            for p in self._predictions.values():
                if p.resource_type not in latest or p.predicted_at > latest[p.resource_type].predicted_at:
                    latest[p.resource_type] = p
            return [
                {"resource_type": rt, "predicted_demand_units": p.predicted_demand_units,
                 "horizon_days": p.horizon_days, "confidence_pct": p.confidence_pct}
                for rt, p in latest.items()
            ]


resource_demand_predictor = ResourceDemandPredictor()
