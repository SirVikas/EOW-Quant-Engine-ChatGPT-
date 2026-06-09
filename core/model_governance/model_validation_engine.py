"""Model Validation Engine — validates models before promotion."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal, Optional


ValidationType = Literal["BACKTEST", "SHADOW", "STRESS"]
ValidationOutcome = Literal["PASS", "FAIL"]


@dataclass
class ValidationRecord:
    validation_id: str
    model_id: str
    validation_type: ValidationType
    outcome: ValidationOutcome
    metrics: dict
    validated_at: datetime = field(default_factory=datetime.utcnow)


class ModelValidationEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: List[ValidationRecord] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"VAL-{self._counter:03d}"

    def validate(self, model_id: str, validation_type: ValidationType, outcome: ValidationOutcome, metrics: dict) -> ValidationRecord:
        with self._lock:
            rec = ValidationRecord(
                validation_id=self._next_id(),
                model_id=model_id,
                validation_type=validation_type,
                outcome=outcome,
                metrics=metrics,
            )
            self._records.append(rec)
            return rec

    def validations_for(self, model_id: str) -> List[dict]:
        with self._lock:
            return [vars(r) for r in self._records if r.model_id == model_id]

    def last_validation(self, model_id: str) -> Optional[dict]:
        with self._lock:
            matches = [r for r in self._records if r.model_id == model_id]
            return vars(matches[-1]) if matches else None


model_validation_engine = ModelValidationEngine()
