"""Model Registry — registry of analytical/ML models."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal


ModelStage = Literal["EXPERIMENTAL", "STAGING", "PRODUCTION", "DEPRECATED", "RETIRED"]


@dataclass
class ModelRecord:
    model_id: str
    name: str
    model_type: str
    stage: ModelStage
    version: str
    registered_at: datetime = field(default_factory=datetime.utcnow)


class ModelRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._models: List[ModelRecord] = []
        self._counter = 0
        self._seed()

    def _next_id(self) -> str:
        self._counter += 1
        return f"MDL-{self._counter:03d}"

    def _seed(self):
        for name, model_type, stage, version in [
            ("RL_Strategy_Engine", "REINFORCEMENT_LEARNING", "PRODUCTION", "1.0.0"),
            ("ETE_Truth_Scorer", "SCORING", "PRODUCTION", "1.0.0"),
            ("Regime_Classifier", "CLASSIFICATION", "STAGING", "0.9.0"),
        ]:
            self._models.append(ModelRecord(
                model_id=self._next_id(),
                name=name,
                model_type=model_type,
                stage=stage,
                version=version,
            ))

    def register(self, name: str, model_type: str, stage: ModelStage, version: str) -> ModelRecord:
        with self._lock:
            rec = ModelRecord(
                model_id=self._next_id(),
                name=name,
                model_type=model_type,
                stage=stage,
                version=version,
            )
            self._models.append(rec)
            return rec

    def by_stage(self, stage: ModelStage) -> List[dict]:
        with self._lock:
            return [vars(m) for m in self._models if m.stage == stage]

    def registry_summary(self) -> dict:
        with self._lock:
            summary: dict = {}
            for m in self._models:
                summary[m.stage] = summary.get(m.stage, 0) + 1
            return {"total_models": len(self._models), "by_stage": summary}

    def get(self, model_id: str):
        with self._lock:
            return next((m for m in self._models if m.model_id == model_id), None)


model_registry = ModelRegistry()
