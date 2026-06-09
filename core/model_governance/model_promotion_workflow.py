"""Model Promotion Workflow — manages model stage transitions."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal


ModelStage = Literal["EXPERIMENTAL", "STAGING", "PRODUCTION", "DEPRECATED", "RETIRED"]

VALID_TRANSITIONS = {
    "EXPERIMENTAL": "STAGING",
    "STAGING": "PRODUCTION",
    "PRODUCTION": "DEPRECATED",
    "DEPRECATED": "RETIRED",
}


@dataclass
class PromotionRecord:
    promotion_id: str
    model_id: str
    from_stage: str
    to_stage: str
    approved: bool
    reason: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ModelPromotionWorkflow:
    def __init__(self):
        self._lock = threading.RLock()
        self._history: List[PromotionRecord] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"PRO-{self._counter:03d}"

    def request_promotion(self, model_id: str, target_stage: ModelStage) -> dict:
        from core.model_governance.model_registry import model_registry
        with self._lock:
            model = model_registry.get(model_id)
            if model is None:
                return {"approved": False, "reason": f"Model {model_id} not found"}
            expected_next = VALID_TRANSITIONS.get(model.stage)
            if expected_next != target_stage:
                reason = f"Invalid transition {model.stage} → {target_stage}; expected {expected_next}"
                rec = PromotionRecord(self._next_id(), model_id, model.stage, target_stage, False, reason)
                self._history.append(rec)
                return {"approved": False, "reason": reason}
            model.stage = target_stage
            reason = f"Approved: {model.stage} → {target_stage}"
            rec = PromotionRecord(self._next_id(), model_id, model.stage, target_stage, True, reason)
            self._history.append(rec)
            return {"approved": True, "reason": reason}

    def promotion_history(self) -> List[dict]:
        with self._lock:
            return [vars(r) for r in self._history]


model_promotion_workflow = ModelPromotionWorkflow()
