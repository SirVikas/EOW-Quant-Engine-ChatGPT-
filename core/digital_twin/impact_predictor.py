"""
PHOENIX Digital Twin — Impact Predictor
Keyword-heuristic prediction of strategy change impacts.
"""
from __future__ import annotations
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid


@dataclass
class ImpactPrediction:
    pred_id: str
    subject: str
    subject_type: str  # RECOMMENDATION/STRATEGY_CHANGE/RULE_CHANGE
    predicted_profit_impact: float
    predicted_drawdown_impact: float
    predicted_sharpe_impact: float
    predicted_stability_impact: float
    confidence: float
    created_at: str


class ImpactPredictor:
    def __init__(self):
        self._lock = threading.RLock()
        self._predictions: Dict[str, ImpactPrediction] = {}

    def predict(self, subject: str, subject_type: str, context: dict = None) -> dict:
        text = subject.lower()
        profit_impact = 0.0
        drawdown_impact = 0.0
        sharpe_impact = 0.0
        stability_impact = 0.0
        confidence = 0.3

        conservative_kw = ["reduce", "limit", "cap"]
        aggressive_kw = ["increase", "expand", "boost"]
        quality_kw = ["filter", "quality"]

        if any(kw in text for kw in conservative_kw):
            drawdown_impact = 0.02
            profit_impact = -0.01
            stability_impact = 0.01
            confidence = 0.6
        elif any(kw in text for kw in aggressive_kw):
            drawdown_impact = -0.02
            profit_impact = 0.02
            stability_impact = -0.01
            confidence = 0.55
        elif any(kw in text for kw in quality_kw):
            sharpe_impact = 0.05
            confidence = 0.5

        pred_id = f"PRED-{uuid.uuid4().hex[:8].upper()}"
        pred = ImpactPrediction(
            pred_id=pred_id,
            subject=subject,
            subject_type=subject_type,
            predicted_profit_impact=profit_impact,
            predicted_drawdown_impact=drawdown_impact,
            predicted_sharpe_impact=sharpe_impact,
            predicted_stability_impact=stability_impact,
            confidence=confidence,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            self._predictions[pred_id] = pred
        return asdict(pred)

    def all_predictions(self, limit: int = 50) -> list:
        with self._lock:
            items = list(self._predictions.values())
        items.sort(key=lambda x: x.created_at, reverse=True)
        return [asdict(p) for p in items[:limit]]

    def prediction_accuracy_report(self) -> dict:
        # Placeholder — requires actuals comparison once trade history available
        return {
            "status": "PENDING_ACTUALS",
            "note": "Accuracy comparison requires 50+ resolved predictions",
            "total_predictions": len(self._predictions),
        }


impact_predictor = ImpactPredictor()
