"""Data Catalog — registry of datasets with sensitivity classification."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal


SensitivityLevel = Literal["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"]


@dataclass
class DatasetRecord:
    dataset_id: str
    name: str
    owner: str
    domain: str
    sensitivity: SensitivityLevel
    registered_at: datetime = field(default_factory=datetime.utcnow)


class DataCatalog:
    def __init__(self):
        self._lock = threading.RLock()
        self._datasets: List[DatasetRecord] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"DS-{self._counter:03d}"

    def register(self, name: str, owner: str, domain: str, sensitivity: SensitivityLevel) -> DatasetRecord:
        with self._lock:
            rec = DatasetRecord(
                dataset_id=self._next_id(),
                name=name,
                owner=owner,
                domain=domain,
                sensitivity=sensitivity,
            )
            self._datasets.append(rec)
            return rec

    def all_datasets(self) -> List[dict]:
        with self._lock:
            return [vars(d) for d in self._datasets]

    def by_sensitivity(self, level: SensitivityLevel) -> List[dict]:
        with self._lock:
            return [vars(d) for d in self._datasets if d.sensitivity == level]

    def catalog_summary(self) -> dict:
        with self._lock:
            summary: dict = {}
            for d in self._datasets:
                summary[d.sensitivity] = summary.get(d.sensitivity, 0) + 1
            return {"total_datasets": len(self._datasets), "by_sensitivity": summary}


data_catalog = DataCatalog()
