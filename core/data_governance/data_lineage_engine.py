"""Data Lineage Engine — tracks data flow between datasets."""
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class LineageRecord:
    lineage_id: str
    source_dataset: str
    target_dataset: str
    transformation: str
    recorded_at: datetime = field(default_factory=datetime.utcnow)


class DataLineageEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: List[LineageRecord] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"LIN-{self._counter:03d}"

    def record_lineage(self, source: str, target: str, transformation: str) -> LineageRecord:
        with self._lock:
            rec = LineageRecord(
                lineage_id=self._next_id(),
                source_dataset=source,
                target_dataset=target,
                transformation=transformation,
            )
            self._records.append(rec)
            return rec

    def upstream_of(self, dataset_name: str) -> List[dict]:
        with self._lock:
            return [vars(r) for r in self._records if r.target_dataset == dataset_name]

    def downstream_of(self, dataset_name: str) -> List[dict]:
        with self._lock:
            return [vars(r) for r in self._records if r.source_dataset == dataset_name]

    def lineage_graph(self) -> List[dict]:
        with self._lock:
            return [vars(r) for r in self._records]


data_lineage_engine = DataLineageEngine()
