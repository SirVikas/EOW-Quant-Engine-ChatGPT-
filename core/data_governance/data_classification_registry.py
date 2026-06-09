"""Data Classification Registry — master data governance engine."""
import threading
from typing import Literal


SensitivityLevel = Literal["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"]


class DataClassificationRegistry:
    def __init__(self):
        self._lock = threading.RLock()

    def governance_report(self) -> dict:
        from core.data_governance.data_catalog import data_catalog
        from core.data_governance.data_quality_monitor import data_quality_monitor
        from core.data_governance.data_retention_engine import data_retention_engine
        from core.data_governance.data_lineage_engine import data_lineage_engine

        with self._lock:
            catalog_summary = data_catalog.catalog_summary()
            retention_summary = data_retention_engine.retention_summary()
            lineage_count = len(data_lineage_engine.lineage_graph())
            failing = data_quality_monitor.failing_datasets()

            return {
                "total_datasets": catalog_summary["total_datasets"],
                "quality_summary": {"failing_datasets": failing},
                "retention_compliance": retention_summary,
                "lineage_coverage": {"total_lineage_records": lineage_count},
            }

    def classify(self, dataset_name: str, sensitivity: SensitivityLevel) -> dict:
        from core.data_governance.data_catalog import data_catalog
        with self._lock:
            matches = [d for d in data_catalog.all_datasets() if d["name"] == dataset_name]
            return {"dataset_name": dataset_name, "sensitivity": sensitivity, "updated": len(matches) > 0}


data_classification_registry = DataClassificationRegistry()
